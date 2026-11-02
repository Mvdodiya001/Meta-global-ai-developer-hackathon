"""T7.2: scanned page → clause text via Muse Spark image input (F3).

The model transcribes one scanned page through the gateway (image input
on the Responses API); the service validates the structured output and
returns a clause plus a candidate fact. The fact is only ever stored by
the caller as `document_extracted` against a document version — model
output alone admits nothing, and nothing here decides a finding.
Only PNG/JPEG are supported: PDF input was not probed on this tier and
is rejected with a typed error rather than guessed at.
"""

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.agent import llm, prompts
from app.core.errors import ExtractionError

SCAN_MODEL = "muse-spark-1.3-contributor"
MEDIA_TYPES = frozenset({"image/png", "image/jpeg"})
MAX_SCAN_RETRIES = 2


class ScanError(ExtractionError):
    """A scanned page cannot be transcribed as one clause (T7.2)."""


@dataclass(frozen=True)
class ScanResult:
    """One transcribed clause plus its candidate fact (T7.2)."""

    clause_ref: str
    heading: str
    text: str
    fact_statement: str
    model: str = ""
    request_sha: str = ""
    cached: bool = False


def scan_request(image_bytes: bytes, media_type: str) -> dict[str, Any]:
    """Build the exact gateway request for one page (T7.2)."""
    data_uri = f"data:{media_type};base64,{base64.b64encode(image_bytes).decode()}"
    return {
        "model": SCAN_MODEL,
        "input": prompts.build_scan_input(data_uri),
        "tools": [prompts.SCAN_TOOL],
        "tool_choice": "auto",
        "parallel_tool_calls": False,
        "temperature": 0,
    }


def parse_scan(arguments: Any) -> ScanResult:
    """Validate one emit_scan call into a ScanResult (T7.2)."""
    if not isinstance(arguments, dict):
        raise ScanError("scan arguments must be an object")
    fields: dict[str, str] = {}
    for key in ("clause_ref", "heading", "text", "fact_statement"):
        value = arguments.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ScanError(f"scan needs a non-empty {key}")
        fields[key] = value
    return ScanResult(
        clause_ref=fields["clause_ref"],
        heading=fields["heading"],
        text=fields["text"],
        fact_statement=fields["fact_statement"],
    )


def scan_page(
    image_bytes: bytes,
    media_type: str = "image/png",
    mode: str | None = None,
    cache_dir: str | Path = llm.DEFAULT_CACHE_DIR,
    session: Session | None = None,
    run_id: str | None = None,
    max_retries: int = MAX_SCAN_RETRIES,
) -> ScanResult:
    """Transcribe one scanned page through a single emit_scan call (T7.2)."""
    if media_type not in MEDIA_TYPES:
        raise ScanError(
            f"unsupported media type {media_type!r}; scanned pages must be image/png or image/jpeg"
        )
    if not image_bytes:
        raise ScanError("scanned page is empty")
    request = scan_request(image_bytes, media_type)
    resolved = llm.resolve_mode(mode)
    attempts = 1 + max_retries if resolved == "live" else 1
    last_error: ScanError | None = None
    for _ in range(attempts):
        response = llm.call_llm(
            request, mode=resolved, cache_dir=cache_dir, session=session, run_id=run_id
        )
        calls = [call for call in response.tool_calls if call.get("name") == "emit_scan"]
        if len(calls) != 1:
            last_error = ScanError(f"expected exactly one emit_scan call, got {len(calls)}")
            continue
        try:
            parsed = parse_scan(calls[0].get("arguments", {}))
        except ScanError as exc:
            last_error = exc
            continue
        return ScanResult(
            clause_ref=parsed.clause_ref,
            heading=parsed.heading,
            text=parsed.text,
            fact_statement=parsed.fact_statement,
            model=response.model,
            request_sha=response.request_sha,
            cached=response.cached,
        )
    raise last_error if last_error is not None else ScanError("scan failed")
