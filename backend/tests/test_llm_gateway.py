"""T2.1 tests (written first): replay is identical, live is blocked under pytest."""

import os
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.agent import llm
from app.core.errors import CassetteMissing, LiveCallsBlocked
from app.db import init_db


def make_session(tmp_path: Path) -> Session:
    """Open a fresh T1.1 database with a session (T2.1)."""
    engine = init_db(tmp_path / "llm.db")
    return sessionmaker(bind=engine, future=True)()


RAW_RESPONSE = {
    "id": "resp-test-1",
    "model": "muse-spark-1.3",
    "output": [
        {
            "type": "message",
            "content": [{"type": "output_text", "text": "Clause 9.2 holds."}],
        },
        {
            "type": "function_call",
            "name": "verify_derivation",
            "arguments": '{"claim_id": "C-001"}',
            "call_id": "call-1",
        },
    ],
    "usage": {
        "input_tokens": 120,
        "output_tokens": 30,
        "total_tokens": 150,
        "input_tokens_details": {"cached_tokens": 20},
    },
}

REQUEST = {
    "model": "muse-spark-1.3",
    "input": "Does clause 9.2 meet the consent rules?",
    "tools": [],
    "temperature": 0,
}


def seed_cassette(cache_dir: Path) -> str:
    """Store one canned raw response; return its request hash (T2.1)."""
    request_hash = llm.request_hash(REQUEST)
    llm.save_cassette(cache_dir, request_hash, REQUEST, RAW_RESPONSE)
    return request_hash


def test_replay_returns_identical_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """T2.1: Done when replay returns identical output without touching the network."""
    cache_dir = tmp_path / "llm"
    request_hash = seed_cassette(cache_dir)

    def _no_network(*args: object, **kwargs: object) -> object:
        raise AssertionError("network must not be used in replay mode")

    monkeypatch.setattr(llm, "_post_json", _no_network)
    first = llm.call_llm(REQUEST, mode="replay", cache_dir=cache_dir)
    second = llm.call_llm(REQUEST, mode="replay", cache_dir=cache_dir)
    assert first == second
    assert first.cached is True
    assert first.request_sha == request_hash
    assert first.text == "Clause 9.2 holds."
    assert first.tool_calls == [
        {"name": "verify_derivation", "arguments": {"claim_id": "C-001"}, "call_id": "call-1"}
    ]
    assert (first.input_tokens, first.output_tokens) == (120, 30)


def test_replay_missing_cassette_raises(tmp_path: Path) -> None:
    """T2.1: replay with no cassette fails loudly instead of going live."""
    with pytest.raises(CassetteMissing):
        llm.call_llm(REQUEST, mode="replay", cache_dir=tmp_path / "empty")


def test_live_blocked_under_pytest(tmp_path: Path) -> None:
    """T2.1: Done when live calls are blocked under pytest."""
    assert "PYTEST_CURRENT_TEST" in os.environ
    with pytest.raises(LiveCallsBlocked):
        llm.call_llm(REQUEST, mode="live", cache_dir=tmp_path)


def test_mock_returns_canned_response(tmp_path: Path) -> None:
    """T2.1: mock mode answers locally with zero tokens."""
    response = llm.call_llm(REQUEST, mode="mock", cache_dir=tmp_path)
    assert response.cached is False
    assert response.text != ""
    assert (response.input_tokens, response.output_tokens) == (0, 0)


def test_unknown_mode_rejected(tmp_path: Path) -> None:
    """T2.1: an unknown LLM_MODE is rejected."""
    with pytest.raises(ValueError):
        llm.call_llm(REQUEST, mode="turbo", cache_dir=tmp_path)  # type: ignore[arg-type]


def test_llm_calls_logged(tmp_path: Path) -> None:
    """T2.1: Done when mock and replay calls land in `llm_calls`."""
    session = make_session(tmp_path)
    try:
        cache_dir = tmp_path / "llm"
        seed_cassette(cache_dir)
        llm.call_llm(REQUEST, mode="mock", cache_dir=cache_dir, session=session)
        llm.call_llm(REQUEST, mode="replay", cache_dir=cache_dir, session=session)
        rows = session.execute(sa.select(models.LlmCall)).scalars().all()
        assert len(rows) == 2
        assert {row.cached for row in rows} == {False, True}
        assert {row.model for row in rows} == {"muse-spark-1.3"}
        assert all(row.request_sha256 for row in rows)
    finally:
        session.close()


def test_cost_estimate_matches_t03_calibration() -> None:
    """T2.1: cost math follows the T0.3 price table."""
    cost = llm.estimate_cost("muse-spark-1.3", 1_000_000, 0, 0)
    assert cost == pytest.approx(1.25)
    cost = llm.estimate_cost("muse-spark-1.3-contributor", 1_000_000, 0, 0)
    assert cost == pytest.approx(0.10)
    assert llm.estimate_cost("unknown-model", 100, 0, 10) == 0.0


def test_request_hash_stable() -> None:
    """T2.1: the cache key is deterministic for identical requests."""
    assert llm.request_hash(REQUEST) == llm.request_hash(dict(REQUEST))
    other = dict(REQUEST, temperature=1)
    assert llm.request_hash(other) != llm.request_hash(REQUEST)
