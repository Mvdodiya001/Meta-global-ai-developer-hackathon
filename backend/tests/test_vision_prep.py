"""P-A: vision payload efficiency — small prepared images, shared cassettes."""

import difflib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.modules.intake import pdf, scan, vision_prep

GROUND_TRUTH_BODY = (
    "Nimbus shall process order data outside India only for fraud screening. "
    "Nimbus shall keep transfer logs for review. Acme may audit the logs on request."
)

CASSETTES = Path(__file__).resolve().parents[2] / "corpus" / "cassettes"


def _dense_pdf_bytes() -> bytes:
    """Image-only PDF page with dense small-print clause text (P-A)."""
    clause = (
        "Stratus shall implement and maintain appropriate technical and organisational "
        "measures to ensure a level of security appropriate to the risk, including "
        "pseudonymisation and encryption of Personal Data. Stratus shall notify Beacon "
        "without undue delay and in any event within seventy-two hours of becoming "
        "aware of a Personal Data Breach, and shall keep transfer logs for review."
    )
    import textwrap

    lines = ["8.4  Security safeguards and breach notification", ""] + textwrap.wrap(clause, 88)
    img = Image.new("RGB", (1000, 900), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        fontb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except OSError:
        font = ImageFont.load_default()  # type: ignore[assignment]
        fontb = font
    y = 40
    for i, line in enumerate(lines):
        draw.text((50, y), line, fill="black", font=fontb if i == 0 else font)
        y += 22
    import io

    # Headings render larger/bolder than body, as in real documents —
    # a uniform-14pt fixture caused a measured "8.4"→"B.4" vision misread.
    head_font = fontb.font_variant(size=22) if hasattr(fontb, "font_variant") else fontb
    img2 = Image.new("RGB", (1000, 900), "white")
    draw2 = ImageDraw.Draw(img2)

    y = 40
    for i, line in enumerate(lines):
        draw2.text((50, y), line, fill="black", font=head_font if i == 0 else font)  # type: ignore[arg-type]
        y += 34 if i == 0 else 22
    out = io.BytesIO()
    # resolution=200 matches real scan quality; upscaling a 72-dpi embed
    # blurs small print.
    img2.save(out, "PDF", resolution=200.0)
    return out.getvalue()


def _sample_png() -> bytes:
    """One rendered text page as PNG bytes (self-contained fixture)."""
    import io

    img = Image.new("RGB", (800, 300), "white")
    draw = ImageDraw.Draw(img)
    draw.text((40, 40), "9.2 Stratus shall keep transfer logs for review.", fill="black")
    out = io.BytesIO()
    img.save(out, "PNG")
    return out.getvalue()


def test_prepared_jpeg_is_smaller_than_png() -> None:
    """P-A: on a realistic page the prepared payload is much smaller."""

    png = vision_prep.render_page(_dense_pdf_bytes(), 1)
    prepared = vision_prep.prepare_image(png)
    assert len(prepared) < len(png) // 2, (len(prepared), len(png))
    assert vision_prep.image_hash(prepared) == vision_prep.image_hash(
        vision_prep.prepare_image(png)
    )


def test_image_hash_is_content_keyed() -> None:
    """P-A: identical pages hash equal; one flipped byte hashes different."""
    png = _sample_png()
    assert vision_prep.image_hash(png) == vision_prep.image_hash(bytes(png))
    flipped = bytearray(png)
    flipped[-1] ^= 1
    assert vision_prep.image_hash(bytes(flipped)) != vision_prep.image_hash(png)


def test_replay_prepared_page_transcribes() -> None:
    """P-A: the dense fixture page transcribes verbatim from the recorded cassette."""
    prepared, _digest = vision_prep.prepare_page(_dense_pdf_bytes(), 1)
    result = scan.scan_page(prepared, media_type="image/jpeg", cache_dir=CASSETTES)
    assert result.cached is True
    assert result.clause_ref == "8.4"
    got, want = " ".join(result.text.split()), " ".join(GROUND_TRUTH_DENSE.split())
    assert "transfer logs" in got
    assert difflib.SequenceMatcher(None, got, want).ratio() > 0.95


GROUND_TRUTH_DENSE = (
    "Stratus shall implement and maintain appropriate technical and organisational "
    "measures to ensure a level of security appropriate to the risk, including "
    "pseudonymisation and encryption of Personal Data. Stratus shall notify Beacon "
    "without undue delay and in any event within seventy-two hours of becoming "
    "aware of a Personal Data Breach, and shall keep transfer logs for review."
)


def test_pdf_vision_route_uses_prepared_images(tmp_path: Path) -> None:
    """P-A: image-only PDF pages route through the prepared vision path."""
    pages = pdf.extract_pages(_dense_pdf_bytes(), cache_dir=CASSETTES)
    assert pages[0].source == "vision"
    assert "transfer logs" in pages[0].text


def test_batch_prepare_matches_per_page() -> None:
    """Efficient batch render is byte-identical to per-page (no cassette churn)."""
    raw = _dense_pdf_bytes()
    batched = vision_prep.prepare_pages(raw, [1])
    single, _digest = vision_prep.prepare_page(raw, 1)
    assert batched[1][0] == single
    texts = pdf.transcribe_vision_pages(raw, [1], CASSETTES)
    assert "transfer logs" in texts[1]
