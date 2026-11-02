"""Phase 2 (contract v9): lawyer display labels beside the machine fields."""

import asyncio
from pathlib import Path
from typing import Any

import httpx
import pytest

from app.services import seed

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "corpus"

FOLLOWS_LABEL = "Meets the requirement — on the facts and law listed below"
STALE_LABEL = "Needs re-check: the law it relied on has changed"
CONFLICTING_LABEL = "Two readings of the law conflict — your call"


def make_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Real router on a freshly seeded demo DB (Phase 2)."""
    db = tmp_path / "labels.db"
    seed.seed_demo(db, CORPUS_ROOT)
    monkeypatch.setenv("API_STUB", "0")
    monkeypatch.setenv("CLAUSETRACE_DB", str(db))
    from app.main import create_app

    return create_app()


async def _call(app: Any, method: str, path: str, body: Any = None) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
        if method == "get":
            return await client.get(path)
        return await client.post(path, json=body)


def get(app: Any, path: str) -> httpx.Response:
    return asyncio.run(_call(app, "get", path))


def post(app: Any, path: str, body: Any = None) -> httpx.Response:
    return asyncio.run(_call(app, "post", path, body))


def test_finding_display_labels(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """V9: an asked finding carries lawyer labels; machine fields unchanged."""
    app = make_app(tmp_path, monkeypatch)
    created = post(
        app,
        "/api/claims",
        {
            "clause_id": "CL-10",
            "question": seed.DEMO_92_QUESTION,
            "as_of": seed.DEMO_92_AS_OF,
        },
    )
    assert created.status_code == 200, created.text
    current = get(app, f"/api/claims/{created.json()['claim_id']}/current").json()
    assert current["status"] == "FOLLOWS"  # machine field stays
    assert current["status_label"] == FOLLOWS_LABEL
    assert current["clause_ref"] == "9.2"
    assert "transfer logs" in current["clause_quote"]
    assert current["id"].startswith("FND-")  # id still present, beside labels
    assert current["proof"]["steps"]  # proof JSON still present
    line = current["fact_lines"][0]
    assert line["label"] == current["proof"]["premises"][0]["statement"]
    assert line["trust_label"] == "Taken from the document"


def test_finding_section_and_law_version_labels(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """V9: the seeded breach finding names its section and law version."""
    app = make_app(tmp_path, monkeypatch)
    finding = get(app, "/api/findings/FND-RC-CT3-BREACH-01").json()
    assert finding["section_label"].endswith("s 8(6)")
    assert "personal data breach" in finding["section_quote"]
    assert "version v1" in finding["law_version_label"]
    assert finding["law_version_date"] == "2025-11-13"


def test_impact_and_reverify_labels(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """V9: STALE rows read as re-check needs, with their clause ref."""
    app = make_app(tmp_path, monkeypatch)
    monkeypatch.setenv("DEMO_MODE", "1")
    scenario = post(app, "/api/demo/scenario/stale-demo", {})
    assert scenario.status_code == 200, scenario.text
    listed = get(app, "/api/reverify-list?matter_id=MAT-01").json()["findings"]
    assert listed, "expected stale findings after the scenario"
    for item in listed:
        assert item["reason"] == "STALE"  # machine field stays
        assert item["reason_label"] == STALE_LABEL
        assert item["finding_id"].startswith("FND-")
        assert item["clause_ref"]
    impact = get(app, "/api/impact/IMP-SV-DPDP-ACT-V2SIM").json()
    for row in impact["affected"]:
        assert row["state"] == "STALE"
        assert row["status_label"] == STALE_LABEL
        assert row["clause_ref"]


def test_counterfactual_follow_label(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """V9: affected rows carry a plain would-follow sentence."""
    app = make_app(tmp_path, monkeypatch)
    result = post(app, "/api/counterfactual", {"source_version_id": "SV-DPDP-ACT-V2SIM"})
    assert result.status_code == 200, result.text
    row = next(
        item for item in result.json()["affected"] if item["finding_id"] == "FND-RC-CT3-BREACH-01"
    )
    assert row["would_remain_valid"] is False  # machine field stays
    assert row["would_follow_label"] == "This answer would no longer follow"
    assert row["logic"]["valid"] is False  # logic still present


def test_trust_labels_on_facts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """V9: facts carry trust_label beside trust_class."""
    app = make_app(tmp_path, monkeypatch)
    facts = {f["id"]: f for f in get(app, "/api/matters/MAT-01/facts").json()["facts"]}
    assert facts["F-LOOP-92"]["trust_class"] == "document_extracted"
    assert facts["F-LOOP-92"]["trust_label"] == "Taken from the document"
    approved = post(app, "/api/facts/F-LOOP-92/approve", {"reviewer": "lawyer"})
    assert approved.status_code == 200, approved.text
    facts = {f["id"]: f for f in get(app, "/api/matters/MAT-01/facts").json()["facts"]}
    confirmed = facts[approved.json()["fact_id"]]
    assert confirmed["trust_label"] == "Confirmed by you"
    challenged = post(
        app, f"/api/facts/{approved.json()['fact_id']}/challenge", {"reason": " doubt"}
    )
    facts = {f["id"]: f for f in get(app, "/api/matters/MAT-01/facts").json()["facts"]}
    assert facts[challenged.json()["fact_id"]]["trust_label"] == "Disputed by you"


def test_error_messages_are_plain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """V9: codes stay; messages carry no cassette/502/MODEL_ wording."""
    app = make_app(tmp_path, monkeypatch)
    missed = post(
        app,
        "/api/claims",
        {
            "clause_id": "CL-10",
            "question": "An unrecorded question about clause 9.2?",
            "as_of": "2026-11-20",
        },
    )
    assert missed.status_code == 502
    error = missed.json()["error"]
    assert error["code"] == "MODEL_UNAVAILABLE"  # code stays
    for banned in ("cassette", "502", "MODEL_"):
        assert banned not in error["message"]

    created = post(
        app,
        "/api/claims",
        {
            "clause_id": "CL-10",
            "question": seed.DEMO_92_QUESTION,
            "as_of": seed.DEMO_92_AS_OF,
        },
    )
    claim_id = created.json()["claim_id"]
    proof = get(app, f"/api/claims/{claim_id}/current").json()["proof"]
    proof["premises"][0]["statement"] = "Edited wording."
    verified = post(app, "/api/proofs/verify", {"claim_id": claim_id, "proof": proof})
    messages = {e["code"]: e["message"] for e in verified.json()["errors"]}
    assert messages["PREMISE_MISMATCH"] == "This fact no longer matches the document"
