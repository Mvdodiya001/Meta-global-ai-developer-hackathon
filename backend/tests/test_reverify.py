"""T4.3 tests (written first): re-verify chain and re-query enforcement."""

from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.agent import tools
from app.core.errors import MemoryServiceError
from app.db import init_db
from app.services import memory, reverify

MATTER = "MAT-01"


def make_session(tmp_path: Path) -> Session:
    """Open a fresh database with a session (T4.3)."""
    engine = init_db(tmp_path / "reverify.db")
    return sessionmaker(bind=engine, future=True)()


def seed(session: Session) -> str:
    """Old FOLLOWS finding with CURRENT + STALE events (T4.3)."""
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
    for vid, sup in (("SV-01", None), ("SV-02", "SV-01")):
        session.add(
            models.SourceVersion(
                id=vid,
                source_id="SRC-01",
                version_label=vid,
                published_on="2023-08-11",
                effective_from="2023-08-11",
                effective_until=None,
                retrieved_at="2026-01-01T00:00:00Z",
                content_sha256="0" * 64,
                raw_text="text",
                is_simulated=False,
                supersedes_id=sup,
            )
        )
    for pid, vid, key, text in (
        ("PRV-01", "SV-01", "Section 6", "old section 6 text"),
        ("PRV-02", "SV-02", "Section 6", "new section 6 text"),
    ):
        session.add(
            models.Provision(
                id=pid,
                source_version_id=vid,
                key=key,
                text=text,
                text_sha256=f"sha-{pid}",
                effective_from="2023-08-11",
                effective_until=None,
            )
        )
    session.add(
        models.RuleCard(
            id="RC-01",
            provision_id="PRV-01",
            kind="statutory",
            claim_type="CT2",
            predicate_json=None,
            interpretation_text="interp",
            span_start=0,
            span_end=4,
            trust_class="lawyer_confirmed",
            approved_by="human",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Fact(
            id="F-01",
            matter_id=MATTER,
            clause_id=None,
            statement="Clause 9.2 requires transfer logs.",
            structured_json=None,
            origin="extracted",
            trust_class="document_extracted",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Claim(
            id="C-01",
            matter_id=MATTER,
            clause_id="CL-01",
            claim_type="CT2",
            params_json={"element": "transfer logs"},
            question_text="Does clause 9.2 require transfer logs?",
            as_of="2026-11-20",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Finding(
            id="FND-OLD",
            claim_id="C-01",
            version_no=1,
            status="FOLLOWS",
            confidence_band="medium",
            proof_json=None,
            as_of="2026-11-20",
            source_version_ids_json=["SV-01"],
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.FindingEvent(
            id="FE-OLD-CUR",
            finding_id="FND-OLD",
            state="CURRENT",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.FindingEvent(
            id="FE-OLD-STALE",
            finding_id="FND-OLD",
            state="STALE",
            reason="provision 'Section 6' changed in SV-02",
            caused_by_type="source_version",
            caused_by_id="SV-02",
            created_at="2026-01-02T00:00:00Z",
        )
    )
    session.add(
        models.Run(
            id="RUN-02",
            trigger="reverify",
            claim_id="C-01",
            started_at="2026-01-03T00:00:00Z",
        )
    )
    session.commit()
    return "FND-OLD"


def proof(conclusion: str = "holds") -> dict[str, Any]:
    """A checker-valid draft over the seeded fact (T4.3)."""
    return {
        "claim_id": "C-01",
        "as_of": "2026-11-20",
        "conclusion": conclusion,
        "premises": [
            {
                "fact_id": "F-01",
                "statement": "Clause 9.2 requires transfer logs.",
                "trust_class": "document_extracted",
            }
        ],
        "steps": [
            {"kind": "cite_fact", "fact_id": "F-01"},
            {"kind": "conclude", "conclusion": conclusion},
        ],
    }


def fresh_lookup(session: Session) -> None:
    """Log a fresh lookup of the current version in the reverify run (T4.3)."""
    tools.call_tool(
        session,
        run_id="RUN-02",
        matter_id=MATTER,
        tool="lookup_source",
        args={"source_id": "SRC-01"},
    )


def states(session: Session, finding_id: str) -> set[str]:
    """All event states recorded for one finding (T4.3)."""
    return {
        str(row.state)
        for row in session.execute(
            sa.select(models.FindingEvent).where(
                models.FindingEvent.finding_id == finding_id
            )
        )
        .scalars()
        .all()
    }


def test_reverify_supersedes_old_finding(tmp_path: Path) -> None:
    """T4.3: Done when the new finding supersedes the old and the old is kept."""
    session = make_session(tmp_path)
    old_id = seed(session)
    fresh_lookup(session)
    new = reverify.reverify_finding(
        session, finding_id=old_id, proof=proof(), run_id="RUN-02"
    )
    assert new.status == "FOLLOWS"
    assert new.version_no == 2
    assert new.supersedes_finding_id == old_id
    assert states(session, old_id) == {"CURRENT", "STALE", "SUPERSEDED"}
    assert states(session, str(new.id)) == {"CURRENT"}
    assert session.get(models.Finding, old_id) is not None
    session.close()


def test_unchanged_outcome_audited(tmp_path: Path) -> None:
    """T4.3: Done when an equal outcome writes a rechecked-unchanged audit row."""
    session = make_session(tmp_path)
    old_id = seed(session)
    fresh_lookup(session)
    new = reverify.reverify_finding(
        session, finding_id=old_id, proof=proof(), run_id="RUN-02"
    )
    assert new.status == "FOLLOWS"
    rows = session.execute(
        sa.select(models.AuditLog).where(
            models.AuditLog.event == "finding.rechecked"
        )
    ).scalars().all()
    assert len(rows) == 1
    assert rows[0].object_id == new.id
    assert rows[0].details_json == {
        "old_finding_id": old_id,
        "status": "FOLLOWS",
        "unchanged": True,
    }
    session.close()


def test_changed_outcome_writes_no_unchanged_audit(tmp_path: Path) -> None:
    """T4.3: a flipped outcome records the new decision without the audit."""
    session = make_session(tmp_path)
    old_id = seed(session)
    fresh_lookup(session)
    new = reverify.reverify_finding(
        session, finding_id=old_id, proof=proof("does not hold"), run_id="RUN-02"
    )
    assert new.status == "RULED_OUT"
    rows = session.execute(
        sa.select(sa.func.count())
        .select_from(models.AuditLog)
        .where(models.AuditLog.event == "finding.rechecked")
    ).scalar()
    assert rows == 0
    session.close()


def test_rejection_without_fresh_lookup(tmp_path: Path) -> None:
    """T4.3: Done when re-verify without a fresh lookup is rejected cleanly."""
    session = make_session(tmp_path)
    old_id = seed(session)
    with pytest.raises(MemoryServiceError, match="fresh lookup"):
        reverify.reverify_finding(
            session, finding_id=old_id, proof=proof(), run_id="RUN-02"
        )
    assert (
        session.execute(
            sa.select(sa.func.count()).select_from(models.Finding)
        ).scalar()
        == 1
    )
    assert "SUPERSEDED" not in states(session, old_id)
    session.close()


def test_non_stale_finding_rejected(tmp_path: Path) -> None:
    """T4.3: a finding with no STALE event is not eligible for re-verify."""
    session = make_session(tmp_path)
    seed(session)
    fresh_lookup(session)
    session.add(
        models.Finding(
            id="FND-FRESH",
            claim_id="C-01",
            version_no=9,
            status="FOLLOWS",
            confidence_band="high",
            proof_json=None,
            as_of="2026-11-20",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.FindingEvent(
            id="FE-FRESH",
            finding_id="FND-FRESH",
            state="CURRENT",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.commit()
    with pytest.raises(MemoryServiceError, match="not stale"):
        reverify.reverify_finding(
            session, finding_id="FND-FRESH", proof=proof(), run_id="RUN-02"
        )
    session.close()


def test_unknown_finding_raises(tmp_path: Path) -> None:
    """T4.3: re-verify of a missing finding raises a typed error."""
    session = make_session(tmp_path)
    seed(session)
    with pytest.raises(MemoryServiceError):
        reverify.reverify_finding(
            session, finding_id="FND-NOPE", proof=proof(), run_id="RUN-02"
        )
    session.close()


def test_invalid_proof_decides_review(tmp_path: Path) -> None:
    """T4.3: a tampered draft still replaces the stale finding as review."""
    session = make_session(tmp_path)
    old_id = seed(session)
    fresh_lookup(session)
    bad = proof()
    bad["premises"][0]["statement"] = "Tampered."
    new = reverify.reverify_finding(
        session, finding_id=old_id, proof=bad, run_id="RUN-02"
    )
    assert new.status == "REQUIRES_REVIEW"
    assert "SUPERSEDED" in states(session, old_id)
    session.close()


def test_memory_module_still_decides(tmp_path: Path) -> None:
    """T4.3: the memory service path is untouched by the reverify layer."""
    session = make_session(tmp_path)
    seed(session)
    fresh_lookup(session)
    finding = memory.decide_finding(
        session, claim_id="C-01", proof=proof(), run_id="RUN-02"
    )
    assert finding.status == "FOLLOWS"
    session.close()
