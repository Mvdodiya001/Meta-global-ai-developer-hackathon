"""T4.5: real DB-backed API router (contract v1, DATA_MODEL_API §7).

Included instead of the stub router when `API_STUB != 1`. Every handler
reads the database on each request through `default_db_path()`, so tests
point it at a scratch file with `CLAUSETRACE_DB`. Model calls (extract,
claims) go through the gateway; replay mode serves the demo cassettes.
Handlers are `async def` so SQLite stays on one thread; the blocking
SQLAlchemy calls are short demo queries.
"""

import base64
import binascii
import functools
import re
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from fastapi import APIRouter, BackgroundTasks, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app import models, schemas
from app.agent import claims, scan, tools, transcribe
from app.agent import loop as loop_agent
from app.core.errors import (
    CassetteMissing,
    ClaimError,
    ExtractionError,
    LiveCallsBlocked,
    LLMRequestFailed,
    MemoryServiceError,
    RuleCardError,
    SourceUnavailable,
    ToolError,
)
from app.db import default_db_path, init_db
from app.modules.intake import jobs as intake_jobs
from app.modules.intake import pdf as pdf_intake
from app.services import counterfactual as counterfactual_service
from app.services import graph, impact, memory, premises, reverify, seed, sources

router = APIRouter()

CASSETTES_DIR = Path(__file__).resolve().parents[2] / "corpus" / "cassettes"

_engines: dict[str, Engine] = {}


def _utcnow() -> str:
    """Current UTC time in ISO-8601 (T4.5)."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    """One prefixed random id for API-created rows (T4.5)."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _engine_for(path: str) -> Engine:
    """Cache one engine per database path (T4.5).

    Uses `init_db`, not bare `get_engine`: booting the server must also
    create missing tables and heal additive columns on an older demo file
    (otherwise a stale file 500s on INSERT).
    """
    engine = _engines.get(path)
    if engine is None:
        engine = init_db(path)
        _engines[path] = engine
    return engine


def db_session() -> Any:
    """Per-request session on the configured database (T4.5)."""
    session = sessionmaker(bind=_engine_for(str(default_db_path())), future=True)()
    try:
        yield session
    finally:
        session.close()


def _error(status: int, code: str, message: str) -> JSONResponse:
    """§7 error envelope (T4.5)."""
    return JSONResponse(
        status_code=status, content={"error": {"code": code, "message": message}}
    )


def endpoint(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Map typed service errors to the §7 error envelope (T4.5)."""

    @functools.wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await fn(*args, **kwargs)
        except SourceUnavailable as exc:
            return _error(404, "SOURCE_UNAVAILABLE", str(exc))
        except MemoryServiceError as exc:
            if str(exc).startswith("unknown"):
                return _error(404, "NOT_FOUND", str(exc))
            return _error(400, "DECISION_REJECTED", str(exc))
        except (RuleCardError, ClaimError, ExtractionError, transcribe.TranscribeError) as exc:
            return _error(400, type(exc).__name__, str(exc))
        except ToolError as exc:
            if exc.code.startswith("unknown"):
                return _error(404, "NOT_FOUND", str(exc))
            return _error(400, exc.code.upper(), str(exc))
        except (CassetteMissing, LLMRequestFailed, LiveCallsBlocked):
            # Code stays for machines; the message is for the lawyer.
            return _error(
                502,
                "MODEL_UNAVAILABLE",
                "This question is not in the prepared set for the offline "
                "demo. Ask one of the prepared questions, or run the "
                "server in live mode.",
            )
        except ValueError as exc:
            return _error(400, "BAD_REQUEST", str(exc))

    return wrapper


def _finding_state(session: Session, finding_id: str) -> str:
    """Display state: SUPERSEDED wins over STALE wins over CURRENT (T4.5)."""
    states = {
        str(row.state)
        for row in session.execute(
            sa.select(models.FindingEvent).where(
                models.FindingEvent.finding_id == finding_id
            )
        )
        .scalars()
        .all()
    }
    for state in ("SUPERSEDED", "REJECTED", "REVIEWED", "STALE", "CURRENT"):
        if state in states:
            return state
    return "CURRENT"


def _ai_draft_label(session: Session, finding_id: str) -> str:
    """Disclaimer badge text for a finding (T4.5)."""
    reviewed = session.execute(
        sa.select(models.FindingEvent.id).where(
            models.FindingEvent.finding_id == finding_id,
            models.FindingEvent.state == "REVIEWED",
        )
    ).first()
    if reviewed is not None:
        return "Reviewed by lawyer"
    return "AI draft — not yet reviewed"


def _challenger_payload(session: Session, finding_id: str) -> dict[str, Any] | None:
    """Echo the stored second-pass review, if the finding has one (ask-frontend).

    `blocking` is derived from the stored objection severities, the same rule
    the challenger uses when it builds its verdict.
    """
    row = (
        session.execute(
            sa.select(models.ChallengerReport)
            .where(models.ChallengerReport.finding_id == finding_id)
            .order_by(models.ChallengerReport.created_at.desc())
        )
        .scalars()
        .first()
    )
    if row is None:
        return None
    objections = list(row.objections_json or [])
    return {
        "model": row.model,
        "blocking": any(
            isinstance(item, dict) and item.get("severity") == "blocking"
            for item in objections
        ),
        "objections": objections,
    }


STATUS_LABELS = {
    "FOLLOWS": "Meets the requirement — on the facts and law listed below",
    "RULED_OUT": "Does not meet the requirement, on the material listed",
    "UNKNOWN": "Cannot be determined from the available material",
    "REQUIRES_REVIEW": "Needs your review before it can be relied on",
    "CONFLICTING": "Two readings of the law conflict — your call",
}

TRUST_LABELS = {
    "lawyer_confirmed": "Confirmed by you",
    "document_extracted": "Taken from the document",
    "ai_inferred": "Proposed — not yet approved by you",
    "disputed": "Disputed by you",
}

STALE_LABEL = "Needs re-check: the law it relied on has changed"

REASON_LABELS = {
    "STALE": STALE_LABEL,
    "CONFLICTING": STATUS_LABELS["CONFLICTING"],
}


def _trust_label(trust_class: str) -> str:
    """Lawyer wording for one trust class (contract v9)."""
    return TRUST_LABELS.get(trust_class, trust_class)


def _section_text(key: str) -> str:
    """Section token from a provision key, e.g. s8(6) → 's 8(6)' (v9)."""
    token = key.rsplit("_", 1)[-1] if "_" in key else key
    if len(token) > 1 and token[0] in "sr" and token[1].isdigit():
        return f"{token[0]} {token[1:]}"
    return token


def _clause_ref_for_claim(session: Session, claim_id: str) -> str:
    """Clause ref a claim targets, for display beside finding ids (v9)."""
    claim = session.get(models.Claim, claim_id)
    clause = session.get(models.Clause, claim.clause_id) if claim is not None else None
    return str(clause.ref) if clause is not None else ""


def _display_fields(session: Session, finding: models.Finding) -> dict[str, Any]:
    """Human display fields beside the machine fields (contract v9).

    Everything here is derived from stored rows: clause quote from the
    claim's clause, section quote/label from the first cited rule card's
    provision and its law version, and one line per premise fact. The
    machine fields (ids, proof JSON, hashes) are untouched.
    """
    claim = session.get(models.Claim, finding.claim_id)
    clause = session.get(models.Clause, claim.clause_id) if claim is not None else None
    card_ids = list(finding.rule_card_ids_json or [])
    if not card_ids:
        card_ids = [
            str(edge.dst_id)
            for edge in session.execute(
                sa.select(models.Edge).where(
                    models.Edge.src_type == "finding",
                    models.Edge.src_id == finding.id,
                    models.Edge.rel == "DEPENDS_ON",
                    models.Edge.dst_type == "rule_card",
                )
            ).scalars().all()
        ]
    section_label = ""
    section_quote = ""
    law_version_label = ""
    law_version_date = ""
    version: models.SourceVersion | None = None
    if card_ids:
        card = session.get(models.RuleCard, card_ids[0])
        provision = (
            session.get(models.Provision, card.provision_id) if card is not None else None
        )
        if provision is not None:
            section_quote = str(provision.text)
            version = session.get(models.SourceVersion, provision.source_version_id)
            source = (
                session.get(models.Source, version.source_id) if version is not None else None
            )
            title = str(source.title) if source is not None else ""
            section = _section_text(str(provision.key))
            section_label = f"{title}, {section}" if title else section
    if version is None:
        version_ids = list(finding.source_version_ids_json or [])
        if version_ids:
            version = session.get(models.SourceVersion, version_ids[0])
    if version is not None:
        source = session.get(models.Source, version.source_id)
        title = str(source.title) if source is not None else ""
        label = f"version {version.version_label}"
        law_version_label = f"{title}, {label}" if title else label
        law_version_date = str(version.effective_from)
    fact_lines = []
    for fact_id in list(finding.premise_ids_json or []):
        fact = session.get(models.Fact, fact_id)
        if fact is None:
            continue
        review = session.execute(
            sa.select(models.Review)
            .where(models.Review.item_type == "fact", models.Review.item_id == fact_id)
            .order_by(models.Review.created_at.desc())
        ).scalars().first()
        fact_lines.append(
            {
                "label": str(fact.statement),
                "trust_label": _trust_label(str(fact.trust_class)),
                "confirmed_by": str(review.reviewer) if review is not None else None,
            }
        )
    return {
        "status_label": STATUS_LABELS.get(str(finding.status), str(finding.status)),
        "clause_ref": str(clause.ref) if clause is not None else "",
        "clause_quote": str(clause.text) if clause is not None else "",
        "section_label": section_label,
        "section_quote": section_quote,
        "law_version_label": law_version_label,
        "law_version_date": law_version_date,
        "fact_lines": fact_lines,
    }


def _finding_payload(session: Session, finding: models.Finding) -> dict[str, Any]:
    """Serialize one finding against the v1 Finding schema (T4.5)."""
    proof = finding.proof_json if isinstance(finding.proof_json, dict) else {}
    report = finding.checker_report_json
    return {
        "id": finding.id,
        "claim_id": finding.claim_id,
        "version_no": finding.version_no,
        "status": finding.status,
        **_display_fields(session, finding),
        "confidence_band": finding.confidence_band,
        "proof": proof,
        "as_of": finding.as_of,
        "source_version_ids": list(finding.source_version_ids_json or []),
        "premise_ids": list(finding.premise_ids_json or []),
        "rule_card_ids": list(finding.rule_card_ids_json or []),
        "checker_report": dict(report) if isinstance(report, dict) else None,
        "challenger_report": _challenger_payload(session, str(finding.id)),
        "run_id": finding.run_id or "",
        "created_at": finding.created_at,
        "supersedes_finding_id": finding.supersedes_finding_id,
        "state": _finding_state(session, str(finding.id)),
        "ai_draft_label": _ai_draft_label(session, str(finding.id)),
    }


def _require_matter(session: Session, matter_id: str) -> models.Matter:
    """Fetch a matter or raise a 404 error (T4.5)."""
    matter = session.get(models.Matter, matter_id)
    if matter is None:
        raise SourceUnavailable(f"unknown matter: {matter_id}")
    return matter


@router.get("/api/matters/{id}", response_model=schemas.Matter)
@endpoint
async def get_matter(id: str, session: Session = Depends(db_session)) -> Any:
    """Matter plus context panel (F18)."""
    matter = _require_matter(session, id)
    rows = session.execute(
        sa.select(models.MatterContext)
        .where(models.MatterContext.matter_id == id)
        .order_by(models.MatterContext.id)
    ).scalars().all()
    return {
        "id": matter.id,
        "client_name": matter.client_name,
        "title": matter.title,
        "context": [
            {
                "id": row.id,
                "matter_id": row.matter_id,
                "kind": row.kind,
                "title": row.title,
                "due_at": row.due_at,
                "source_label": row.source_label,
            }
            for row in rows
        ],
    }


@router.get("/api/matters/{id}/documents", response_model=schemas.DocumentList)
@endpoint
async def list_documents(id: str, session: Session = Depends(db_session)) -> Any:
    """Document list for a matter (F3)."""
    _require_matter(session, id)
    rows = session.execute(
        sa.select(models.Document)
        .where(models.Document.matter_id == id)
        .order_by(models.Document.id)
    ).scalars().all()
    return {
        "documents": [
            {"id": row.id, "matter_id": row.matter_id, "title": row.title, "kind": row.kind}
            for row in rows
        ]
    }


def _latest_version(session: Session, document_id: str) -> models.DocumentVersion | None:
    """Newest document version by creation time (T4.5)."""
    return session.execute(
        sa.select(models.DocumentVersion)
        .where(models.DocumentVersion.document_id == document_id)
        .order_by(models.DocumentVersion.created_at.desc(), models.DocumentVersion.id.desc())
    ).scalars().first()


@router.get("/api/documents/{id}/clauses", response_model=schemas.ClauseList)
@endpoint
async def list_clauses(id: str, session: Session = Depends(db_session)) -> Any:
    """Clauses of the latest document version (F3)."""
    if session.get(models.Document, id) is None:
        raise SourceUnavailable(f"unknown document: {id}")
    version = _latest_version(session, id)
    rows = (
        session.execute(
            sa.select(models.Clause)
            .where(models.Clause.document_version_id == version.id)
            .order_by(models.Clause.id)
        ).scalars().all()
        if version is not None
        else []
    )
    return {
        "clauses": [
            {
                "id": row.id,
                "document_version_id": row.document_version_id,
                "ref": row.ref,
                "heading": row.heading,
                "text": row.text,
                "span_start": row.span_start,
                "span_end": row.span_end,
            }
            for row in rows
        ]
    }


@router.get("/api/matters/{id}/facts", response_model=schemas.FactList)
@endpoint
async def list_facts(id: str, session: Session = Depends(db_session)) -> Any:
    """Facts with trust classes (F8)."""
    _require_matter(session, id)
    rows = session.execute(
        sa.select(models.Fact)
        .where(models.Fact.matter_id == id)
        .order_by(models.Fact.id)
    ).scalars().all()
    return {
        "facts": [
            {
                "id": row.id,
                "matter_id": row.matter_id,
                "clause_id": row.clause_id,
                "statement": row.statement,
                "structured": dict(row.structured_json or {}),
                "origin": row.origin,
                "trust_class": row.trust_class,
                "trust_label": _trust_label(str(row.trust_class)),
                "created_at": row.created_at,
            }
            for row in rows
        ]
    }


def _reviewer(body: schemas.FactActionBody) -> str:
    """Lawyer identity for trust actions (T4.5)."""
    return body.reviewer or "lawyer"


@router.post("/api/facts/{id}/approve", response_model=schemas.FactAction)
@endpoint
async def approve_fact(
    id: str, body: schemas.FactActionBody | None = None, session: Session = Depends(db_session)
) -> Any:
    """Lawyer approve: new lawyer_confirmed row (F15)."""
    _ = body
    new = premises.approve_fact(
        session, fact_id=id, reviewer=_reviewer(body or schemas.FactActionBody())
    )
    return {"fact_id": new.id, "trust_class": new.trust_class, "supersedes_id": new.supersedes_id}


@router.post("/api/facts/{id}/challenge", response_model=schemas.FactAction)
@endpoint
async def challenge_fact(
    id: str, body: schemas.FactActionBody | None = None, session: Session = Depends(db_session)
) -> Any:
    """Lawyer challenge: new disputed row, dependents staled (F15)."""
    payload = body or schemas.FactActionBody()
    new = premises.challenge_fact(
        session, fact_id=id, reason=payload.reason or "", reviewer=_reviewer(payload)
    )
    return {"fact_id": new.id, "trust_class": new.trust_class, "supersedes_id": new.supersedes_id}


@router.post("/api/facts/{id}/reject", response_model=schemas.FactAction)
@endpoint
async def reject_fact(
    id: str, body: schemas.FactActionBody | None = None, session: Session = Depends(db_session)
) -> Any:
    """Lawyer reject: new disputed row, dependents staled (F15)."""
    payload = body or schemas.FactActionBody()
    new = premises.reject_fact(
        session, fact_id=id, reason=payload.reason or "", reviewer=_reviewer(payload)
    )
    return {"fact_id": new.id, "trust_class": new.trust_class, "supersedes_id": new.supersedes_id}


@router.post("/api/documents/{id}/extract", response_model=schemas.ExtractResult)
@endpoint
async def extract_document(
    id: str, body: dict[str, Any] | None = None, session: Session = Depends(db_session)
) -> Any:
    """Run extraction and persist a new version with clauses + facts (F3)."""
    _ = body
    document = session.get(models.Document, id)
    if document is None:
        raise SourceUnavailable(f"unknown document: {id}")
    if _latest_version(session, id) is None:
        raise SourceUnavailable(f"document {id} has no versions")
    stored = intake_jobs.extract_and_store(session, id, CASSETTES_DIR)
    return {
        "clauses": stored["clauses"],
        "facts": [
            {**fact, "trust_label": _trust_label(str(fact["trust_class"]))}
            for fact in stored["facts"]
        ],
    }


_CLAUSE_REF_RE = re.compile(r"\bclause\s+(\d+(?:\.\d+)?)\b", re.IGNORECASE)


def _resolve_clause(
    session: Session, clause: models.Clause, question: str
) -> models.Clause:
    """Target the clause the question names, when it names one (ask-502).

    The loop prompt embeds the target clause text verbatim, so a claim
    stored against the wrong clause can never replay (502) and any proof
    would be about the wrong text. An explicit "clause <ref>" in the
    question is authoritative: resolve it inside the same document
    version. No ref (or an unknown ref) keeps the caller's clause.
    """
    match = _CLAUSE_REF_RE.search(question)
    if match is None or match.group(1) == clause.ref:
        return clause
    target = session.execute(
        sa.select(models.Clause).where(
            models.Clause.document_version_id == clause.document_version_id,
            models.Clause.ref == match.group(1),
        )
    ).scalars().first()
    return target if target is not None else clause


def _run_job_later(job_id: str) -> None:
    """Background worker entry: fresh session, job records its outcome (P3)."""
    session = sessionmaker(bind=_engine_for(str(default_db_path())), future=True)()
    try:
        intake_jobs.process_job(session, job_id, CASSETTES_DIR)
    finally:
        session.close()


@router.post("/api/matters/{id}/documents/upload", response_model=schemas.UploadResult)
@endpoint
async def upload_document(
    id: str,
    body: schemas.UploadDocumentRequest,
    background: BackgroundTasks,
    session: Session = Depends(db_session),
) -> Any:
    """Store an uploaded document and queue its extraction job (P3).

    Text is decoded directly; PDFs go through the page pipeline (text
    layer first, vision for image-only pages). Extraction itself runs
    in the background job; poll GET /api/jobs/{id}.
    """
    _require_matter(session, id)
    try:
        raw = base64.b64decode(body.file_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("file_base64 is not valid base64") from exc
    upload_input_b64: str | None = None
    if body.media_type == "application/pdf":
        classified = pdf_intake.classify_pages(raw)
        if not classified:
            raise ValueError("the uploaded file produced no text")
        text_pages = sum(1 for page in classified if page.source == "text")
        if text_pages == len(classified):
            # All text: deterministic path still resolves synchronously.
            text = "\n\n".join(page.text for page in classified)
        else:
            # Mixed/scanned: transcription happens in the worker with
            # per-page progress; store a placeholder version meanwhile.
            text = "pending transcription"
            upload_input_b64 = body.file_base64
    elif (
        body.media_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        from app.modules.intake import docx as docx_intake

        text, _spans = seed.build_document(docx_intake.docx_to_clauses(raw))
    elif body.media_type == "application/msword":
        from app.modules.intake import docx as docx_intake

        docx_intake.reject_legacy_doc()
    elif body.media_type == "text/plain":
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("text upload must be UTF-8") from exc
    else:
        raise ValueError(f"unsupported media type: {body.media_type}")
    if body.media_type != "application/pdf" and not text.strip():
        raise ValueError("the uploaded file produced no text")
    if text.strip():
        # Contract-shaped text is stored as the built document text (the
        # same normalization the seed applies), so extraction sees clauses.
        try:
            built, _spans = seed.build_document(seed.parse_contract(text))
            text = built
        except Exception:
            pass  # not contract-shaped; store raw and let the job decide
    now = _utcnow()
    document_id = _new_id("DOC")
    session.add(
        models.Document(id=document_id, matter_id=id, title=body.title, kind="upload")
    )
    session.add(
        models.DocumentVersion(
            id=_new_id("DV"),
            document_id=document_id,
            text=text,
            sha256=sources.sha256_text(text),
            created_at=now,
        )
    )
    session.commit()
    job = intake_jobs.create_job(
        session,
        kind="document_extract",
        matter_id=id,
        document_id=document_id,
        input_b64=upload_input_b64,
    )
    background.add_task(_run_job_later, str(job.id))
    return {"document_id": document_id, "job_id": str(job.id), "status": str(job.status)}


@router.get("/api/documents/{id}/pages", response_model=schemas.DocumentPages)
@endpoint
async def document_pages(id: str, session: Session = Depends(db_session)) -> Any:
    """Per-page origins from the latest completed intake job (P-C).

    Lawyers use this to spot-check transcribed pages: `text` pages were
    read from the file, `vision` pages were transcribed from a scan.
    Empty when no completed intake exists for the document.
    """
    if session.get(models.Document, id) is None:
        raise SourceUnavailable(f"unknown document: {id}")
    job = session.execute(
        sa.select(models.IntakeJob)
        .where(
            models.IntakeJob.document_id == id,
            models.IntakeJob.status == "done",
        )
        .order_by(models.IntakeJob.updated_at.desc(), models.IntakeJob.id.desc())
    ).scalars().first()
    pages: list[dict[str, object]] = []
    if job is not None and isinstance(job.result_json, dict):
        raw_pages = job.result_json.get("pages", [])
        if isinstance(raw_pages, list):
            pages = [
                {"page": item.get("page"), "source": item.get("source")}
                for item in raw_pages
                if isinstance(item, dict)
            ]
    return {"document_id": id, "pages": pages}


@router.get("/api/jobs/{id}", response_model=schemas.JobStatus)
@endpoint
async def get_job(id: str, session: Session = Depends(db_session)) -> Any:
    """One intake job's progress (P3)."""
    job = session.get(models.IntakeJob, id)
    if job is None:
        raise SourceUnavailable(f"unknown job: {id}")
    return {
        "id": job.id,
        "kind": job.kind,
        "status": job.status,
        "stage": job.stage,
        "document_id": job.document_id,
        "result": dict(job.result_json) if isinstance(job.result_json, dict) else None,
        "error": job.error,
    }


@router.post("/api/facts/{id}/correct", response_model=schemas.FactAction)
@endpoint
async def correct_fact(
    id: str, body: schemas.FactCorrectBody, session: Session = Depends(db_session)
) -> Any:
    """Lawyer correction: new fact row with edited wording, same trust (P3)."""
    new = premises.correct_fact(
        session, fact_id=id, statement=body.statement, reviewer=body.reviewer or "lawyer"
    )
    return {"fact_id": new.id, "trust_class": new.trust_class, "supersedes_id": new.supersedes_id}


@router.post("/api/scans", response_model=schemas.ScanResult)
@endpoint
async def scan_page(body: schemas.ScanRequest, session: Session = Depends(db_session)) -> Any:
    """Store one scanned page as a new document + clause + fact (T7.2).

    The transcription comes from Muse Spark image input through the
    gateway; the fact is stored `document_extracted` against the new
    document version, exactly like text extraction (F3).
    """
    _require_matter(session, body.matter_id)
    try:
        image_bytes = base64.b64decode(body.image_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("image_base64 is not valid base64") from exc
    result = scan.scan_page(
        image_bytes, media_type=body.media_type, cache_dir=CASSETTES_DIR, session=session
    )
    now = _utcnow()
    document_id = _new_id("DOC")
    version_id = _new_id("DV")
    clause_id = _new_id("CL")
    fact_id = _new_id("F")
    session.add(
        models.Document(
            id=document_id, matter_id=body.matter_id, title=body.title, kind="scan"
        )
    )
    session.add(
        models.DocumentVersion(
            id=version_id,
            document_id=document_id,
            text=result.text,
            sha256=sources.sha256_text(result.text),
            created_at=now,
        )
    )
    clause_payload = {
        "id": clause_id,
        "document_version_id": version_id,
        "ref": result.clause_ref,
        "heading": result.heading,
        "text": result.text,
        "span_start": 0,
        "span_end": len(result.text),
    }
    session.add(models.Clause(**clause_payload))
    fact_payload = {
        "id": fact_id,
        "matter_id": body.matter_id,
        "clause_id": clause_id,
        "statement": result.fact_statement,
        "structured": {"clause_ref": result.clause_ref},
        "origin": "extracted",
        "trust_class": "document_extracted",
        "trust_label": _trust_label("document_extracted"),
        "created_at": now,
    }
    session.add(
        models.Fact(
            id=fact_id,
            matter_id=body.matter_id,
            clause_id=clause_id,
            statement=result.fact_statement,
            structured_json={"clause_ref": result.clause_ref},
            origin="extracted",
            trust_class="document_extracted",
            created_at=now,
        )
    )
    session.commit()
    return {"document_id": document_id, "clause": clause_payload, "fact": fact_payload}


@router.post("/api/dictations", response_model=schemas.DictationResult)
@endpoint
async def create_dictation(
    body: schemas.DictationRequest, session: Session = Depends(db_session)
) -> Any:
    """Dictate a proposed fact: transcript stored ai_inferred (T7.1).

    The approval gate is the point: an `ai_inferred` fact can never be a
    proof premise (the checker rejects it) until a lawyer approves it via
    POST /api/facts/{id}/approve, which mints the lawyer_confirmed copy.
    """
    _require_matter(session, body.matter_id)
    if body.clause_id is not None and session.get(models.Clause, body.clause_id) is None:
        raise SourceUnavailable(f"unknown clause: {body.clause_id}")
    try:
        audio_bytes = base64.b64decode(body.audio_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("audio_base64 is not valid base64") from exc
    result = transcribe.transcribe_audio(audio_bytes, cache_dir=CASSETTES_DIR, session=session)
    if not result.transcript:
        raise ValueError("transcription produced no text")
    fact_id = _new_id("F")
    session.add(
        models.Fact(
            id=fact_id,
            matter_id=body.matter_id,
            clause_id=body.clause_id,
            statement=result.transcript,
            structured_json={"source": "voice_dictation"},
            origin="voice_dictation",
            trust_class="ai_inferred",
            created_at=_utcnow(),
        )
    )
    session.commit()
    return {
        "fact_id": fact_id,
        "transcript": result.transcript,
        "trust_class": "ai_inferred",
    }


@router.get("/api/admin/overview", response_model=schemas.AdminOverview)
@endpoint
async def admin_overview(session: Session = Depends(db_session)) -> Any:
    """Internal counts + spend for staff (P5; auth lands with Identity)."""
    from app.agent.budgets import spend_for_tenant

    tenant_id = "demo"
    findings = session.execute(
        sa.select(models.Finding.status, sa.func.count())
        .join(models.Claim, models.Finding.claim_id == models.Claim.id)
        .where(models.Claim.tenant_id == tenant_id)
        .group_by(models.Finding.status)
    ).all()
    facts = session.execute(
        sa.select(models.Fact.trust_class, sa.func.count())
        .where(models.Fact.tenant_id == tenant_id)
        .group_by(models.Fact.trust_class)
    ).all()
    jobs = session.execute(
        sa.select(models.IntakeJob.status, sa.func.count()).group_by(models.IntakeJob.status)
    ).all()
    matters = session.execute(
        sa.select(sa.func.count()).select_from(models.Matter).where(
            models.Matter.tenant_id == tenant_id
        )
    ).scalar() or 0
    return {
        "tenant_id": tenant_id,
        "matters": int(matters),
        "findings_by_status": {str(k): int(v) for k, v in findings},
        "facts_by_trust": {str(k): int(v) for k, v in facts},
        "spend_usd": spend_for_tenant(session, tenant_id),
        "jobs": {str(k): int(v) for k, v in jobs},
    }


@router.post("/api/auth/register", response_model=schemas.AuthResult)
@endpoint
async def register(body: schemas.RegisterRequest, session: Session = Depends(db_session)) -> Any:
    """Create an account and return a session token (Identity)."""
    from app.modules.identity import auth

    try:
        user = auth.register_user(
            session, email=body.email, password=body.password, name=body.name
        )
    except auth.AuthError as exc:
        return _error(400, "AUTH_FAILED", str(exc))
    return {
        "token": auth.issue_token(user),
        "email": user.email,
        "name": user.name,
        "tenant_id": user.tenant_id,
    }


@router.post("/api/auth/login", response_model=schemas.AuthResult)
@endpoint
async def login(body: schemas.LoginRequest, session: Session = Depends(db_session)) -> Any:
    """Sign in and return a session token (Identity)."""
    from app.modules.identity import auth

    try:
        user = auth.authenticate(session, email=body.email, password=body.password)
    except auth.AuthError as exc:
        return _error(401, "AUTH_FAILED", str(exc))
    return {
        "token": auth.issue_token(user),
        "email": user.email,
        "name": user.name,
        "tenant_id": user.tenant_id,
    }


@router.get("/api/me", response_model=schemas.AuthResult)
@endpoint
async def me(
    authorization: str | None = Header(default=None),
    session: Session = Depends(db_session),
) -> Any:
    """Who am I: resolve the bearer token (Identity)."""
    return _me(authorization, session)


def _me(authorization: str | None, session: Session) -> Any:
    """Token resolution shared by /api/me and tests (Identity)."""
    from app.modules.identity import auth

    if not authorization or not authorization.startswith("Bearer "):
        return _error(401, "AUTH_REQUIRED", "sign-in required")
    user = auth.verify_token(session, authorization.removeprefix("Bearer "))
    if user is None:
        return _error(401, "AUTH_REQUIRED", "sign-in required")
    return {"token": "", "email": user.email, "name": user.name, "tenant_id": user.tenant_id}


@router.post("/api/transcribe", response_model=schemas.TranscribeResult)
@endpoint
async def transcribe_only(
    body: schemas.DictationRequest, session: Session = Depends(db_session)
) -> Any:
    """Transcribe audio to text without storing a fact (dictation page)."""
    _require_matter(session, body.matter_id)
    try:
        audio_bytes = base64.b64decode(body.audio_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("audio_base64 is not valid base64") from exc
    result = transcribe.transcribe_audio(audio_bytes, cache_dir=CASSETTES_DIR, session=session)
    return {"transcript": result.transcript}


@router.post("/api/documents/{id}/clauses/{clause_id}/update", response_model=schemas.Clause)
@endpoint
async def update_clause(
    id: str,
    clause_id: str,
    body: schemas.ClauseUpdateRequest,
    session: Session = Depends(db_session),
) -> Any:
    """Store edited clause wording as a new document version (clauses page).

    Nothing is edited in place: the new version carries every clause,
    with the target clause's text (and heading, if given) replaced and
    spans rebuilt. Facts recorded against the old clause stay as they
    are; lawyers correct them in the control room.
    """
    if session.get(models.Document, id) is None:
        raise SourceUnavailable(f"unknown document: {id}")
    version = _latest_version(session, id)
    if version is None:
        raise SourceUnavailable(f"document {id} has no versions")
    rows = session.execute(
        sa.select(models.Clause)
        .where(models.Clause.document_version_id == version.id)
        .order_by(models.Clause.id)
    ).scalars().all()
    target = next((row for row in rows if str(row.id) == clause_id), None)
    if target is None:
        raise SourceUnavailable(f"unknown clause: {clause_id}")
    if not body.text.strip():
        raise ValueError("clause text must not be empty")
    triples = [
        (
            str(row.ref),
            body.heading if row.id == clause_id and body.heading else str(row.heading),
            body.text if row.id == clause_id else str(row.text),
        )
        for row in rows
    ]
    text, spans = seed.build_document(triples)
    now = _utcnow()
    if now <= str(version.created_at):
        from datetime import datetime, timedelta

        parsed = datetime.strptime(str(version.created_at), "%Y-%m-%dT%H:%M:%SZ")
        now = (parsed + timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_version = models.DocumentVersion(
        id=_new_id("DV"),
        document_id=id,
        text=text,
        sha256=sources.sha256_text(text),
        created_at=now,
    )
    session.add(new_version)
    for (ref, heading, clause_text), (start, end) in zip(triples, spans, strict=True):
        new_id = _new_id("CL")
        session.add(
            models.Clause(
                id=new_id,
                document_version_id=new_version.id,
                ref=ref,
                heading=heading,
                text=clause_text,
                span_start=start,
                span_end=end,
            )
        )
    session.commit()
    # Re-read the created target clause from the new version.
    created_row = session.execute(
        sa.select(models.Clause).where(
            models.Clause.document_version_id == new_version.id,
            models.Clause.ref == target.ref,
        )
    ).scalars().first()
    assert created_row is not None
    return {
        "id": created_row.id,
        "document_version_id": created_row.document_version_id,
        "ref": created_row.ref,
        "heading": created_row.heading,
        "text": created_row.text,
        "span_start": created_row.span_start,
        "span_end": created_row.span_end,
    }


@router.post("/api/claims", response_model=schemas.ClaimCreated)
@endpoint
async def create_claim(body: schemas.ClaimRequest, session: Session = Depends(db_session)) -> Any:
    """Structure a question, store the claim and open a run (F4, F5)."""
    if not body.clause_id or not body.question or not body.as_of:
        raise ValueError("clause_id, question and as_of are required")
    clause = session.get(models.Clause, body.clause_id)
    if clause is None:
        raise SourceUnavailable(f"unknown clause: {body.clause_id}")
    clause = _resolve_clause(session, clause, body.question)
    inventory = claims.default_inventory()
    draft = claims.structure_claim(
        body.question, inventory, body.as_of, session=session, cache_dir=CASSETTES_DIR
    )
    claim_id = _new_id("C")
    run_id = _new_id("RUN")
    session.add(
        models.Claim(
            id=claim_id,
            matter_id=_matter_for_document(session, clause),
            clause_id=clause.id,
            claim_type=draft.claim_type,
            params_json=dict(draft.params),
            question_text=draft.question_text,
            as_of=body.as_of,
            created_at=_utcnow(),
        )
    )
    session.add(
        models.Run(
            id=run_id,
            trigger="verify",
            claim_id=claim_id,
            started_at=_utcnow(),
        )
    )
    session.commit()
    if draft.claim_type not in memory.SUPPORTED_TYPES:
        # UNKNOWN questions have no proof to draft: the memory service
        # decides UNKNOWN directly (gate fix; the loop 502'd in replay).
        finding = memory.decide_finding(
            session,
            claim_id=claim_id,
            proof={
                "claim_id": claim_id,
                "as_of": body.as_of,
                "conclusion": "",
                "premises": [],
                "steps": [],
                "explanation": draft.explanation,
            },
            run_id=run_id,
            challenger_cache_dir=CASSETTES_DIR,
        )
        run_row = session.get(models.Run, run_id)
        if run_row is not None:
            run_row.ended_at = _utcnow()
            run_row.outcome = "unknown"
            session.commit()
        return {
            "claim_id": claim_id,
            "run_id": run_id,
            "finding_id": str(finding.id),
            "status": str(finding.status),
        }
    loop_result = loop_agent.run_verify(
        session,
        claim_id=claim_id,
        matter_id=_matter_for_document(session, clause),
        cache_dir=CASSETTES_DIR,
    )
    finding_id: str | None = None
    status: str | None = None
    if loop_result.accepted and loop_result.proof is not None:
        finding = memory.decide_finding(
            session,
            claim_id=claim_id,
            proof=loop_result.proof,
            run_id=loop_result.run_id,
            challenger_cache_dir=CASSETTES_DIR,
        )
        finding_id = str(finding.id)
        status = str(finding.status)
    # Return the loop's run, not the claim-open placeholder: the UI polls
    # this id for the tool trace and run status (integration fix).
    return {
        "claim_id": claim_id,
        "run_id": loop_result.run_id,
        "finding_id": finding_id,
        "status": status,
    }


def _matter_for_document(session: Session, clause: models.Clause) -> str:
    """Matter owning a clause through its document (T4.5)."""
    version = session.get(models.DocumentVersion, clause.document_version_id)
    document = session.get(models.Document, version.document_id) if version else None
    if document is None:
        raise SourceUnavailable(f"clause {clause.id} has no document")
    return str(document.matter_id)


def _run_status(run: models.Run) -> str:
    """Running while open, otherwise the stored outcome (T4.5)."""
    if run.ended_at is None:
        return "running"
    return str(run.outcome or "done")


@router.get("/api/runs/{id}", response_model=schemas.Run)
@endpoint
async def get_run(id: str, session: Session = Depends(db_session)) -> Any:
    """Run status (F5)."""
    run = session.get(models.Run, id)
    if run is None:
        raise SourceUnavailable(f"unknown run: {id}")
    return {
        "id": run.id,
        "trigger": run.trigger,
        "claim_id": run.claim_id,
        "status": _run_status(run),
    }


@router.get("/api/runs/{id}/events", response_model=schemas.RunEvents)
@endpoint
async def get_run_events(id: str, session: Session = Depends(db_session)) -> Any:
    """Tool-call trace for a run (F5)."""
    if session.get(models.Run, id) is None:
        raise SourceUnavailable(f"unknown run: {id}")
    rows = session.execute(
        sa.select(models.ToolCall)
        .where(models.ToolCall.run_id == id)
        .order_by(models.ToolCall.seq)
    ).scalars().all()
    return {
        "events": [
            {
                "seq": row.seq,
                "tool": row.tool,
                "args": dict(row.args_json or {}),
                "result": dict(row.result_json or {}),
                "ok": row.ok,
            }
            for row in rows
        ]
    }


def _latest_finding(session: Session, claim_id: str) -> models.Finding | None:
    """Highest-version finding for a claim (T4.5)."""
    return session.execute(
        sa.select(models.Finding)
        .where(models.Finding.claim_id == claim_id)
        .order_by(models.Finding.version_no.desc())
    ).scalars().first()


@router.get("/api/claims/{id}/current", response_model=schemas.Finding)
@endpoint
async def get_current_finding(id: str, session: Session = Depends(db_session)) -> Any:
    """Current (latest-version) finding for a claim (F7)."""
    if session.get(models.Claim, id) is None:
        raise SourceUnavailable(f"unknown claim: {id}")
    finding = _latest_finding(session, id)
    if finding is None:
        raise SourceUnavailable(f"claim {id} has no findings")
    return _finding_payload(session, finding)


@router.get("/api/claims/{id}/history", response_model=schemas.FindingHistory)
@endpoint
async def get_finding_history(id: str, session: Session = Depends(db_session)) -> Any:
    """All finding versions for a claim, newest first (F12)."""
    if session.get(models.Claim, id) is None:
        raise SourceUnavailable(f"unknown claim: {id}")
    rows = session.execute(
        sa.select(models.Finding)
        .where(models.Finding.claim_id == id)
        .order_by(models.Finding.version_no.desc())
    ).scalars().all()
    return {"versions": [_finding_payload(session, row) for row in rows]}


@router.get("/api/findings/{id}", response_model=schemas.Finding)
@endpoint
async def get_finding(id: str, session: Session = Depends(db_session)) -> Any:
    """Proof, traces and reports for one finding (F9)."""
    finding = session.get(models.Finding, id)
    if finding is None:
        raise SourceUnavailable(f"unknown finding: {id}")
    return _finding_payload(session, finding)


@router.post("/api/findings/{id}/review", response_model=schemas.ReviewResult)
@endpoint
async def review_finding(
    id: str, body: schemas.ReviewBody, session: Session = Depends(db_session)
) -> Any:
    """Lawyer review: approve/reject records an event; annotate only notes (F16)."""
    finding = session.get(models.Finding, id)
    if finding is None:
        raise SourceUnavailable(f"unknown finding: {id}")
    if body.action not in ("approve", "reject", "annotate"):
        raise ValueError("action must be approve, reject or annotate")
    reviewer = body.reviewer or "lawyer"
    session.add(
        models.Review(
            id=_new_id("RV"),
            item_type="finding",
            item_id=id,
            reason=body.note or "",
            status=body.action,
            reviewer=reviewer,
            note=None,
            created_at=_utcnow(),
        )
    )
    if body.action in ("approve", "reject"):
        state = "REVIEWED" if body.action == "approve" else "REJECTED"
        session.add(
            models.FindingEvent(
                id=_new_id("FE"),
                finding_id=id,
                state=state,
                reason=body.note,
                caused_by_type="lawyer",
                caused_by_id=reviewer,
                created_at=_utcnow(),
            )
        )
    session.commit()
    return {"finding_id": id, "state": _finding_state(session, id)}


@router.get("/api/sources", response_model=schemas.SourceList)
@endpoint
async def list_sources(session: Session = Depends(db_session)) -> Any:
    """Source registry (F1)."""
    rows = session.execute(sa.select(models.Source).order_by(models.Source.id)).scalars().all()
    return {
        "sources": [
            {
                "id": row.id,
                "key": row.key,
                "title": row.title,
                "publisher": row.publisher,
                "url": row.url,
                "jurisdiction": row.jurisdiction,
            }
            for row in rows
        ]
    }


@router.get("/api/sources/{id}/versions", response_model=schemas.SourceVersionList)
@endpoint
async def list_source_versions(id: str, session: Session = Depends(db_session)) -> Any:
    """Version registry for one source (F1)."""
    if session.get(models.Source, id) is None:
        raise SourceUnavailable(f"unknown source: {id}")
    rows = session.execute(
        sa.select(models.SourceVersion)
        .where(models.SourceVersion.source_id == id)
        .order_by(models.SourceVersion.id)
    ).scalars().all()
    return {
        "versions": [
            {
                "id": row.id,
                "source_id": row.source_id,
                "version_label": row.version_label,
                "published_on": row.published_on,
                "effective_from": row.effective_from,
                "effective_until": row.effective_until,
                "content_sha256": row.content_sha256,
                "is_simulated": bool(row.is_simulated),
                "supersedes_id": row.supersedes_id,
            }
            for row in rows
        ]
    }


def _provision_payload(row: models.Provision) -> dict[str, Any]:
    """Serialize one provision row (T4.5)."""
    return {
        "id": row.id,
        "source_version_id": row.source_version_id,
        "key": row.key,
        "text": row.text,
        "text_sha256": row.text_sha256,
        "effective_from": row.effective_from,
        "effective_until": row.effective_until,
    }


@router.get("/api/source-versions/{id}/diff", response_model=schemas.DiffResult)
@endpoint
async def diff_versions(
    id: str, against: str, session: Session = Depends(db_session)
) -> Any:
    """Side-by-side diff data between two versions (F11)."""
    current = session.get(models.SourceVersion, id)
    other = session.get(models.SourceVersion, against)
    if current is None:
        raise SourceUnavailable(f"unknown source version: {id}")
    if other is None:
        raise SourceUnavailable(f"unknown source version: {against}")
    before = impact.version_provisions(session, against)
    after = impact.version_provisions(session, id)
    diff = impact.diff_provisions(
        [impact.snapshot(row) for row in before],
        [impact.snapshot(row) for row in after],
    )
    changed_keys = sorted(set(diff["changed"]) | set(diff["added"]) | set(diff["removed"]))
    # F1: changed provisions lead both lists, so a before/after view shows
    # the amended section first instead of the first provision overall.
    # NOTE (F1): before/after stay in stored provision order; clients
    # round-trip these lists into ingest, whose content hash is
    # order-sensitive. Select the amended provision by changed_keys.
    return {
        "against": against,
        "current": id,
        "changed_keys": changed_keys,
        "before": [_provision_payload(row) for row in before],
        "after": [_provision_payload(row) for row in after],
    }


def _ingest_version_id(session: Session, source_id: str) -> str:
    """Next version id for a source (T4.5)."""
    count = session.execute(
        sa.select(sa.func.count())
        .select_from(models.SourceVersion)
        .where(models.SourceVersion.source_id == source_id)
    ).scalar()
    return f"{source_id}-v{(count or 0) + 1}"


@router.post("/api/sources/{id}/ingest", response_model=schemas.IngestResult)
@endpoint
async def ingest_source(
    id: str, body: schemas.IngestBody | None = None, session: Session = Depends(db_session)
) -> Any:
    """Store an inline new version and report its impact (F11)."""
    source = session.get(models.Source, id)
    if source is None:
        raise SourceUnavailable(f"unknown source: {id}")
    payload = body or schemas.IngestBody()
    if payload.fixture is not None or payload.url is not None:
        raise ValueError("only inline version objects are supported in v1")
    spec = payload.version
    if spec is None:
        raise ValueError("an inline version object is required")
    provisions: list[dict[str, str | None]] = []
    for item in spec.provisions:
        key = item.get("key")
        text = item.get("text")
        effective_from = item.get("effective_from")
        if not isinstance(key, str) or not isinstance(text, str) or not isinstance(
            effective_from, str
        ):
            raise ValueError("each provision needs key, text and effective_from")
        until = item.get("effective_until")
        provisions.append(
            {
                "key": key,
                "text": text,
                "sha": sources.sha256_text(text),
                "from": effective_from,
                "until": until if isinstance(until, str) else None,
            }
        )
    raw_text = "\n\n".join(str(item["text"]) for item in provisions)
    digest = sources.sha256_text(raw_text)
    same = session.execute(
        sa.select(models.SourceVersion.id).where(
            models.SourceVersion.source_id == id,
            models.SourceVersion.content_sha256 == digest,
        )
    ).scalar_one_or_none()
    if same is not None:
        impact.apply_version(session, str(same))
        return {"source_version_id": str(same), "impact_report_id": f"IMP-{same}"}
    current = session.execute(
        sa.select(models.SourceVersion.id).where(
            models.SourceVersion.source_id == id,
            models.SourceVersion.supersedes_id.is_(None),
        )
    ).scalars().all()
    supersedes = str(current[0]) if current else None
    version_id = _ingest_version_id(session, id)
    now = _utcnow()
    session.add(
        models.SourceVersion(
            id=version_id,
            source_id=id,
            version_label=spec.version_label,
            published_on=spec.published_on,
            effective_from=spec.effective_from,
            effective_until=None,
            retrieved_at=now,
            content_sha256=digest,
            raw_text=raw_text,
            is_simulated=False,
            supersedes_id=supersedes,
        )
    )
    for index, item in enumerate(provisions):
        session.add(
            models.Provision(
                id=f"{version_id}-P{index + 1:02d}",
                source_version_id=version_id,
                key=str(item["key"]),
                text=str(item["text"]),
                text_sha256=str(item["sha"]),
                effective_from=str(item["from"]),
                effective_until=item["until"] if isinstance(item["until"], str) else None,
            )
        )
    session.commit()
    impact.apply_version(session, version_id)
    return {"source_version_id": version_id, "impact_report_id": f"IMP-{version_id}"}


def _impact_version_id(impact_id: str) -> str:
    """Impact ids are IMP-prefixed version ids (T4.5)."""
    return impact_id[4:] if impact_id.startswith("IMP-") else impact_id


@router.get("/api/impact/{id}", response_model=schemas.ImpactReport)
@endpoint
async def get_impact(id: str, session: Session = Depends(db_session)) -> Any:
    """Impact report: findings with STALE events from one version (F11)."""
    version_id = _impact_version_id(id)
    version = session.get(models.SourceVersion, version_id)
    if version is None:
        raise SourceUnavailable(f"unknown impact: {id}")
    stale = session.execute(
        sa.select(models.FindingEvent).where(
            models.FindingEvent.state == "STALE",
            models.FindingEvent.caused_by_type == "source_version",
            models.FindingEvent.caused_by_id == version_id,
        )
    ).scalars().all()
    affected = []
    for event in stale:
        finding = session.get(models.Finding, event.finding_id)
        if finding is None or not graph.is_current_finding(session, str(finding.id)):
            continue
        affected.append(
            {
                "claim_id": finding.claim_id,
                "finding_id": finding.id,
                "state": "STALE",
                "status_label": STALE_LABEL,
                "clause_ref": _clause_ref_for_claim(session, str(finding.claim_id)),
            }
        )
    affected.sort(key=lambda item: str(item["finding_id"]))
    return {"id": f"IMP-{version_id}", "source_version_id": version_id, "affected": affected}


@router.post("/api/impact/{id}/reverify", response_model=schemas.ReverifyResult)
@endpoint
async def reverify_impact(
    id: str, body: schemas.ReverifyBody | None = None, session: Session = Depends(db_session)
) -> Any:
    """Re-run stale findings for one version with fresh lookups (F12)."""
    version_id = _impact_version_id(id)
    version = session.get(models.SourceVersion, version_id)
    if version is None:
        raise SourceUnavailable(f"unknown impact: {id}")
    payload = body or schemas.ReverifyBody()
    stale = session.execute(
        sa.select(models.FindingEvent).where(
            models.FindingEvent.state == "STALE",
            models.FindingEvent.caused_by_type == "source_version",
            models.FindingEvent.caused_by_id == version_id,
        )
    ).scalars().all()
    superseded: list[str] = []
    current: list[str] = []
    skipped: list[str] = []
    for event in stale:
        finding = session.get(models.Finding, event.finding_id)
        if finding is None or not graph.is_current_finding(session, str(finding.id)):
            continue
        proof = payload.proofs.get(str(finding.id))
        if proof is None:
            stored = finding.proof_json
            if not isinstance(stored, dict):
                # F1: never drop a stale row silently; it stays in the
                # reverify list and is reported here as skipped.
                skipped.append(str(finding.id))
                continue
            proof = stored
        run_id = _new_id("RUN")
        session.add(
            models.Run(
                id=run_id,
                trigger="reverify",
                claim_id=finding.claim_id,
                started_at=_utcnow(),
            )
        )
        session.commit()
        claim = session.get(models.Claim, finding.claim_id)
        matter_id = str(claim.matter_id) if claim is not None else ""
        tools.call_tool(
            session,
            run_id=run_id,
            matter_id=matter_id,
            tool="lookup_source",
            args={"source_id": version.source_id},
        )
        new = reverify.reverify_finding(
            session, finding_id=str(finding.id), proof=proof, run_id=run_id
        )
        superseded.append(str(finding.id))
        current.append(str(new.id))
    return {
        "superseded": sorted(superseded),
        "current": sorted(current),
        "skipped": sorted(skipped),
    }


def _graph_label(kind: str, row: Any) -> str:
    """Short human label for a graph node (T4.5)."""
    if kind == "finding":
        return f"{row.id} {row.status}"
    if kind == "fact":
        return str(row.statement)[:60]
    if kind == "rule_card":
        return f"{row.id} {row.claim_type}"
    if kind == "provision":
        return str(row.key)
    if kind == "source_version":
        label = str(row.version_label)
        return f"{label} SIMULATED" if row.is_simulated else label
    return str(row.id)


@router.get("/api/graph", response_model=schemas.GraphSlice)
@endpoint
async def get_graph(
    matter_id: str | None = None, focus: str | None = None, session: Session = Depends(db_session)
) -> Any:
    """Nodes + edges for React Flow, optionally focused (F10)."""
    if matter_id is None:
        raise ValueError("matter_id is required")
    _require_matter(session, matter_id)
    findings = session.execute(
        sa.select(models.Finding)
        .join(models.Claim, models.Finding.claim_id == models.Claim.id)
        .where(models.Claim.matter_id == matter_id)
    ).scalars().all()
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []
    seen_edges: set[tuple[str, str, str]] = set()

    def add_node(kind: str, row: Any) -> None:
        node_id = str(row.id)
        if node_id not in nodes:
            nodes[node_id] = {"id": node_id, "kind": kind, "label": _graph_label(kind, row)}

    def add_edge_view(src: str, dst: str, rel: str) -> None:
        if (src, dst, rel) not in seen_edges:
            seen_edges.add((src, dst, rel))
            edges.append({"src": src, "dst": dst, "rel": rel})

    for finding in findings:
        add_node("finding", finding)
        nodes[str(finding.id)]["state"] = _finding_state(session, str(finding.id))
        for edge in session.execute(
            sa.select(models.Edge).where(
                models.Edge.src_type == "finding",
                models.Edge.src_id == finding.id,
                models.Edge.rel == "DEPENDS_ON",
            )
        ).scalars().all():
            target: Any = None
            if edge.dst_type == "fact":
                target = session.get(models.Fact, edge.dst_id)
            elif edge.dst_type == "rule_card":
                target = session.get(models.RuleCard, edge.dst_id)
            if target is None:
                continue
            add_node(edge.dst_type, target)
            add_edge_view(str(finding.id), str(target.id), "DEPENDS_ON")
            if edge.dst_type == "rule_card":
                card = target
                provision = session.get(models.Provision, card.provision_id)
                if provision is not None:
                    add_node("provision", provision)
                    add_edge_view(str(card.id), str(provision.id), "DERIVED_FROM")
                    version = session.get(models.SourceVersion, provision.source_version_id)
                    if version is not None:
                        add_node("source_version", version)
                        add_edge_view(str(provision.id), str(version.id), "PART_OF")
    if focus is not None:
        if focus not in nodes:
            raise SourceUnavailable(f"unknown focus: {focus}")
        neighbours: dict[str, set[str]] = {}
        for view in edges:
            neighbours.setdefault(view["src"], set()).add(view["dst"])
            neighbours.setdefault(view["dst"], set()).add(view["src"])
        component = {focus}
        frontier = [focus]
        while frontier:
            node = frontier.pop()
            for other in neighbours.get(node, set()):
                if other not in component:
                    component.add(other)
                    frontier.append(other)
        nodes = {node_id: node for node_id, node in nodes.items() if node_id in component}
        edges = [
            view for view in edges if view["src"] in component and view["dst"] in component
        ]
    node_list = [nodes[node_id] for node_id in sorted(nodes)]
    return {"nodes": node_list, "edges": edges}


def _audit_matches(session: Session, row: models.AuditLog, matter_id: str | None) -> bool:
    """Whether an audit row belongs to a matter (T4.5)."""
    if matter_id is None:
        return True
    details = row.details_json if isinstance(row.details_json, dict) else {}
    if details.get("matter_id") == matter_id:
        return True
    claim_id = details.get("claim_id")
    if isinstance(claim_id, str):
        claim = session.get(models.Claim, claim_id)
        if claim is not None and claim.matter_id == matter_id:
            return True
    old_id = details.get("old_finding_id")
    if isinstance(old_id, str):
        old = session.get(models.Finding, old_id)
        if old is not None:
            claim = session.get(models.Claim, old.claim_id)
            if claim is not None and claim.matter_id == matter_id:
                return True
    fact_id = details.get("old_fact_id")
    if isinstance(fact_id, str):
        fact = session.get(models.Fact, fact_id)
        if fact is not None and fact.matter_id == matter_id:
            return True
    stale_ids = details.get("stale_findings")
    if isinstance(stale_ids, list):
        for stale_id in stale_ids:
            if not isinstance(stale_id, str):
                continue
            stale = session.get(models.Finding, stale_id)
            if stale is None:
                continue
            claim = session.get(models.Claim, stale.claim_id)
            if claim is not None and claim.matter_id == matter_id:
                return True
    return False


@router.get("/api/audit", response_model=schemas.AuditTrail)
@endpoint
async def get_audit(
    matter_id: str | None = None, session: Session = Depends(db_session)
) -> Any:
    """Audit trail, optionally scoped to a matter (F14)."""
    rows = session.execute(
        sa.select(models.AuditLog).order_by(models.AuditLog.ts.desc()).limit(200)
    ).scalars().all()
    return {
        "rows": [
            {
                "id": row.id,
                "ts": row.ts,
                "actor_type": row.actor_type,
                "actor_id": row.actor_id,
                "event": row.event,
                "object_type": row.object_type,
                "object_id": row.object_id,
                "details": dict(row.details_json or {}),
            }
            for row in rows
            if _audit_matches(session, row, matter_id)
        ]
    }


PLAIN_CHECKER_MESSAGES = {
    "PREMISE_MISMATCH": "This fact no longer matches the document",
    "PREMISE_UNTRUSTED": "This fact has not been approved, so it cannot be relied on",
    "PREMISE_UNKNOWN": "This fact is not on record",
    "CONCLUDE_MISMATCH": "The conclusion does not match the reasoning steps",
}


@router.post("/api/proofs/verify", response_model=schemas.ProofVerifyResult)
@endpoint
async def verify_proof(
    body: schemas.ProofVerifyBody, session: Session = Depends(db_session)
) -> Any:
    """Tamper demo: run the checker on an edited proof (G8)."""
    claim = session.get(models.Claim, body.claim_id)
    if claim is None:
        raise SourceUnavailable(f"unknown claim: {body.claim_id}")
    report = tools.verify_proof(session, str(claim.matter_id), body.claim_id, body.proof)
    # Codes stay for machines; known messages read plainly for lawyers.
    for error in report["errors"]:
        plain = PLAIN_CHECKER_MESSAGES.get(str(error.get("code")))
        if plain is not None:
            error["message"] = plain
    return report


@router.post("/api/counterfactual", response_model=schemas.CounterfactualResult)
@endpoint
async def counterfactual(
    body: dict[str, Any] | None = None, session: Session = Depends(db_session)
) -> Any:
    """What-if traversal: dry-run a version, write nothing (T7.3, F19)."""
    payload = body or {}
    version_id = payload.get("source_version_id")
    if not isinstance(version_id, str) or not version_id:
        return {
            "available": False,
            "note": "counterfactual needs a source_version_id to simulate",
            "nodes": [],
            "edges": [],
        }
    return counterfactual_service.run_counterfactual(session, version_id)


@router.get("/api/reverify-list", response_model=schemas.ReverifyList)
@endpoint
async def reverify_list(
    matter_id: str | None = None, session: Session = Depends(db_session)
) -> Any:
    """Findings awaiting re-verification in a matter (T7.3, T7.4).

    STALE findings (source changed under them) and CONFLICTING findings
    (cited rule cards contradict each other) both need a fresh verified
    decision before they can be relied on.
    """
    if matter_id is None:
        raise ValueError("matter_id is required")
    _require_matter(session, matter_id)
    findings = session.execute(
        sa.select(models.Finding)
        .join(models.Claim, models.Finding.claim_id == models.Claim.id)
        .where(models.Claim.matter_id == matter_id)
    ).scalars().all()
    items = []
    for finding in findings:
        if _finding_state(session, str(finding.id)) == "STALE":
            reason = "STALE"
        elif str(finding.status) == "CONFLICTING":
            reason = "CONFLICTING"
        else:
            continue
        items.append(
            {
                "finding_id": str(finding.id),
                "claim_id": str(finding.claim_id),
                "reason": reason,
                "reason_label": REASON_LABELS.get(reason, reason),
                "clause_ref": _clause_ref_for_claim(session, str(finding.claim_id)),
            }
        )
    return {"findings": sorted(items, key=lambda item: item["finding_id"])}


@router.post("/api/demo/reset")
@endpoint
async def demo_reset(body: dict[str, Any] | None = None) -> Any:
    """Reseed the demo database; only if `DEMO_MODE=1` (DATA_MODEL_API §7)."""
    _ = body
    import os as _os

    if _os.getenv("DEMO_MODE", "0") != "1":
        return JSONResponse(
            status_code=403,
            content={"error": {"code": "DEMO_DISABLED", "message": "demo routes need DEMO_MODE=1"}},
        )
    seed.seed_demo(default_db_path())
    return {"reset": True, "matter_id": seed.MATTER_ID}


@router.post("/api/demo/scenario/{name}")
@endpoint
async def demo_scenario(name: str, body: dict[str, Any] | None = None) -> Any:
    """Named demo setup; only if `DEMO_MODE=1` (DATA_MODEL_API §7)."""
    _ = body
    import os as _os

    if _os.getenv("DEMO_MODE", "0") != "1":
        return JSONResponse(
            status_code=403,
            content={"error": {"code": "DEMO_DISABLED", "message": "demo routes need DEMO_MODE=1"}},
        )
    if name != "stale-demo":
        return _error(404, "SCENARIO_UNKNOWN", f"unknown scenario: {name}")
    session = sessionmaker(bind=_engine_for(str(default_db_path())), future=True)()
    try:
        seed.seed_demo(default_db_path())
        version_id = "SV-DPDP-ACT-V2SIM"
        if session.get(models.SourceVersion, version_id) is None:
            return _error(404, "SCENARIO_UNKNOWN", f"scenario needs {version_id}")
        report = impact.apply_version(session, version_id)
    finally:
        session.close()
    return {
        "scenario": name,
        "steps": [
            "seeded demo database",
            f"applied {report['new_version_id']}",
            f"stale findings: {', '.join(report['stale_findings'])}",
        ],
    }
