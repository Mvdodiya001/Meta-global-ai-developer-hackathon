"""Rewrite P5: eval gate + per-tenant budgets + performance budgets."""

import time
from pathlib import Path

import pytest
from sqlalchemy.orm import sessionmaker

from app import models
from app.agent import budgets
from app.agent.evals import run_evals
from app.core.errors import LLMRequestFailed
from app.db import init_db
from app.services import seed

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "corpus"


def test_eval_gate_report_shape(tmp_path: Path) -> None:
    """P5: the golden gate passes on record with zero violations."""
    report = run_evals(tmp_path / "evals.db")
    assert report["total"] == 5
    assert report["gate_passed"] is True, report
    assert report["verdict_agreement"] == 1.0
    assert report["premise_violations"] == 0


def test_tenant_budget(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """P5: spend sums per tenant; over-budget raises in live checks."""
    db = tmp_path / "budget.db"
    seed.seed_demo(db, CORPUS_ROOT)
    session = sessionmaker(bind=init_db(db), future=True)()
    session.add(
        models.Run(
            id="RUN-B", trigger="verify", claim_id="C-LOOP-92",
            started_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.LlmCall(
            id="LC-B", run_id="RUN-B", role="agent", model="muse-spark-1.3-contributor",
            request_sha256="x", tokens_in=1, tokens_out=1, cost_est=2.5,
            latency_ms=1, cached=False,
        )
    )
    session.commit()
    assert budgets.spend_for_tenant(session, "demo") == pytest.approx(2.5)
    assert budgets.spend_for_tenant(session, "other") == 0.0
    monkeypatch.setenv("CT_TENANT_BUDGET_USD", "2.0")
    with pytest.raises(LLMRequestFailed, match="over its model budget"):
        budgets.check_budget(session, "demo")
    assert budgets.check_budget(session, "other") == 0.0
    session.close()


def test_admin_overview_counts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """P5: the internal overview reports counts and spend for staff."""
    import asyncio

    import httpx

    db = tmp_path / "admin.db"
    seed.seed_demo(db, CORPUS_ROOT)
    monkeypatch.setenv("API_STUB", "0")
    monkeypatch.setenv("CLAUSETRACE_DB", str(db))
    from app.main import create_app

    app = create_app()

    async def get(path: str) -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
            return await client.get(path)

    response = asyncio.run(get("/api/admin/overview"))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tenant_id"] == "demo"
    assert body["matters"] == 1
    assert body["findings_by_status"].get("FOLLOWS", 0) >= 1
    assert "document_extracted" in body["facts_by_trust"]
    assert body["spend_usd"] >= 0.0


def test_checker_performance_budget() -> None:
    """P5: the deterministic checker decides well under 10 ms per proof."""
    from checker.verify import verify

    text = "current provision text"
    proof = {
        "claim_id": "C-01", "as_of": "2026-11-20", "conclusion": "holds",
        "premises": [
            {"fact_id": "F-1", "statement": "s", "trust_class": "document_extracted"}
        ],
        "steps": [
            {"kind": "cite_fact", "fact_id": "F-1"},
            {"kind": "conclude", "conclusion": "holds"},
        ],
    }
    premises = {"F-1": {"statement": "s", "trust_class": "document_extracted"}}
    provisions = {
        "PRV-01": {
            "source_version_id": "SV-01", "key": "Section 6", "text": text,
            "text_sha256": "b" * 64, "effective_from": "2023-08-11",
            "effective_until": None,
        }
    }
    started = time.perf_counter()
    for _ in range(50):
        verify(proof, premises, provisions, {}, {}, {}, as_of="2026-11-20")
    elapsed_ms = (time.perf_counter() - started) * 1000 / 50
    assert elapsed_ms < 10, f"checker took {elapsed_ms:.2f} ms per proof"
