"""T2.5 tests: loop shape, mock termination, scripted dispatch, budget cap.

The replay test needs the recorded clause-9.2 loop (`corpus/cassettes/`,
via `make record`) and skips without it.
"""

from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.agent import llm, loop
from app.agent import tools as tool_module
from app.core.errors import CassetteMissing
from app.db import init_db
from app.services import seed

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "corpus"
CASSETTES_DIR = CORPUS_ROOT / "cassettes"

MATTER = "MAT-01"
CLAUSE_TEXT_92 = (
    "Nimbus may transfer order data to its analytics cluster outside India "
    "for fraud screening. Such transfers are limited to order identifiers and "
    "risk scores, and Nimbus shall keep transfer logs for review."
)


def make_session(tmp_path: Path) -> Session:
    """Open a fresh database with a session (T2.5)."""
    engine = init_db(tmp_path / "loop.db")
    return sessionmaker(bind=engine, future=True)()


def seed_minimal(session: Session) -> str:
    """One matter, source, clause 9.2, fact and claim (T2.5). Returns claim id."""
    session.add(models.Matter(id=MATTER, client_name="Acme", title="M1"))
    session.add(
        models.Source(
            id="SRC-01",
            key="dpdp-act",
            title="DPDP Act",
            publisher="MeitY",
            url="https://example.invalid",
            jurisdiction="IN",
        )
    )
    session.add(
        models.SourceVersion(
            id="SV-01",
            source_id="SRC-01",
            version_label="v1",
            published_on="2023-08-11",
            effective_from="2023-08-11",
            effective_until=None,
            retrieved_at="2026-01-01T00:00:00Z",
            content_sha256="0" * 64,
            raw_text="text",
            is_simulated=False,
            supersedes_id=None,
        )
    )
    session.add(
        models.Provision(
            id="PRV-01",
            source_version_id="SV-01",
            key="Section 6",
            text="provision text",
            text_sha256="a" * 64,
            effective_from="2023-08-11",
            effective_until=None,
        )
    )
    session.add(
        models.DocumentVersion(
            id="DV-01",
            document_id="DOC-01",
            text=CLAUSE_TEXT_92,
            sha256="b" * 64,
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Clause(
            id="CL-10",
            document_version_id="DV-01",
            ref="9.2",
            heading="Transfer",
            text=CLAUSE_TEXT_92,
            span_start=0,
            span_end=len(CLAUSE_TEXT_92),
        )
    )
    session.add(
        models.Fact(
            id="F-01",
            matter_id=MATTER,
            clause_id="CL-10",
            statement="Clause 9.2 requires Nimbus to keep transfer logs.",
            structured_json={"element": "transfer logs"},
            origin="extracted",
            trust_class="document_extracted",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Claim(
            id="C-01",
            matter_id=MATTER,
            clause_id="CL-10",
            claim_type="CT2",
            params_json={"element": "transfer logs"},
            question_text="Does clause 9.2 require transfer logs?",
            as_of="2026-11-20",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.commit()
    return "C-01"


def scripted_proof() -> dict[str, Any]:
    """A checker-valid draft over the seeded rows (T2.5)."""
    return {
        "claim_id": "C-01",
        "as_of": "2026-11-20",
        "conclusion": "holds",
        "premises": [
            {
                "fact_id": "F-01",
                "statement": "Clause 9.2 requires Nimbus to keep transfer logs.",
                "trust_class": "document_extracted",
            }
        ],
        "steps": [
            {"kind": "cite_fact", "fact_id": "F-01"},
            {
                "kind": "contains_element",
                "clause_id": "CL-10",
                "quote": "keep transfer logs",
            },
            {"kind": "conclude", "conclusion": "holds"},
        ],
    }


def fake_llm(responses: list[list[dict[str, Any]]]) -> Any:
    """A scripted gateway: one tool-call list per loop turn (T2.5)."""
    state = {"turn": 0}

    def _fake(request: dict[str, Any], **kwargs: Any) -> llm.LLMResponse:
        turn = state["turn"]
        state["turn"] += 1
        calls = responses[turn] if turn < len(responses) else []
        return llm.LLMResponse(text="", tool_calls=calls, model="scripted")

    return _fake


def test_proof_request_shape() -> None:
    """T2.5: the loop asks the model with the six tools and temp 0."""
    request = loop.proof_request([{"type": "message"}])  # type: ignore[list-item]
    assert request["model"] == "muse-spark-1.3-contributor"
    assert request["temperature"] == 0
    assert request["tool_choice"] == "auto"
    assert request["parallel_tool_calls"] is False
    assert [tool["name"] for tool in request["tools"]] == list(tool_module.TOOL_NAMES)


def test_live_loop_without_key_fails_fast(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """T2.5: live mode without MODEL_API_KEY names the cause, no retries."""
    from app.core.errors import LLMRequestFailed

    session = make_session(tmp_path)
    claim_id = seed_minimal(session)
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    with pytest.raises(LLMRequestFailed, match="MODEL_API_KEY is missing"):
        loop.run_verify(session, claim_id=claim_id, matter_id=MATTER, mode="live")
    session.close()


def test_mock_loop_terminates_without_proof(tmp_path: Path) -> None:
    """T2.5: mock mode answers with no tool calls, so the loop ends cleanly."""
    session = make_session(tmp_path)
    claim_id = seed_minimal(session)
    result = loop.run_verify(session, claim_id=claim_id, matter_id=MATTER, mode="mock")
    assert result.accepted is False
    assert result.outcome == "no_proof"
    assert result.tool_calls == 0
    run = session.get(models.Run, result.run_id)
    assert run is not None and run.outcome == "no_proof"
    session.close()


def test_scripted_loop_accepts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """T2.5: lookup, premise, verify then propose ends accepted with a report."""
    session = make_session(tmp_path)
    claim_id = seed_minimal(session)
    proof = scripted_proof()
    monkeypatch.setenv("MODEL_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.agent.llm.call_llm",
        fake_llm(
            [
                [{"name": "lookup_source", "arguments": {"source_id": "SRC-01"}}],
                [
                    {
                        "name": "get_premise",
                        "arguments": {"matter_id": MATTER, "premise_id": "F-01"},
                    }
                ],
                [
                    {
                        "name": "verify_derivation",
                        "arguments": {"claim_id": claim_id, "proof": proof},
                    }
                ],
                [
                    {
                        "name": "propose_finding",
                        "arguments": {"claim_id": claim_id, "proof": proof},
                    }
                ],
            ]
        ),
    )
    result = loop.run_verify(session, claim_id=claim_id, matter_id=MATTER, mode="live")
    assert result.accepted is True
    assert result.outcome == "accepted"
    assert result.proof == proof
    assert result.report is not None and result.report["valid"] is True
    assert result.tool_calls == 5
    rows = session.execute(
        sa.select(models.ToolCall)
        .where(models.ToolCall.run_id == result.run_id)
        .order_by(models.ToolCall.seq)
    ).scalars().all()
    assert [row.seq for row in rows] == [1, 2, 3, 4, 5]
    assert all(row.ok for row in rows)
    session.close()


def test_tool_error_is_fed_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """T2.5: a failed tool call becomes model-visible output, not a crash."""
    session = make_session(tmp_path)
    claim_id = seed_minimal(session)
    proof = scripted_proof()
    monkeypatch.setenv("MODEL_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.agent.llm.call_llm",
        fake_llm(
            [
                [{"name": "lookup_source", "arguments": {"source_id": "SRC-NOPE"}}],
                [
                    {
                        "name": "propose_finding",
                        "arguments": {"claim_id": claim_id, "proof": proof},
                    }
                ],
            ]
        ),
    )
    result = loop.run_verify(session, claim_id=claim_id, matter_id=MATTER, mode="live")
    assert result.accepted is True
    rows = session.execute(
        sa.select(models.ToolCall).where(
            models.ToolCall.run_id == result.run_id
        )
    ).scalars().all()
    assert [row.ok for row in rows] == [False, True, True]
    session.close()


def test_report_without_budget_uses_direct_verify(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """T2.5: an accepted proof at the budget edge still gets a valid report."""
    session = make_session(tmp_path)
    claim_id = seed_minimal(session)
    proof = scripted_proof()
    monkeypatch.setenv("MODEL_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.agent.llm.call_llm",
        fake_llm(
            [
                [
                    {
                        "name": "propose_finding",
                        "arguments": {"claim_id": claim_id, "proof": proof},
                    }
                ],
            ]
        ),
    )
    result = loop.run_verify(
        session, claim_id=claim_id, matter_id=MATTER, mode="live", max_tool_calls=1
    )
    assert result.accepted is True
    assert result.outcome == "accepted"
    assert result.report is not None and result.report["valid"] is True
    assert result.tool_calls == 1
    session.close()


def test_budget_cap_stops_the_loop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """T2.5: a looping model stops at the call budget with no proof."""
    session = make_session(tmp_path)
    claim_id = seed_minimal(session)
    monkeypatch.setenv("MODEL_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.agent.llm.call_llm",
        fake_llm(
            [[{"name": "lookup_source", "arguments": {"source_id": "SRC-01"}}]] * 10
        ),
    )
    result = loop.run_verify(
        session, claim_id=claim_id, matter_id=MATTER, mode="live", max_tool_calls=3
    )
    assert result.accepted is False
    assert result.outcome == "budget_exhausted"
    assert result.tool_calls == 3
    session.close()


def test_replay_clause_92_loop(tmp_path: Path) -> None:
    """T2.5: Done when the recorded loop yields a proof verify_derivation accepts."""
    engine = init_db(tmp_path / "replay.db")
    session = sessionmaker(bind=engine, future=True)()
    seed.seed_demo(tmp_path / "replay.db", CORPUS_ROOT)
    claim_id = loop.ensure_demo_92_claim(session)
    try:
        result = loop.run_verify(
            session, claim_id=claim_id, matter_id="MAT-01", cache_dir=CASSETTES_DIR
        )
    except CassetteMissing:
        pytest.skip("loop cassettes not recorded; run make record with a key")
        return
    assert result.accepted is True, result.report
    assert result.report is not None and result.report["valid"] is True
    assert result.proof is not None and result.proof["claim_id"] == claim_id
    run = session.get(models.Run, result.run_id)
    assert run is not None and run.outcome == "accepted"
    session.close()
