"""T3.3 tests (written first): status decision, band, writes, re-query check."""

from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.agent import tools
from app.core.errors import MemoryServiceError
from app.db import init_db
from app.services import memory

MATTER = "MAT-01"


def make_session(tmp_path: Path) -> Session:
    """Open a fresh database with a session (T3.3)."""
    engine = init_db(tmp_path / "memory.db")
    return sessionmaker(bind=engine, future=True)()


def seed(session: Session) -> None:
    """Sources, cards, facts and claims for every status path (T3.3)."""
    session.add(models.Matter(id=MATTER, client_name="Acme", title="M1"))
    session.add(
        models.Source(
            id="SRC-01",
            key="dpdp-act",
            title="DPDP Act",
            publisher="MeitY",
            url="https://example.invalid",
            jurisdiction="IN",
        )
    )
    session.add(
        models.Source(
            id="SRC-02",
            key="dpdp-rules",
            title="DPDP Rules",
            publisher="MeitY",
            url="https://example.invalid",
            jurisdiction="IN",
        )
    )
    for vid, sup in (
        ("SV-00", None),
        ("SV-01", "SV-00"),
        ("SV-10SIM", None),
    ):
        session.add(
            models.SourceVersion(
                id=vid,
                source_id="SRC-02" if vid == "SV-10SIM" else "SRC-01",
                version_label=vid,
                published_on="2023-08-11",
                effective_from="2023-08-11",
                effective_until=None,
                retrieved_at="2026-01-01T00:00:00Z",
                content_sha256="0" * 64,
                raw_text="text",
                is_simulated=vid == "SV-10SIM",
                supersedes_id=sup,
            )
        )
    session.add(
        models.Provision(
            id="PRV-00",
            source_version_id="SV-00",
            key="Section 6",
            text="old provision text",
            text_sha256="a" * 64,
            effective_from="2023-08-11",
            effective_until=None,
        )
    )
    session.add(
        models.Provision(
            id="PRV-01",
            source_version_id="SV-01",
            key="Section 6",
            text="current provision text",
            text_sha256="b" * 64,
            effective_from="2023-08-11",
            effective_until=None,
        )
    )
    session.add(
        models.Provision(
            id="PRV-10",
            source_version_id="SV-10SIM",
            key="Rule 6",
            text="simulated provision text",
            text_sha256="c" * 64,
            effective_from="2026-01-01",
            effective_until=None,
        )
    )
    for cid, pid, kind, trust in (
        ("RC-00", "PRV-00", "statutory", "lawyer_confirmed"),
        ("RC-01", "PRV-01", "statutory", "lawyer_confirmed"),
        ("RC-02", "PRV-10", "statutory", "lawyer_confirmed"),
        ("RC-03", "PRV-01", "interpretation", "document_extracted"),
    ):
        session.add(
            models.RuleCard(
                id=cid,
                provision_id=pid,
                kind=kind,
                claim_type="CT2",
                predicate_json=None,
                interpretation_text="interpretation",
                span_start=0,
                span_end=4,
                trust_class=trust,
                approved_by="human",
                created_at="2026-01-01T00:00:00Z",
            )
        )
    for fid, trust in (
        ("F-L1", "lawyer_confirmed"),
        ("F-E1", "document_extracted"),
        ("F-D1", "disputed"),
    ):
        session.add(
            models.Fact(
                id=fid,
                matter_id=MATTER,
                clause_id=None,
                statement=f"Statement {fid}.",
                structured_json=None,
                origin="lawyer" if fid == "F-L1" else "extracted",
                trust_class=trust,
                created_at="2026-01-01T00:00:00Z",
            )
        )
    for cid, ctype in (
        ("C-01", "CT2"),
        ("C-UNK", "UNKNOWN"),
        ("C-NORULE", "CT4"),
    ):
        session.add(
            models.Claim(
                id=cid,
                matter_id=MATTER,
                clause_id="CL-01",
                claim_type=ctype,
                params_json={"element": "transfer logs"},
                question_text=f"Question {cid}?",
                as_of="2026-11-20",
                created_at="2026-01-01T00:00:00Z",
            )
        )
    session.add(
        models.Run(id="RUN-01", trigger="verify", claim_id="C-01",
                   started_at="2026-01-01T00:00:00Z")
    )
    session.commit()


def proof(
    claim_id: str = "C-01",
    conclusion: str = "holds",
    fact_id: str = "F-E1",
    statement: str = "Statement F-E1.",
    trust: str = "document_extracted",
) -> dict[str, Any]:
    """A minimal checker-valid draft over the seeded rows (T3.3)."""
    return {
        "claim_id": claim_id,
        "as_of": "2026-11-20",
        "conclusion": conclusion,
        "premises": [
            {"fact_id": fact_id, "statement": statement, "trust_class": trust}
        ],
        "steps": [
            {"kind": "cite_fact", "fact_id": fact_id},
            {"kind": "conclude", "conclusion": conclusion},
        ],
    }


def decide(
    session: Session,
    claim_id: str = "C-01",
    draft: dict[str, Any] | None = None,
    run_id: str = "RUN-01",
    **kwargs: Any,
) -> models.Finding:
    """Decide one proof through the memory service (T3.3)."""
    return memory.decide_finding(
        session,
        claim_id=claim_id,
        proof=draft if draft is not None else proof(claim_id=claim_id),
        run_id=run_id,
        **kwargs,
    )


def fresh_lookup(session: Session, run_id: str = "RUN-01") -> None:
    """Log a fresh lookup_source of the current version (T3.3)."""
    tools.call_tool(
        session,
        run_id=run_id,
        matter_id=MATTER,
        tool="lookup_source",
        args={"source_id": "SRC-01"},
    )


def citing_proof() -> dict[str, Any]:
    """A checker-valid draft citing the current card and version (T3.3)."""
    draft = proof()
    draft["steps"] = [
        {"kind": "cite_fact", "fact_id": "F-E1"},
        {
            "kind": "cite_rule",
            "rule_card_id": "RC-01",
            "citation": {
                "source_version_id": "SV-01",
                "provision_id": "PRV-01",
                "span": [0, 22],
                "sha256": "b" * 64,
            },
        },
        {"kind": "conclude", "conclusion": "holds"},
    ]
    return draft


def test_follows_path_writes_finding_edges_audit(tmp_path: Path) -> None:
    """T3.3: a checked proof with a fresh lookup becomes FOLLOWS."""
    session = make_session(tmp_path)
    seed(session)
    fresh_lookup(session)
    finding = decide(session, draft=citing_proof())
    assert finding.status == "FOLLOWS"
    assert finding.version_no == 1
    assert finding.source_version_ids_json == ["SV-01"]
    assert finding.premise_ids_json == ["F-E1"]
    assert finding.checker_report_json is not None
    assert finding.checker_report_json["valid"] is True
    events = session.execute(
        sa.select(models.FindingEvent).where(
            models.FindingEvent.finding_id == finding.id
        )
    ).scalars().all()
    assert [event.state for event in events] == ["CURRENT"]
    edges = session.execute(
        sa.select(models.Edge).where(models.Edge.src_id == finding.id)
    ).scalars().all()
    assert {(edge.rel, edge.dst_id) for edge in edges} == {
        ("DEPENDS_ON", "F-E1"),
        ("DEPENDS_ON", "RC-01"),
    }
    audits = session.execute(
        sa.select(models.AuditLog).where(models.AuditLog.object_id == finding.id)
    ).scalars().all()
    assert len(audits) == 1
    assert audits[0].event == "finding.decided"
    session.close()


def test_ruled_out_path(tmp_path: Path) -> None:
    """T3.3: a valid proof of the negation becomes RULED_OUT."""
    session = make_session(tmp_path)
    seed(session)
    fresh_lookup(session)
    finding = decide(session, draft=proof(conclusion="does not hold"))
    assert finding.status == "RULED_OUT"
    session.close()


def test_unknown_type_path(tmp_path: Path) -> None:
    """T3.3: an unsupported claim type becomes UNKNOWN without the checker."""
    session = make_session(tmp_path)
    seed(session)
    finding = decide(session, claim_id="C-UNK")
    assert finding.status == "UNKNOWN"
    assert finding.checker_report_json is None
    assert finding.confidence_band == "low"
    session.close()


def test_unknown_no_rule_card_path(tmp_path: Path) -> None:
    """T3.3: a type with no applicable card becomes UNKNOWN."""
    session = make_session(tmp_path)
    seed(session)
    finding = decide(session, claim_id="C-NORULE")
    assert finding.status == "UNKNOWN"
    session.close()


def test_model_cannot_set_status(tmp_path: Path) -> None:
    """T3.3: Done when a status smuggled into the proof is ignored."""
    session = make_session(tmp_path)
    seed(session)
    fresh_lookup(session)
    smuggled = proof(conclusion="does not hold")
    smuggled["status"] = "FOLLOWS"
    finding = decide(session, draft=smuggled)
    assert finding.status == "RULED_OUT"
    bad = proof()
    bad["premises"][0]["statement"] = "Tampered."
    bad["status"] = "FOLLOWS"
    refused = decide(session, draft=bad)
    assert refused.status == "REQUIRES_REVIEW"
    session.close()


def test_stale_version_proof_rejected(tmp_path: Path) -> None:
    """T3.3: Done when a proof citing a superseded version is rejected."""
    session = make_session(tmp_path)
    seed(session)
    stale = proof()
    stale["steps"] = [
        {"kind": "cite_fact", "fact_id": "F-E1"},
        {
            "kind": "cite_rule",
            "rule_card_id": "RC-00",
            "citation": {
                "source_version_id": "SV-00",
                "provision_id": "PRV-00",
                "span": [0, 18],
                "sha256": "a" * 64,
            },
        },
        {"kind": "conclude", "conclusion": "holds"},
    ]
    finding = decide(session, draft=stale)
    assert finding.status == "REQUIRES_REVIEW"
    report = finding.checker_report_json
    assert report is not None and report["valid"] is False
    assert "VERSION_SUPERSEDED" in [error["code"] for error in report["errors"]]
    session.close()


def test_missing_lookup_rejected(tmp_path: Path) -> None:
    """T3.3: a proof with no fresh lookup in the run log is rejected."""
    session = make_session(tmp_path)
    seed(session)
    finding = decide(session, draft=citing_proof())
    assert finding.status == "REQUIRES_REVIEW"
    session.close()


def test_disputed_premise_requires_review(tmp_path: Path) -> None:
    """T3.3: a disputed premise forces REQUIRES_REVIEW."""
    session = make_session(tmp_path)
    seed(session)
    fresh_lookup(session)
    draft = proof(fact_id="F-D1", statement="Statement F-D1.", trust="disputed")
    finding = decide(session, draft=draft)
    assert finding.status == "REQUIRES_REVIEW"
    session.close()


def test_challenger_blocking_requires_review(tmp_path: Path) -> None:
    """T3.3: a blocking challenger objection forces REQUIRES_REVIEW."""
    session = make_session(tmp_path)
    seed(session)
    fresh_lookup(session)
    finding = decide(session, challenger_blocking=True)
    assert finding.status == "REQUIRES_REVIEW"
    session.close()


def test_confidence_bands(tmp_path: Path) -> None:
    """T3.3: HIGH/MEDIUM/LOW follow ARCHITECTURE §6."""
    session = make_session(tmp_path)
    seed(session)
    fresh_lookup(session)
    assert decide(session).confidence_band == "medium"
    high = proof(fact_id="F-L1", statement="Statement F-L1.", trust="lawyer_confirmed")
    assert decide(session, draft=high).confidence_band == "high"
    sim = proof()
    sim["steps"] = [
        {"kind": "cite_fact", "fact_id": "F-E1"},
        {
            "kind": "cite_rule",
            "rule_card_id": "RC-02",
            "citation": {
                "source_version_id": "SV-10SIM",
                "provision_id": "PRV-10",
                "span": [0, 24],
                "sha256": "c" * 64,
            },
        },
        {"kind": "conclude", "conclusion": "holds"},
    ]
    tools.call_tool(
        session,
        run_id="RUN-01",
        matter_id=MATTER,
        tool="lookup_source",
        args={"source_id": "SRC-02"},
    )
    assert decide(session, draft=sim).confidence_band == "low"
    interp = proof()
    interp["steps"] = [
        {"kind": "cite_fact", "fact_id": "F-E1"},
        {
            "kind": "cite_rule",
            "rule_card_id": "RC-03",
            "citation": {
                "source_version_id": "SV-01",
                "provision_id": "PRV-01",
                "span": [0, 22],
                "sha256": "b" * 64,
            },
        },
        {"kind": "conclude", "conclusion": "holds"},
    ]
    assert decide(session, draft=interp).confidence_band == "low"
    assert decide(session, challenger_note=True).confidence_band == "low"
    session.close()


def test_second_decision_supersedes_first(tmp_path: Path) -> None:
    """T3.3: a new finding version supersedes the previous CURRENT one."""
    session = make_session(tmp_path)
    seed(session)
    fresh_lookup(session)
    first = decide(session)
    second = decide(session)
    assert second.version_no == 2
    assert second.supersedes_finding_id == first.id
    states: dict[str, set[str]] = {}
    for event in session.execute(sa.select(models.FindingEvent)).scalars().all():
        states.setdefault(str(event.finding_id), set()).add(str(event.state))
    assert states[first.id] == {"CURRENT", "SUPERSEDED"}
    assert states[second.id] == {"CURRENT"}
    session.close()


def test_unknown_claim_raises(tmp_path: Path) -> None:
    """T3.3: deciding for a missing claim raises a typed error."""
    session = make_session(tmp_path)
    seed(session)
    with pytest.raises(MemoryServiceError):
        decide(session, claim_id="C-NOPE")
    session.close()
