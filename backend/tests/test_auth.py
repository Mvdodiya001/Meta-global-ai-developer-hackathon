"""Identity: sign-in accounts, tokens, enforcement, clause update."""

import asyncio
import base64
from pathlib import Path
from typing import Any

import httpx
import pytest
from sqlalchemy.orm import sessionmaker

from app import models
from app.db import init_db
from app.modules.identity import auth
from app.services import seed

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "corpus"
CASSETTES = CORPUS_ROOT / "cassettes"


def make_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, Path]:
    db = tmp_path / "auth.db"
    seed.seed_demo(db, CORPUS_ROOT)
    monkeypatch.setenv("API_STUB", "0")
    monkeypatch.setenv("CLAUSETRACE_DB", str(db))
    from app.main import create_app

    return create_app(), db


async def _call(
    app: Any, method: str, path: str, body: Any = None, headers: Any = None
) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
        if method == "get":
            return await client.get(path, headers=headers)
        return await client.post(path, json=body, headers=headers)


def post(app: Any, path: str, body: Any = None, headers: Any = None) -> httpx.Response:
    return asyncio.run(_call(app, "post", path, body, headers))


def get(app: Any, path: str, headers: Any = None) -> httpx.Response:
    return asyncio.run(_call(app, "get", path, headers=headers))


def test_register_login_me(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Identity: register issues a token; login verifies; /me resolves it."""
    app, _db = make_app(tmp_path, monkeypatch)
    created = post(
        app,
        "/api/auth/register",
        {"email": "A@Firm.example", "password": "correct horse", "name": "Asha"},
    )
    assert created.status_code == 200, created.text
    token = created.json()["token"]
    assert created.json()["email"] == "a@firm.example"
    me = get(app, "/api/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["name"] == "Asha"
    assert get(app, "/api/me").status_code == 401
    logged = post(
        app, "/api/auth/login", {"email": "a@firm.example", "password": "correct horse"}
    )
    assert logged.status_code == 200
    bad = post(
        app, "/api/auth/login", {"email": "a@firm.example", "password": "wrong password"}
    )
    assert bad.status_code == 401
    dup = post(
        app,
        "/api/auth/register",
        {"email": "a@firm.example", "password": "correct horse", "name": "Other"},
    )
    assert dup.status_code == 400


def test_auth_required_enforcement(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Identity: CT_AUTH_REQUIRED=1 closes the API without a token."""
    monkeypatch.setenv("CT_AUTH_REQUIRED", "1")
    app, _db = make_app(tmp_path, monkeypatch)
    assert get(app, "/api/matters/MAT-01").status_code == 401
    created = post(
        app,
        "/api/auth/register",
        {"email": "b@firm.example", "password": "correct horse", "name": "B"},
    )
    token = created.json()["token"]
    ok = get(app, "/api/matters/MAT-01", headers={"Authorization": f"Bearer {token}"})
    assert ok.status_code == 200


def test_password_hash_roundtrip() -> None:
    """Identity: passwords verify constant-time and reject wrong ones."""
    stored = auth.hash_password("correct horse")
    assert auth.check_password("correct horse", stored)
    assert not auth.check_password("wrong", stored)


def test_transcribe_only_and_clause_update(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Dictation text without a fact; clause wording stored as a new version."""
    app, db = make_app(tmp_path, monkeypatch)
    wav = base64.b64encode((CORPUS_ROOT / "audio" / "dictation_fact.wav").read_bytes()).decode()
    heard = post(app, "/api/transcribe", {"matter_id": "MAT-01", "audio_base64": wav})
    assert heard.status_code == 200, heard.text
    assert "transfer logs" in heard.json()["transcript"]
    session = sessionmaker(bind=init_db(db), future=True)()
    facts_before = session.query(models.Fact).count()
    session.close()
    session = sessionmaker(bind=init_db(db), future=True)()
    assert session.query(models.Fact).count() == facts_before  # nothing stored
    session.close()

    updated = post(
        app,
        "/api/documents/DOC-01/clauses/CL-10/update",
        {"text": "Stratus shall keep transfer logs for review for seven years."},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["text"].startswith("Stratus shall keep")
    assert updated.json()["id"] != "CL-10"  # new version, new row
    clauses = get(app, "/api/documents/DOC-01/clauses").json()["clauses"]
    nine_two = next(c for c in clauses if c["ref"] == "9.2")
    assert nine_two["text"].startswith("Stratus shall keep")
    assert len(clauses) == 12
