"""Rewrite P3: intake jobs, PDF pipeline, upload, lawyer correction, gate."""

import asyncio
import base64
from pathlib import Path
from typing import Any

import httpx
import pytest
from sqlalchemy.orm import sessionmaker

from app import models
from app.agent import tools
from app.db import init_db
from app.modules.intake import jobs, pdf
from app.services import seed

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "corpus"
CASSETTES = CORPUS_ROOT / "cassettes"


def make_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, Path]:
    """Real router on a seeded demo DB (P3)."""
    db = tmp_path / "p3.db"
    seed.seed_demo(db, CORPUS_ROOT)
    monkeypatch.setenv("API_STUB", "0")
    monkeypatch.setenv("CLAUSETRACE_DB", str(db))
    from app.main import create_app

    return create_app(), db


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


def _text_pdf(text: str) -> bytes:
    """One-page PDF with an embedded text layer (minimal, uncompressed)."""
    stream = f"BT /F1 12 Tf 50 700 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    return out


def test_pdf_text_layer_and_image_detection(tmp_path: Path) -> None:
    """P3: text pages read the layer; image-only pages are detected."""
    pages = pdf.extract_pages(_text_pdf("9.2 Stratus shall keep transfer logs " * 3), vision=False)
    assert pages[0].source == "text"
    assert "transfer logs" in pages[0].text

    from PIL import Image, ImageDraw

    image_path = tmp_path / "page.png"
    img = Image.new("RGB", (800, 400), "white")
    ImageDraw.Draw(img).text((40, 40), "Scanned clause page with no text layer", fill="black")
    img.save(image_path)
    pdf_path = tmp_path / "image.pdf"
    img.save(pdf_path, "PDF")
    pages = pdf.extract_pages(pdf_path.read_bytes(), vision=False)
    assert pages[0].source == "image"
    with pytest.raises(pdf.PdfError):
        pdf.extract_pages(b"not a pdf")


def test_upload_job_processes_and_corrects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """P3 gate (part 1): a non-seeded DPA uploads, extracts, corrects, approves."""
    app, db = make_app(tmp_path, monkeypatch)
    variant = (CORPUS_ROOT / "contracts" / "variant_dpa.md").read_text(encoding="utf-8")
    uploaded = post(
        app,
        "/api/matters/MAT-01/documents/upload",
        {
            "title": "Beacon-Stratus DPA",
            "file_base64": base64.b64encode(variant.encode()).decode(),
            "media_type": "text/plain",
        },
    )
    assert uploaded.status_code == 200, uploaded.text
    document_id = uploaded.json()["document_id"]
    job_id = uploaded.json()["job_id"]

    # The worker runs the job (background in production; direct here).
    session = sessionmaker(bind=init_db(db), future=True)()
    intake_session = sessionmaker(bind=init_db(db), future=True)()
    job = jobs.process_job(intake_session, job_id, CASSETTES)
    assert job.status == "done", job.error
    intake_session.close()

    status = get(app, f"/api/jobs/{job_id}")
    assert status.status_code == 200, status.text
    assert status.json()["result"]["clauses"] == 12

    clauses = get(app, f"/api/documents/{document_id}/clauses").json()["clauses"]
    assert len(clauses) == 12
    facts = [
        fact
        for fact in get(app, "/api/matters/MAT-01/facts").json()["facts"]
        if fact["clause_id"] in {clause["id"] for clause in clauses}
    ]
    assert facts and all(fact["trust_class"] == "document_extracted" for fact in facts)

    # Lawyer correction: new row, same trust, old row kept.
    target = facts[0]
    corrected = post(
        app,
        f"/api/facts/{target['id']}/correct",
        {"statement": "Corrected: Stratus shall keep transfer logs.", "reviewer": "lawyer"},
    )
    assert corrected.status_code == 200, corrected.text
    assert corrected.json()["supersedes_id"] == target["id"]
    session2 = sessionmaker(bind=init_db(db), future=True)()
    new_fact = session2.get(models.Fact, corrected.json()["fact_id"])
    assert new_fact is not None
    assert new_fact.statement.startswith("Corrected:")
    assert new_fact.trust_class == "document_extracted"
    assert session2.get(models.Fact, target["id"]) is not None
    session2.close()

    # Gate (part 2): the corrected fact, once lawyer-approved, supports
    # a checker-valid proof — the uploaded document reaches a verified
    # answer without any seed script touching it.
    approved = post(
        app, f"/api/facts/{corrected.json()['fact_id']}/approve", {"reviewer": "lawyer"}
    )
    assert approved.status_code == 200, approved.text
    session3 = sessionmaker(bind=init_db(db), future=True)()
    confirmed = session3.get(models.Fact, approved.json()["fact_id"])
    assert confirmed is not None
    verdict = tools.verify_proof(
        session3,
        "MAT-01",
        "C-LOOP-92",
        {
            "claim_id": "C-LOOP-92",
            "as_of": "2026-11-20",
            "conclusion": "holds",
            "premises": [
                {
                    "fact_id": confirmed.id,
                    "statement": confirmed.statement,
                    "trust_class": "lawyer_confirmed",
                }
            ],
            "steps": [
                {"kind": "cite_fact", "fact_id": confirmed.id},
                {"kind": "conclude", "conclusion": "holds"},
            ],
        },
    )
    assert verdict["valid"] is True, verdict
    session3.close()
    session.close()


def test_job_failure_is_recorded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """P3: a document whose text cannot extract fails the job, typed."""
    app, db = make_app(tmp_path, monkeypatch)
    uploaded = post(
        app,
        "/api/matters/MAT-01/documents/upload",
        {
            "title": "Tiny",
            "file_base64": base64.b64encode(b"one tiny clause").decode(),
            "media_type": "text/plain",
        },
    )
    job_id = uploaded.json()["job_id"]
    session = sessionmaker(bind=init_db(db), future=True)()
    job = jobs.process_job(session, job_id, CASSETTES)
    assert job.status == "failed"
    assert job.error
    session.close()
    status = get(app, f"/api/jobs/{job_id}")
    assert status.json()["status"] == "failed"
