"""Phase 2a: model-drafted rule cards + lawyer confirmation queue."""

import asyncio
from pathlib import Path
from typing import Any

import httpx
import pytest
from sqlalchemy.orm import sessionmaker

from app import models
from app.db import init_db


def make_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Real router on a scratch DB with one provision (Phase 2a)."""
    db = tmp_path / "cards.db"
    engine = init_db(db)
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
            key="DPDP-Act-2023_s6",
            text="6. Consent shall be free, specific, informed and unambiguous. "
            "The Data Fiduciary shall give notice before seeking consent.",
            text_sha256="a" * 64,
            effective_from="2027-05-13",
            effective_until=None,
        )
    )
    session.commit()
    session.close()
    monkeypatch.setenv("API_STUB", "0")
    monkeypatch.setenv("CLAUSETRACE_DB", str(db))
    monkeypatch.setenv("LLM_MODE", "mock")
    from app.main import create_app

    return create_app()


async def _call(app: Any, method: str, path: str, body: Any = None) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
        if method == "get":
            return await client.get(path)
        return await client.post(path, json=body)


def call(app: Any, method: str, path: str, body: Any = None) -> httpx.Response:
    return asyncio.run(_call(app, method, path, body))


def test_draft_confirm_reject_flow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Phase 2a: draft (ai_inferred) -> confirm mints confirmed; reject leaves queue."""
    app = make_app(tmp_path, monkeypatch)

    provisions = call(app, "get", "/api/source-versions/SV-01/provisions")
    assert provisions.status_code == 200
    assert [p["id"] for p in provisions.json()["provisions"]] == ["PRV-01"]

    drafted = call(app, "post", "/api/rule-cards/draft", {"provision_id": "PRV-01"})
    assert drafted.status_code == 201, drafted.text
    draft = drafted.json()
    assert draft["trust_class"] == "ai_inferred"
    assert draft["provision_key"] == "DPDP-Act-2023_s6"
    assert "Consent shall be free" in draft["span_text"]

    again = call(app, "post", "/api/rule-cards/draft", {"provision_id": "PRV-01"})
    assert again.json()["id"] == draft["id"]  # idempotent

    queue = call(app, "get", "/api/rule-cards/drafts").json()["drafts"]
    assert [d["id"] for d in queue] == [draft["id"]]

    confirmed = call(
        app,
        "post",
        f"/api/rule-cards/{draft['id']}/confirm",
        {"reviewer": "counsel@example.com", "claim_type": "CT2"},
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["trust_class"] == "lawyer_confirmed"
    assert confirmed.json()["id"] != draft["id"]
    assert call(app, "get", "/api/rule-cards/drafts").json()["drafts"] == []

    # A second draft can be rejected out of the queue.
    drafted2 = call(app, "post", "/api/rule-cards/draft", {"provision_id": "PRV-01"})
    assert drafted2.status_code == 201
    rejected = call(app, "post", f"/api/rule-cards/{drafted2.json()['id']}/reject", {})
    assert rejected.status_code == 200
    assert call(app, "get", "/api/rule-cards/drafts").json()["drafts"] == []


def test_draft_unknown_provision_404(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Phase 2a: drafting for a missing provision is a typed 404."""
    app = make_app(tmp_path, monkeypatch)
    response = call(app, "post", "/api/rule-cards/draft", {"provision_id": "NOPE"})
    assert response.status_code == 404, response.text
