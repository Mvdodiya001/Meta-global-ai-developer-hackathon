"""T3.1 tests (written first): schema/order, admission, span substring + hash."""

import hashlib
from pathlib import Path
from typing import Any

from checker import verify as checker

CORPUS_TEXT = (
    Path(__file__).resolve().parents[2] / "corpus" / "raw" / "DPDP-Act-2023_s8-6.txt"
).read_text(encoding="utf-8")


def provisions() -> dict[str, dict[str, Any]]:
    """One real provision snapshot keyed by id (T3.1)."""
    return {
        "PRV-SEC-6": {
            "source_version_id": "SV-01",
            "key": "Section 6",
            "text": CORPUS_TEXT,
            "text_sha256": hashlib.sha256(CORPUS_TEXT.encode("utf-8")).hexdigest(),
        }
    }


def premises() -> dict[str, dict[str, Any]]:
    """One admitted premise (T3.1)."""
    return {
        "F-001": {"statement": "Clause 9.2 permits transfer.", "trust_class": "document_extracted"}
    }


RULE_CARDS: dict[str, dict[str, Any]] = {
    "RC-01": {"provision_id": "PRV-SEC-6", "claim_type": "CT3"}
}
VERSIONS: dict[str, dict[str, Any]] = {"SV-01": {"supersedes_id": None}}
CLAUSES: dict[str, str] = {}


def proof(**overrides: Any) -> dict[str, Any]:
    """A minimal valid proof; overrides replace top-level fields (T3.1)."""
    base: dict[str, Any] = {
        "claim_id": "C-001",
        "as_of": "2025-10-01",
        "premises": [
            {
                "fact_id": "F-001",
                "statement": "Clause 9.2 permits transfer.",
                "trust_class": "document_extracted",
            }
        ],
        "steps": [
            {"kind": "cite_fact", "fact_id": "F-001"},
            {
                "kind": "cite_rule",
                "rule_card_id": "RC-01",
                "citation": {
                    "source_version_id": "SV-01",
                    "provision_id": "PRV-SEC-6",
                    "span": [0, len(CORPUS_TEXT)],
                    "sha256": hashlib.sha256(CORPUS_TEXT.encode("utf-8")).hexdigest(),
                },
            },
            {"kind": "conclude", "conclusion": "holds"},
        ],
        "conclusion": "holds",
    }
    base.update(overrides)
    return base


def codes(report: dict[str, Any]) -> list[str]:
    """Error codes of a report (T3.1)."""
    return [error["code"] for error in report["errors"]]


def test_valid_proof_passes() -> None:
    """T3.1: a well-formed proof over admitted premises verifies."""
    report = checker.verify(proof(), premises(), provisions(), RULE_CARDS, VERSIONS, CLAUSES)
    assert report["valid"] is True
    assert report["errors"] == []
    assert report["cited_source_versions"] == ["SV-01"]


def test_missing_claim_id_rejected() -> None:
    """T3.1: schema requires a claim id."""
    bad = proof()
    del bad["claim_id"]
    report = checker.verify(bad, premises(), provisions(), RULE_CARDS, VERSIONS, CLAUSES)
    assert report["valid"] is False
    assert checker.SCHEMA_MISSING_FIELD in codes(report)


def test_empty_steps_rejected() -> None:
    """T3.1: a proof with no steps is rejected."""
    report = checker.verify(
        proof(steps=[]), premises(), provisions(), RULE_CARDS, VERSIONS, CLAUSES
    )
    assert report["valid"] is False
    assert checker.EMPTY_STEPS in codes(report)


def test_conclude_must_be_last() -> None:
    """T3.1: order requires exactly one conclude step at the end."""
    steps = proof()["steps"]
    rotated = steps[2:] + steps[:2]
    report = checker.verify(
        proof(steps=rotated), premises(), provisions(), RULE_CARDS, VERSIONS, CLAUSES
    )
    assert report["valid"] is False
    assert checker.CONCLUDE_POSITION in codes(report)


def test_missing_conclude_rejected() -> None:
    """T3.1: a proof with no conclude step is rejected."""
    steps = [step for step in proof()["steps"] if step["kind"] != "conclude"]
    report = checker.verify(
        proof(steps=steps), premises(), provisions(), RULE_CARDS, VERSIONS, CLAUSES
    )
    assert report["valid"] is False
    assert checker.CONCLUDE_POSITION in codes(report)


def test_ai_inferred_premise_rejected() -> None:
    """T3.1: admission rejects ai_inferred premises."""
    store = {
        "F-001": {"statement": "Clause 9.2 permits transfer.", "trust_class": "ai_inferred"}
    }
    claimed = proof()
    claimed["premises"][0]["trust_class"] = "ai_inferred"
    report = checker.verify(claimed, store, provisions(), RULE_CARDS, VERSIONS, CLAUSES)
    assert report["valid"] is False
    assert checker.PREMISE_UNTRUSTED in codes(report)


def test_disputed_premise_rejected() -> None:
    """T3.1: admission rejects disputed premises."""
    store = {
        "F-001": {"statement": "Clause 9.2 permits transfer.", "trust_class": "disputed"}
    }
    claimed = proof()
    claimed["premises"][0]["trust_class"] = "disputed"
    report = checker.verify(claimed, store, provisions(), RULE_CARDS, VERSIONS, CLAUSES)
    assert report["valid"] is False
    assert checker.PREMISE_UNTRUSTED in codes(report)


def test_unknown_premise_rejected() -> None:
    """T3.1: premises must exist in the store."""
    report = checker.verify(proof(), {}, provisions(), RULE_CARDS, VERSIONS, CLAUSES)
    assert report["valid"] is False
    assert checker.PREMISE_UNKNOWN in codes(report)


def test_premise_mismatch_rejected() -> None:
    """T3.1: proof premises must match the stored statement and class."""
    claimed = proof()
    claimed["premises"][0]["statement"] = "Clause 9.2 forbids transfer."
    report = checker.verify(claimed, premises(), provisions(), RULE_CARDS, VERSIONS, CLAUSES)
    assert report["valid"] is False
    assert checker.PREMISE_MISMATCH in codes(report)


def test_unknown_provision_rejected() -> None:
    """T3.1: citations must name a stored provision."""
    bad = proof()
    bad["steps"][1]["citation"]["provision_id"] = "PRV-NOPE"
    report = checker.verify(bad, premises(), provisions(), RULE_CARDS, VERSIONS, CLAUSES)
    assert report["valid"] is False
    assert checker.CITATION_UNKNOWN_PROVISION in codes(report)


def test_span_out_of_range_rejected() -> None:
    """T3.1: span substring must lie inside the stored snapshot."""
    bad = proof()
    bad["steps"][1]["citation"]["span"] = [0, len(CORPUS_TEXT) + 50]
    report = checker.verify(bad, premises(), provisions(), RULE_CARDS, VERSIONS, CLAUSES)
    assert report["valid"] is False
    assert checker.CITATION_SPAN_RANGE in codes(report)


def test_hash_mismatch_rejected() -> None:
    """T3.1: citation sha256 must equal the snapshot hash."""
    bad = proof()
    bad["steps"][1]["citation"]["sha256"] = "0" * 64
    report = checker.verify(bad, premises(), provisions(), RULE_CARDS, VERSIONS, CLAUSES)
    assert report["valid"] is False
    assert checker.CITATION_HASH_MISMATCH in codes(report)


def test_version_mismatch_rejected() -> None:
    """T3.1: the cited version must own the cited provision."""
    bad = proof()
    bad["steps"][1]["citation"]["source_version_id"] = "SV-02"
    report = checker.verify(bad, premises(), provisions(), RULE_CARDS, VERSIONS, CLAUSES)
    assert report["valid"] is False
    assert checker.CITATION_VERSION_MISMATCH in codes(report)


def test_malformed_citation_rejected() -> None:
    """T3.1: citations need the full tuple shape."""
    bad = proof()
    bad["steps"][1]["citation"] = {"provision_id": "PRV-SEC-6"}
    report = checker.verify(bad, premises(), provisions(), RULE_CARDS, VERSIONS, CLAUSES)
    assert report["valid"] is False
    assert checker.CITATION_MALFORMED in codes(report)


def test_collects_multiple_errors() -> None:
    """T3.1: one bad proof can fail admission and citation checks together."""
    bad = proof(steps=[])
    report = checker.verify(bad, {}, provisions(), RULE_CARDS, VERSIONS, CLAUSES)
    assert report["valid"] is False
    assert len(report["errors"]) >= 2
