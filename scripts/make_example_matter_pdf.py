"""Generate corpus/example_matter.pdf from the fictional variant DPA.

Stdlib-only PDF writer: Helvetica / Helvetica-Bold are PDF base-14
fonts, so no font embedding is needed. Headings render bold; body
wraps by measured width (DejaVu metrics via PIL when available,
character-count fallback otherwise). Every page carries a real text
layer, so the intake pipeline reads it deterministically.
"""

import textwrap
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]

PAGE_W, PAGE_H = 595, 842  # A4 points
MARGIN = 56
BODY_SIZE, HEAD_SIZE = 11, 15
LEADING = 15


def _widths(text: str, bold: bool) -> list[int]:
    """Per-character widths in points (measured when PIL is present)."""
    try:
        from PIL import ImageFont

        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        font = ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", 100)
        return [font.getlength(ch) or 600 for ch in text]
    except Exception:
        return []


def _wrap(line: str, max_width: float, bold: bool, size: int) -> list[str]:
    """Greedy wrap by measured width, falling back to char count."""
    widths = _widths(line, bold)
    if not widths:
        return textwrap.wrap(line, width=int(max_width / (size * 0.55)))
    out, current, current_w = [], "", 0.0
    for word, chars in zip(line.split(" "), _split_words(line, widths)):
        word_w = sum(chars) * size / 100
        add = word_w if not current else word_w + sum(widths[0:1]) * size / 100
        if current and current_w + add > max_width:
            out.append(current)
            current, current_w = word, word_w
        else:
            current = f"{current} {word}".strip()
            current_w += add
    if current:
        out.append(current)
    return out


def _split_words(line: str, widths: list[int]) -> list[list[int]]:
    """Split per-char widths back into per-word groups."""
    groups, current = [], []
    for char, width in zip(line, widths):
        if char == " ":
            if current:
                groups.append(current)
                current = []
        else:
            current.append(width)
    if current:
        groups.append(current)
    return groups


def _pdf_text_line(text: str, x: int, y: int, font: str, size: int) -> bytes:
    """One PDF text-showing operation with XML/PDF escaping."""
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return f"BT /{font} {size} Tf {x} {y} Td ({safe}) Tj ET".encode()


def build_pdf(title: str, blocks: list[tuple[str, bool]]) -> bytes:
    """Lay out (text, is_heading) blocks into A4 pages; return PDF bytes."""
    pages: list[list[bytes]] = [[]]
    y = PAGE_H - MARGIN

    def new_page() -> None:
        pages.append([])
        nonlocal_y[0] = PAGE_H - MARGIN

    nonlocal_y = [y]

    def emit(line: str, bold: bool) -> None:
        size = HEAD_SIZE if bold else BODY_SIZE
        font = "F2" if bold else "F1"
        for wrapped in _wrap(line, PAGE_W - 2 * MARGIN, bold, size) or [""]:
            if nonlocal_y[0] < MARGIN + LEADING:
                new_page()
            pages[-1].append(_pdf_text_line(wrapped, MARGIN, nonlocal_y[0], font, size))
            nonlocal_y[0] -= LEADING + (6 if bold else 0)

    for text, bold in blocks:
        emit(text, bold)
        nonlocal_y[0] -= 4

    first_stream = 3 + len(pages)
    font_f1 = first_stream + len(pages)
    font_f2 = font_f1 + 1
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{' '.join(f'{3 + i} 0 R' for i in range(len(pages)))}] /Count {len(pages)} >>".encode(),
    ]
    for i, lines in enumerate(pages):
        stream = b"\n".join(lines)
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_W} {PAGE_H}] "
            f"/Contents {first_stream + i} 0 R /Resources << /Font << /F1 {font_f1} 0 R /F2 {font_f2} 0 R >> >> >>".encode()
        )
    for lines in pages:
        stream = b"\n".join(lines)
        objects.append(
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"
        )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

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


def markdown_to_blocks(md: str) -> list[tuple[str, str]]:
    """Variant DPA markdown → (text, kind) blocks for layout."""
    blocks: list[tuple[str, str]] = []
    for line in md.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            blocks.append((stripped[3:].strip(), "heading"))
        elif stripped.startswith("# "):
            blocks.append((stripped[2:].strip(), "title"))
        elif stripped:
            blocks.append((stripped, "body"))
    return blocks


def main() -> None:
    """Write the example matter PDF and report its shape."""
    md = (ROOT / "corpus" / "contracts" / "variant_dpa.md").read_text(encoding="utf-8")
    marvel_blocks = [(text, kind == "heading") for text, kind in markdown_to_blocks(md)]
    pdf = build_pdf("Beacon-Stratus DPA", marvel_blocks)
    out = ROOT / "corpus" / "example_matter.pdf"
    out.write_bytes(pdf)
    print(f"wrote {out} ({len(pdf)} bytes)")


if __name__ == "__main__":
    main()
