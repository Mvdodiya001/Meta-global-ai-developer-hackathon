"""T7.1: voice dictation → proposed fact (ai_inferred until lawyer-approved)."""

import base64
from pathlib import Path

import pytest
from sqlalchemy.orm import sessionmaker

from app import models
from app.agent import tools, transcribe
from app.db import init_db
from app.services import seed

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "corpus"
CASSETTES = CORPUS_ROOT / "cassettes"
FIXTURE = CORPUS_ROOT / "audio" / "dictation_fact.wav"


def test_transcribe_rejects_non_wav() -> None:
    """T7.1: only RIFF/WAVE audio is accepted (docs: WAV container)."""
    with pytest.raises(transcribe.TranscribeError, match="WAV"):
        transcribe.transcribe_audio(b"not audio", cache_dir=CASSETTES)


def test_replay_transcription() -> None:
    """T7.1: the fictional dictation transcribes from the ASR cassette."""
    result = transcribe.transcribe_audio(FIXTURE.read_bytes(), cache_dir=CASSETTES)
    assert result.cached is True
    assert "transfer logs" in result.transcript
    assert "seven years" in result.transcript


def test_replay_miss_falls_through_to_live(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A real voice is never pre-recorded: miss + key = live, then cached."""
    from app.core.errors import CassetteMissing
    from app.modules.intake import transcribe

    audio = bytearray(FIXTURE.read_bytes())
    audio[-1] ^= 1  # same clip, new hash: no cassette can exist
    cache = tmp_path / "cassettes"
    with pytest.raises(CassetteMissing):
        transcribe.transcribe_audio(bytes(audio), cache_dir=cache)

    monkeypatch.setenv("MODEL_API_KEY", "test-key")
    monkeypatch.setattr(
        transcribe,
        "_post_multipart",
        lambda _audio, _key: {
            "transcript": "Nimbus shall keep transfer logs for review for seven years.",
            "turns": [],
            "audioDurationMs": 3840,
        },
    )
    live = transcribe.transcribe_audio(bytes(audio), cache_dir=cache)
    assert live.cached is False
    assert "transfer logs" in live.transcript
    replayed = transcribe.transcribe_audio(bytes(audio), cache_dir=cache)
    assert replayed.cached is True
    assert replayed.transcript == live.transcript


def test_dictation_fact_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """T7.1: proposed fact is ai_inferred, checker rejects it, approve admits it."""
    import asyncio

    import httpx

    db = tmp_path / "voice.db"
    seed.seed_demo(db, CORPUS_ROOT)
    monkeypatch.setenv("API_STUB", "0")
    monkeypatch.setenv("CLAUSETRACE_DB", str(db))
    from app.main import create_app

    app = create_app()

    async def post(path: str, body: object) -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
            return await client.post(path, json=body)

    audio_b64 = base64.b64encode(FIXTURE.read_bytes()).decode()
    created = asyncio.run(
        post(
            "/api/dictations",
            {"matter_id": "MAT-01", "clause_id": "CL-10", "audio_base64": audio_b64},
        )
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["trust_class"] == "ai_inferred"
    assert "transfer logs" in body["transcript"]
    proposed_id = body["fact_id"]

    session = sessionmaker(bind=init_db(db), future=True)()
    fact = session.get(models.Fact, proposed_id)
    assert fact is not None
    assert fact.trust_class == "ai_inferred"
    assert fact.origin == "voice_dictation"

    proof = {
        "claim_id": "C-LOOP-92",
        "as_of": "2026-11-20",
        "conclusion": "holds",
        "premises": [
            {
                "fact_id": proposed_id,
                "statement": fact.statement,
                "trust_class": "ai_inferred",
            }
        ],
        "steps": [
            {"kind": "cite_fact", "fact_id": proposed_id},
            {"kind": "conclude", "conclusion": "holds"},
        ],
    }
    rejected = tools.verify_proof(session, "MAT-01", "C-LOOP-92", proof)
    assert rejected["valid"] is False
    assert "PREMISE_UNTRUSTED" in [e["code"] for e in rejected["errors"]]
    session.close()

    approved = asyncio.run(post(f"/api/facts/{proposed_id}/approve", {"reviewer": "lawyer"}))
    assert approved.status_code == 200, approved.text
    confirmed_id = approved.json()["fact_id"]
    assert approved.json()["trust_class"] == "lawyer_confirmed"

    session = sessionmaker(bind=init_db(db), future=True)()
    confirmed = session.get(models.Fact, confirmed_id)
    assert confirmed is not None
    proof["premises"] = [
        {
            "fact_id": confirmed_id,
            "statement": confirmed.statement,
            "trust_class": "lawyer_confirmed",
        }
    ]
    proof["steps"] = [
        {"kind": "cite_fact", "fact_id": confirmed_id},
        {"kind": "conclude", "conclusion": "holds"},
    ]
    accepted = tools.verify_proof(session, "MAT-01", "C-LOOP-92", proof)
    assert accepted["valid"] is True, accepted
    session.close()
