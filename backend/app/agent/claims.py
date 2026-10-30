"""T2.3: question → typed claim via the gateway (F4).

The closed taxonomy comes from ARCHITECTURE §7: CT1 numeric_bound, CT2
required_element, CT3 in_force_on, CT4 role_applies; anything else is UNKNOWN
with a one-sentence explanation. The model sees the clause inventory (refs +
headings) plus the question — enough to type the question, deliberately not
the full text. Param shapes are validated service-side; CT3 dates must be
plain YYYY-MM-DD copied from the question, never invented.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.agent import llm, prompts
from app.core.errors import ClaimError
from app.services import seed

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CORPUS_ROOT = REPO_ROOT / "corpus"

CLAIM_MODEL = "muse-spark-1.3-contributor"
DEFAULT_AS_OF = "2026-11-20"
MAX_CLAIM_RETRIES = 2

CLAIM_TYPES = frozenset({"CT1", "CT2", "CT3", "CT4", "UNKNOWN"})

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# T2.3 sample set: 4 supported (one per type) + 2 unsupported.
CLAIM_SAMPLES = [
    {
        "id": "ct1-window",
        "question": "Is clause 10's 72-hour timeline for full breach details "
        "within the required reporting window?",
    },
    {
        "id": "ct2-deletion",
        "question": "Does the agreement require the processor to delete data "
        "when instructed?",
    },
    {
        "id": "ct3-inforce",
        "question": "Is clause 11's retention duty in force on 2027-06-01?",
    },
    {
        "id": "ct4-role",
        "question": "Is Nimbus a Data Processor under this agreement?",
    },
    {"id": "unk-fairness", "question": "Is this agreement fair to Nimbus?"},
    {
        "id": "unk-summary",
        "question": "Summarise the entire agreement in one paragraph.",
    },
]


@dataclass(frozen=True)
class ClaimDraft:
    """A typed but undecided claim (T2.3, F4). Status comes later, from memory."""

    claim_type: str
    params: dict[str, Any]
    question_text: str
    explanation: str = ""
    model: str = ""
    request_sha: str = ""
    cached: bool = False


def build_inventory(clauses: list[tuple[str, str, str]]) -> str:
    """Render the clause inventory the structurer sees (T2.3)."""
    return "\n".join(f"{ref} {heading}" for ref, heading, _ in clauses)


def default_inventory(corpus_root: str | Path = DEFAULT_CORPUS_ROOT) -> str:
    """Build the inventory from the checked-in contract (T2.3)."""
    raw = (Path(corpus_root) / "contracts" / "master_dpa.md").read_text(encoding="utf-8")
    return build_inventory(seed.parse_contract(raw))


def claim_request(
    question: str, inventory: str, as_of: str = DEFAULT_AS_OF
) -> dict[str, Any]:
    """Build the exact gateway request for one question (T2.3)."""
    return {
        "model": CLAIM_MODEL,
        "input": prompts.build_claim_input(question, inventory, as_of),
        "tools": [prompts.CLAIM_TOOL],
        "tool_choice": "auto",
        "parallel_tool_calls": False,
        "temperature": 0,
    }


def _nonempty(value: Any, what: str) -> str:
    """Require a non-empty string (T2.3)."""
    if not isinstance(value, str) or not value:
        raise ClaimError(f"{what} must be a non-empty string")
    return value


def _check_params(claim_type: str, params: Any) -> dict[str, Any]:
    """Validate type-specific params (T2.3)."""
    if not isinstance(params, dict):
        raise ClaimError("params must be an object")
    if claim_type == "CT1":
        value = params.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ClaimError("CT1 params need a numeric value")
        _nonempty(params.get("unit"), "CT1 params need a unit")
    elif claim_type == "CT2":
        _nonempty(params.get("element"), "CT2 params need an element")
    elif claim_type == "CT3":
        date = params.get("date", "")
        if not isinstance(date, str) or not DATE_RE.match(date):
            raise ClaimError("CT3 params need a date as YYYY-MM-DD")
    elif claim_type == "CT4":
        _nonempty(params.get("party"), "CT4 params need a party")
        _nonempty(params.get("role"), "CT4 params need a role")
    return dict(params)


def parse_claim(arguments: dict[str, Any], question: str) -> ClaimDraft:
    """Validate tool arguments into a ClaimDraft (T2.3)."""
    if not isinstance(arguments, dict):
        raise ClaimError("claim arguments must be an object")
    claim_type = arguments.get("claim_type", "")
    if claim_type not in CLAIM_TYPES:
        raise ClaimError(f"unknown claim_type {claim_type!r}")
    question_text = arguments.get("question_text", "")
    if not isinstance(question_text, str) or not question_text:
        if not question:
            raise ClaimError("claim needs a non-empty question")
        question_text = question
    explanation = arguments.get("explanation", "")
    if not isinstance(explanation, str):
        raise ClaimError("explanation must be a string")
    if claim_type == "UNKNOWN" and not explanation:
        raise ClaimError("UNKNOWN claims need an explanation")
    return ClaimDraft(
        claim_type=str(claim_type),
        params=_check_params(str(claim_type), arguments.get("params", {})),
        question_text=question_text,
        explanation=explanation,
    )


def structure_claim(
    question: str,
    inventory: str,
    as_of: str = DEFAULT_AS_OF,
    mode: str | None = None,
    cache_dir: str | Path = llm.DEFAULT_CACHE_DIR,
    session: Session | None = None,
    run_id: str | None = None,
    max_retries: int = MAX_CLAIM_RETRIES,
) -> ClaimDraft:
    """Type one question through a single emit_claim call (T2.3, F4)."""
    request = claim_request(question, inventory, as_of)
    resolved = llm.resolve_mode(mode)
    attempts = 1 + max_retries if resolved == "live" else 1
    last_error: ClaimError | None = None
    for _ in range(attempts):
        response = llm.call_llm(
            request, mode=resolved, cache_dir=cache_dir, session=session, run_id=run_id
        )
        calls = [call for call in response.tool_calls if call.get("name") == "emit_claim"]
        if len(calls) != 1:
            last_error = ClaimError(f"expected exactly one emit_claim call, got {len(calls)}")
            continue
        try:
            parsed = parse_claim(calls[0].get("arguments", {}), question)
        except ClaimError as exc:
            last_error = exc
            continue
        return ClaimDraft(
            claim_type=parsed.claim_type,
            params=parsed.params,
            question_text=parsed.question_text,
            explanation=parsed.explanation,
            model=response.model,
            request_sha=response.request_sha,
            cached=response.cached,
        )
    raise last_error if last_error is not None else ClaimError("claim typing failed")
