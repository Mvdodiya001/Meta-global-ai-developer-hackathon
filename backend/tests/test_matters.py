"""Phase 0: matter CRUD + membership visibility."""

import asyncio
from pathlib import Path
from typing import Any

import httpx
import pytest
from sqlalchemy.orm import sessionmaker

from app import models
from app.db import init_db


def make_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Real router on a scratch DB with one seeded matter (Phase 0)."""
    db = tmp_path / "matters.db"
    engine = init_db(db)
    session = sessionmaker(bind=engine, future=True)()
    session.add(models.Matter(id="MAT-01", client_name="Acme", title="Seeded"))
    session.commit()
    session.close()
    monkeypatch.setenv("API_STUB", "0")
    monkeypatch.setenv("CLAUSETRACE_DB", str(db))
    from app.main import create_app

    return create_app()


async def _call(
    app: Any, method: str, path: str, body: Any = None, token: str | None = None
) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with httpx.AsyncClient(
        transport=transport, base_url="http://t", headers=headers
    ) as client:
        if method == "get":
            return await client.get(path)
        return await client.post(path, json=body)


def call(
    app: Any, method: str, path: str, body: Any = None, token: str | None = None
) -> httpx.Response:
    return asyncio.run(_call(app, method, path, body, token))


def register(app: Any, email: str) -> str:
    response = call(
        app, "post", "/api/auth/register", {"email": email, "password": "password123", "name": "T"}
    )
    assert response.status_code == 200, response.text
    return str(response.json()["token"])


def test_list_and_create_matter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Phase 0: anonymous list shows seeded matter; create adds one."""
    app = make_app(tmp_path, monkeypatch)
    listed = call(app, "get", "/api/matters")
    assert listed.status_code == 200
    assert [m["id"] for m in listed.json()["matters"]] == ["MAT-01"]

    created = call(app, "post", "/api/matters", {"title": "New DPA review", "client_name": "Beta"})
    assert created.status_code == 201, created.text
    assert created.json()["title"] == "New DPA review"
    ids = [m["id"] for m in call(app, "get", "/api/matters").json()["matters"]]
    assert created.json()["id"] in ids


def test_created_matter_is_private_to_creator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Phase 0: membership filter hides another user's created matter."""
    app = make_app(tmp_path, monkeypatch)
    token_a = register(app, "a@example.com")
    token_b = register(app, "b@example.com")

    created = call(
        app,
        "post",
        "/api/matters",
        {"title": "A private", "client_name": "A Co"},
        token=token_a,
    )
    assert created.status_code == 201, created.text
    private_id = created.json()["id"]

    mine = [m["id"] for m in call(app, "get", "/api/matters", token=token_a).json()["matters"]]
    theirs = [m["id"] for m in call(app, "get", "/api/matters", token=token_b).json()["matters"]]
    assert private_id in mine
    assert "MAT-01" in mine  # joined existing workspace at registration
    assert private_id not in theirs
    assert "MAT-01" in theirs


def test_create_matter_validates_body(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Phase 0: empty title is a typed 400, not a 500."""
    app = make_app(tmp_path, monkeypatch)
    response = call(app, "post", "/api/matters", {"title": "  ", "client_name": "Beta"})
    assert response.status_code == 400, response.text
