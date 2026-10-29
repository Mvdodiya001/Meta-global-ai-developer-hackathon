"""T1.4: fictional matter + contract seeding (F3, F18). All data is fictional demo data.

`seed_demo()` builds a fresh demo database: matter, one hearing + one task
(both labelled demo data), the Master DPA document with 12 clauses and exact
spans, plus the T1.2 corpus and T1.3 rule cards for a complete demo state.
Re-running on the same database is a no-op for the contract part (the corpus
and card loaders are already idempotent).
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.db import init_db
from app.services import rulecards, sources

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CORPUS_ROOT = REPO_ROOT / "corpus"

MATTER_ID = "MAT-01"
DOCUMENT_ID = "DOC-01"
DOC_VERSION_ID = "DOCV-01"

EXPECTED_REFS = ["1", "2", "3", "4", "5", "6", "7", "8", "9.1", "9.2", "10", "11"]


def _utcnow() -> str:
    """Current UTC time in ISO-8601 (T1.4)."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_contract(text: str) -> list[tuple[str, str, str]]:
    """Parse `## <ref> <heading>` sections; refs must match EXPECTED_REFS (T1.4)."""
    clauses: list[tuple[str, str, str]] = []
    ref: str | None = None
    heading = ""
    body: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if ref is not None:
                clauses.append((ref, heading, "\n".join(body).strip()))
            head = line[3:].strip()
            ref, _, heading = head.partition(" ")
            if not ref or not heading:
                raise ValueError(f"bad section header: {line!r}")
            body = []
        elif ref is not None and line.strip() != "":
            body.append(line.strip())
    if ref is not None:
        clauses.append((ref, heading, "\n".join(body).strip()))
    refs = [item[0] for item in clauses]
    if refs != EXPECTED_REFS:
        raise ValueError(f"expected clause refs {EXPECTED_REFS}, got {refs}")
    if any(not item[2] for item in clauses):
        raise ValueError("every clause needs a non-empty body")
    return clauses


def build_document(clauses: list[tuple[str, str, str]]) -> tuple[str, list[tuple[int, int]]]:
    """Join clause bodies into one snapshot; return text plus body spans (T1.4)."""
    parts: list[str] = []
    spans: list[tuple[int, int]] = []
    offset = 0
    for ref, heading, body in clauses:
        block = f"{ref} {heading}\n{body}\n\n"
        parts.append(block)
        start = offset + len(f"{ref} {heading}\n")
        spans.append((start, start + len(body)))
        offset += len(block)
    return "".join(parts), spans


def seed_demo(
    db_path: str | Path, corpus_root: str | Path = DEFAULT_CORPUS_ROOT
) -> dict[str, Any]:
    """Seed matter, contract, corpus and cards; return what was written (T1.4)."""
    corpus_root = Path(corpus_root)
    engine = init_db(db_path)
    session: Session = sessionmaker(bind=engine, future=True)()
    version_ids = sources.load_corpus(session, corpus_root / "raw")
    card_ids = rulecards.load_rulecards(session, corpus_root / "rulecards")
    if session.get(models.Matter, MATTER_ID) is None:
        text = (corpus_root / "contracts" / "master_dpa.md").read_text(encoding="utf-8")
        clauses = parse_contract(text)
        doc_text, spans = build_document(clauses)
        now = _utcnow()
        session.execute(
            sa.insert(models.Matter).values(
                id=MATTER_ID,
                client_name="Acme Retail Pvt Ltd",
                title="Acme–Nimbus Master Data Processing Agreement",
            )
        )
        session.execute(
            sa.insert(models.MatterContext).values(
                id="MC-01",
                matter_id=MATTER_ID,
                kind="hearing",
                title="Quarterly compliance review",
                due_at="2026-11-15T10:00:00Z",
                source_label="demo data",
            )
        )
        session.execute(
            sa.insert(models.MatterContext).values(
                id="MC-02",
                matter_id=MATTER_ID,
                kind="task",
                title="Confirm processor contract terms",
                due_at="2026-11-20T10:00:00Z",
                source_label="demo data",
            )
        )
        session.execute(
            sa.insert(models.Document).values(
                id=DOCUMENT_ID,
                matter_id=MATTER_ID,
                title="Master Data Processing Agreement",
                kind="dpa",
            )
        )
        session.execute(
            sa.insert(models.DocumentVersion).values(
                id=DOC_VERSION_ID,
                document_id=DOCUMENT_ID,
                text=doc_text,
                sha256=sources.sha256_text(doc_text),
                created_at=now,
            )
        )
        for index, ((ref, heading, body), (start, end)) in enumerate(
            zip(clauses, spans, strict=True), start=1
        ):
            session.execute(
                sa.insert(models.Clause).values(
                    id=f"CL-{index:02d}",
                    document_version_id=DOC_VERSION_ID,
                    ref=ref,
                    heading=heading,
                    text=body,
                    span_start=start,
                    span_end=end,
                )
            )
        session.commit()
    clause_count = session.execute(
        sa.select(sa.func.count()).select_from(models.Clause)
    ).scalar()
    session.close()
    return {
        "db": str(db_path),
        "matter_id": MATTER_ID,
        "clauses": int(clause_count or 0),
        "versions": sorted(version_ids.values()),
        "cards": card_ids,
    }
