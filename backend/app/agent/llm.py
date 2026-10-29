"""T2.1: LLM gateway — the only path to the Meta Model API (M).

Modes (`LLM_MODE`, default `replay`): `live` calls the Responses API and
caches by request hash; `replay` serves identical output from `.cache/llm/`
and fails loudly on a miss; `mock` answers locally with zero tokens. Every
call is logged to `llm_calls` when a session is given. Caps: 2 retries plus
one 120 s timeout per attempt (the 12-tool-call loop cap lands in T2.5).
Pricing follows the T0.3 calibration; tests never use `live`.
"""

import hashlib
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from app import models
from app.core.errors import CassetteMissing, LiveCallsBlocked, LLMRequestFailed

API_URL = "https://api.meta.ai/v1"
RESPONSES_PATH = "/responses"
DEFAULT_MODEL = "muse-spark-1.3"

MODES = ("live", "replay", "mock")
MAX_RETRIES = 2
HTTP_TIMEOUT_S = 120

# (input, cached input, output) USD per 1M tokens — T0.3 calibration.
PRICES = {
    "muse-spark-1.3": (1.25, 0.15, 4.25),
    "muse-spark-1.3-contributor": (0.10, 0.002, 0.20),
}

MOCK_TEXT = "Mock model answer: replace with a recorded cassette via replay mode."

DEFAULT_CACHE_DIR = Path(__file__).resolve().parents[3] / ".cache" / "llm"


@dataclass(frozen=True)
class LLMResponse:
    """One parsed model answer with usage (T2.1)."""

    text: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    model: str = DEFAULT_MODEL
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0
    latency_ms: float = 0.0
    cached: bool = False
    request_sha: str = ""


def request_hash(request: dict[str, Any]) -> str:
    """Stable cache key for a request body (T2.1)."""
    canonical = json.dumps(request, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def resolve_mode(mode: str | None) -> str:
    """Validate the gateway mode (T2.1)."""
    resolved = (mode or os.environ.get("LLM_MODE", "replay")).lower()
    if resolved not in MODES:
        raise ValueError(f"unknown LLM mode {resolved!r}; expected one of {MODES}")
    return resolved


def cache_file(cache_dir: str | Path, request_sha: str) -> Path:
    """Cassette path for a request hash (T2.1)."""
    return Path(cache_dir) / f"{request_sha}.json"


def save_cassette(
    cache_dir: str | Path,
    request_sha: str,
    request: dict[str, Any],
    raw_response: dict[str, Any],
) -> None:
    """Persist a raw API response for replay mode (T2.1)."""
    path = cache_file(cache_dir, request_sha)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"request": request, "response": raw_response}, indent=2) + "\n",
        encoding="utf-8",
    )


def load_cassette(cache_dir: str | Path, request_sha: str) -> dict[str, Any]:
    """Load a raw cached response or raise (T2.1)."""
    path = cache_file(cache_dir, request_sha)
    if not path.exists():
        raise CassetteMissing(f"no cassette for request {request_sha} in {cache_dir}")
    payload = cast("dict[str, Any]", json.loads(path.read_text(encoding="utf-8")))
    return cast("dict[str, Any]", payload["response"])


def estimate_cost(
    model: str, input_tokens: int, cached_input_tokens: int, output_tokens: int
) -> float:
    """USD estimate from the T0.3 price table; 0.0 for unknown models (T2.1)."""
    prices = PRICES.get(model)
    if prices is None:
        return 0.0
    per_in, per_cached, per_out = prices
    uncached = max(input_tokens - cached_input_tokens, 0)
    total = uncached * per_in + cached_input_tokens * per_cached + output_tokens * per_out
    return total / 1_000_000


def parse_response(
    raw: dict[str, Any],
    model: str,
    request_sha: str,
    cached: bool,
    latency_ms: float,
) -> LLMResponse:
    """Parse a raw Responses API body into an LLMResponse (T2.1)."""
    texts: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    output = raw.get("output", [])
    if not isinstance(output, list):
        raise LLMRequestFailed("malformed Responses API body: `output` is not a list")
    for item in output:
        if not isinstance(item, dict):
            raise LLMRequestFailed("malformed Responses API body: output item")
        if item.get("type") == "message":
            for content in item.get("content", []):
                if isinstance(content, dict) and content.get("type") == "output_text":
                    texts.append(str(content.get("text", "")))
        elif item.get("type") == "function_call":
            try:
                arguments = json.loads(item.get("arguments", "{}"))
            except ValueError as exc:
                raise LLMRequestFailed("malformed function_call arguments") from exc
            if not isinstance(arguments, dict):
                raise LLMRequestFailed("malformed function_call arguments")
            tool_calls.append(
                {
                    "name": str(item.get("name", "")),
                    "arguments": arguments,
                    "call_id": item.get("call_id"),
                }
            )
    usage = raw.get("usage", {})
    if not isinstance(usage, dict):
        raise LLMRequestFailed("malformed Responses API body: `usage` is not an object")
    input_tokens = int(usage.get("input_tokens", 0) or 0)
    output_tokens = int(usage.get("output_tokens", 0) or 0)
    details = usage.get("input_tokens_details", {})
    cached_tokens = int(details.get("cached_tokens", 0) or 0) if isinstance(details, dict) else 0
    return LLMResponse(
        text="\n".join(texts),
        tool_calls=tool_calls,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_input_tokens=min(cached_tokens, input_tokens),
        latency_ms=latency_ms,
        cached=cached,
        request_sha=request_sha,
    )


def _post_json(url: str, payload: dict[str, Any], api_key: str) -> dict[str, Any]:
    """POST JSON with the bearer key; never include the key in errors (T2.1)."""
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"Authorization": "Bearer REDACTED", "Content-Type": "application/json"},
        method="POST",
    )
    request.add_unredirected_header("Authorization", f"Bearer {api_key}")
    try:
        with urlopen(request, timeout=HTTP_TIMEOUT_S) as response:
            return cast("dict[str, Any]", json.loads(response.read().decode("utf-8")))
    except HTTPError as exc:
        raise LLMRequestFailed(f"Meta API HTTP {exc.code}") from exc
    except (URLError, TimeoutError) as exc:
        raise LLMRequestFailed(f"Meta API request failed: {type(exc).__name__}") from exc


def _call_live(
    payload: dict[str, Any], model: str, request_sha: str, cache_dir: Path
) -> LLMResponse:
    """Call the Responses API with retries, then cache the raw body (T2.1)."""
    api_key = os.environ.get("MODEL_API_KEY")
    if not api_key:
        raise LLMRequestFailed("MODEL_API_KEY is missing")
    try:
        cached_raw = load_cassette(cache_dir, request_sha)
    except CassetteMissing:
        cached_raw = None
    if cached_raw is not None:
        return parse_response(cached_raw, model, request_sha, cached=True, latency_ms=0.0)
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        started = time.monotonic()
        try:
            raw = _post_json(API_URL + RESPONSES_PATH, payload, api_key)
        except LLMRequestFailed as exc:
            last_error = exc
            time.sleep(attempt + 1)
            continue
        latency_ms = (time.monotonic() - started) * 1000.0
        save_cassette(cache_dir, request_sha, payload, raw)
        return parse_response(raw, model, request_sha, cached=False, latency_ms=latency_ms)
    raise LLMRequestFailed(f"live call failed after {MAX_RETRIES + 1} attempts: {last_error}")


def log_call(
    session: Session,
    run_id: str | None,
    role: str,
    response: LLMResponse,
) -> str:
    """Append one `llm_calls` row and return its id (T2.1)."""
    call_id = f"LC-{uuid.uuid4().hex[:12]}"
    session.add(
        models.LlmCall(
            id=call_id,
            run_id=run_id,
            role=role,
            model=response.model,
            request_sha256=response.request_sha,
            tokens_in=response.input_tokens,
            tokens_out=response.output_tokens,
            cost_est=estimate_cost(
                response.model,
                response.input_tokens,
                response.cached_input_tokens,
                response.output_tokens,
            ),
            latency_ms=int(response.latency_ms),
            cached=response.cached,
        )
    )
    session.commit()
    return call_id


def call_llm(
    request: dict[str, Any],
    mode: str | None = None,
    cache_dir: str | Path = DEFAULT_CACHE_DIR,
    session: Session | None = None,
    run_id: str | None = None,
    role: str = "agent",
) -> LLMResponse:
    """Answer through the gateway in `live|replay|mock` mode (T2.1)."""
    resolved = resolve_mode(mode)
    if resolved == "live" and "PYTEST_CURRENT_TEST" in os.environ:
        raise LiveCallsBlocked("live model calls are blocked under pytest")
    resolved_request = dict(request)
    resolved_request.setdefault("model", DEFAULT_MODEL)
    resolved_request.setdefault("temperature", 0)
    model = str(resolved_request["model"])
    request_sha = request_hash(resolved_request)
    cache_path = Path(cache_dir)
    if resolved == "mock":
        response = LLMResponse(
            text=MOCK_TEXT, model=model, request_sha=request_sha, cached=False
        )
    elif resolved == "replay":
        raw = load_cassette(cache_path, request_sha)
        response = parse_response(raw, model, request_sha, cached=True, latency_ms=0.0)
    else:
        response = _call_live(resolved_request, model, request_sha, cache_path)
    if session is not None:
        log_call(session, run_id, role, response)
    return response
