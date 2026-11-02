"""T1.4: fictional matter + contract seeding (F3, F18). All data is fictional demo data.

`seed_demo()` builds a fresh demo database: matter, one hearing + one task
(both labelled demo data), the Master DPA document with 12 clauses and exact
spans, the replay-extracted DOC-01 facts (G8, deterministic `F-SEED-*` ids),
plus the T1.2 corpus and T1.3 rule cards for a complete demo state.
Re-running on the same database is a no-op for the contract part (the corpus
and card loaders are already idempotent).
"""

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.agent import extract as extract_agent
from app.core.errors import ToolError
from app.db import init_db
from app.services import graph, rulecards, sources

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CORPUS_ROOT = REPO_ROOT / "corpus"

MATTER_ID = "MAT-01"
DOCUMENT_ID = "DOC-01"
DOC_VERSION_ID = "DOCV-01"

SEED_EXTRACT_ID_PREFIX = "F-SEED-"
SEED_EXTRACT_CREATED_AT = "2026-01-01T00:00:00Z"

EXPECTED_REFS = ["1", "2", "3", "4", "5", "6", "7", "8", "9.1", "9.2", "10", "11"]

DEMO_92_FACT_ID = "F-LOOP-92"
DEMO_92_CLAIM_ID = "C-LOOP-92"
DEMO_92_QUESTION = "Does clause 9.2 require Nimbus to keep transfer logs?"
DEMO_92_AS_OF = "2026-11-20"
DEMO_92_STATEMENT = "Clause 9.2 requires Nimbus to keep transfer logs for review."


def ensure_demo_92_claim(session: Session) -> str:
    """Create the fixed clause-9.2 fact and claim when missing (T2.5).

    Record and replay share these exact rows so the loop request hashes
    match; ids, text and dates are constants, never generated. Called by
    `seed_demo` so every demo database carries the 9.2 question context.
    """
    clause = session.execute(
        sa.select(models.Clause).where(models.Clause.ref == "9.2")
    ).scalars().first()
    if clause is None:
        raise ToolError("demo contract has no clause 9.2", code="unknown_clause")
    if session.get(models.Fact, DEMO_92_FACT_ID) is None:
        session.add(
            models.Fact(
                id=DEMO_92_FACT_ID,
                matter_id="MAT-01",
                clause_id=clause.id,
                statement=DEMO_92_STATEMENT,
                structured_json={"element": "transfer logs", "clause_ref": "9.2"},
                origin="extracted",
                trust_class="document_extracted",
                created_at="2026-01-01T00:00:00Z",
            )
        )
    if session.get(models.Claim, DEMO_92_CLAIM_ID) is None:
        session.add(
            models.Claim(
                id=DEMO_92_CLAIM_ID,
                matter_id="MAT-01",
                clause_id=clause.id,
                claim_type="CT2",
                params_json={"element": "transfer logs"},
                question_text=DEMO_92_QUESTION,
                as_of=DEMO_92_AS_OF,
                created_at="2026-01-01T00:00:00Z",
            )
        )
    session.commit()
    return DEMO_92_CLAIM_ID


def _utcnow() -> str:
    """Current UTC time in ISO-8601 (T1.4)."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _seed_extraction_facts(session: Session, corpus_root: Path) -> int:
    """Persist replay-extracted DOC-01 facts with deterministic ids (G8).

    Runs the recorded T2.2 extraction in `replay` mode (zero model spend)
    and attaches one fact per extracted clause to the seeded seed version,
    so Screen 3 is populated right after a reset. Ids (`F-SEED-01`, …),
    text and dates are constants derived from the pinned cassette, never
    generated, so every reset yields byte-identical prompt hashes.
    """
    version = session.get(models.DocumentVersion, DOC_VERSION_ID)
    if version is None:
        raise ValueError(f"seeded document version {DOC_VERSION_ID} missing")
    result = extract_agent.extract_document(
        str(version.text), mode="replay", cache_dir=corpus_root / "cassettes"
    )
    clause_ids = {
        str(row.ref): str(row.id)
        for row in session.execute(
            sa.select(models.Clause).where(
                models.Clause.document_version_id == DOC_VERSION_ID
            )
        )
        .scalars()
        .all()
    }
    existing: list[str] = list(
        session.execute(
            sa.select(models.Fact.id).where(
                models.Fact.id.startswith(SEED_EXTRACT_ID_PREFIX)
            )
        )
        .scalars()
        .all()
    )
    if existing:
        if len(existing) != len(result.facts):
            raise ValueError(
                f"partial seeded extraction: {len(existing)} of "
                f"{len(result.facts)} facts present"
            )
        return len(existing)
    for index, fact in enumerate(result.facts, start=1):
        clause_id = clause_ids.get(str(fact.clause_ref))
        if clause_id is None:
            raise ValueError(f"extracted fact points at unknown clause {fact.clause_ref!r}")
        session.add(
            models.Fact(
                id=f"{SEED_EXTRACT_ID_PREFIX}{index:02d}",
                matter_id=MATTER_ID,
                clause_id=clause_id,
                statement=fact.statement,
                structured_json=dict(fact.structured),
                origin=fact.origin,
                trust_class=fact.trust_class,
                created_at=SEED_EXTRACT_CREATED_AT,
            )
        )
    session.commit()
    return len(result.facts)


_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    """Significant words in a clause or card span (F11)."""
    return {token for token in _TOKEN.findall(text.lower()) if len(token) > 3}


def _clause_for_card(
    clauses: list[models.Clause], card: models.RuleCard, provision: models.Provision
) -> models.Clause:
    """Pick the contract clause that shares the most words with the card (F11)."""
    needles = _tokens(card.interpretation_text)
    needles |= _tokens(provision.text[card.span_start : card.span_end])
    requires = card.predicate_json.get("requires") if isinstance(card.predicate_json, dict) else []
    for item in requires or []:
        needles |= _tokens(str(item).replace("_", " "))

    def score(clause: models.Clause) -> int:
        return len(needles & _tokens(f"{clause.heading} {clause.text}"))

    return sorted(clauses, key=lambda clause: (-score(clause), str(clause.id)))[0]


def _proof_for_card(
    claim_id: str, as_of: str, card: models.RuleCard, provision: models.Provision
) -> dict[str, Any]:
    """A proof that cites this card's stored span (F11)."""
    return {
        "claim_id": claim_id,
        "as_of": as_of,
        "premises": [],
        "steps": [
            {
                "kind": "cite_rule",
                "rule_card_id": str(card.id),
                "citation": {
                    "source_version_id": str(provision.source_version_id),
                    "provision_id": str(provision.id),
                    "span": [int(card.span_start), int(card.span_end)],
                    "sha256": str(provision.text_sha256),
                },
            },
            {"kind": "conclude", "conclusion": "holds"},
        ],
        "conclusion": "holds",
    }


def ensure_rule_card_findings(session: Session) -> list[str]:
    """Ensure each loaded rule card has one current dependent finding (F11).

    Impact only marks findings that already depend on a changed provision.
    Ids, questions and citations come from the card and the clause text, so
    a new card participates without a special case. Existing rows are kept.
    """
    clauses = list(
        session.execute(sa.select(models.Clause).order_by(models.Clause.id)).scalars().all()
    )
    if not clauses:
        return []
    created: list[str] = []
    cards = list(
        session.execute(sa.select(models.RuleCard).order_by(models.RuleCard.id)).scalars().all()
    )
    for card in cards:
        finding_id = f"FND-{card.id}"
        if session.get(models.Finding, finding_id) is not None:
            continue
        provision = session.get(models.Provision, card.provision_id)
        if provision is None:
            continue
        claim_id = f"C-{card.id}"
        clause = _clause_for_card(clauses, card, provision)
        as_of = str(provision.effective_from)
        if session.get(models.Claim, claim_id) is None:
            question = " ".join(str(card.interpretation_text).split())
            session.add(
                models.Claim(
                    id=claim_id,
                    matter_id=MATTER_ID,
                    clause_id=str(clause.id),
                    claim_type=str(card.claim_type),
                    params_json={"requires": list((card.predicate_json or {}).get("requires", []))},
                    question_text=question,
                    as_of=as_of,
                    created_at=SEED_EXTRACT_CREATED_AT,
                )
            )
        band = "low" if card.trust_class == "ai_inferred" else "medium"
        session.add(
            models.Finding(
                id=finding_id,
                claim_id=claim_id,
                version_no=1,
                status="FOLLOWS",
                confidence_band=band,
                proof_json=_proof_for_card(claim_id, as_of, card, provision),
                as_of=as_of,
                source_version_ids_json=[str(provision.source_version_id)],
                premise_ids_json=[],
                rule_card_ids_json=[str(card.id)],
                checker_report_json=None,
                run_id=None,
                created_at=SEED_EXTRACT_CREATED_AT,
            )
        )
        session.add(
            models.FindingEvent(
                id=f"FE-{card.id}",
                finding_id=finding_id,
                state="CURRENT",
                reason="seeded from rule card",
                caused_by_type="rule_card",
                caused_by_id=str(card.id),
                created_at=SEED_EXTRACT_CREATED_AT,
            )
        )
        graph.add_edge(
            session,
            src_type="finding",
            src_id=finding_id,
            dst_type="rule_card",
            dst_id=str(card.id),
            rel="DEPENDS_ON",
        )
        created.append(finding_id)
    if created:
        session.commit()
    return created


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
    ensure_demo_92_claim(session)
    fact_count = _seed_extraction_facts(session, corpus_root)
    ensure_rule_card_findings(session)
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
        "facts": int(fact_count or 0),
    }
