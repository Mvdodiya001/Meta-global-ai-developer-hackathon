"""T7.3: counterfactual dry run — propositional validity, reverify list, no writes."""

from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.db import init_db
from app.services import counterfactual, graph, seed

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "corpus"

PROOF = {
    "claim_id": "C-SC-BREACH",
    "as_of": "2026-11-20",
    "conclusion": "holds",
    "premises": [
        {
            "fact_id": "F-LOOP-92",
            "statement": "Clause 9.2 requires Nimbus to keep transfer logs for review.",
            "trust_class": "document_extracted",
        }
    ],
    "steps": [
        {"kind": "cite_fact", "fact_id": "F-LOOP-92"},
        {
            "kind": "cite_rule",
            "rule_card_id": "RC-CT3-BREACH-01",
            "citation": {
                "source_version_id": "SV-DPDP-ACT-V1",
                "provision_id": "PRV-DPDP-Act-2023-s8-6",
                "span": [0, 10],
                "sha256": "unused-by-entailment",
            },
        },
        {"kind": "conclude", "conclusion": "holds"},
    ],
}


def seeded_session(tmp_path: Path) -> Session:
    """Seeded demo DB plus one CURRENT finding citing the s8(6) card."""
    db = tmp_path / "cf.db"
    seed.seed_demo(db, CORPUS_ROOT)
    session = sessionmaker(bind=init_db(db), future=True)()
    session.add(
        models.Claim(
            id="C-SC-BREACH",
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
            id="FND-SC-BREACH",
            claim_id="C-SC-BREACH",
            version_no=1,
            status="FOLLOWS",
            confidence_band="high",
            proof_json=PROOF,
            as_of="2026-11-20",
            checker_report_json={"valid": True, "errors": [], "cited_source_versions": []},
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.FindingEvent(
            id="FE-SC-BREACH",
            finding_id="FND-SC-BREACH",
            state="CURRENT",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    graph.add_edge(
        session,
        src_type="finding",
        src_id="FND-SC-BREACH",
        dst_type="rule_card",
        dst_id="RC-CT3-BREACH-01",
        rel="DEPENDS_ON",
    )
    session.commit()
    return session


def _counts(session: Session) -> dict[str, int]:
    """Row counts the dry run must never change."""
    return {
        table.__tablename__: session.execute(
            sa.select(sa.func.count()).select_from(table)
        ).scalar()
        or 0
        for table in (models.Finding, models.FindingEvent, models.Edge, models.AuditLog)
    }


def test_counterfactual_flags_dependent_as_invalid(tmp_path: Path) -> None:
    """Simulated v2 changes s8(6): the dependent finding would not remain valid."""
    session = seeded_session(tmp_path)
    before = _counts(session)
    result = counterfactual.run_counterfactual(session, "SV-DPDP-ACT-V2SIM")
    assert result["available"] is True
    assert result["changed_keys"] == ["DPDP-Act-2023_s8(6)"]
    affected_ids = [item["finding_id"] for item in result["affected"]]
    # The seed attaches one finding per s8(6) card (both breach cards).
    assert affected_ids == [
        "FND-RC-CT3-BREACH-01",
        "FND-RC-CT3-BREACH-CONFLICT-01",
        "FND-SC-BREACH",
    ]
    item = next(i for i in result["affected"] if i["finding_id"] == "FND-SC-BREACH")
    assert item["would_remain_valid"] is False
    assert item["logic"]["valid"] is False
    assert item["logic"]["counterexample"] is not None
    assert "FND-SC-BREACH" in result["reverify_list"]
    assert _counts(session) == before
    session.close()


def test_counterfactual_decoy_affects_nothing(tmp_path: Path) -> None:
    """A version with no predecessor/dependents affects no findings."""
    session = seeded_session(tmp_path)
    result = counterfactual.run_counterfactual(session, "SV-DECOY-V1")
    assert result["available"] is True
    assert result["affected"] == []
    assert result["reverify_list"] == []
    session.close()


def test_counterfactual_unknown_version(tmp_path: Path) -> None:
    """Unknown versions report unavailable, not an exception or a write."""
    session = seeded_session(tmp_path)
    result = counterfactual.run_counterfactual(session, "SV-NOPE")
    assert result["available"] is False
    assert "SV-NOPE" in result["note"]
    session.close()


def test_counterfactual_and_reverify_list_endpoints(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """T7.3 API: counterfactual dry run + STALE findings in reverify-list."""
    import asyncio

    import httpx

    from app.services import impact

    db = tmp_path / "cfapi.db"
    seed.seed_demo(db, CORPUS_ROOT)
    session = sessionmaker(bind=init_db(db), future=True)()
    # One CURRENT finding dependent on the s8(6) card, then really apply v2.
    session.add(
        models.Claim(
            id="C-SC-BREACH",
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
            id="FND-SC-BREACH",
            claim_id="C-SC-BREACH",
            version_no=1,
            status="FOLLOWS",
            confidence_band="high",
            proof_json=PROOF,
            as_of="2026-11-20",
            checker_report_json={"valid": True, "errors": [], "cited_source_versions": []},
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.FindingEvent(
            id="FE-SC-BREACH",
            finding_id="FND-SC-BREACH",
            state="CURRENT",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    graph.add_edge(
        session,
        src_type="finding",
        src_id="FND-SC-BREACH",
        dst_type="rule_card",
        dst_id="RC-CT3-BREACH-01",
        rel="DEPENDS_ON",
    )
    session.commit()
    impact.apply_version(session, "SV-DPDP-ACT-V2SIM")
    session.close()

    monkeypatch.setenv("API_STUB", "0")
    monkeypatch.setenv("CLAUSETRACE_DB", str(db))
    from app.main import create_app

    app = create_app()

    async def call(method: str, path: str, body: object = None) -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
            if method == "get":
                return await client.get(path)
            return await client.post(path, json=body)

    listed = asyncio.run(call("get", "/api/reverify-list?matter_id=MAT-01"))
    assert listed.status_code == 200, listed.text
    listed_ids = [item["finding_id"] for item in listed.json()["findings"]]
    assert "FND-SC-BREACH" in listed_ids
    assert all(item["reason"] == "STALE" for item in listed.json()["findings"])
    dry = asyncio.run(
        call("post", "/api/counterfactual", {"source_version_id": "SV-DPDP-ACT-V2SIM"})
    )
    assert dry.status_code == 200, dry.text
    assert "FND-SC-BREACH" in dry.json()["reverify_list"]
    empty = asyncio.run(call("post", "/api/counterfactual", {"provision_key": "x"}))
    assert empty.json()["available"] is False
