"""Live transcription WebSocket over the whole-clip gateway (streaming)."""

import base64
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from app import models
from app.db import init_db
from app.modules.intake.transcribe import TranscriptResult

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "corpus"
CASSETTES = CORPUS_ROOT / "cassettes"
FIXTURE = CORPUS_ROOT / "audio" / "dictation_fact.wav"


def _client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """App with an isolated database file (T-stream)."""
    monkeypatch.setenv("API_STUB", "0")
    monkeypatch.setenv("CLAUSETRACE_DB", str(tmp_path / "ws.db"))
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    from app.main import create_app

    return TestClient(create_app())


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


def _fake_transcribe_factory(calls: list[str]):
    def _fake(audio_bytes: bytes, cache_dir=None, session=None) -> TranscriptResult:  # type: ignore[no-untyped-def]
        calls.append("x")
        return TranscriptResult(
            transcript="hello live",
            turns=[],
            audio_duration_ms=1000,
            request_sha="test",
        )

    return _fake


def test_interim_ok_true(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Mocked gateway text streams back as an interim draft (T-stream)."""
    import app.api as api_mod

    calls: list[str] = []
    monkeypatch.setattr(
        api_mod.transcribe, "transcribe_audio", _fake_transcribe_factory(calls)
    )
    client = _client(tmp_path, monkeypatch)
    with client.websocket_connect("/api/transcribe/stream") as ws:
        ws.send_json({"type": "audio", "audio_base64": _b64(FIXTURE.read_bytes())})
        first = ws.receive_json()
        assert first["type"] == "interim"
        assert first["ok"] is True
        assert first["transcript"] == "hello live"
        assert len(calls) == 1


def test_replay_miss_interim_ok_false_stays_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unknown voice in replay without a key: ok:false, never fake text (T-stream)."""
    client = _client(tmp_path, monkeypatch)
    audio = bytearray(FIXTURE.read_bytes())
    audio[-1] ^= 1  # same clip, new hash: no cassette can exist
    with client.websocket_connect("/api/transcribe/stream") as ws:
        ws.send_json({"type": "audio", "audio_base64": _b64(bytes(audio))})
        missed = ws.receive_json()
        assert missed["type"] == "interim"
        assert missed["ok"] is False
        assert isinstance(missed.get("reason"), str) and missed["reason"]
        # Connection stays open: a bad type still gets a typed error.
        ws.send_json({"type": "bogus"})
        err = ws.receive_json()
        assert err["type"] == "error"
        assert isinstance(err.get("reason"), str) and err["reason"]


def test_finalize_returns_transcript(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Finalize bills once through the connection session, then closes (T-stream)."""
    import app.api as api_mod

    calls: list[str] = []
    monkeypatch.setattr(
        api_mod.transcribe, "transcribe_audio", _fake_transcribe_factory(calls)
    )
    client = _client(tmp_path, monkeypatch)
    with client.websocket_connect("/api/transcribe/stream") as ws:
        ws.send_json({"type": "audio", "audio_base64": _b64(FIXTURE.read_bytes())})
        assert ws.receive_json()["ok"] is True
        ws.send_json({"type": "finalize"})
        final = ws.receive_json()
        assert final["type"] == "final"
        assert final["ok"] is True
        assert final["transcript"] == "hello live"


def test_bad_message_type_gives_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Unknown client messages get a typed error, never a traceback (T-stream)."""
    client = _client(tmp_path, monkeypatch)
    with client.websocket_connect("/api/transcribe/stream") as ws:
        ws.send_text("not json at all")
        first = ws.receive_json()
        assert first["type"] == "error"
        ws.send_json({"type": "definitely-not-a-type"})
        second = ws.receive_json()
        assert second["type"] == "error"
        assert "definitely-not-a-type" in second["reason"]


def test_throttle_second_audio_is_listening(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two rapid buffers bill at most one interim transcription (T-stream)."""
    import app.api as api_mod

    calls: list[str] = []
    monkeypatch.setattr(
        api_mod.transcribe, "transcribe_audio", _fake_transcribe_factory(calls)
    )
    client = _client(tmp_path, monkeypatch)
    with client.websocket_connect("/api/transcribe/stream") as ws:
        payload = _b64(FIXTURE.read_bytes())
        ws.send_json({"type": "audio", "audio_base64": payload})
        assert ws.receive_json()["ok"] is True
        ws.send_json({"type": "audio", "audio_base64": payload})
        second = ws.receive_json()
        assert second["type"] == "interim"
        assert second["ok"] is False
        assert "listening" in second["reason"]
        assert len(calls) == 1


def test_only_finalize_is_logged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Interims skip the cost log; the finalize writes exactly one row (T-stream)."""
    client = _client(tmp_path, monkeypatch)
    db_path = tmp_path / "ws.db"
    with client.websocket_connect("/api/transcribe/stream") as ws:
        ws.send_json({"type": "audio", "audio_base64": _b64(FIXTURE.read_bytes())})
        assert ws.receive_json()["ok"] is True

        def _count() -> int:
            session = sessionmaker(bind=init_db(db_path), future=True)()
            try:
                rows = session.execute(select(func.count()).select_from(models.LlmCall))
                return int(rows.scalar() or 0)
            finally:
                session.close()

        assert _count() == 0
        ws.send_json({"type": "finalize"})
        final = ws.receive_json()
        assert final["ok"] is True
        assert _count() == 1
