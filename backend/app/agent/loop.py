"""T2.5: bounded agent loop — Responses API function calling (F5).

`run_verify` drafts a proof for one claim with the six tools from T2.4,
dispatching each model-requested call through `tools.call_tool` so matter
scoping, the 12-call budget and `tool_calls` logging always apply. The run
row records the outcome (`accepted`, `no_proof`, `rejected`,
`budget_exhausted`). Model errors on live calls retry twice; tool errors
are fed back to the model as outputs. All model access goes through the
gateway; temperature is 0 for proofs.
"""

import json
import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app import models
from app.agent import llm, prompts, tools
from app.core.errors import LLMRequestFailed, SourceUnavailable, ToolError

LOOP_MODEL = "muse-spark-1.3-contributor"
MAX_AGENT_RETRIES = 2


@dataclass(frozen=True)
class LoopResult:
    """Outcome of one agent-loop run (T2.5)."""

    run_id: str
    accepted: bool
    proof: dict[str, Any] | None
    report: dict[str, Any] | None
    outcome: str
    tool_calls: int


def proof_request(history: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the exact gateway request for one loop turn (T2.5)."""
    return {
        "model": LOOP_MODEL,
        "input": list(history),
        "tools": tools.TOOL_SCHEMAS,
        "tool_choice": "auto",
        "parallel_tool_calls": False,
        "temperature": 0,
    }


def _logged_call_count(session: Session, run_id: str) -> int:
    """Tool calls logged for a run so far (T2.5)."""
    total = session.execute(
        sa.select(sa.func.count())
        .select_from(models.ToolCall)
        .where(models.ToolCall.run_id == run_id)
    ).scalar()
    assert total is not None
    return int(total)


def _claim_context(session: Session, claim: models.Claim) -> tuple[str, str, str]:
    """Target clause ref, heading and text for a claim (T2.5)."""
    clause = session.get(models.Clause, claim.clause_id)
    if clause is None:
        raise ToolError(f"unknown clause {claim.clause_id!r}", code="unknown_clause")
    return str(clause.ref), str(clause.heading), str(clause.text)


def _inventory(session: Session, document_version_id: str) -> str:
    """Clause inventory (ref + heading) for the prompt (T2.5)."""
    rows = list(
        session.execute(
            sa.select(models.Clause)
            .where(models.Clause.document_version_id == document_version_id)
            .order_by(models.Clause.id)
        )
        .scalars()
        .all()
    )
    return "\n".join(f"{row.ref} {row.heading}" for row in rows)


def _source_lines(session: Session) -> list[str]:
    """Source registry rendered for the prompt (T2.5)."""
    rows = list(
        session.execute(sa.select(models.Source).order_by(models.Source.id))
        .scalars()
        .all()
    )
    return [f"{row.id} | {row.key} | {row.title}" for row in rows]


def _fact_lines(session: Session, matter_id: str) -> list[str]:
    """Admitted premises rendered for the prompt (T2.5)."""
    rows = list(
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


def _finish_run(session: Session, run_id: str, outcome: str) -> None:
    """Stamp a run row with its outcome (T2.5)."""
    run = session.get(models.Run, run_id)
    assert run is not None
    run.outcome = outcome
    run.ended_at = datetime_now()
    session.commit()


def datetime_now() -> str:
    """Current UTC time in ISO-8601 (T2.5)."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


DEMO_92_FACT_ID = "F-LOOP-92"
DEMO_92_CLAIM_ID = "C-LOOP-92"
DEMO_92_QUESTION = "Does clause 9.2 require Nimbus to keep transfer logs?"
DEMO_92_AS_OF = "2026-11-20"
DEMO_92_STATEMENT = "Clause 9.2 requires Nimbus to keep transfer logs for review."


def ensure_demo_92_claim(session: Session) -> str:
    """Create the fixed clause-9.2 fact and claim when missing (T2.5).

    Record and replay share these exact rows so the loop request hashes
    match; ids, text and dates are constants, never generated.
    """
    clause = session.execute(
        sa.select(models.Clause).where(models.Clause.ref == "9.2")
    ).scalars().first()
    if clause is None:
        raise ToolError("demo contract has no clause 9.2", code="unknown_clause")
    if session.get(models.Fact, DEMO_92_FACT_ID) is None:
        session.add(
            models.Fact(
                id=DEMO_92_FACT_ID,
                matter_id="MAT-01",
                clause_id=clause.id,
                statement=DEMO_92_STATEMENT,
                structured_json={"element": "transfer logs", "clause_ref": "9.2"},
                origin="extracted",
                trust_class="document_extracted",
                created_at="2026-01-01T00:00:00Z",
            )
        )
    if session.get(models.Claim, DEMO_92_CLAIM_ID) is None:
        session.add(
            models.Claim(
                id=DEMO_92_CLAIM_ID,
                matter_id="MAT-01",
                clause_id=clause.id,
                claim_type="CT2",
                params_json={"element": "transfer logs"},
                question_text=DEMO_92_QUESTION,
                as_of=DEMO_92_AS_OF,
                created_at="2026-01-01T00:00:00Z",
            )
        )
    session.commit()
    return DEMO_92_CLAIM_ID


def run_verify(
    session: Session,
    *,
    claim_id: str,
    matter_id: str,
    mode: str | None = None,
    cache_dir: str | Path = llm.DEFAULT_CACHE_DIR,
    max_tool_calls: int = tools.MAX_TOOL_CALLS_PER_RUN,
    max_retries: int = MAX_AGENT_RETRIES,
) -> LoopResult:
    """Draft a proof for one claim through the six tools (T2.5, F5)."""
    claim = session.get(models.Claim, claim_id)
    if claim is None:
        raise ToolError(f"unknown claim {claim_id!r}", code="unknown_claim")
    if claim.matter_id != matter_id:
        raise ToolError("claim is outside the session matter", code="cross_matter")
    run_id = f"RUN-{uuid.uuid4().hex[:12]}"
    session.add(
        models.Run(
            id=run_id,
            trigger="verify",
            claim_id=claim.id,
            started_at=datetime_now(),
        )
    )
    session.commit()
    clause = session.get(models.Clause, claim.clause_id)
    if clause is None:
        raise ToolError(f"unknown clause {claim.clause_id!r}", code="unknown_clause")
    ref, heading, text = _claim_context(session, claim)
    origin = prompts.build_proof_input(
        question=str(claim.question_text),
        claim_type=str(claim.claim_type),
        params=dict(claim.params_json or {}),
        as_of=str(claim.as_of),
        matter_id=matter_id,
        clause_ref=ref,
        clause_heading=heading,
        clause_text=text,
        inventory=_inventory(session, str(clause.document_version_id)),
        fact_lines=_fact_lines(session, matter_id),
        source_lines=_source_lines(session),
    )
    history: list[dict[str, Any]] = [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": origin}],
        }
    ]
    resolved = llm.resolve_mode(mode)
    if resolved == "live" and not os.environ.get("MODEL_API_KEY"):
        raise LLMRequestFailed(
            "MODEL_API_KEY is missing: export it or run with .env sourced "
            "(set -a; source .env; set +a)"
        )
    accepted = False
    proof: dict[str, Any] | None = None
    outcome = "no_proof"
    while True:
        if _logged_call_count(session, run_id) >= max_tool_calls:
            outcome = "budget_exhausted"
            break
        request = proof_request(history)
        attempts = 1 + max_retries if resolved == "live" else 1
        response: llm.LLMResponse | None = None
        for _ in range(attempts):
            try:
                response = llm.call_llm(
                    request,
                    mode=resolved,
                    cache_dir=cache_dir,
                    session=session,
                    run_id=run_id,
                )
                break
            except LLMRequestFailed:
                continue
        if response is None:
            raise LLMRequestFailed("agent loop retries exhausted")
        if not response.tool_calls:
            outcome = "no_proof"
            break
        for call in response.tool_calls:
            if _logged_call_count(session, run_id) >= max_tool_calls:
                outcome = "budget_exhausted"
                break
            name = str(call.get("name", ""))
            arguments = call.get("arguments", {})
            if not isinstance(arguments, dict):
                arguments = {}
            try:
                result = tools.call_tool(
                    session,
                    run_id=run_id,
                    matter_id=matter_id,
                    tool=name,
                    args=arguments,
                )
            except (ToolError, SourceUnavailable) as exc:
                code = getattr(exc, "code", None)
                result = {
                    "error": {
                        "code": code if isinstance(code, str) else type(exc).__name__,
                        "message": str(exc),
                    }
                }
            history.append(
                {
                    "type": "function_call",
                    "call_id": call.get("call_id"),
                    "name": name,
                    "arguments": json.dumps(arguments),
                }
            )
            history.append(
                {
                    "type": "function_call_output",
                    "call_id": call.get("call_id"),
                    "output": json.dumps(result),
                }
            )
            if name == "propose_finding" and result.get("accepted") is True:
                accepted = True
                candidate = arguments.get("proof")
                proof = candidate if isinstance(candidate, dict) else None
                outcome = "accepted"
                break
        else:
            continue
        break
    report: dict[str, Any] | None = None
    if accepted and proof is not None:
        if _logged_call_count(session, run_id) < max_tool_calls:
            report = tools.call_tool(
                session,
                run_id=run_id,
                matter_id=matter_id,
                tool="verify_derivation",
                args={"claim_id": claim.id, "proof": proof},
            )
        else:
            report = tools.verify_proof(session, matter_id, claim.id, proof)
        if not report.get("valid", False):
            accepted = False
            outcome = "rejected"
    if not accepted and outcome == "accepted":
        outcome = "rejected"
    _finish_run(session, run_id, outcome)
    return LoopResult(
        run_id=run_id,
        accepted=accepted,
        proof=proof,
        report=report,
        outcome=outcome,
        tool_calls=_logged_call_count(session, run_id),
    )
