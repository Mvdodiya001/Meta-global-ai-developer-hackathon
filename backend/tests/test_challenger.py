"""T6.1 tests: challenger review, provider switch, decide integration."""

from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.agent import challenger, llm, loop
from app.core.errors import CassetteMissing, ChallengerError
from app.db import init_db
from app.services import memory, seed

MATTER = "MAT-01"
CORPUS_ROOT = Path(__file__).resolve().parents[2] / "corpus"
CASSETTES_DIR = CORPUS_ROOT / "cassettes"


def make_session(tmp_path: Path) -> Session:
    """Open a fresh database with a session (T6.1)."""
    engine = init_db(tmp_path / "challenger.db")
    return sessionmaker(bind=engine, future=True)()


def seed_rows(session: Session) -> None:
    """One extracted fact, one CT2 claim and card (T6.1)."""
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
            text_sha256="b" * 64,
            effective_from="2023-08-11",
            effective_until=None,
        )
    )
    session.add(
        models.RuleCard(
            id="RC-01",
            provision_id="PRV-01",
            kind="statutory",
            claim_type="CT2",
            predicate_json=None,
            interpretation_text="interp",
            span_start=0,
            span_end=4,
            trust_class="lawyer_confirmed",
            approved_by="human",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Fact(
            id="F-01",
            matter_id=MATTER,
            clause_id=None,
            statement="Clause 9.2 requires transfer logs.",
            structured_json=None,
            origin="extracted",
            trust_class="document_extracted",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Claim(
            id="C-01",
            matter_id=MATTER,
            clause_id="CL-01",
            claim_type="CT2",
            params_json={"element": "transfer logs"},
            question_text="Does clause 9.2 require transfer logs?",
            as_of="2026-11-20",
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.add(
        models.Run(
            id="RUN-01",
            trigger="verify",
            claim_id="C-01",
            started_at="2026-01-01T00:00:00Z",
        )
    )
    session.commit()


def valid_proof() -> dict[str, Any]:
    """A checker-valid draft over the seeded fact (T6.1)."""
    return {
        "claim_id": "C-01",
        "as_of": "2026-11-20",
        "conclusion": "holds",
        "premises": [
            {
                "fact_id": "F-01",
                "statement": "Clause 9.2 requires transfer logs.",
                "trust_class": "document_extracted",
            }
        ],
        "steps": [
            {"kind": "cite_fact", "fact_id": "F-01"},
            {"kind": "conclude", "conclusion": "holds"},
        ],
    }


def fake_llm(objections: list[dict[str, Any]]) -> Any:
    """A scripted gateway answering with one emit_objections call (T6.1)."""

    def _fake(request: dict[str, Any], **kwargs: Any) -> llm.LLMResponse:
        return llm.LLMResponse(
            text="",
            tool_calls=[
                {"name": "emit_objections", "arguments": {"objections": objections}}
            ],
            model="scripted",
        )

    return _fake


def test_challenger_request_shape() -> None:
    """T6.1: the review asks the second-pass model with temp 0."""
    request = challenger.challenger_request("q", "CT2", {}, {}, [], [])
    assert request["model"] == "muse-spark-1.2"
    assert request["temperature"] == 0
    assert request["tool_choice"] == "auto"
    assert request["parallel_tool_calls"] is False
    assert request["tools"][0]["name"] == "emit_objections"


def test_parse_objections() -> None:
    """T6.1: severities validate; bad shapes raise a typed error."""
    objections = challenger.parse_objections(
        {"objections": [{"severity": "blocking", "reason": "premise mismatch"}]}
    )
    assert objections == [{"severity": "blocking", "reason": "premise mismatch"}]
    with pytest.raises(ChallengerError):
        challenger.parse_objections({"objections": [{"severity": "fatal", "reason": "x"}]})
    with pytest.raises(ChallengerError):
        challenger.parse_objections({"objections": [{"severity": "note", "reason": ""}]})
    with pytest.raises(ChallengerError):
        challenger.parse_objections({"objections": "none"})


def test_unknown_provider_rejected() -> None:
    """T6.1: Done when a non-meta provider switch is refused."""
    with pytest.raises(ChallengerError, match="unknown challenger provider"):
        challenger.resolve_provider("openweights")


def test_scripted_blocking_objection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """T6.1: a blocking objection parses with blocking set."""
    session = make_session(tmp_path)
    seed_rows(session)
    monkeypatch.setattr(
        "app.agent.llm.call_llm",
        fake_llm([{"severity": "blocking", "reason": "statement differs"}]),
    )
    report = challenger.review_claim("q", "CT2", {}, valid_proof(), [], [])
    assert report.blocking is True
    assert report.note is False
    assert report.objections[0]["reason"] == "statement differs"
    session.close()


def test_objection_forces_requires_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """T6.1: Done when an objection forces REQUIRES_REVIEW."""
    session = make_session(tmp_path)
    seed_rows(session)
    monkeypatch.setenv("CHALLENGER", "on")
    monkeypatch.setattr(
        "app.agent.llm.call_llm",
        fake_llm([{"severity": "blocking", "reason": "statement differs"}]),
    )
    finding = memory.decide_finding(
        session, claim_id="C-01", proof=valid_proof(), run_id="RUN-01"
    )
    assert finding.status == "REQUIRES_REVIEW"
    session.close()


def test_endorsement_keeps_follows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """T6.1: an empty objection list leaves a valid proof at FOLLOWS."""
    session = make_session(tmp_path)
    seed_rows(session)
    monkeypatch.setenv("CHALLENGER", "on")
    monkeypatch.setattr("app.agent.llm.call_llm", fake_llm([]))
    finding = memory.decide_finding(
        session, claim_id="C-01", proof=valid_proof(), run_id="RUN-01"
    )
    assert finding.status == "FOLLOWS"
    session.close()


def replay_session(tmp_path: Path) -> tuple[Session, str]:
    """Seeded demo database with the fixed 9.2 rows (T6.1)."""
    engine = init_db(tmp_path / "replay.db")
    session = sessionmaker(bind=engine, future=True)()
    seed.seed_demo(str(tmp_path / "replay.db"), CORPUS_ROOT)
    claim_id = loop.ensure_demo_92_claim(session)
    return session, claim_id


def test_replay_challenger_blocks_tampered_proof(tmp_path: Path) -> None:
    """T6.1: the recorded review flags the tampered premise as blocking."""
    session, claim_id = replay_session(tmp_path)
    claim = session.get(models.Claim, claim_id)
    assert claim is not None
    try:
        report = challenger.review_claim(
            question=str(claim.question_text),
            claim_type=str(claim.claim_type),
            params=dict(claim.params_json or {}),
            proof=challenger.demo_flawed_proof(),
            premise_lines=challenger.premise_lines(session, "MAT-01"),
            card_lines=challenger.card_lines(session),
            mode="replay",
            cache_dir=CASSETTES_DIR,
        )
    except CassetteMissing:
        pytest.skip("challenger cassette not recorded; run make record with a key")
        return
    assert report.blocking is True
    assert len(report.objections) == 2
    assert {item["severity"] for item in report.objections} == {"blocking"}
    session.close()


def test_replay_decide_with_challenger(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """T6.1: decide with CHALLENGER=on replays to REQUIRES_REVIEW."""
    session, claim_id = replay_session(tmp_path)
    monkeypatch.setenv("CHALLENGER", "on")
    try:
        finding = memory.decide_finding(
            session,
            claim_id=claim_id,
            proof=challenger.demo_flawed_proof(),
            run_id="RUN-01",
            challenger_cache_dir=CASSETTES_DIR,
        )
    except CassetteMissing:
        pytest.skip("challenger cassette not recorded; run make record with a key")
        return
    assert finding.status == "REQUIRES_REVIEW"
    session.close()


def test_challenger_off_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """T6.1: with no flag the second pass never runs."""
    session = make_session(tmp_path)
    seed_rows(session)
    monkeypatch.delenv("CHALLENGER", raising=False)

    def _boom(request: dict[str, Any], **kwargs: Any) -> llm.LLMResponse:
        raise AssertionError("challenger must not run")

    monkeypatch.setattr("app.agent.llm.call_llm", _boom)
    finding = memory.decide_finding(
        session, claim_id="C-01", proof=valid_proof(), run_id="RUN-01"
    )
    assert finding.status == "FOLLOWS"
    session.close()
