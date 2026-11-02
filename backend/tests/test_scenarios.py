"""T8.1 scenario tests on the real seeded corpus (gate Phase 4).

Scenario map (T8.1): decoy → no stale (here); future provision not in
force (here); stale chain flags exactly the dependents (here); matter
isolation (here, tool level); source failure (here); UNKNOWN question,
tampered premise, challenger objection (test_api.py:
test_unknown_question_returns_unknown_finding,
test_proof_round_trip_verifies, test_challenger_miss_still_decides /
test_challenger_report_returned).
"""

from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.core.errors import SourceUnavailable, ToolError
from app.db import init_db
from app.services import diff, graph, impact, seed, sources

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "corpus"


def seeded_session(tmp_path: Path) -> Session:
    """One session on a freshly seeded demo database (T8.1)."""
    db = tmp_path / "scenario.db"
    seed.seed_demo(db, CORPUS_ROOT)
    return sessionmaker(bind=init_db(db), future=True)()


def _add_finding(session: Session, finding_id: str, claim_id: str, card_id: str) -> None:
    """A CURRENT finding depending on one rule card (T8.1)."""
    session.add(
        models.Claim(
            id=claim_id,
            matter_id="MAT-01",
            clause_id="CL-11",
            claim_type="CT3",
            params_json={"date": "2027-06-01"},
            question_text="scenario",
            as_of="2026-11-20",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Finding(
            id=finding_id,
            claim_id=claim_id,
            version_no=1,
            status="FOLLOWS",
            confidence_band="high",
            proof_json=None,
            as_of="2026-11-20",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.FindingEvent(
            id=f"FE-{finding_id}",
            finding_id=finding_id,
            state="CURRENT",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    graph.add_edge(
        session,
        src_type="finding",
        src_id=finding_id,
        dst_type="rule_card",
        dst_id=card_id,
        rel="DEPENDS_ON",
    )
    session.commit()


def test_scenario_decoy_provision_has_no_dependents(tmp_path: Path) -> None:
    """T8.1 decoy: the Emblems Act provision flags no findings."""
    session = seeded_session(tmp_path)
    decoy = session.get(models.Provision, "PRV-DECOY-Emblems-Act-1950-s3")
    assert decoy is not None
    assert graph.dependent_findings(session, str(decoy.id)) == []
    report = impact.apply_version(session, "SV-DECOY-V1")
    assert report["stale_findings"] == []
    session.close()


def test_scenario_future_provision_not_in_force(tmp_path: Path) -> None:
    """T8.1 future provision: s8(6) is out of force before 2027-05-13."""
    session = seeded_session(tmp_path)
    provision = session.get(models.Provision, "PRV-DPDP-Act-2023-s8-6")
    assert provision is not None
    assert diff.in_force(provision, "2026-11-20") is False
    assert diff.in_force(provision, "2027-05-12") is False
    assert diff.in_force(provision, "2027-05-13") is True
    commencement = session.get(models.Provision, "PRV-DPDP-Act-2023-s1")
    assert commencement is not None
    assert diff.in_force(commencement, "2025-11-12") is False
    assert diff.in_force(commencement, "2025-11-13") is True
    session.close()


def test_scenario_stale_chain_flags_exactly_dependents(tmp_path: Path) -> None:
    """T8.1 stale chain: simulated v2 (s8(6)) flags only its dependents."""
    session = seeded_session(tmp_path)
    _add_finding(session, "FND-SC-BREACH", "C-SC-BREACH", "RC-CT3-BREACH-01")
    _add_finding(session, "FND-SC-SAFE", "C-SC-SAFE", "RC-CT2-SAFE-01")
    report = impact.apply_version(session, "SV-DPDP-ACT-V2SIM")
    assert report["changed"] == ["DPDP-Act-2023_s8(6)"]
    assert "FND-SC-BREACH" in report["stale_findings"]
    assert "FND-SC-SAFE" not in report["stale_findings"]
    assert graph.is_current_finding(session, "FND-SC-SAFE")
    session.close()


def test_scenario_cross_matter_tool_access_rejected(tmp_path: Path) -> None:
    """T8.1 matter isolation: another matter cannot read MAT-01 premises."""
    from app.agent import tools

    session = seeded_session(tmp_path)
    session.add(models.Matter(id="MAT-OTHER", client_name="Other", title="Other matter"))
    session.add(
        models.Run(
            id="RUN-SC", trigger="verify", claim_id="C-LOOP-92", started_at="2026-01-01T00:00:00Z"
        )
    )
    session.commit()
    with pytest.raises(ToolError) as excinfo:
        tools.call_tool(
            session,
            run_id="RUN-SC",
            matter_id="MAT-OTHER",
            tool="get_premise",
            args={"fact_id": "F-LOOP-92"},
        )
    assert excinfo.value.code == "cross_matter"
    session.close()


def test_scenario_unknown_source_raises_typed_error(tmp_path: Path) -> None:
    """T8.1 source failure: unknown versions raise SourceUnavailable."""
    session = seeded_session(tmp_path)
    with pytest.raises(SourceUnavailable):
        sources.get_version(session, "SV-NOPE")
    with pytest.raises(SourceUnavailable):
        impact.apply_version(session, "SV-NOPE")
    session.close()
