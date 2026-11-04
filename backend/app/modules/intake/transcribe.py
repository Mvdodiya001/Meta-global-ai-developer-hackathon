"""T7.1: Muse Voice Transcribe — dictated audio → transcript (F8).

Per the Meta speech-to-text docs: model `muse-voice-transcribe-1.0`,
file endpoint `POST /v1/asr/transcribe` with a multipart body (`request`
JSON part + `audio` WAV part; mono 16-bit PCM WAV at 16/24 kHz).
Modes mirror the gateway: `live` uploads and caches the raw response,
`replay` serves the cassette for the audio hash, `mock` answers locally.
Live never runs under pytest. The transcript becomes a *proposed* fact
only at the API layer, stored `ai_inferred` — this module decides no
status and admits no premise.
"""

import hashlib
import json
import os
import time
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast
from urllib.error import HTTPError, URLError

from sqlalchemy.orm import Session

from app import models
from app.core.errors import LiveCallsBlocked

ASR_URL = "https://api.meta.ai/v1/asr/transcribe"
ASR_MODEL = "muse-voice-transcribe-1.0"
HTTP_TIMEOUT_S = 120


class TranscribeError(Exception):
    """Audio cannot be transcribed or is not a supported WAV (T7.1)."""


@dataclass(frozen=True)
class TranscriptResult:
    """One finished transcription (T7.1)."""

    transcript: str
    turns: list[dict[str, Any]]
    audio_duration_ms: int
    model: str = ASR_MODEL
    request_sha: str = ""
    cached: bool = False


def audio_hash(audio_bytes: bytes) -> str:
    """Cassette key for one audio upload (model included) (T7.1)."""
    return hashlib.sha256(ASR_MODEL.encode() + b"\x00" + audio_bytes).hexdigest()


def _cassette_path(cache_dir: str | Path, request_sha: str) -> Path:
    """ASR cassettes sit next to gateway cassettes with an .asr suffix."""
    return Path(cache_dir) / f"{request_sha}.asr.json"


def _resolve_mode(mode: str | None) -> str:
    """Gateway-compatible mode resolution (T7.1)."""
    resolved = (mode or os.environ.get("LLM_MODE", "replay")).lower()
    if resolved not in ("live", "replay", "mock"):
        raise TranscribeError(f"unknown LLM mode {resolved!r}")
    return resolved


def _parse_response(raw: dict[str, Any], request_sha: str, cached: bool) -> TranscriptResult:
    """Validate one ASR JSON response (T7.1)."""
    transcript = raw.get("transcript")
    if not isinstance(transcript, str):
        raise TranscribeError("ASR response has no transcript text")
    turns = raw.get("turns", [])
    duration = raw.get("audioDurationMs", 0)
    return TranscriptResult(
        transcript=transcript.strip(),
        turns=[dict(t) for t in turns if isinstance(t, dict)] if isinstance(turns, list) else [],
        audio_duration_ms=int(duration) if isinstance(duration, (int, float)) else 0,
        request_sha=request_sha,
        cached=cached,
    )


def _post_multipart(audio_bytes: bytes, api_key: str) -> dict[str, Any]:
    """POST the docs' multipart shape with stdlib only (T7.1)."""
    boundary = f"clausetrace-{uuid.uuid4().hex}"
    request_part = json.dumps(
        {"mode": "PUSH_TO_TALK", "model": ASR_MODEL, "audioEncoding": "WAV"}
    ).encode()
    body = b"".join(
        [
            f"--{boundary}\r\n".encode(),
            b'Content-Disposition: form-data; name="request"\r\n',
            b"Content-Type: application/json\r\n\r\n",
            request_part,
            b"\r\n",
            f"--{boundary}\r\n".encode(),
            b'Content-Disposition: form-data; name="audio"; filename="dictation.wav"\r\n',
            b"Content-Type: audio/wav\r\n\r\n",
            audio_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    request = urllib.request.Request(
        ASR_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_S) as response:
            return cast("dict[str, Any]", json.loads(response.read().decode("utf-8")))
    except HTTPError as exc:
        raise TranscribeError(f"ASR HTTP {exc.code}") from exc
    except (URLError, TimeoutError) as exc:
        raise TranscribeError(f"ASR request failed: {type(exc).__name__}") from exc


def _log_call(session: Session | None, result: TranscriptResult, latency_ms: float) -> None:
    """One llm_calls row for the transcription (zero tokens; per-hour pricing)."""
    if session is None:
        return
    session.add(
        models.LlmCall(
            id=f"LC-{uuid.uuid4().hex[:12]}",
            run_id=None,
            role="transcribe",
            model=result.model,
            request_sha256=result.request_sha,
            tokens_in=0,
            tokens_out=0,
            cost_est=0.18 * (result.audio_duration_ms / 3_600_000),
            latency_ms=int(latency_ms),
            cached=result.cached,
        )
    )
    session.commit()


def transcribe_audio(
    audio_bytes: bytes,
    mode: str | None = None,
    cache_dir: str | Path = Path(__file__).resolve().parents[4] / "corpus" / "cassettes",
    session: Session | None = None,
) -> TranscriptResult:
    """Transcribe one WAV clip in live|replay|mock mode (T7.1)."""
    if len(audio_bytes) < 12 or audio_bytes[:4] != b"RIFF" or audio_bytes[8:12] != b"WAVE":
        raise TranscribeError("audio must be a WAV file (RIFF/WAVE container)")
    resolved = _resolve_mode(mode)
    if resolved == "live" and "PYTEST_CURRENT_TEST" in os.environ:
        raise LiveCallsBlocked("live ASR calls are blocked under pytest")
    request_sha = audio_hash(audio_bytes)
    cassette = _cassette_path(cache_dir, request_sha)
    if resolved == "mock":
        result = TranscriptResult(
            transcript="Mock transcript: replace with a recorded cassette via replay mode.",
            turns=[],
            audio_duration_ms=0,
            request_sha=request_sha,
        )
        _log_call(session, result, 0.0)
        return result
    if resolved in ("replay", "live") and cassette.exists():
        raw = cast("dict[str, Any]", json.loads(cassette.read_text(encoding="utf-8")))
        result = _parse_response(raw, request_sha, cached=True)
        _log_call(session, result, 0.0)
        return result
    if resolved == "replay":
        # Real voices are never in the prepared set: a cassette miss on
        # ASR falls through to a live transcription (which then becomes
        # the cassette), but only when a key is present. Without a key
        # the miss stays a loud typed error — never a fabricated text.
        from app.core.errors import CassetteMissing

        if not os.environ.get("MODEL_API_KEY"):
            raise CassetteMissing(
                f"no ASR cassette for audio {request_sha} in {cache_dir}: "
                "run with LLM_MODE=live and a key, or `make record`"
            )
    api_key = os.environ.get("MODEL_API_KEY")
    if not api_key:
        raise TranscribeError("MODEL_API_KEY is missing")
    started = time.monotonic()
    raw = _post_multipart(audio_bytes, api_key)
    latency_ms = (time.monotonic() - started) * 1000.0
    try:
        cassette.parent.mkdir(parents=True, exist_ok=True)
        cassette.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        # Caching is best-effort: a read-only cassette dir (e.g. the
        # container image) must never lose a paid-for transcript.
        print(f"warning: ASR cassette not written to {cassette}: {exc}")
    result = _parse_response(raw, request_sha, cached=False)
    _log_call(session, result, latency_ms)
    return result
