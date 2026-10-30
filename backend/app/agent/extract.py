"""T2.2: clause extraction through the LLM gateway (F3).

The model segments the contract and quotes each clause body verbatim via the
`emit_extraction` function tool. Spans are computed service-side by unique
substring search, so a stored span always matches the document bytes; a quote
that is missing or ambiguous rejects the extraction instead of being guessed.
Each clause yields one candidate fact (`document_extracted`); the fact's
evidence span is its clause's span. Richer fact typing lands in T2.3.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.agent import llm, prompts
from app.core.errors import ExtractionError

EXTRACTION_MODEL = "muse-spark-1.3"
MAX_EXTRACTION_RETRIES = 2


@dataclass(frozen=True)
class Clause:
    """One extracted clause with its snapshot span (T2.2, F3)."""

    ref: str
    heading: str
    text: str
    span_start: int
    span_end: int


@dataclass(frozen=True)
class Fact:
    """One candidate fact drawn from a clause (T2.2, F3, F8)."""

    statement: str
    clause_ref: str
    span_start: int
    span_end: int
    structured: dict[str, Any] = field(default_factory=dict)
    trust_class: str = "document_extracted"
    origin: str = "extracted"


@dataclass(frozen=True)
class ExtractionResult:
    """Validated extraction of one document (T2.2)."""

    clauses: list[Clause]
    facts: list[Fact]
    model: str
    request_sha: str
    cached: bool


def extraction_request(document_text: str) -> dict[str, Any]:
    """Build the exact gateway request for one document (T2.2)."""
    return {
        "model": EXTRACTION_MODEL,
        "input": prompts.build_extraction_input(document_text),
        "tools": [prompts.EXTRACTION_TOOL],
        "tool_choice": "auto",
        "parallel_tool_calls": False,
        "temperature": 0,
    }


def _locate(text: str, quote: str, ref: str) -> tuple[int, int]:
    """Unique-substring span lookup; rejects missing or ambiguous quotes (T2.2)."""
    if not quote:
        raise ExtractionError(f"clause {ref}: empty quote")
    count = text.count(quote)
    if count == 0:
        raise ExtractionError(f"clause {ref}: quote not found in document")
    if count > 1:
        raise ExtractionError(f"clause {ref}: quote occurs {count} times, ambiguous")
    start = text.index(quote)
    return start, start + len(quote)


def parse_extraction(
    document_text: str, arguments: dict[str, Any]
) -> ExtractionResult:
    """Validate tool arguments and compute spans (T2.2)."""
    if not isinstance(arguments, dict):
        raise ExtractionError("extraction arguments must be an object")
    raw_clauses = arguments.get("clauses")
    raw_facts = arguments.get("facts")
    if not isinstance(raw_clauses, list) or not raw_clauses:
        raise ExtractionError("extraction must list at least one clause")
    if not isinstance(raw_facts, list):
        raise ExtractionError("extraction must list facts")
    clauses: list[Clause] = []
    seen_refs: set[str] = set()
    for entry in raw_clauses:
        if not isinstance(entry, dict):
            raise ExtractionError("each clause must be an object")
        ref = entry.get("ref", "")
        heading = entry.get("heading", "")
        body = entry.get("text", "")
        if not isinstance(ref, str) or not ref:
            raise ExtractionError("each clause needs a non-empty ref")
        if ref in seen_refs:
            raise ExtractionError(f"duplicate clause ref {ref!r}")
        seen_refs.add(ref)
        if not isinstance(heading, str) or not heading:
            raise ExtractionError(f"clause {ref}: empty heading")
        if not isinstance(body, str) or not body:
            raise ExtractionError(f"clause {ref}: empty text")
        start, end = _locate(document_text, body, ref)
        clauses.append(Clause(ref=ref, heading=heading, text=body, span_start=start, span_end=end))
    spans = {clause.ref: (clause.span_start, clause.span_end) for clause in clauses}
    facts: list[Fact] = []
    for entry in raw_facts:
        if not isinstance(entry, dict):
            raise ExtractionError("each fact must be an object")
        statement = entry.get("statement", "")
        clause_ref = entry.get("clause_ref", "")
        structured = entry.get("structured", {})
        if not isinstance(statement, str) or not statement:
            raise ExtractionError("each fact needs a non-empty statement")
        if clause_ref not in spans:
            raise ExtractionError(f"fact points at unknown clause {clause_ref!r}")
        if not isinstance(structured, dict):
            raise ExtractionError("fact structured must be an object")
        start, end = spans[clause_ref]
        facts.append(
            Fact(
                statement=statement,
                clause_ref=str(clause_ref),
                span_start=start,
                span_end=end,
                structured=dict(structured),
            )
        )
    missing = seen_refs - {fact.clause_ref for fact in facts}
    if missing:
        raise ExtractionError(f"clauses without facts: {sorted(missing)}")
    return ExtractionResult(clauses=clauses, facts=facts, model="", request_sha="", cached=False)


def extract_document(
    document_text: str,
    mode: str | None = None,
    cache_dir: str | Path = llm.DEFAULT_CACHE_DIR,
    session: Session | None = None,
    run_id: str | None = None,
    max_retries: int = MAX_EXTRACTION_RETRIES,
) -> ExtractionResult:
    """Extract clauses + candidate facts via one function-tool call (T2.2, F3)."""
    request = extraction_request(document_text)
    resolved = llm.resolve_mode(mode)
    attempts = 1 + max_retries if resolved == "live" else 1
    last_error: ExtractionError | None = None
    for _ in range(attempts):
        response = llm.call_llm(
            request, mode=resolved, cache_dir=cache_dir, session=session, run_id=run_id
        )
        calls = [call for call in response.tool_calls if call.get("name") == "emit_extraction"]
        if len(calls) != 1:
            last_error = ExtractionError(
                f"expected exactly one emit_extraction call, got {len(calls)}"
            )
            continue
        try:
            parsed = parse_extraction(document_text, calls[0].get("arguments", {}))
        except ExtractionError as exc:
            last_error = exc
            continue
        return ExtractionResult(
            clauses=parsed.clauses,
            facts=parsed.facts,
            model=response.model,
            request_sha=response.request_sha,
            cached=response.cached,
        )
    raise last_error if last_error is not None else ExtractionError("extraction failed")
