"""Phase 5: document comparison, coverage roll-up, review flagging."""

import asyncio
from pathlib import Path
from typing import Any

import httpx
import pytest
from sqlalchemy.orm import sessionmaker

from app import models
from app.db import init_db
from app.services import sources

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "corpus"


def make_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Real router: two documents in one matter over the real corpus."""
    db = tmp_path / "compare.db"
    engine = init_db(db)
    session = sessionmaker(bind=engine, future=True)()
    sources.load_corpus(session, CORPUS_ROOT / "raw")
    session.add(models.Matter(id="MAT-01", client_name="Acme", title="M1"))
    for doc_id, version_id, clauses in (
        (
            "DOC-A",
            "DV-A",
            (
                ("CL-A1", "9.2", "Nimbus shall keep transfer logs for review."),
                ("CL-A2", "10", "Nimbus shall intimate Acme within twenty-four hours of a breach."),
            ),
        ),
        (
            "DOC-B",
            "DV-B",
            (
                ("CL-B1", "9.2", "Nimbus shall keep transfer logs for three years."),
                ("CL-B2", "11", "Nimbus shall erase personal data on request."),
            ),
        ),
    ):
        session.add(models.Document(id=doc_id, matter_id="MAT-01", title=doc_id, kind="dpa"))
        session.add(
            models.DocumentVersion(
                id=version_id,
                document_id=doc_id,
                text="text",
                sha256="0" * 64,
                created_at="2026-01-01T00:00:00Z",
            )
        )
        for clause_id, ref, text in clauses:
            session.add(
                models.Clause(
                    id=clause_id,
                    document_version_id=version_id,
                    ref=ref,
                    heading=f"Clause {ref}",
                    text=text,
                    span_start=0,
                    span_end=len(text),
                )
            )
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


def test_compare_aligns_by_ref(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Phase 5: shared refs pair up; wording differences are flagged."""
    app = make_app(tmp_path, monkeypatch)
    response = call(app, "get", "/api/matters/MAT-01/compare?a=DOC-A&b=DOC-B")
    assert response.status_code == 200, response.text
    report = response.json()
    assert [(p["ref"], p["changed"]) for p in report["pairs"]] == [("9.2", True)]
    assert report["only_a"] == ["10"]
    assert report["only_b"] == ["11"]


def test_coverage_matches_provisions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Phase 5: every clause gets a matched provision from the corpus."""
    app = make_app(tmp_path, monkeypatch)
    response = call(app, "get", "/api/documents/DOC-A/coverage")
    assert response.status_code == 200, response.text
    rows = response.json()["rows"]
    assert [row["ref"] for row in rows] == ["9.2", "10"]
    assert all(row["provision_key"] for row in rows)
    assert all(row["source_title"] for row in rows)


def test_flag_records_review_not_finding(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Phase 5: flagging writes a Review row; no finding is created."""
    app = make_app(tmp_path, monkeypatch)
    response = call(app, "post", "/api/matters/MAT-01/compare/flag", {"clause_ref": "9.2"})
    assert response.status_code == 200, response.text
    assert response.json() == {"flagged": True, "clause_ref": "9.2"}

    engine = init_db(tmp_path / "compare.db")
    session = sessionmaker(bind=engine, future=True)()
    reviews = session.query(models.Review).all()
    assert len(reviews) == 1 and reviews[0].status == "flagged"
    assert session.query(models.Finding).count() == 0
    session.close()
