"""T3.2 tests (written first): all seven step kinds plus the CLI.

Fixtures reuse the real s8(6) snapshot; the clause text is a short fictional
extract in the demo's wording.
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from checker import verify as checker

BACKEND_DIR = Path(__file__).resolve().parents[1]
CORPUS_TEXT = (
    BACKEND_DIR.parent / "corpus" / "raw" / "DPDP-Act-2023_s8-6.txt"
).read_text(encoding="utf-8")
TEXT_SHA = hashlib.sha256(CORPUS_TEXT.encode("utf-8")).hexdigest()

CLAUSE_TEXT = (
    "Nimbus may transfer order data to its analytics cluster outside India "
    "for fraud screening."
)


def provisions() -> dict[str, dict[str, Any]]:
    """One real provision snapshot (T3.2)."""
    return {
        "PRV-SEC-6": {
            "source_version_id": "SV-01",
            "key": "Section 6",
            "text": CORPUS_TEXT,
            "text_sha256": TEXT_SHA,
            "effective_from": "2026-01-01",
            "effective_until": None,
        }
    }


def premises() -> dict[str, dict[str, Any]]:
    """One admitted premise (T3.2)."""
    return {
        "F-001": {
            "statement": "Clause 10 gives 72-hour details.",
            "trust_class": "document_extracted",
        }
    }


def rule_cards() -> dict[str, dict[str, Any]]:
    """One rule card bound to the real provision (T3.2)."""
    return {"RC-01": {"provision_id": "PRV-SEC-6", "claim_type": "CT3"}}


def versions() -> dict[str, dict[str, Any]]:
    """SV-01 current on its own (T3.2)."""
    return {"SV-01": {"supersedes_id": None}}


def versions_with_supersession() -> dict[str, dict[str, Any]]:
    """SV-02SIM supersedes SV-01 (T3.2)."""
    return {"SV-01": {"supersedes_id": None}, "SV-02": {"supersedes_id": "SV-01"}}


def clauses() -> dict[str, str]:
    """One fictional clause body (T3.2)."""
    return {"CL-9.2": CLAUSE_TEXT}


def valid_proof() -> dict[str, Any]:
    """A proof exercising all seven step kinds (T3.2)."""
    return {
        "claim_id": "C-001",
        "as_of": "2027-06-01",
        "premises": [
            {
                "fact_id": "F-001",
                "statement": "Clause 10 gives 72-hour details.",
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
                    "sha256": TEXT_SHA,
                },
            },
            {"kind": "in_force", "provision_id": "PRV-SEC-6"},
            {"kind": "compare", "value": 72, "op": "<=", "bound": 72},
            {
                "kind": "contains_element",
                "clause_id": "CL-9.2",
                "quote": "outside India for fraud screening",
            },
            {
                "kind": "role_applies",
                "party": "Nimbus",
                "role": "Data Processor",
                "clause_id": "CL-9.2",
                "quote": "Nimbus may transfer order data",
            },
            {"kind": "conclude", "conclusion": "holds"},
        ],
        "conclusion": "holds",
    }


def check(proof: dict[str, Any]) -> dict[str, Any]:
    """Run the full-context verifier (T3.2)."""
    return checker.verify(
        proof, premises(), provisions(), rule_cards(), versions(), clauses(), as_of="2027-06-01"
    )


def codes(report: dict[str, Any]) -> list[str]:
    """Error codes of a report (T3.2)."""
    return [error["code"] for error in report["errors"]]


def test_valid_proof_passes() -> None:
    """T3.2: Done when a valid proof passes."""
    report = check(valid_proof())
    assert report["valid"] is True, report["errors"]
    assert report["errors"] == []
    assert report["cited_source_versions"] == ["SV-01"]


def test_tampered_premise_fails() -> None:
    """T3.2: Done when a tampered premise fails with a specific code."""
    bad = valid_proof()
    bad["premises"][0]["statement"] = "Clause 10 gives no details."
    report = check(bad)
    assert report["valid"] is False
    assert checker.PREMISE_MISMATCH in codes(report)


def test_wrong_value_fails() -> None:
    """T3.2: Done when a wrong comparison value fails with a specific code."""
    bad = valid_proof()
    bad["steps"][3] = {"kind": "compare", "value": 96, "op": "<=", "bound": 72}
    report = check(bad)
    assert report["valid"] is False
    assert checker.COMPARE_FAILED in codes(report)


def test_out_of_force_provision_fails() -> None:
    """T3.2: Done when an out-of-force provision fails with a specific code."""
    bad = valid_proof()
    bad["as_of"] = "2025-10-01"
    report = checker.verify(
        bad, premises(), provisions(), rule_cards(), versions(), clauses(), as_of="2025-10-01"
    )
    assert report["valid"] is False
    assert checker.PROVISION_NOT_IN_FORCE in codes(report)


def test_superseded_version_fails() -> None:
    """T3.2: Done when a superseded version fails with a specific code."""
    bad = valid_proof()
    report = checker.verify(
        bad,
        premises(),
        provisions(),
        rule_cards(),
        versions_with_supersession(),
        clauses(),
        as_of="2027-06-01",
    )
    assert report["valid"] is False
    assert checker.VERSION_SUPERSEDED in codes(report)


def test_unknown_step_kind_rejected() -> None:
    """T3.2: the closed set has exactly seven kinds."""
    bad = valid_proof()
    bad["steps"].insert(0, {"kind": "appeal_to_authority"})
    report = check(bad)
    assert report["valid"] is False
    assert checker.STEP_UNKNOWN_KIND in codes(report)


def test_cite_fact_needs_proof_premise() -> None:
    """T3.2: cited facts must be proof premises."""
    bad = valid_proof()
    bad["steps"][0] = {"kind": "cite_fact", "fact_id": "F-999"}
    report = check(bad)
    assert report["valid"] is False
    assert checker.STEP_UNKNOWN_FACT in codes(report)


def test_unknown_rule_card_rejected() -> None:
    """T3.2: cited rule cards must exist."""
    bad = valid_proof()
    bad["steps"][1]["rule_card_id"] = "RC-NOPE"
    report = check(bad)
    assert report["valid"] is False
    assert checker.STEP_UNKNOWN_RULE in codes(report)


def test_rule_provision_binding() -> None:
    """T3.2: the citation must name the card's own provision."""
    bad = valid_proof()
    bad["steps"][1]["rule_card_id"] = "RC-01"
    bad["steps"][1]["citation"]["provision_id"] = "PRV-SEC-6"
    cards = {"RC-01": {"provision_id": "PRV-OTHER", "claim_type": "CT3"}}
    report = checker.verify(
        bad, premises(), provisions(), cards, versions(), clauses(), as_of="2027-06-01"
    )
    assert report["valid"] is False
    assert checker.RULE_PROVISION_MISMATCH in codes(report)


def test_quote_must_match_clause() -> None:
    """T3.2: evidence quotes must be verbatim substrings of the clause."""
    bad = valid_proof()
    bad["steps"][4]["quote"] = "outside India forever and ever"
    report = check(bad)
    assert report["valid"] is False
    assert checker.QUOTE_NOT_FOUND in codes(report)


def test_unknown_clause_rejected() -> None:
    """T3.2: evidence must cite a known clause."""
    bad = valid_proof()
    bad["steps"][4]["clause_id"] = "CL-99"
    report = check(bad)
    assert report["valid"] is False
    assert checker.EVIDENCE_UNKNOWN_CLAUSE in codes(report)


def test_conclude_must_match_proof() -> None:
    """T3.2: the conclude step must repeat the proof conclusion."""
    bad = valid_proof()
    bad["steps"][6] = {"kind": "conclude", "conclusion": "does not hold"}
    report = check(bad)
    assert report["valid"] is False
    assert checker.CONCLUDE_MISMATCH in codes(report)


def test_in_force_unknown_provision() -> None:
    """T3.2: in_force over a missing provision fails."""
    bad = valid_proof()
    bad["steps"][2] = {"kind": "in_force", "provision_id": "PRV-NOPE"}
    report = check(bad)
    assert report["valid"] is False
    assert checker.PROVISION_UNKNOWN in codes(report)


def test_malformed_compare_rejected() -> None:
    """T3.2: compare needs numeric value, known op, numeric bound."""
    for step in (
        {"kind": "compare", "value": "lots", "op": "<=", "bound": 72},
        {"kind": "compare", "value": 72, "op": "≈", "bound": 72},
        {"kind": "compare", "value": 72, "op": "<="},
    ):
        bad = valid_proof()
        bad["steps"][3] = step
        report = check(bad)
        assert report["valid"] is False
        assert checker.COMPARE_MALFORMED in codes(report)


def bundle(proof: dict[str, Any]) -> dict[str, Any]:
    """A self-contained CLI bundle (T3.2)."""
    return {
        "proof": proof,
        "premises": premises(),
        "provisions": provisions(),
        "rule_cards": rule_cards(),
        "versions": versions(),
        "clauses": clauses(),
        "as_of": "2027-06-01",
    }


def test_cli_verify_proof(tmp_path: Path) -> None:
    """T3.2: `python -m checker verify proof.json` prints a valid report."""
    target = tmp_path / "proof.json"
    target.write_text(json.dumps(bundle(valid_proof())), encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, "-m", "checker", "verify", str(target)],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["valid"] is True
    assert report["cited_source_versions"] == ["SV-01"]


def test_cli_rejects_bad_file(tmp_path: Path) -> None:
    """T3.2: the CLI exits nonzero on unusable input."""
    target = tmp_path / "proof.json"
    target.write_text("{oops", encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, "-m", "checker", "verify", str(target)],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 2
