"""T6.1: challenger — Muse Spark second pass with structured objections (F17).

A different model version and a different prompt from the proposer review
the finished draft; any `blocking` objection forces REQUIRES_REVIEW in
the memory service. Provider switch: `CHALLENGER_PROVIDER=meta` (default);
the openweights challenger lands in T7.5.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app import models
from app.agent import llm, prompts
from app.core.errors import ChallengerError

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CORPUS_ROOT = REPO_ROOT / "corpus"

CHALLENGER_MODEL = "muse-spark-1.2"
CHALLENGER_PROVIDER = "meta"
MAX_CHALLENGER_RETRIES = 2

SEVERITIES = frozenset({"blocking", "note"})


@dataclass(frozen=True)
class ChallengerReport:
    """Structured second-pass verdict (T6.1, F17)."""

    objections: list[dict[str, Any]] = field(default_factory=list)
    blocking: bool = False
    note: bool = False
    model: str = ""
    request_sha: str = ""
    cached: bool = False


def challenger_request(
    question: str,
    claim_type: str,
    params: dict[str, Any],
    proof: dict[str, Any],
    premise_lines: list[str],
    card_lines: list[str],
) -> dict[str, Any]:
    """Build the exact gateway request for one review (T6.1)."""
    return {
        "model": CHALLENGER_MODEL,
        "input": prompts.build_challenger_input(
            question, claim_type, params, proof, premise_lines, card_lines
        ),
        "tools": [prompts.CHALLENGER_TOOL],
        "tool_choice": "auto",
        "parallel_tool_calls": False,
        "temperature": 0,
    }


def resolve_provider(provider: str | None) -> str:
    """Validate the challenger provider switch (T6.1)."""
    resolved = (provider or os.environ.get("CHALLENGER_PROVIDER", "meta")).lower()
    if resolved != CHALLENGER_PROVIDER:
        raise ChallengerError(
            f"unknown challenger provider {resolved!r}; expected 'meta'"
        )
    return resolved


def parse_objections(arguments: Any) -> list[dict[str, Any]]:
    """Validate tool arguments into an objection list (T6.1)."""
    if not isinstance(arguments, dict):
        raise ChallengerError("objection arguments must be an object")
    objections = arguments.get("objections", [])
    if not isinstance(objections, list):
        raise ChallengerError("objections must be a list")
    parsed: list[dict[str, Any]] = []
    for objection in objections:
        if not isinstance(objection, dict):
            raise ChallengerError("each objection must be an object")
        severity = objection.get("severity", "")
        if severity not in SEVERITIES:
            raise ChallengerError(f"unknown severity {severity!r}")
        reason = objection.get("reason", "")
        if not isinstance(reason, str) or not reason:
            raise ChallengerError("each objection needs a non-empty reason")
        entry: dict[str, Any] = {"severity": severity, "reason": reason}
        quote = objection.get("quote", "")
        if isinstance(quote, str) and quote:
            entry["quote"] = quote
        parsed.append(entry)
    return parsed


def review_claim(
    question: str,
    claim_type: str,
    params: dict[str, Any],
    proof: dict[str, Any],
    premise_lines: list[str],
    card_lines: list[str],
    mode: str | None = None,
    cache_dir: str | Path = llm.DEFAULT_CACHE_DIR,
    session: Session | None = None,
    run_id: str | None = None,
    provider: str | None = None,
    max_retries: int = MAX_CHALLENGER_RETRIES,
) -> ChallengerReport:
    """Review one draft proof through a single emit_objections call (T6.1)."""
    resolve_provider(provider)
    request = challenger_request(
        question, claim_type, params, proof, premise_lines, card_lines
    )
    resolved = llm.resolve_mode(mode)
    attempts = 1 + max_retries if resolved == "live" else 1
    last_error: ChallengerError | None = None
    for _ in range(attempts):
        response = llm.call_llm(
            request, mode=resolved, cache_dir=cache_dir, session=session, run_id=run_id
        )
        calls = [call for call in response.tool_calls if call.get("name") == "emit_objections"]
        if len(calls) != 1:
            last_error = ChallengerError(
                f"expected exactly one emit_objections call, got {len(calls)}"
            )
            continue
        try:
            objections = parse_objections(calls[0].get("arguments", {}))
        except ChallengerError as exc:
            last_error = exc
            continue
        return ChallengerReport(
            objections=objections,
            blocking=any(item["severity"] == "blocking" for item in objections),
            note=any(item["severity"] == "note" for item in objections),
            model=response.model,
            request_sha=response.request_sha,
            cached=response.cached,
        )
    raise last_error if last_error is not None else ChallengerError("review failed")


def premise_lines(session: Session, matter_id: str) -> list[str]:
    """Admitted premises rendered for the challenger (T6.1)."""
    rows = (
        session.execute(
            sa.select(models.Fact)
            .where(models.Fact.matter_id == matter_id)
            .order_by(models.Fact.id)
        )
        .scalars()
        .all()
    )
    return [
        f"{row.id} | {row.trust_class} | {row.clause_id} | {row.statement}"
        for row in rows
    ]


def card_lines(session: Session) -> list[str]:
    """Rule cards rendered for the challenger (T6.1)."""
    rows = (
        session.execute(sa.select(models.RuleCard).order_by(models.RuleCard.id))
        .scalars()
        .all()
    )
    return [
        f"{row.id} | {row.claim_type} | {row.provision_id} | {row.kind}"
        for row in rows
    ]


def demo_flawed_proof() -> dict[str, Any]:
    """Fixed tampered-premise proof for the recorded review (T6.1).

    Shared by the record script and the replay test so the challenger
    request hash matches; every string is a constant, never generated.
    """
    from app.agent import loop

    return {
        "claim_id": loop.DEMO_92_CLAIM_ID,
        "as_of": loop.DEMO_92_AS_OF,
        "conclusion": "holds",
        "premises": [
            {
                "fact_id": loop.DEMO_92_FACT_ID,
                "statement": "Clause 9.2 forbids all cross-border transfers.",
                "trust_class": "document_extracted",
            }
        ],
        "steps": [
            {"kind": "cite_fact", "fact_id": loop.DEMO_92_FACT_ID},
            {"kind": "conclude", "conclusion": "holds"},
        ],
    }
