"""T7.2: scanned page → clause text (replay cassette + endpoint storage)."""

import base64
from pathlib import Path

import pytest
from sqlalchemy.orm import sessionmaker

from app import models
from app.agent import scan
from app.db import init_db
from app.services import seed

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "corpus"
CASSETTES = CORPUS_ROOT / "cassettes"
FIXTURE = CORPUS_ROOT / "scans" / "clause_9_2_page.png"


def test_parse_scan_validation() -> None:
    """T7.2: malformed emit_scan arguments are rejected with ScanError."""
    with pytest.raises(scan.ScanError):
        scan.parse_scan({"clause_ref": "9.2", "heading": "x", "text": "", "fact_statement": "y"})
    with pytest.raises(scan.ScanError):
        scan.parse_scan("nope")
    parsed = scan.parse_scan(
        {"clause_ref": "9.2", "heading": "h", "text": "body", "fact_statement": "fact"}
    )
    assert parsed.clause_ref == "9.2"


def test_scan_rejects_unprobed_media() -> None:
    """T7.2: PDF input was not probed on this tier; reject, never guess."""
    with pytest.raises(scan.ScanError, match="unsupported media type"):
        scan.scan_page(b"%PDF-fake", media_type="application/pdf", cache_dir=CASSETTES)


def test_replay_scan_transcribes_fixture() -> None:
    """T7.2: the fictional scanned page transcribes in replay mode."""
    image = FIXTURE.read_bytes()
    result = scan.scan_page(image, cache_dir=CASSETTES)
    assert result.cached is True
    assert result.clause_ref == "9.2"
    assert "transfer logs" in result.text
    assert "transfer logs" in result.fact_statement


def test_scan_endpoint_stores_document_extracted_fact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """T7.2: POST /api/scans stores a new document, clause and admitted fact."""
    import asyncio

    import httpx

    db = tmp_path / "scan.db"
    seed.seed_demo(db, CORPUS_ROOT)
    monkeypatch.setenv("API_STUB", "0")
    monkeypatch.setenv("CLAUSETRACE_DB", str(db))
    from app.main import create_app

    app = create_app()

    async def post(path: str, body: object) -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
            return await client.post(path, json=body)

    image_b64 = base64.b64encode(FIXTURE.read_bytes()).decode()
    created = asyncio.run(
        post(
            "/api/scans",
            {"matter_id": "MAT-01", "title": "Scanned clause 9.2", "image_base64": image_b64},
        )
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["clause"]["ref"] == "9.2"
    assert body["fact"]["trust_class"] == "document_extracted"
    assert body["fact"]["clause_id"] == body["clause"]["id"]

    session = sessionmaker(bind=init_db(db), future=True)()
    document = session.get(models.Document, body["document_id"])
    assert document is not None
    assert document.kind == "scan"
    fact = session.get(models.Fact, body["fact"]["id"])
    assert fact is not None
    assert fact.trust_class == "document_extracted"
    session.close()

    bad = asyncio.run(
        post(
            "/api/scans",
            {"matter_id": "MAT-01", "title": "x", "image_base64": "not-base64!!"},
        )
    )
    assert bad.status_code == 400
