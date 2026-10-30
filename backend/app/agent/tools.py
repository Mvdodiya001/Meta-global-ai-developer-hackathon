"""T2.4: the six bounded model tools (F5).

Schemas match DATA_MODEL_API §4 exactly (Responses API function-tool shape);
`TOOL_NAMES` is the closed set — anything else is rejected. The session fixes
`matter_id`: any arg resolving to another matter raises `ToolError`
(`cross_matter`). At most 12 calls run per run id; the 13th raises
(`tool_budget_exhausted`). Every dispatched call is logged to `tool_calls`
with its sequence number, args, result and outcome, feeding T3.3 re-query
enforcement. Only `propose_finding` accepts a proof, and even an accepted
draft writes no finding row — status decisions stay in T3.3 memory service.
"""

import uuid
from datetime import UTC, datetime
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app import models
from app.core.errors import SourceUnavailable, ToolError
from checker import verify as checker

TOOL_NAMES = (
    "lookup_source",
    "list_dependent_claims",
    "get_premise",
    "verify_derivation",
    "propose_finding",
    "request_lawyer_review",
)

MAX_TOOL_CALLS_PER_RUN = 12
MAX_PROVISIONS_PER_LOOKUP = 5
MAX_DEPENDENT_ITEMS = 20

REVIEW_ITEM_TYPES = frozenset({"claim", "finding", "fact", "rule_card"})

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "lookup_source",
        "description": (
            "Fetch provisions of a source at a specific version (default: "
            "the version valid on as_of). Max 5 provisions returned."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "source_id": {"type": "string"},
                "version": {
                    "type": "string",
                    "description": "'current' or a source_version id",
                },
                "provision_key": {"type": "string"},
            },
            "required": ["source_id"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "list_dependent_claims",
        "description": (
            "List claims/findings in this matter that depend on a source "
            "or provision. Max 20."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "source_id": {"type": "string"},
                "provision_key": {"type": "string"},
            },
            "required": ["source_id"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_premise",
        "description": "Fetch one fact with its trust class and origin span.",
        "parameters": {
            "type": "object",
            "properties": {
                "matter_id": {"type": "string"},
                "premise_id": {"type": "string"},
            },
            "required": ["matter_id", "premise_id"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "verify_derivation",
        "description": (
            "Run the deterministic checker on a draft proof. "
            "Read-only; changes no state."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "claim_id": {"type": "string"},
                "proof": {"type": "object"},
            },
            "required": ["claim_id", "proof"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "propose_finding",
        "description": (
            "Propose a proof for a claim. The memory service re-checks it "
            "and decides the status. You cannot set a status."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "claim_id": {"type": "string"},
                "proof": {"type": "object"},
            },
            "required": ["claim_id", "proof"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "request_lawyer_review",
        "description": "Flag an item for lawyer review with a reason.",
        "parameters": {
            "type": "object",
            "properties": {
                "item_type": {
                    "type": "string",
                    "enum": ["claim", "finding", "fact", "rule_card"],
                },
                "item_id": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["item_type", "item_id", "reason"],
            "additionalProperties": False,
        },
    },
]


def _utcnow() -> str:
    """Current UTC time in ISO-8601 (T2.4)."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    """One prefixed random id for tool-created rows (T2.4)."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _check_matter_arg(matter_id: str, value: Any) -> None:
    """Reject a matter arg pointing outside the session matter (T2.4)."""
    if value != matter_id:
        raise ToolError(
            f"matter {value!r} is outside the session matter {matter_id!r}",
            code="cross_matter",
        )


def _scoped_claim(session: Session, matter_id: str, claim_id: Any) -> models.Claim:
    """Fetch a claim or reject unknown ids and other matters (T2.4)."""
    claim = session.get(models.Claim, claim_id) if isinstance(claim_id, str) else None
    if claim is None:
        raise ToolError(f"unknown claim {claim_id!r}", code="unknown_claim")
    if claim.matter_id != matter_id:
        raise ToolError(
            f"claim {claim_id!r} is outside the session matter",
            code="cross_matter",
        )
    return claim


def _log_call(
    session: Session,
    run_id: str,
    seq: int,
    tool: str,
    args: dict[str, Any],
    ok: bool,
    result: dict[str, Any],
) -> None:
    """Append one `tool_calls` row (T2.4)."""
    session.add(
        models.ToolCall(
            id=_new_id("TC"),
            run_id=run_id,
            seq=seq,
            tool=tool,
            args_json=args,
            result_json=result,
            ok=ok,
            created_at=_utcnow(),
        )
    )
    session.commit()


def _call_count(session: Session, run_id: str) -> int:
    """Number of logged calls for a run (T2.4)."""
    total = session.execute(
        sa.select(sa.func.count())
        .select_from(models.ToolCall)
        .where(models.ToolCall.run_id == run_id)
    ).scalar()
    assert total is not None
    return int(total)


def _resolve_version(
    session: Session, source_id: str, version: Any
) -> models.SourceVersion:
    """Resolve 'current'/omitted to the non-superseded version (T2.4)."""
    rows = list(
        session.execute(
            sa.select(models.SourceVersion)
            .where(models.SourceVersion.source_id == source_id)
            .order_by(models.SourceVersion.id)
        )
        .scalars()
        .all()
    )
    if not rows:
        raise SourceUnavailable(f"unknown source: {source_id}")
    if version is None or version == "current":
        superseded = {row.supersedes_id for row in rows if row.supersedes_id}
        current = [row for row in rows if row.id not in superseded]
        if not current:
            raise SourceUnavailable(f"no current version for source {source_id}")
        return max(current, key=lambda row: str(row.effective_from))
    for row in rows:
        if row.id == version:
            return row
    raise SourceUnavailable(f"unknown source version: {version}")


def _lookup_source(
    session: Session, matter_id: str, args: dict[str, Any]
) -> dict[str, Any]:
    """Fetch up to 5 provisions of one source version (T2.4)."""
    source_id = args.get("source_id")
    if not isinstance(source_id, str):
        raise ToolError("lookup_source needs a source_id", code="bad_args")
    source = session.get(models.Source, source_id)
    if source is None:
        raise SourceUnavailable(f"unknown source: {source_id}")
    version = _resolve_version(session, source_id, args.get("version", "current"))
    key = args.get("provision_key")
    rows = list(
        session.execute(
            sa.select(models.Provision)
            .where(models.Provision.source_version_id == version.id)
            .order_by(models.Provision.id)
        )
        .scalars()
        .all()
    )
    if isinstance(key, str):
        rows = [row for row in rows if row.key == key]
    truncated = len(rows) > MAX_PROVISIONS_PER_LOOKUP
    return {
        "source_version_id": version.id,
        "version_label": version.version_label,
        "effective_from": version.effective_from,
        "effective_until": version.effective_until,
        "is_simulated": bool(version.is_simulated),
        "provisions": [
            {
                "provision_id": row.id,
                "key": row.key,
                "text": row.text,
                "sha256": row.text_sha256,
            }
            for row in rows[:MAX_PROVISIONS_PER_LOOKUP]
        ],
        "truncated": truncated,
    }


def _dependent_provision_ids(
    session: Session, source_id: str, provision_key: Any
) -> set[str]:
    """Provision ids of a source (all versions), optionally by key (T2.4)."""
    rows = list(
        session.execute(
            sa.select(models.Provision)
            .join(
                models.SourceVersion,
                models.Provision.source_version_id == models.SourceVersion.id,
            )
            .where(models.SourceVersion.source_id == source_id)
        )
        .scalars()
        .all()
    )
    if isinstance(provision_key, str):
        rows = [row for row in rows if row.key == provision_key]
    return {str(row.id) for row in rows}


def _finding_state(session: Session, finding: models.Finding) -> str:
    """Latest event state for a finding, else its stored status (T2.4)."""
    event = session.execute(
        sa.select(models.FindingEvent)
        .where(models.FindingEvent.finding_id == finding.id)
        .order_by(models.FindingEvent.created_at.desc())
    ).scalars().first()
    return str(event.state) if event is not None else str(finding.status)


def _list_dependent_claims(
    session: Session, matter_id: str, args: dict[str, Any]
) -> dict[str, Any]:
    """Claims/findings in this matter depending on a source (T2.4)."""
    source_id = args.get("source_id")
    if not isinstance(source_id, str):
        raise ToolError("list_dependent_claims needs a source_id", code="bad_args")
    if session.get(models.Source, source_id) is None:
        raise SourceUnavailable(f"unknown source: {source_id}")
    provision_ids = _dependent_provision_ids(
        session, source_id, args.get("provision_key")
    )
    card_ids = {
        str(row.id)
        for row in session.execute(
            sa.select(models.RuleCard).where(
                models.RuleCard.provision_id.in_(provision_ids)
            )
            if provision_ids
            else sa.select(models.RuleCard).where(sa.false())
        )
        .scalars()
        .all()
    }
    edges = (
        session.execute(
            sa.select(models.Edge)
            .where(models.Edge.rel == "DEPENDS_ON")
            .order_by(models.Edge.id)
        )
        .scalars()
        .all()
    )
    items: list[dict[str, Any]] = []
    for edge in edges:
        if edge.dst_type == "provision" and edge.dst_id not in provision_ids:
            continue
        if edge.dst_type == "rule_card" and edge.dst_id not in card_ids:
            continue
        if edge.dst_type not in ("provision", "rule_card"):
            continue
        if edge.src_type != "finding":
            continue
        finding = session.get(models.Finding, edge.src_id)
        if finding is None:
            continue
        claim = session.get(models.Claim, finding.claim_id)
        if claim is None or claim.matter_id != matter_id:
            continue
        items.append(
            {
                "claim_id": claim.id,
                "finding_id": finding.id,
                "state": _finding_state(session, finding),
            }
        )
        if len(items) >= MAX_DEPENDENT_ITEMS:
            break
    return {"items": items}


def _get_premise(
    session: Session, matter_id: str, args: dict[str, Any]
) -> dict[str, Any]:
    """Fetch one fact with its trust class and origin span (T2.4)."""
    _check_matter_arg(matter_id, args.get("matter_id"))
    premise_id = args.get("premise_id")
    fact = session.get(models.Fact, premise_id) if isinstance(premise_id, str) else None
    if fact is None:
        raise ToolError(f"unknown fact {premise_id!r}", code="unknown_fact")
    if fact.matter_id != matter_id:
        raise ToolError(
            f"fact {premise_id!r} is outside the session matter",
            code="cross_matter",
        )
    clause_id: str | None = None
    span: list[int] | None = None
    if fact.clause_id is not None:
        clause = session.get(models.Clause, fact.clause_id)
        if clause is not None:
            clause_id = clause.id
            span = [clause.span_start, clause.span_end]
    return {
        "fact_id": fact.id,
        "statement": fact.statement,
        "structured": fact.structured_json,
        "trust_class": fact.trust_class,
        "origin": {"clause_id": clause_id, "span": span},
    }


def _checker_stores(session: Session) -> dict[str, dict[str, Any]]:
    """Build the checker's premise/provision/card/version/clause stores (T2.4)."""
    provisions = {
        str(row.id): {
            "source_version_id": str(row.source_version_id),
            "key": str(row.key),
            "text": str(row.text),
            "text_sha256": str(row.text_sha256),
            "effective_from": str(row.effective_from),
            "effective_until": row.effective_until,
        }
        for row in session.execute(sa.select(models.Provision)).scalars().all()
    }
    rule_cards = {
        str(row.id): {
            "provision_id": str(row.provision_id),
            "claim_type": str(row.claim_type),
        }
        for row in session.execute(sa.select(models.RuleCard)).scalars().all()
    }
    versions = {
        str(row.id): {"supersedes_id": row.supersedes_id}
        for row in session.execute(sa.select(models.SourceVersion)).scalars().all()
    }
    clauses = {
        str(row.id): str(row.text)
        for row in session.execute(sa.select(models.Clause)).scalars().all()
    }
    return {
        "provisions": provisions,
        "rule_cards": rule_cards,
        "versions": versions,
        "clauses": clauses,
    }


def verify_proof(
    session: Session, matter_id: str, claim_id: Any, proof: Any
) -> dict[str, Any]:
    """Validate a draft proof and return the checker verdict (T2.5).

    Same computation as `verify_derivation` without consuming run budget;
    for the loop's final report after the model already verified.
    """
    claim = _scoped_claim(session, matter_id, claim_id)
    if not isinstance(proof, dict):
        raise ToolError("a proof object is required", code="bad_args")
    premises: dict[str, dict[str, Any]] = {}
    entries = proof.get("premises", [])
    if not isinstance(entries, list):
        raise ToolError("proof premises must be a list", code="bad_args")
    for entry in entries:
        fact_id = entry.get("fact_id") if isinstance(entry, dict) else None
        fact = session.get(models.Fact, fact_id) if isinstance(fact_id, str) else None
        if fact is None:
            raise ToolError(f"unknown fact {fact_id!r}", code="unknown_fact")
        if fact.matter_id != matter_id:
            raise ToolError(
                f"fact {fact_id!r} is outside the session matter",
                code="cross_matter",
            )
        premises[str(fact.id)] = {
            "statement": str(fact.statement),
            "trust_class": str(fact.trust_class),
        }
    stores = _checker_stores(session)
    report = checker.verify(
        proof,
        premises,
        stores["provisions"],
        stores["rule_cards"],
        stores["versions"],
        stores["clauses"],
        as_of=str(claim.as_of),
    )
    return {
        "valid": bool(report["valid"]),
        "errors": list(report["errors"]),
        "cited_source_versions": list(report["cited_source_versions"]),
    }


def _run_checker(
    session: Session, matter_id: str, args: dict[str, Any]
) -> dict[str, Any]:
    """Shared proof validation for verify/propose (T2.4)."""
    return verify_proof(session, matter_id, args.get("claim_id"), args.get("proof"))


def _verify_derivation(
    session: Session, matter_id: str, args: dict[str, Any]
) -> dict[str, Any]:
    """Run the checker on a draft proof without changing state (T2.4)."""
    return _run_checker(session, matter_id, args)


def _propose_finding(
    session: Session, matter_id: str, args: dict[str, Any]
) -> dict[str, Any]:
    """Accept a checker-valid draft; persistence stays in T3.3 (T2.4)."""
    report = _run_checker(session, matter_id, args)
    if not report["valid"]:
        first = report["errors"][0] if report["errors"] else {}
        reason = f"{first.get('code', 'INVALID')}: {first.get('message', 'invalid')}"
        return {"accepted": False, "rejection_reason": reason}
    return {"accepted": True}


def _request_lawyer_review(
    session: Session, matter_id: str, args: dict[str, Any]
) -> dict[str, Any]:
    """Flag an item for lawyer review and return the review id (T2.4)."""
    item_type = args.get("item_type")
    item_id = args.get("item_id")
    reason = args.get("reason")
    if item_type not in REVIEW_ITEM_TYPES:
        raise ToolError(f"unknown item type {item_type!r}", code="bad_item_type")
    if not isinstance(item_id, str) or not isinstance(reason, str) or not reason:
        raise ToolError("request_lawyer_review needs item_id and reason", code="bad_args")
    entity = {
        "claim": models.Claim,
        "finding": models.Finding,
        "fact": models.Fact,
        "rule_card": models.RuleCard,
    }[str(item_type)]
    item = session.get(entity, item_id)
    if item is None:
        raise ToolError(f"unknown {item_type} {item_id!r}", code="unknown_item")
    if isinstance(item, models.Finding):
        claim = session.get(models.Claim, item.claim_id)
        owner = claim.matter_id if claim is not None else None
    elif isinstance(item, models.RuleCard):
        owner = None
    else:
        member = cast("models.Claim | models.Fact", item)
        owner = member.matter_id
    if owner is not None and owner != matter_id:
        raise ToolError(
            f"{item_type} {item_id!r} is outside the session matter",
            code="cross_matter",
        )
    review_id = _new_id("RV")
    session.add(
        models.Review(
            id=review_id,
            item_type=str(item_type),
            item_id=item_id,
            reason=reason,
            status="open",
            reviewer="unassigned",
            note=None,
            created_at=_utcnow(),
        )
    )
    session.commit()
    return {"review_id": review_id}


_HANDLERS = {
    "lookup_source": _lookup_source,
    "list_dependent_claims": _list_dependent_claims,
    "get_premise": _get_premise,
    "verify_derivation": _verify_derivation,
    "propose_finding": _propose_finding,
    "request_lawyer_review": _request_lawyer_review,
}


def call_tool(
    session: Session, *, run_id: str, matter_id: str, tool: str, args: dict[str, Any]
) -> dict[str, Any]:
    """Dispatch one bounded tool call with scoping, caps and logging (T2.4).

    Raises `ToolError` for unknown tools, exhausted budgets, cross-matter
    args and bad shapes; `SourceUnavailable` for missing sources/versions.
    """
    run = session.get(models.Run, run_id)
    if run is None:
        raise ToolError(f"unknown run {run_id!r}", code="unknown_run")
    if session.get(models.Matter, matter_id) is None:
        raise ToolError(f"unknown matter {matter_id!r}", code="unknown_matter")
    claim = session.get(models.Claim, run.claim_id)
    if claim is None or claim.matter_id != matter_id:
        raise ToolError(
            f"run {run_id!r} is outside the session matter",
            code="cross_matter",
        )
    if tool not in _HANDLERS:
        _log_call(
            session,
            run_id,
            _call_count(session, run_id) + 1,
            tool,
            args,
            False,
            {"error": {"code": "unknown_tool", "message": f"unknown tool {tool!r}"}},
        )
        raise ToolError(f"unknown tool {tool!r}", code="unknown_tool")
    seq = _call_count(session, run_id) + 1
    if seq > MAX_TOOL_CALLS_PER_RUN:
        raise ToolError(
            f"tool budget exhausted ({MAX_TOOL_CALLS_PER_RUN} calls per run)",
            code="tool_budget_exhausted",
        )
    try:
        result = _HANDLERS[tool](session, matter_id, args)
    except Exception as exc:
        code = exc.code if isinstance(exc, ToolError) else type(exc).__name__
        _log_call(
            session,
            run_id,
            seq,
            tool,
            args,
            False,
            {"error": {"code": code, "message": str(exc)}},
        )
        raise
    _log_call(session, run_id, seq, tool, args, True, result)
    return result
