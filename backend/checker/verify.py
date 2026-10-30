"""Deterministic proof checker (T3.1, F9).

Pure Python: no `app.agent`, no network, no LLM client. The checker validates
what the model proposed — proof schema and step order, premise admission
against the stored trust classes, and citation integrity (provision exists,
span in range, sha256 matches the snapshot). Step-kind semantics land in T3.2.
"""

from typing import Any, cast

ADMITTED_TRUST = frozenset({"lawyer_confirmed", "document_extracted"})

STEP_KINDS = frozenset(
    {
        "cite_fact",
        "cite_rule",
        "in_force",
        "compare",
        "contains_element",
        "role_applies",
        "conclude",
    }
)

SCHEMA_MISSING_FIELD = "SCHEMA_MISSING_FIELD"
SCHEMA_BAD_TYPE = "SCHEMA_BAD_TYPE"
EMPTY_STEPS = "EMPTY_STEPS"
CONCLUDE_POSITION = "CONCLUDE_POSITION"
PREMISE_UNKNOWN = "PREMISE_UNKNOWN"
PREMISE_UNTRUSTED = "PREMISE_UNTRUSTED"
PREMISE_MISMATCH = "PREMISE_MISMATCH"
CITATION_MALFORMED = "CITATION_MALFORMED"
CITATION_UNKNOWN_PROVISION = "CITATION_UNKNOWN_PROVISION"
CITATION_SPAN_RANGE = "CITATION_SPAN_RANGE"
CITATION_HASH_MISMATCH = "CITATION_HASH_MISMATCH"
CITATION_VERSION_MISMATCH = "CITATION_VERSION_MISMATCH"
STEP_UNKNOWN_KIND = "STEP_UNKNOWN_KIND"
STEP_UNKNOWN_FACT = "STEP_UNKNOWN_FACT"
STEP_UNKNOWN_RULE = "STEP_UNKNOWN_RULE"
RULE_PROVISION_MISMATCH = "RULE_PROVISION_MISMATCH"
VERSION_UNKNOWN = "VERSION_UNKNOWN"
VERSION_SUPERSEDED = "VERSION_SUPERSEDED"
PROVISION_UNKNOWN = "PROVISION_UNKNOWN"
PROVISION_NOT_IN_FORCE = "PROVISION_NOT_IN_FORCE"
COMPARE_MALFORMED = "COMPARE_MALFORMED"
COMPARE_FAILED = "COMPARE_FAILED"
EVIDENCE_UNKNOWN_CLAUSE = "EVIDENCE_UNKNOWN_CLAUSE"
QUOTE_NOT_FOUND = "QUOTE_NOT_FOUND"
CONCLUDE_MISMATCH = "CONCLUDE_MISMATCH"


def _error(step: int | None, code: str, message: str) -> dict[str, Any]:
    """Build one checker error in the verify_derivation shape (T3.1)."""
    return {"step": step, "code": code, "message": message}


def _check_schema(proof: Any, errors: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Validate the proof envelope; return it typed or None (T3.1)."""
    if not isinstance(proof, dict):
        errors.append(_error(None, SCHEMA_BAD_TYPE, "proof must be an object"))
        return None
    for field in ("claim_id", "as_of", "premises", "steps", "conclusion"):
        if field not in proof:
            errors.append(_error(None, SCHEMA_MISSING_FIELD, f"missing field {field!r}"))
    if errors:
        return None
    if not isinstance(proof["claim_id"], str) or not proof["claim_id"]:
        errors.append(
            _error(None, SCHEMA_BAD_TYPE, "claim_id must be a non-empty string")
        )
    if not isinstance(proof["as_of"], str) or not proof["as_of"]:
        errors.append(_error(None, SCHEMA_BAD_TYPE, "as_of must be a non-empty string"))
    if not isinstance(proof["premises"], list):
        errors.append(_error(None, SCHEMA_BAD_TYPE, "premises must be a list"))
    if not isinstance(proof["steps"], list):
        errors.append(_error(None, SCHEMA_BAD_TYPE, "steps must be a list"))
    if not isinstance(proof["conclusion"], str) or not proof["conclusion"]:
        errors.append(_error(None, SCHEMA_BAD_TYPE, "conclusion must be a non-empty string"))
    if errors:
        return None
    return proof


def _check_order(steps: list[Any], errors: list[dict[str, Any]]) -> None:
    """Steps must be non-empty with exactly one conclude step last (T3.1)."""
    if not steps:
        errors.append(_error(None, EMPTY_STEPS, "proof has no steps"))
        return
    for index, step in enumerate(steps):
        if not isinstance(step, dict) or not isinstance(step.get("kind"), str):
            errors.append(_error(index, SCHEMA_BAD_TYPE, "each step needs a string kind"))
    concludes = [
        index
        for index, step in enumerate(steps)
        if isinstance(step, dict) and step.get("kind") == "conclude"
    ]
    if len(concludes) != 1 or concludes[0] != len(steps) - 1:
        errors.append(
            _error(None, CONCLUDE_POSITION, "exactly one conclude step is required, last")
        )


def _check_premises(
    proof: dict[str, Any],
    premises: dict[str, dict[str, Any]],
    errors: list[dict[str, Any]],
) -> None:
    """Premises must exist, be admitted, and match the store (T3.1, F9)."""
    for entry in proof["premises"]:
        if not isinstance(entry, dict):
            errors.append(_error(None, SCHEMA_BAD_TYPE, "each premise must be an object"))
            continue
        fact_id = entry.get("fact_id")
        if not isinstance(fact_id, str) or not fact_id:
            errors.append(_error(None, SCHEMA_BAD_TYPE, "each premise needs a fact_id"))
            continue
        stored = premises.get(fact_id)
        if stored is None:
            errors.append(_error(None, PREMISE_UNKNOWN, f"unknown premise {fact_id!r}"))
            continue
        if stored.get("trust_class") not in ADMITTED_TRUST:
            errors.append(
                _error(
                    None,
                    PREMISE_UNTRUSTED,
                    f"premise {fact_id!r} has unadmitted trust class "
                    f"{stored.get('trust_class')!r}",
                )
            )
        if entry.get("statement") != stored.get("statement"):
            errors.append(
                _error(None, PREMISE_MISMATCH, f"premise {fact_id!r} statement differs from store")
            )
        if entry.get("trust_class") != stored.get("trust_class"):
            errors.append(
                _error(
                    None, PREMISE_MISMATCH, f"premise {fact_id!r} trust class differs from store"
                )
            )


def _check_citation(
    step_index: int,
    citation: Any,
    provisions: dict[str, dict[str, Any]],
    errors: list[dict[str, Any]],
) -> str | None:
    """Validate one citation tuple; return its version id or None (T3.1)."""
    if not isinstance(citation, dict):
        errors.append(_error(step_index, CITATION_MALFORMED, "citation must be an object"))
        return None
    source_version_id = citation.get("source_version_id")
    provision_id = citation.get("provision_id")
    span = citation.get("span")
    sha256 = citation.get("sha256")
    if (
        not isinstance(source_version_id, str)
        or not isinstance(provision_id, str)
        or not isinstance(span, list)
        or len(span) != 2
        or not all(isinstance(bound, int) and not isinstance(bound, bool) for bound in span)
        or not isinstance(sha256, str)
    ):
        errors.append(
            _error(
                step_index,
                CITATION_MALFORMED,
                "citation needs (source_version_id, provision_id, span, sha256)",
            )
        )
        return None
    provision = provisions.get(provision_id)
    if provision is None:
        errors.append(
            _error(step_index, CITATION_UNKNOWN_PROVISION, f"unknown provision {provision_id!r}")
        )
        return str(source_version_id)
    text = provision.get("text", "")
    start, end = span[0], span[1]
    if not 0 <= start < end <= len(text):
        errors.append(
            _error(
                step_index,
                CITATION_SPAN_RANGE,
                f"span [{start}:{end}] outside snapshot of length {len(text)}",
            )
        )
    if sha256 != provision.get("text_sha256"):
        errors.append(
            _error(step_index, CITATION_HASH_MISMATCH, "citation sha256 differs from snapshot")
        )
    if source_version_id != provision.get("source_version_id"):
        errors.append(
            _error(
                step_index,
                CITATION_VERSION_MISMATCH,
                "cited version does not own the cited provision",
            )
        )
    return str(source_version_id)


def _is_number(value: Any) -> bool:
    """Plain ints and floats, never bools (T3.2)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_current(version_id: str, versions: dict[str, dict[str, Any]]) -> bool | None:
    """Whether a version is current; None when unknown (T3.2)."""
    if version_id not in versions:
        return None
    return not any(
        row.get("supersedes_id") == version_id for row in versions.values()
    )


def _in_force_on(
    effective_from: str, effective_until: Any, as_of: str
) -> bool:
    """Plain-date applicability, mirroring services/diff.py (T3.2, F11)."""
    day = as_of[:10]
    if day < effective_from:
        return False
    if isinstance(effective_until, str) and day >= effective_until:
        return False
    return True


def _check_kinds(steps: list[Any], errors: list[dict[str, Any]]) -> None:
    """Steps must use the closed seven-kind set (T3.2)."""
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        if step.get("kind") not in STEP_KINDS:
            errors.append(
                _error(index, STEP_UNKNOWN_KIND, f"unknown step kind {step.get('kind')!r}")
            )


def _check_conclude_content(
    proof: dict[str, Any], errors: list[dict[str, Any]]
) -> None:
    """Conclude steps must repeat the proof conclusion (T3.2)."""
    for index, step in enumerate(proof["steps"]):
        if not isinstance(step, dict) or step.get("kind") != "conclude":
            continue
        conclusion = step.get("conclusion")
        if not isinstance(conclusion, str) or not conclusion:
            errors.append(_error(index, SCHEMA_BAD_TYPE, "conclude needs a conclusion"))
        elif conclusion != proof["conclusion"]:
            errors.append(
                _error(index, CONCLUDE_MISMATCH, "conclude differs from proof conclusion")
            )


def _check_fact_linkage(
    proof: dict[str, Any], errors: list[dict[str, Any]]
) -> None:
    """Cited facts must be proof premises (T3.2)."""
    premise_ids = {
        entry.get("fact_id") for entry in proof["premises"] if isinstance(entry, dict)
    }
    for index, step in enumerate(proof["steps"]):
        if not isinstance(step, dict) or step.get("kind") != "cite_fact":
            continue
        if step.get("fact_id") not in premise_ids:
            errors.append(
                _error(index, STEP_UNKNOWN_FACT, f"unknown fact {step.get('fact_id')!r}")
            )


def _check_rule(
    index: int,
    step: dict[str, Any],
    rule_cards: dict[str, dict[str, Any]],
    versions: dict[str, dict[str, Any]],
    errors: list[dict[str, Any]],
) -> None:
    """Rule citations bind card, provision and a current version (T3.2)."""
    card_id = step.get("rule_card_id")
    card = rule_cards.get(card_id) if isinstance(card_id, str) else None
    if card is None:
        errors.append(_error(index, STEP_UNKNOWN_RULE, f"unknown rule card {card_id!r}"))
        return
    citation = step.get("citation")
    if not isinstance(citation, dict):
        errors.append(_error(index, SCHEMA_BAD_TYPE, "cite_rule needs a citation"))
        return
    provision_id = citation.get("provision_id")
    source_version_id = citation.get("source_version_id")
    if not isinstance(provision_id, str) or not isinstance(source_version_id, str):
        return
    if provision_id != card.get("provision_id"):
        errors.append(
            _error(
                index,
                RULE_PROVISION_MISMATCH,
                "citation names a different provision than the card",
            )
        )
    current = _is_current(source_version_id, versions)
    if current is None:
        errors.append(
            _error(index, VERSION_UNKNOWN, f"unknown version {source_version_id!r}")
        )
    elif not current:
        errors.append(
            _error(index, VERSION_SUPERSEDED, f"version {source_version_id!r} is superseded")
        )


def _check_in_force(
    index: int,
    step: dict[str, Any],
    provisions: dict[str, dict[str, Any]],
    as_of: str,
    errors: list[dict[str, Any]],
) -> None:
    """The named provision must apply on as_of (T3.2)."""
    provision_id = step.get("provision_id")
    if not isinstance(provision_id, str):
        errors.append(_error(index, SCHEMA_BAD_TYPE, "in_force needs a provision_id"))
        return
    provision = provisions.get(provision_id)
    if provision is None:
        errors.append(
            _error(index, PROVISION_UNKNOWN, f"unknown provision {provision_id!r}")
        )
        return
    if not as_of:
        errors.append(_error(index, SCHEMA_BAD_TYPE, "in_force needs as_of"))
        return
    if not _in_force_on(
        str(provision.get("effective_from", "")),
        provision.get("effective_until"),
        as_of,
    ):
        errors.append(
            _error(
                index,
                PROVISION_NOT_IN_FORCE,
                f"provision {provision_id!r} not in force on {as_of}",
            )
        )


def _check_compare(index: int, step: dict[str, Any], errors: list[dict[str, Any]]) -> None:
    """Numeric comparisons are recomputed, not trusted (T3.2)."""
    value = step.get("value")
    op = step.get("op")
    bound = step.get("bound")
    if (
        not _is_number(value)
        or not _is_number(bound)
        or op not in ("<=", ">=", "==", "<", ">")
    ):
        errors.append(
            _error(index, COMPARE_MALFORMED, "compare needs numeric value, op, bound")
        )
        return
    left = float(cast(Any, value))
    right = float(cast(Any, bound))
    holds = {
        "<=": left <= right,
        ">=": left >= right,
        "==": left == right,
        "<": left < right,
        ">": left > right,
    }[str(op)]
    if not holds:
        errors.append(
            _error(index, COMPARE_FAILED, f"comparison {value!r} {op} {bound!r} is false")
        )


def _check_evidence(
    index: int,
    step: dict[str, Any],
    clauses: dict[str, str],
    errors: list[dict[str, Any]],
) -> None:
    """Evidence quotes must be verbatim substrings of the clause (T3.2)."""
    if step.get("kind") == "role_applies":
        for field in ("party", "role"):
            if not isinstance(step.get(field), str) or not step.get(field):
                errors.append(_error(index, SCHEMA_BAD_TYPE, f"role_applies needs {field}"))
                return
    clause_id = step.get("clause_id")
    quote = step.get("quote")
    if not isinstance(clause_id, str) or clause_id not in clauses:
        errors.append(
            _error(index, EVIDENCE_UNKNOWN_CLAUSE, f"unknown clause {clause_id!r}")
        )
        return
    if not isinstance(quote, str) or not quote:
        errors.append(_error(index, SCHEMA_BAD_TYPE, "evidence needs a quote"))
        return
    if quote not in clauses[clause_id]:
        errors.append(_error(index, QUOTE_NOT_FOUND, "quote is not in the clause text"))


def verify(
    proof: dict[str, Any],
    premises: dict[str, dict[str, Any]],
    provisions: dict[str, dict[str, Any]],
    rule_cards: dict[str, dict[str, Any]],
    versions: dict[str, dict[str, Any]],
    clauses: dict[str, str],
    as_of: str = "",
) -> dict[str, Any]:
    """Deterministically verify a proposed proof (T3.1 core, T3.2 steps, F9).

    Returns the `verify_derivation` shape:
    `{valid, errors:[{step, code, message}], cited_source_versions}`.
    """
    errors: list[dict[str, Any]] = []
    typed = _check_schema(proof, errors)
    if typed is not None:
        _check_order(typed["steps"], errors)
        _check_kinds(typed["steps"], errors)
        _check_premises(typed, premises, errors)
        _check_conclude_content(typed, errors)
        _check_fact_linkage(typed, errors)
        cited: list[str] = []
        for index, step in enumerate(typed["steps"]):
            if not isinstance(step, dict):
                continue
            if "citation" in step:
                version_id = _check_citation(index, step["citation"], provisions, errors)
                if version_id is not None and version_id not in cited:
                    cited.append(version_id)
            kind = step.get("kind")
            if kind == "cite_rule":
                _check_rule(index, step, rule_cards, versions, errors)
            elif kind == "in_force":
                _check_in_force(index, step, provisions, as_of, errors)
            elif kind == "compare":
                _check_compare(index, step, errors)
            elif kind in ("contains_element", "role_applies"):
                _check_evidence(index, step, clauses, errors)
    else:
        cited = []
    return {
        "valid": not errors,
        "errors": errors,
        "cited_source_versions": sorted(cited),
    }
