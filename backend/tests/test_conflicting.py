"""T7.4: CONFLICTING status when cited rule cards contradict each other."""

from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.agent import tools
from app.db import init_db
from app.services import memory


def make_session(tmp_path: Path) -> Session:
    """Fresh DB: one provision, an agreeing card and a conflicting pair."""
    engine = init_db(tmp_path / "conflict.db")
    session = sessionmaker(bind=engine, future=True)()
    session.add(models.Matter(id="MAT-01", client_name="Acme", title="M1"))
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
    for cid, requires in (
        ("RC-KEEP", ["transfer_logs_kept"]),
        ("RC-NOKEEP", ["no_transfer_logs_kept"]),
        ("RC-PLAIN", None),
    ):
        session.add(
            models.RuleCard(
                id=cid,
                provision_id="PRV-01",
                kind="statutory",
                claim_type="CT2",
                predicate_json={"requires": requires} if requires else None,
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
            id="F-E1",
            matter_id="MAT-01",
            clause_id=None,
            statement="Statement F-E1.",
            structured_json=None,
            origin="extracted",
            trust_class="document_extracted",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Claim(
            id="C-01",
            matter_id="MAT-01",
            clause_id="CL-01",
            claim_type="CT2",
            params_json={"element": "transfer logs"},
            question_text="Does clause 9.2 require transfer logs?",
            as_of="2026-11-20",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Run(
            id="RUN-01", trigger="verify", claim_id="C-01", started_at="2026-01-01T00:00:00Z"
        )
    )
    session.commit()
    tools.call_tool(
        session,
        run_id="RUN-01",
        matter_id="MAT-01",
        tool="lookup_source",
        args={"source_id": "SRC-01"},
    )
    return session


def proof_with_cards(*card_ids: str, statement: str = "Statement F-E1.") -> dict[str, Any]:
    """Checker-valid proof citing the given cards on PRV-01."""
    steps: list[dict[str, Any]] = [{"kind": "cite_fact", "fact_id": "F-E1"}]
    for card_id in card_ids:
        steps.append(
            {
                "kind": "cite_rule",
                "rule_card_id": card_id,
                "citation": {
                    "source_version_id": "SV-01",
                    "provision_id": "PRV-01",
                    "span": [0, 22],
                    "sha256": "b" * 64,
                },
            }
        )
    steps.append({"kind": "conclude", "conclusion": "holds"})
    return {
        "claim_id": "C-01",
        "as_of": "2026-11-20",
        "conclusion": "holds",
        "premises": [
            {"fact_id": "F-E1", "statement": statement, "trust_class": "document_extracted"}
        ],
        "steps": steps,
    }


def test_conflicting_cards_decide_conflicting(tmp_path: Path) -> None:
    """T7.4: x and not-x cited together → CONFLICTING, band low, edges kept."""
    session = make_session(tmp_path)
    finding = memory.decide_finding(
        session, claim_id="C-01", proof=proof_with_cards("RC-KEEP", "RC-NOKEEP"), run_id="RUN-01"
    )
    assert finding.status == "CONFLICTING"
    assert finding.confidence_band == "low"
    assert set(finding.rule_card_ids_json or []) == {"RC-KEEP", "RC-NOKEEP"}
    session.close()


def test_agreeing_cards_still_follow(tmp_path: Path) -> None:
    """T7.4: one stance (or a requirement-free card) decides normally."""
    session = make_session(tmp_path)
    finding = memory.decide_finding(
        session, claim_id="C-01", proof=proof_with_cards("RC-KEEP", "RC-PLAIN"), run_id="RUN-01"
    )
    assert finding.status == "FOLLOWS"
    session.close()


def test_invalid_proof_beats_conflict(tmp_path: Path) -> None:
    """T7.4: a tampered proof is REQUIRES_REVIEW even with conflicting cards."""
    session = make_session(tmp_path)
    draft = proof_with_cards("RC-KEEP", "RC-NOKEEP", statement="TAMPERED.")
    finding = memory.decide_finding(session, claim_id="C-01", proof=draft, run_id="RUN-01")
    assert finding.status == "REQUIRES_REVIEW"
    session.close()


def test_demo_conflict_card_end_to_end(tmp_path: Path) -> None:
    """T7.4 demo card: real corpus cards, citing both decides CONFLICTING.

    Uses a v1-only corpus (no simulated v2, so the Act version is current
    and cite_rule can pass the checker), the shipped RC-CT3-BREACH-01 and
    the demo RC-CT3-BREACH-CONFLICT-01.
    """
    from app.services import rulecards, sources

    corpus = Path(__file__).resolve().parents[2] / "corpus"
    engine = init_db(tmp_path / "demo-conflict.db")
    session = sessionmaker(bind=engine, future=True)()
    manifest = sources.load_manifest(corpus / "raw")
    texts = {
        item["file"]: (corpus / "raw" / item["file"]).read_text(encoding="utf-8")
        for version in manifest["versions"]
        for item in version["provisions"]
    }
    for spec in manifest["sources"]:
        sources.ensure_source(session, spec)
    session.commit()
    for spec in manifest["versions"]:
        if spec["id"] in ("SV-DPDP-ACT-V1", "SV-DPDP-RULES-V1"):
            sources.ingest_version(session, spec, texts)
    rulecards.load_rulecards(session, corpus / "rulecards")
    card_ids = {
        row.id for row in session.execute(sa.select(models.RuleCard)).scalars().all()
    }
    assert "RC-CT3-BREACH-CONFLICT-01" in card_ids
    assert len(card_ids) == 8

    session.add(models.Matter(id="MAT-01", client_name="Acme", title="M1"))
    session.add(
        models.Fact(
            id="F-E1",
            matter_id="MAT-01",
            clause_id=None,
            statement="Statement F-E1.",
            structured_json=None,
            origin="extracted",
            trust_class="document_extracted",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    for claim_id in ("C-BOTH", "C-ONE"):
        session.add(
            models.Claim(
                id=claim_id,
                matter_id="MAT-01",
                clause_id="CL-01",
                claim_type="CT3",
                params_json={"date": "2027-06-01"},
                question_text="Breach intimation?",
                as_of="2026-11-20",
                created_at="2026-01-01T00:00:00Z",
            )
        )
        session.add(
            models.Run(
                id=f"RUN-{claim_id}",
                trigger="verify",
                claim_id=claim_id,
                started_at="2026-01-01T00:00:00Z",
            )
        )
    session.commit()

    provision = session.get(models.Provision, "PRV-DPDP-Act-2023-s8-6")
    assert provision is not None
    citation = {
        "source_version_id": "SV-DPDP-ACT-V1",
        "provision_id": provision.id,
        "span": [0, 189],
        "sha256": provision.text_sha256,
    }

    def decide_with(cards: list[str], claim_id: str) -> models.Finding:
        tools.call_tool(
            session,
            run_id=f"RUN-{claim_id}",
            matter_id="MAT-01",
            tool="lookup_source",
            args={"source_id": "SRC-DPDP-ACT"},
        )
        steps: list[dict[str, Any]] = [{"kind": "cite_fact", "fact_id": "F-E1"}]
        for card_id in cards:
            steps.append(
                {"kind": "cite_rule", "rule_card_id": card_id, "citation": citation}
            )
        steps.append({"kind": "conclude", "conclusion": "holds"})
        return memory.decide_finding(
            session,
            claim_id=claim_id,
            proof={
                "claim_id": claim_id,
                "as_of": "2026-11-20",
                "conclusion": "holds",
                "premises": [
                    {
                        "fact_id": "F-E1",
                        "statement": "Statement F-E1.",
                        "trust_class": "document_extracted",
                    }
                ],
                "steps": steps,
            },
            run_id=f"RUN-{claim_id}",
        )

    both = decide_with(["RC-CT3-BREACH-01", "RC-CT3-BREACH-CONFLICT-01"], "C-BOTH")
    assert both.status == "CONFLICTING", both.checker_report_json
    one = decide_with(["RC-CT3-BREACH-01"], "C-ONE")
    assert one.status == "FOLLOWS", one.checker_report_json
    session.close()


def test_conflicting_finding_joins_reverify_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """T7.4: CONFLICTING findings appear in GET /api/reverify-list."""
    import asyncio

    import httpx

    session = make_session(tmp_path)
    finding = memory.decide_finding(
        session, claim_id="C-01", proof=proof_with_cards("RC-KEEP", "RC-NOKEEP"), run_id="RUN-01"
    )
    finding_id = str(finding.id)
    session.close()
    monkeypatch.setenv("API_STUB", "0")
    monkeypatch.setenv("CLAUSETRACE_DB", str(tmp_path / "conflict.db"))
    from app.main import create_app

    app = create_app()

    async def get(path: str) -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
            return await client.get(path)

    listed = asyncio.run(get("/api/reverify-list?matter_id=MAT-01"))
    assert listed.status_code == 200, listed.text
    assert listed.json()["findings"] == [
        {
            "finding_id": finding_id,
            "claim_id": "C-01",
            "reason": "CONFLICTING",
            "reason_label": "Two readings of the law conflict — your call",
            "clause_ref": "",
        }
    ]
