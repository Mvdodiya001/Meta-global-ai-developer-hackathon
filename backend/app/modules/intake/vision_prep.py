"""Vision payload preparation (P-A): send the model the smallest useful image.

Efficiency order for every scanned page:
1. Local work first (free): render at a tuned DPI, grayscale, normalize
   contrast, encode as JPEG.
2. Dedupe by content: pages hash their prepared bytes, so identical pages
   share gateway cassettes instead of paying per page.
3. One structured call per page (the existing `emit_scan` shape).

Settings below are the P-A measured defaults; see the measurement note
in `docs/rewrite/` for how they were chosen (accuracy per byte).
"""

import hashlib
import io
import subprocess
import tempfile
from pathlib import Path

from app.core.errors import ExtractionError

DEFAULT_DPI = 150
DEFAULT_JPEG_QUALITY = 70


def image_hash(image_bytes: bytes) -> str:
    """Content key for one prepared page (P-A dedupe)."""
    return hashlib.sha256(b"vision-page-v1\x00" + image_bytes).hexdigest()


def render_page(pdf_bytes: bytes, page_number: int, dpi: int = DEFAULT_DPI) -> bytes:
    """Render one PDF page to PNG bytes via pdftoppm (P-A)."""
    if not pdf_bytes.startswith(b"%PDF"):
        raise ExtractionError("file is not a PDF")
    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = Path(tmp) / "doc.pdf"
        pdf_path.write_bytes(pdf_bytes)
        prefix = str(Path(tmp) / "page")
        try:
            subprocess.run(
                [
                    "pdftoppm", "-png", "-r", str(dpi),
                    "-f", str(page_number), "-l", str(page_number),
                    str(pdf_path), prefix,
                ],
                check=True, capture_output=True, timeout=60,
            )
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as exc:
            raise ExtractionError("could not render the PDF page for transcription") from exc
        rendered = sorted(Path(tmp).glob("page*.png"))
        if not rendered:
            raise ExtractionError("could not render the PDF page for transcription")
        return rendered[0].read_bytes()


def prepare_image(png_bytes: bytes, jpeg_quality: int = DEFAULT_JPEG_QUALITY) -> bytes:
    """Grayscale + JPEG: the payload sent to vision (P-A).

    No contrast normalization: measured autocontrast flips small glyphs
    ("8.4"→"B.4" at 14-15pt), while plain grayscale reads correctly.
    """
    from PIL import Image

    image = Image.open(io.BytesIO(png_bytes)).convert("L")
    out = io.BytesIO()
    image.save(out, format="JPEG", quality=jpeg_quality)
    return out.getvalue()


def prepare_page(
    pdf_bytes: bytes,
    page_number: int,
    dpi: int = DEFAULT_DPI,
    jpeg_quality: int = DEFAULT_JPEG_QUALITY,
) -> tuple[bytes, str]:
    """Render + prepare one page; return (jpeg_bytes, content_hash) (P-A)."""
    prepared = prepare_image(render_page(pdf_bytes, page_number, dpi), jpeg_quality)
    return prepared, image_hash(prepared)


def prepare_pages(
    pdf_bytes: bytes,
    page_numbers: list[int],
    dpi: int = DEFAULT_DPI,
    jpeg_quality: int = DEFAULT_JPEG_QUALITY,
) -> dict[int, tuple[bytes, str]]:
    """Render + prepare many pages with ONE pdftoppm call (efficient batch).

    One fork for all pages; grayscale PNG intermediates converted to
    JPEG in memory (pdftoppm's `-gray` does not apply to JPEG output).
    Returns {page: (jpeg, hash)}.
    """
    if not pdf_bytes.startswith(b"%PDF"):
        raise ExtractionError("file is not a PDF")
    if not page_numbers:
        return {}
    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = Path(tmp) / "doc.pdf"
        pdf_path.write_bytes(pdf_bytes)
        prefix = str(Path(tmp) / "page")
        try:
            subprocess.run(
                [
                    "pdftoppm", "-png", "-gray", "-r", str(dpi),
                    "-f", str(min(page_numbers)), "-l", str(max(page_numbers)),
                    str(pdf_path), prefix,
                ],
                check=True, capture_output=True, timeout=120,
            )
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as exc:
            raise ExtractionError("could not render the PDF pages for transcription") from exc
        from PIL import Image

        out: dict[int, tuple[bytes, str]] = {}
        for number in page_numbers:
            # Output files carry the document page number (no padding).
            candidates = sorted(Path(tmp).glob(f"page-{number}.png"))
            if not candidates:
                raise ExtractionError(f"pdftoppm produced no output for page {number}")
            with Image.open(io.BytesIO(candidates[0].read_bytes())) as frame:
                image = frame.convert("L")
            buf = io.BytesIO()
            image.save(buf, format="JPEG", quality=jpeg_quality)
            data = buf.getvalue()
            out[number] = (data, image_hash(data))
        return out
