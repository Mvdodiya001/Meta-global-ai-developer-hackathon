"""Phase 6: upload safety, rate limiting, audit export."""

import asyncio
import base64
from pathlib import Path
from typing import Any

import httpx
import pytest
from sqlalchemy.orm import sessionmaker

from app import models
from app.db import init_db
from app.modules.intake import safety


def make_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Real router on a scratch DB with one matter (Phase 6)."""
    db = tmp_path / "hardening.db"
    engine = init_db(db)
    session = sessionmaker(bind=engine, future=True)()
    session.add(models.Matter(id="MAT-01", client_name="Acme", title="M1"))
    session.commit()
    session.close()
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


def call(app: Any, method: str, path: str, body: Any = None) -> httpx.Response:
    return asyncio.run(_call(app, method, path, body))


def test_upload_rejects_eicar_signature(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Phase 6: the malware canary is rejected before any parsing."""
    app = make_app(tmp_path, monkeypatch)
    payload = base64.b64encode(b"9.2 clause text " + b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE").decode()
    response = call(
        app,
        "post",
        "/api/matters/MAT-01/documents/upload",
        {"title": "bad", "file_base64": payload, "media_type": "text/plain"},
    )
    assert response.status_code == 400, response.text
    assert response.json()["error"]["code"] == "UPLOAD_REJECTED"


def test_size_limit_unit() -> None:
    """Phase 6: oversize payloads are rejected by the gate."""
    with pytest.raises(safety.UploadRejected):
        safety.check_size(b"x" * 11, limit=10)
    safety.check_size(b"x" * 10, limit=10)


def test_rate_limit_rejects_bursts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Phase 6: the fourth write in a minute is a 429 when limited to 3."""
    monkeypatch.setenv("CT_RATE_LIMIT_PER_MIN", "3")
    app = make_app(tmp_path, monkeypatch)
    statuses = [
        call(app, "post", "/api/matters", {"title": f"M{i}", "client_name": "C"}).status_code
        for i in range(4)
    ]
    assert statuses[:3] == [201, 201, 201]
    assert statuses[3] == 429


def test_audit_export_shape(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Phase 6: audit export returns the matter's rows as a download shape."""
    app = make_app(tmp_path, monkeypatch)
    response = call(app, "get", "/api/matters/MAT-01/audit-export")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["matter_id"] == "MAT-01"
    assert body["exported_at"]
    assert isinstance(body["rows"], list)
