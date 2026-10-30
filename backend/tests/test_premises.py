"""T4.4 tests (written first): premise challenge/approve/reject."""

from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.core.errors import MemoryServiceError
from app.db import init_db
from app.services import memory, premises

MATTER = "MAT-01"


def make_session(tmp_path: Path) -> Session:
    """Open a fresh database with a session (T4.4)."""
    engine = init_db(tmp_path / "premises.db")
    return sessionmaker(bind=engine, future=True)()


def seed(session: Session) -> None:
    """One extracted fact with a dependent CURRENT finding (T4.4)."""
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
        models.SourceVersion(
            id="SV-01",
            source_id="SRC-01",
            version_label="v1",
            published_on="2023-08-11",
            effective_from="2023-08-11",
            effective_until=None,
            retrieved_at="2026-01-01T00:00:00Z",
            content_sha256="0" * 64,
            raw_text="text",
            is_simulated=False,
            supersedes_id=None,
        )
    )
    session.add(
        models.Fact(
            id="F-01",
            matter_id=MATTER,
            clause_id="CL-10",
            statement="Clause 9.2 requires transfer logs.",
            structured_json={"element": "transfer logs"},
            origin="extracted",
            trust_class="document_extracted",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Provision(
            id="PRV-01",
            source_version_id="SV-01",
            key="Section 6",
            text="provision text",
            text_sha256="b" * 64,
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
        models.Claim(
            id="C-01",
            matter_id=MATTER,
            clause_id="CL-10",
            claim_type="CT2",
            params_json={"element": "transfer logs"},
            question_text="Does clause 9.2 require transfer logs?",
            as_of="2026-11-20",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Finding(
            id="FND-01",
            claim_id="C-01",
            version_no=1,
            status="FOLLOWS",
            confidence_band="medium",
            proof_json=None,
            as_of="2026-11-20",
            premise_ids_json=["F-01"],
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.FindingEvent(
            id="FE-01",
            finding_id="FND-01",
            state="CURRENT",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Edge(
            id="E-01",
            src_type="finding",
            src_id="FND-01",
            dst_type="fact",
            dst_id="F-01",
            rel="DEPENDS_ON",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Run(
            id="RUN-01",
            trigger="verify",
            claim_id="C-01",
            started_at="2026-01-01T00:00:00Z",
        )
    )
    session.commit()


def states(session: Session, finding_id: str) -> set[str]:
    """All event states recorded for one finding (T4.4)."""
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


def test_challenge_creates_disputed_row_and_stales_dependents(
    tmp_path: Path,
) -> None:
    """T4.4: Done when challenge adds a disputed row and stales dependents."""
    session = make_session(tmp_path)
    seed(session)
    new = premises.challenge_fact(
        session, fact_id="F-01", reason="Log wording is ambiguous.", reviewer="lawyer"
    )
    assert new.trust_class == "disputed"
    assert new.supersedes_id == "F-01"
    assert new.statement == "Clause 9.2 requires transfer logs."
    old = session.get(models.Fact, "F-01")
    assert old is not None and old.trust_class == "document_extracted"
    assert states(session, "FND-01") == {"CURRENT", "STALE"}
    reviews = session.execute(sa.select(models.Review)).scalars().all()
    assert len(reviews) == 1
    assert reviews[0].item_id == "F-01"
    assert reviews[0].status == "challenged"
    assert reviews[0].reviewer == "lawyer"
    audits = session.execute(
        sa.select(models.AuditLog).where(models.AuditLog.event == "fact.challenged")
    ).scalars().all()
    assert len(audits) == 1
    session.close()


def test_approve_creates_confirmed_row_without_staling(tmp_path: Path) -> None:
    """T4.4: approval strengthens the premise; dependents stay CURRENT."""
    session = make_session(tmp_path)
    seed(session)
    new = premises.approve_fact(session, fact_id="F-01", reviewer="lawyer")
    assert new.trust_class == "lawyer_confirmed"
    assert new.supersedes_id == "F-01"
    assert new.approved_by == "lawyer"
    assert states(session, "FND-01") == {"CURRENT"}
    session.close()


def test_reject_disputes_and_stales(tmp_path: Path) -> None:
    """T4.4: rejection disputes the premise and stales dependents."""
    session = make_session(tmp_path)
    seed(session)
    new = premises.reject_fact(
        session, fact_id="F-01", reason="No such duty.", reviewer="lawyer"
    )
    assert new.trust_class == "disputed"
    assert states(session, "FND-01") == {"CURRENT", "STALE"}
    reviews = session.execute(sa.select(models.Review)).scalars().all()
    assert [row.status for row in reviews] == ["rejected"]
    session.close()


def test_second_action_on_superseded_fact_refused(tmp_path: Path) -> None:
    """T4.4: only the current row of a fact chain can be acted on."""
    session = make_session(tmp_path)
    seed(session)
    premises.challenge_fact(session, fact_id="F-01", reason="First.")
    with pytest.raises(MemoryServiceError, match="superseded"):
        premises.approve_fact(session, fact_id="F-01", reviewer="lawyer")
    session.close()


def test_unknown_fact_raises(tmp_path: Path) -> None:
    """T4.4: actions on a missing fact raise a typed error."""
    session = make_session(tmp_path)
    seed(session)
    with pytest.raises(MemoryServiceError):
        premises.challenge_fact(session, fact_id="F-NOPE", reason="Why.")
    session.close()


def test_challenge_needs_reason(tmp_path: Path) -> None:
    """T4.4: challenge and reject without a reason are refused."""
    session = make_session(tmp_path)
    seed(session)
    with pytest.raises(MemoryServiceError):
        premises.challenge_fact(session, fact_id="F-01", reason="")
    with pytest.raises(MemoryServiceError):
        premises.reject_fact(session, fact_id="F-01", reason="  ")
    session.close()


def test_recompute_with_disputed_premise_requires_review(
    tmp_path: Path,
) -> None:
    """T4.4: Done when recompute on the disputed row yields REQUIRES_REVIEW."""
    session = make_session(tmp_path)
    seed(session)
    new_fact = premises.challenge_fact(session, fact_id="F-01", reason="Ambiguous.")
    draft: dict[str, Any] = {
        "claim_id": "C-01",
        "as_of": "2026-11-20",
        "conclusion": "holds",
        "premises": [
            {
                "fact_id": str(new_fact.id),
                "statement": "Clause 9.2 requires transfer logs.",
                "trust_class": "disputed",
            }
        ],
        "steps": [
            {"kind": "cite_fact", "fact_id": str(new_fact.id)},
            {"kind": "conclude", "conclusion": "holds"},
        ],
    }
    finding = memory.decide_finding(
        session, claim_id="C-01", proof=draft, run_id="RUN-01"
    )
    assert finding.status == "REQUIRES_REVIEW"
    session.close()
