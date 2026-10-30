"""T4.5: real DB-backed API router (contract v1, DATA_MODEL_API §7).

Included instead of the stub router when `API_STUB != 1`. Every handler
reads the database on each request through `default_db_path()`, so tests
point it at a scratch file with `CLAUSETRACE_DB`. Model calls (extract,
claims) go through the gateway; replay mode serves the demo cassettes.
Handlers are `async def` so SQLite stays on one thread; the blocking
SQLAlchemy calls are short demo queries.
"""

import functools
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app import models, schemas
from app.agent import claims, extract, tools
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
from app.db import default_db_path, get_engine
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
    """Cache one engine per database path (T4.5)."""
    engine = _engines.get(path)
    if engine is None:
        engine = get_engine(path)
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
        except (RuleCardError, ClaimError, ExtractionError) as exc:
            return _error(400, type(exc).__name__, str(exc))
        except ToolError as exc:
            if exc.code.startswith("unknown"):
                return _error(404, "NOT_FOUND", str(exc))
            return _error(400, exc.code.upper(), str(exc))
        except (CassetteMissing, LLMRequestFailed, LiveCallsBlocked) as exc:
            return _error(502, "MODEL_UNAVAILABLE", str(exc))
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


def _finding_payload(session: Session, finding: models.Finding) -> dict[str, Any]:
    """Serialize one finding against the v1 Finding schema (T4.5)."""
    proof = finding.proof_json if isinstance(finding.proof_json, dict) else {}
    report = finding.checker_report_json
    return {
        "id": finding.id,
        "claim_id": finding.claim_id,
        "version_no": finding.version_no,
        "status": finding.status,
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
    version = _latest_version(session, id)
    if version is None:
        raise SourceUnavailable(f"document {id} has no versions")
    result = extract.extract_document(
        version.text, mode=None, cache_dir=CASSETTES_DIR, session=session
    )
    now = _utcnow()
    new_version = models.DocumentVersion(
        id=_new_id("DV"),
        document_id=id,
        text=version.text,
        sha256=sources.sha256_text(version.text),
        created_at=now,
    )
    session.add(new_version)
    clause_ids: dict[str, str] = {}
    for clause_item in result.clauses:
        clause_id = _new_id("CL")
        clause_ids[clause_item.ref] = clause_id
        session.add(
            models.Clause(
                id=clause_id,
                document_version_id=new_version.id,
                ref=clause_item.ref,
                heading=clause_item.heading,
                text=clause_item.text,
                span_start=clause_item.span_start,
                span_end=clause_item.span_end,
            )
        )
    created_facts = []
    for fact_item in result.facts:
        fact_id = _new_id("F")
        created_facts.append(
            models.Fact(
                id=fact_id,
                matter_id=document.matter_id,
                clause_id=clause_ids.get(fact_item.clause_ref),
                statement=fact_item.statement,
                structured_json=dict(fact_item.structured),
                origin=fact_item.origin,
                trust_class=fact_item.trust_class,
                created_at=now,
            )
        )
        session.add(created_facts[-1])
    session.commit()
    return {
        "clauses": [
            {
                "id": cid,
                "document_version_id": new_version.id,
                "ref": clause_item.ref,
                "heading": clause_item.heading,
                "text": clause_item.text,
                "span_start": clause_item.span_start,
                "span_end": clause_item.span_end,
            }
            for cid, clause_item in zip(
                [clause_ids[item.ref] for item in result.clauses], result.clauses
            )
        ],
        "facts": [
            {
                "id": row.id,
                "matter_id": row.matter_id,
                "clause_id": row.clause_id,
                "statement": row.statement,
                "structured": dict(row.structured_json or {}),
                "origin": row.origin,
                "trust_class": row.trust_class,
                "created_at": row.created_at,
            }
            for row in created_facts
        ],
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
    return {
        "claim_id": claim_id,
        "run_id": run_id,
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
    for event in stale:
        finding = session.get(models.Finding, event.finding_id)
        if finding is None or not graph.is_current_finding(session, str(finding.id)):
            continue
        proof = payload.proofs.get(str(finding.id))
        if proof is None:
            stored = finding.proof_json
            if not isinstance(stored, dict):
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
    return {"superseded": sorted(superseded), "current": sorted(current)}


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


@router.post("/api/proofs/verify", response_model=schemas.ProofVerifyResult)
@endpoint
async def verify_proof(
    body: schemas.ProofVerifyBody, session: Session = Depends(db_session)
) -> Any:
    """Tamper demo: run the checker on an edited proof (G8)."""
    claim = session.get(models.Claim, body.claim_id)
    if claim is None:
        raise SourceUnavailable(f"unknown claim: {body.claim_id}")
    return tools.verify_proof(session, str(claim.matter_id), body.claim_id, body.proof)


@router.post("/api/counterfactual", response_model=schemas.CounterfactualResult)
@endpoint
async def counterfactual(body: dict[str, Any] | None = None) -> Any:
    """What-if traversal is stretch; report it as unavailable (F19)."""
    _ = body
    return {
        "available": False,
        "note": "Counterfactual mode lands after v1; use /api/graph for traversal.",
        "nodes": [],
        "edges": [],
    }


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
