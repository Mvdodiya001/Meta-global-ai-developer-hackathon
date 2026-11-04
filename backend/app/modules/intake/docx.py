"""DOCX intake: deterministic OOXML parse, no model (P-B).

Reads `word/document.xml` from the zip with stdlib only: paragraphs in
order with their styles, plus tables (cells joined per row). Clause
boundaries are explicit headings — a `Heading*` style, or a leading
`9.2 Title` line — mirroring `parse_contract`'s `## <ref> <heading>`
rule so a DOCX and its text twin yield the same clauses. Legacy `.doc`
(binary) is rejected with a plain message: save as PDF or DOCX.

Nothing here stores or admits anything; the caller joins the clauses
into one document text.
"""

import re
import zipfile
from dataclasses import dataclass
from io import BytesIO
from xml.etree import ElementTree

from app.core.errors import ExtractionError

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
REF_LINE = re.compile(r"^(\d+(?:\.\d+)?)\s+(.+)$")


class DocxError(ExtractionError):
    """A Word file cannot be read or has no clauses (P-B)."""


@dataclass(frozen=True)
class DocxParagraph:
    """One paragraph: style name (may be empty) and plain text."""

    style: str
    text: str


def _paragraph_text(paragraph: ElementTree.Element) -> str:
    """Concatenate the text runs of one <w:p>, resolving tabs/line breaks."""
    parts: list[str] = []
    for node in paragraph.iter():
        tag = node.tag.split("}")[-1]
        if tag == "t" and node.text:
            parts.append(node.text)
        elif tag == "tab":
            parts.append(" ")
        elif tag == "br":
            parts.append("\n")
    return "".join(parts)


def _paragraph_style(paragraph: ElementTree.Element) -> str:
    """The paragraph's style id (`Heading1`, `Normal`, …) or ''."""
    style = paragraph.find("w:pPr/w:pStyle", NS)
    return str(style.get(f"{{{NS['w']}}}val", "")) if style is not None else ""


def read_paragraphs(docx_bytes: bytes) -> list[DocxParagraph]:
    """Paragraphs (style + text) in document order, tables inline (P-B)."""
    if not docx_bytes.startswith(b"PK"):
        raise DocxError("this file is not a Word document (.docx)")
    try:
        archive = zipfile.ZipFile(BytesIO(docx_bytes))
        xml = archive.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError) as exc:
        raise DocxError("could not read the Word document") from exc
    root = ElementTree.fromstring(xml)
    out: list[DocxParagraph] = []
    for block in root.find("w:body", NS) or []:
        kind = block.tag.split("}")[-1]
        if kind == "p":
            text = _paragraph_text(block).strip()
            if text:
                out.append(DocxParagraph(style=_paragraph_style(block), text=text))
        elif kind == "tbl":
            cells = [
                _paragraph_text(cell).strip()
                for cell in block.iter(f"{{{NS['w']}}}tc")
            ]
            row = " | ".join(part for part in cells if part)
            if row:
                out.append(DocxParagraph(style="Table", text=row))
    if not out:
        raise DocxError("the Word document has no readable text")
    return out


def paragraphs_to_clauses(paragraphs: list[DocxParagraph]) -> list[tuple[str, str, str]]:
    """Split styled paragraphs into (ref, heading, body) clauses (P-B).

    A clause starts at a Heading-style paragraph or a `9.2 Title` line;
    the ref/heading split follows the same `ref + ' ' + heading` rule as
    `parse_contract`, so twins agree.
    """
    clauses: list[tuple[str, str, str]] = []
    ref: str | None = None
    heading = ""
    body: list[str] = []
    for para in paragraphs:
        match = REF_LINE.match(para.text)
        if para.style.startswith("Heading") or match is not None:
            if ref is not None:
                clauses.append((ref, heading, "\n".join(body).strip()))
            if match is not None:
                ref, heading = match.group(1), match.group(2).strip()
            else:
                ref, _, heading = para.text.partition(" ")
                if not ref or not heading:
                    raise DocxError(f"heading has no clause ref: {para.text!r}")
            body = []
        elif ref is not None:
            body.append(para.text)
    if ref is not None:
        clauses.append((ref, heading, "\n".join(body).strip()))
    if not clauses:
        raise DocxError("the Word document has no clause headings")
    if any(not text for _, _, text in clauses):
        raise DocxError("every clause needs a non-empty body")
    return clauses


def docx_to_clauses(docx_bytes: bytes) -> list[tuple[str, str, str]]:
    """One-step DOCX bytes → clauses (P-B)."""
    return paragraphs_to_clauses(read_paragraphs(docx_bytes))


def reject_legacy_doc() -> None:
    """Typed rejection for binary `.doc` uploads (P-B, no legacy support)."""
    raise DocxError(
        "This older Word format (.doc) isn't supported. "
        "Save it as PDF or DOCX and upload again."
    )
