"""P-B: DOCX parsing, .doc rejection, upload parity with the text twin."""

import asyncio
import base64
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

import httpx
import pytest

from app.modules.intake import docx

TWIN_PARAGRAPHS = [
    ("Heading1", "9.2 Cross-border transfer and logs"),
    ("Normal", "Nimbus shall keep transfer logs for review."),
    ("Normal", "Acme may audit the logs on request."),
    ("Heading1", "10 Breach timelines"),
    ("Normal", "Full breach details follow within seventy-two hours."),
]


def _docx_bytes(paragraphs: list[tuple[str, str]]) -> bytes:
    """Minimal valid OOXML with styled paragraphs (P-B fixture)."""
    body = []
    for style, text in paragraphs:
        body.append(
            f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
            f"<w:r><w:t>{escape(text)}</w:t></w:r></w:p>"
        )
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{''.join(body)}</w:body></w:document>"
    )
    out = BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", document)
    return out.getvalue()


def test_docx_matches_text_twin() -> None:
    """P-B: a DOCX and its text twin yield the same clauses."""
    clauses = docx.docx_to_clauses(_docx_bytes(TWIN_PARAGRAPHS))
    assert [(ref, heading) for ref, heading, _ in clauses] == [
        ("9.2", "Cross-border transfer and logs"),
        ("10", "Breach timelines"),
    ]
    assert "transfer logs" in clauses[0][2]
    assert "seventy-two hours" in clauses[1][2]


def test_docx_numbered_line_without_style_is_a_clause() -> None:
    """P-B: `9.2 Title` lines start clauses even in Normal style."""
    clauses = docx.docx_to_clauses(
        _docx_bytes([("Normal", "9.2 Transfer logs"), ("Normal", "Keep the logs.")])
    )
    assert clauses[0][0] == "9.2"


def test_docx_rejects_non_documents_and_empty() -> None:
    """P-B: bad bytes and heading-less files fail typed."""
    with pytest.raises(docx.DocxError):
        docx.docx_to_clauses(b"not a zip")
    with pytest.raises(docx.DocxError):
        docx.docx_to_clauses(_docx_bytes([("Normal", "just a sentence")]))


def test_legacy_doc_rejected_with_plain_message() -> None:
    """P-B: binary .doc uploads are refused, never guessed at."""
    with pytest.raises(docx.DocxError, match="isn't supported"):
        docx.reject_legacy_doc()


def test_docx_upload_end_to_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """P-B: a DOCX twin of clause 9.2 uploads and extracts like text."""

    from app.services import seed

    corpus = Path(__file__).resolve().parents[2] / "corpus"
    db = tmp_path / "docx.db"
    seed.seed_demo(db, corpus)
    monkeypatch.setenv("API_STUB", "0")
    monkeypatch.setenv("CLAUSETRACE_DB", str(db))
    import sys

    sys.path.insert(0, "backend")
    from app.main import create_app

    app = create_app()

    async def call(method: str, path: str, body: Any = None) -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
            if method == "get":
                return await client.get(path)
            return await client.post(path, json=body)

    twin = _docx_bytes(
        [
            ("Heading1", "9.2 Cross-border transfer and logs"),
            ("Normal", "Nimbus shall keep transfer logs for review."),
        ]
    )
    created = asyncio.run(
        call(
            "post",
            "/api/matters/MAT-01/documents/upload",
            {
                "title": "DOCX twin",
                "file_base64": base64.b64encode(twin).decode(),
                "media_type": "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document",
            },
        )
    )
    assert created.status_code == 200, created.text
    # Legacy .doc gets the plain typed refusal, not a 500.
    refused = asyncio.run(
        call(
            "post",
            "/api/matters/MAT-01/documents/upload",
            {
                "title": "legacy",
                "file_base64": base64.b64encode(b"\xd0\xcfword").decode(),
                "media_type": "application/msword",
            },
        )
    )
    assert refused.status_code == 400
    assert "isn't supported" in refused.json()["error"]["message"]
