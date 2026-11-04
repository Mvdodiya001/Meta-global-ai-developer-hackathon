"""P-C: mixed PDFs end-to-end — text page + scanned page, per-page progress."""

import asyncio
import base64
from io import BytesIO
from pathlib import Path
from typing import Any

import httpx
import pytest
from PIL import Image, ImageDraw, ImageFont

from app.services import seed

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "corpus"
CASSETTES = CORPUS_ROOT / "cassettes"


def _text_pdf_page(text: str) -> bytes:
    """One-page PDF with an embedded text layer (P-C)."""
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


def _scan_pdf_page() -> bytes:
    """One image-only PDF page (dense clause text, no text layer) (P-C)."""
    import textwrap

    # A distinct topic from page 1: adjacent pages repeating the same
    # clause invite the model to merge them; real pages differ.
    clause = (
        "Stratus shall notify Beacon of a Personal Data Breach within "
        "seventy-two hours. Beacon may appoint an auditor on thirty days notice."
    )
    lines = ["8.4  Scanned retention clause", ""] + textwrap.wrap(clause, 80)
    img = Image.new("RGB", (1000, 700), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
        fontb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    except OSError:
        font = ImageFont.load_default()  # type: ignore[assignment]
        fontb = font
    y = 40
    for i, line in enumerate(lines):
        draw.text((50, y), line, fill="black", font=fontb if i == 0 else font)
        y += 34 if i == 0 else 22
    out = BytesIO()
    # resolution=200 matches real scan quality (72-dpi embeds blur small print).
    img.save(out, "PDF", resolution=200.0)
    return out.getvalue()


def _mixed_pdf_bytes() -> bytes:
    """Text page + scanned page merged into one PDF (P-C fixture)."""
    from pypdf import PdfReader, PdfWriter

    writer = PdfWriter()
    # Distinct sentences: a repeated sentence would make the verbatim
    # span lookup ambiguous by design (the checker rejects that).
    long_text = (
        "9.2 Transfer logs\\n"
        "Nimbus shall keep transfer logs for review. "
        "Beacon may audit the logs on request. "
        "Transfers outside India need prior written approval. "
        "Breach notices go out within seventy-two hours."
    )
    writer.add_page(PdfReader(BytesIO(_text_pdf_page(long_text))).pages[0])
    writer.add_page(PdfReader(BytesIO(_scan_pdf_page())).pages[0])
    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def make_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, Path]:
    db = tmp_path / "pc.db"
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


def test_mixed_pdf_pages_have_the_right_origins(tmp_path: Path) -> None:
    """P-C: page 1 reads from the file, page 2 is transcribed from a scan."""
    from app.modules.intake import pdf as pdf_intake

    pages = pdf_intake.classify_pages(_mixed_pdf_bytes())
    assert [(page.page, page.source) for page in pages] == [(1, "text"), (2, "vision")]


def test_mixed_pdf_upload_processes_with_per_page_progress(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """P-C: mixed upload → per-page job progress → clauses + page map."""
    from sqlalchemy.orm import sessionmaker

    from app.db import init_db
    from app.modules.intake import jobs

    app, db = make_app(tmp_path, monkeypatch)
    uploaded = post(
        app,
        "/api/matters/MAT-01/documents/upload",
        {
            "title": "Mixed text and scan",
            "file_base64": base64.b64encode(_mixed_pdf_bytes()).decode(),
            "media_type": "application/pdf",
        },
    )
    assert uploaded.status_code == 200, uploaded.text
    document_id = uploaded.json()["document_id"]
    job_id = uploaded.json()["job_id"]

    session = sessionmaker(bind=init_db(db), future=True)()
    job = jobs.process_job(session, job_id, CASSETTES)
    assert job.status == "done", job.error
    assert job.result_json is not None
    assert job.result_json["pages"] == [
        {"page": 1, "source": "text", "confidence": "high"},
        {"page": 2, "source": "vision", "confidence": "low"},
    ]
    session.close()

    status = get(app, f"/api/jobs/{job_id}")
    assert status.json()["stage"] == "done"
    assert status.json()["result"]["pages"][1] == {
        "page": 2,
        "source": "vision",
        "confidence": "low",
    }

    clauses = get(app, f"/api/documents/{document_id}/clauses").json()["clauses"]
    assert len(clauses) == 2
    refs = {clause["ref"] for clause in clauses}
    assert refs == {"9.2", "8.4"}

    pages = get(app, f"/api/documents/{document_id}/pages").json()
    assert pages["pages"] == [
        {"page": 1, "source": "text", "confidence": "high"},
        {"page": 2, "source": "vision", "confidence": "low"},
    ]
