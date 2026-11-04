"""PDF intake: text layer first, vision for image-only pages (P3).

Per page: if the embedded text layer yields enough characters, use it
(deterministic, free). Otherwise the page is rendered to PNG with
poppler (`pdftoppm`, a system dependency — see docs/rewrite/07) and
transcribed through the vision scan path. The caller joins page texts
into one document version; nothing here stores or admits anything.
"""

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from app.core.errors import ExtractionError
from app.modules.intake import scan, vision_prep

TEXT_LAYER_MIN_CHARS = 40


class PdfError(ExtractionError):
    """A PDF cannot be read or rendered (P3)."""


@dataclass(frozen=True)
class PageText:
    """One page's text and how it was obtained (P3)."""

    page: int
    text: str
    source: str  # "text" (embedded layer) or "vision" (scan path)


def transcribe_vision_page(
    pdf_bytes: bytes, page_number: int, cache_dir: str | Path | None
) -> str:
    """Render + prepare + transcribe one image-only page (P-A).

    Returns `ref heading` + body so the joined document stays
    self-describing for extraction (the scan splits them into fields).
    Prepared JPEGs are ~3x smaller than PNG at equal accuracy (measured);
    identical prepared pages share gateway cassettes by content hash, so
    re-running a job never re-pays for a page already transcribed.
    """
    try:
        prepared, _digest = vision_prep.prepare_page(pdf_bytes, page_number)
    except ExtractionError as exc:
        raise PdfError(str(exc)) from exc
    return _transcribe_prepared(prepared, cache_dir)


def _transcribe_prepared(prepared: bytes, cache_dir: str | Path | None) -> str:
    """Transcribe prepared JPEG bytes, prefixing ref + heading."""
    if cache_dir is not None:
        transcribed = scan.scan_page(prepared, media_type="image/jpeg", cache_dir=cache_dir)
    else:
        transcribed = scan.scan_page(prepared, media_type="image/jpeg")
    return f"{transcribed.clause_ref} {transcribed.heading}\n{transcribed.text}"


def transcribe_vision_pages(
    pdf_bytes: bytes, page_numbers: list[int], cache_dir: str | Path | None
) -> dict[int, str]:
    """Batch twin of transcribe_vision_page: one render call (efficient).

    Returns {page: `ref heading` + body text}. Byte-identical images to
    the per-page path, so cassettes are shared, not duplicated.
    """
    try:
        prepared = vision_prep.prepare_pages(pdf_bytes, page_numbers)
    except ExtractionError as exc:
        raise PdfError(str(exc)) from exc
    return {
        number: _transcribe_prepared(image, cache_dir)
        for number, (image, _digest) in prepared.items()
    }


def extract_pages(
    pdf_bytes: bytes,
    vision: bool = True,
    cache_dir: str | Path | None = None,
) -> list[PageText]:
    """Extract per-page text from one PDF (P3)."""
    if not pdf_bytes.startswith(b"%PDF"):
        raise PdfError("file is not a PDF")
    try:
        from pypdf import PdfReader  # type: ignore[import-untyped]

        reader = PdfReader(BytesIO(pdf_bytes))
        pages = list(reader.pages)
    except Exception as exc:
        raise PdfError("could not read the PDF") from exc
    results: list[PageText] = []
    for index, page in enumerate(pages, start=1):
        text = (page.extract_text() or "").strip()
        if len(text) >= TEXT_LAYER_MIN_CHARS:
            results.append(PageText(page=index, text=text, source="text"))
            continue
        if not vision:
            results.append(PageText(page=index, text=text, source="image"))
            continue
        text = transcribe_vision_page(pdf_bytes, index, cache_dir)
        results.append(PageText(page=index, text=text, source="vision"))
    return results


def pdf_to_text(pdf_bytes: bytes, cache_dir: str | Path | None = None) -> str:
    """Whole-document text from page extraction (P3)."""
    return "\n\n".join(page.text for page in extract_pages(pdf_bytes, cache_dir=cache_dir))


@dataclass(frozen=True)
class ClassifiedPage:
    """One page's origin without transcribing it (P-C)."""

    page: int
    source: str  # "text" or "vision"
    text: str  # empty when source is "vision"


def classify_pages(pdf_bytes: bytes) -> list[ClassifiedPage]:
    """Per-page origin using the text layer only — no model calls (P-C)."""
    if not pdf_bytes.startswith(b"%PDF"):
        raise PdfError("file is not a PDF")
    try:
        from pypdf import PdfReader  # type: ignore[import-untyped]

        reader = PdfReader(BytesIO(pdf_bytes))
        raw_pages = list(reader.pages)
    except Exception as exc:
        raise PdfError("could not read the PDF") from exc
    out: list[ClassifiedPage] = []
    for index, page in enumerate(raw_pages, start=1):
        text = (page.extract_text() or "").strip()
        if len(text) >= TEXT_LAYER_MIN_CHARS:
            out.append(ClassifiedPage(page=index, source="text", text=text))
        else:
            out.append(ClassifiedPage(page=index, source="vision", text=""))
    return out
