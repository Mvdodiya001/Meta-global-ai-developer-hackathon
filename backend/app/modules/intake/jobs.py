"""Intake jobs: queued → running → done/failed, one document each (P3).

`extract_and_store` is the single write path for extraction results —
the synchronous endpoint and the background worker both call it, so a
document is stored identically however it was processed. Jobs are
idempotent to re-run after failure: extraction writes a *new* document
version each time (versions are cheap; evidence is never edited).
"""

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app import models
from app.modules.intake import extract
from app.modules.law import sources


def _utcnow() -> str:
    """Current UTC time in ISO-8601 (P3)."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    """One prefixed random id for intake rows (P3)."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def create_job(
    session: Session,
    *,
    kind: str,
    matter_id: str,
    document_id: str | None,
    input_b64: str | None = None,
) -> models.IntakeJob:
    """Queue one intake job (P3)."""
    now = _utcnow()
    job = models.IntakeJob(
        id=_new_id("JOB"),
        matter_id=matter_id,
        kind=kind,
        status="queued",
        stage="queued",
        document_id=document_id,
        input_b64=input_b64,
        created_at=now,
        updated_at=now,
    )
    session.add(job)
    session.commit()
    return job


def _set(session: Session, job: models.IntakeJob, **fields: Any) -> None:
    """Update job progress fields and stamp the time (P3)."""
    for key, value in fields.items():
        setattr(job, key, value)
    job.updated_at = _utcnow()
    session.commit()


def extract_and_store(
    session: Session, document_id: str, cache_dir: str | Path, generic: bool = False
) -> dict[str, Any]:
    """Extract the latest version and store a new one with facts (P3, P-C).

    Uploaded documents use `generic=True` (any clause count); the seeded
    Master DPA keeps the 12-clause seed shape.
    """
    document = session.get(models.Document, document_id)
    if document is None:
        raise ValueError(f"unknown document: {document_id}")
    version = session.execute(
        sa.select(models.DocumentVersion)
        .where(models.DocumentVersion.document_id == document_id)
        .order_by(models.DocumentVersion.created_at.desc(), models.DocumentVersion.id.desc())
    ).scalars().first()
    if version is None:
        raise ValueError(f"document {document_id} has no versions")
    result = extract.extract_document(
        str(version.text), mode=None, cache_dir=cache_dir, session=session,
        generic=generic,
    )
    now = _utcnow()
    if now <= str(version.created_at):
        # Same-second writes must not tie on created_at: "latest version"
        # is ordered by it, so the new version is stamped one second on.
        from datetime import datetime, timedelta

        parsed = datetime.strptime(str(version.created_at), "%Y-%m-%dT%H:%M:%SZ")
        now = (parsed + timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_version = models.DocumentVersion(
        id=_new_id("DV"),
        document_id=document_id,
        text=str(version.text),
        sha256=sources.sha256_text(str(version.text)),
        created_at=now,
    )
    session.add(new_version)
    clauses: list[dict[str, Any]] = []
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
        clauses.append(
            {
                "id": clause_id,
                "document_version_id": new_version.id,
                "ref": clause_item.ref,
                "heading": clause_item.heading,
                "text": clause_item.text,
                "span_start": clause_item.span_start,
                "span_end": clause_item.span_end,
            }
        )
    facts: list[dict[str, Any]] = []
    for fact_item in result.facts:
        new_fact_id = _new_id("F")
        session.add(
            models.Fact(
                id=new_fact_id,
                matter_id=document.matter_id,
                clause_id=clause_ids.get(fact_item.clause_ref),
                statement=fact_item.statement,
                structured_json=dict(fact_item.structured),
                origin=fact_item.origin,
                trust_class=fact_item.trust_class,
                created_at=now,
            )
        )
        facts.append(
            {
                "id": new_fact_id,
                "matter_id": str(document.matter_id),
                "clause_id": clause_ids.get(fact_item.clause_ref),
                "statement": fact_item.statement,
                "structured": dict(fact_item.structured),
                "origin": fact_item.origin,
                "trust_class": fact_item.trust_class,
                "trust_label": "",
                "created_at": now,
            }
        )
    session.commit()
    # Phase 1: structured understanding (parties/obligations/terms/dates)
    # as proposed facts. Best-effort: replay misses must not fail a job
    # whose clauses already extracted cleanly.
    understanding_counts: dict[str, int] = {}
    try:
        from app.modules.intake import understanding

        understanding_counts = understanding.store_understanding(
            session,
            matter_id=str(document.matter_id),
            text=str(version.text),
            clause_ids_by_ref=clause_ids,
        )
    except Exception as exc:  # understanding is additive; clauses stand
        print(f"warning: understanding skipped for {document_id}: {exc}")
    return {
        "document_version_id": new_version.id,
        "clauses": clauses,
        "facts": facts,
        "understanding": understanding_counts,
    }


def _store_text_version(session: Session, document_id: str, text: str) -> str:
    """Store raw text as a new document version; return its id (P-C)."""
    from app.modules.law import sources

    now = _utcnow()
    latest = session.execute(
        sa.select(models.DocumentVersion)
        .where(models.DocumentVersion.document_id == document_id)
        .order_by(models.DocumentVersion.created_at.desc(), models.DocumentVersion.id.desc())
    ).scalars().first()
    if latest is not None and now <= str(latest.created_at):
        from datetime import datetime, timedelta

        parsed = datetime.strptime(str(latest.created_at), "%Y-%m-%dT%H:%M:%SZ")
        now = (parsed + timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    version = models.DocumentVersion(
        id=_new_id("DV"),
        document_id=document_id,
        text=text,
        sha256=sources.sha256_text(text),
        created_at=now,
    )
    session.add(version)
    session.commit()
    return str(version.id)


def process_job(session: Session, job_id: str, cache_dir: str | Path) -> models.IntakeJob:
    """Run one queued job to completion or a typed failure (P3, P-C).

    PDF jobs transcribe image-only pages inside the worker with per-page
    progress (`stage: "page i of n"`) and record each page's origin in the
    result, so lawyers can spot-check transcribed pages. Re-running a
    finished page replays its cassette instead of paying again.
    """
    from app.modules.intake import pdf as pdf_intake

    job = session.get(models.IntakeJob, job_id)
    if job is None:
        raise ValueError(f"unknown job: {job_id}")
    if job.status == "done":
        return job
    _set(session, job, status="running", stage="starting")
    try:
        if job.kind != "document_extract":
            raise ValueError(f"unsupported job kind: {job.kind}")
        if job.document_id is None:
            raise ValueError("job has no document")
        pages: list[dict[str, object]] = []
        if job.input_b64:
            import base64

            raw = base64.b64decode(str(job.input_b64), validate=True)
            classified = pdf_intake.classify_pages(raw)
            total = len(classified)
            texts: list[str] = []
            vision_pages = [page.page for page in classified if page.source == "vision"]
            transcribed: dict[int, str] = {}
            if vision_pages:
                _set(session, job, stage=f"rendering {len(vision_pages)} scanned pages")
                transcribed = pdf_intake.transcribe_vision_pages(raw, vision_pages, cache_dir)
            for page in classified:
                if page.source == "vision":
                    _set(session, job, stage=f"page {page.page} of {total}")
                    texts.append(transcribed[page.page])
                else:
                    texts.append(page.text)
                # Phase 6 quality signal: transcribed pages and thin
                # text layers deserve a lawyer's spot-check.
                page_text = (
                    page.text if page.source == "text" else transcribed.get(page.page, "")
                )
                confidence = (
                    "low" if page.source == "vision" or len(page_text) < 200 else "high"
                )
                pages.append(
                    {"page": page.page, "source": page.source, "confidence": confidence}
                )
            # Page markers preserve document structure for extraction;
            # never quoted (the prompt says so), unlike real text.
            marked = "\n\n".join(
                f"--- page {page['page']} ---\n\n{text}"
                for page, text in zip(pages, texts, strict=True)
            )
            _store_text_version(session, str(job.document_id), marked)
        stored = extract_and_store(session, str(job.document_id), cache_dir, generic=True)
    except Exception as exc:  # job failure is data, recorded on the job row
        _set(
            session,
            job,
            status="failed",
            stage="failed",
            error=f"{type(exc).__name__}: {exc}"[:500],
        )
        return job
    _set(
        session,
        job,
        status="done",
        stage="done",
        result_json={
            "document_version_id": stored["document_version_id"],
            "clauses": len(stored["clauses"]),
            "facts": len(stored["facts"]),
            "understanding": stored.get("understanding", {}),
            "pages": pages,
        },
    )
    return job



