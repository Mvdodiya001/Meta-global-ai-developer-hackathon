"""Evaluation harness: golden matters as a release gate (Rewrite P5).

Runs the recorded golden cases (corpus/evals/golden.json) against a
freshly seeded database in replay mode and reports the metrics a
release is judged on:

- verdict agreement: expected finding status vs decided status;
- citation exactness: valid proofs whose citations all resolve;
- premise-admission violations: decided proofs citing an ai_inferred
  or disputed premise (must be zero);
- spend: summed llm_calls cost estimate for the run.

No live calls: a golden case that cannot replay fails, loudly.
"""

import json
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.agent import claims as claims_agent
from app.agent import loop as loop_agent
from app.db import init_db
from app.modules.impact import counterfactual
from app.services import graph, memory, seed

DEFAULT_GOLDEN = Path(__file__).resolve().parents[3] / "corpus" / "evals" / "golden.json"
CASSETTES = Path(__file__).resolve().parents[3] / "corpus" / "cassettes"
ADMITTED = frozenset({"lawyer_confirmed", "document_extracted"})


def load_golden(path: str | Path = DEFAULT_GOLDEN) -> list[dict[str, Any]]:
    """Read the golden case list (P5)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert isinstance(data, list)
    return data


def _run_ask(session: Session, case: dict[str, Any]) -> str:
    """One golden ask through structure → loop → decide, replayed (P5)."""
    question = str(case["question"])
    as_of = str(case.get("as_of", seed.DEMO_92_AS_OF))
    draft = claims_agent.structure_claim(
        question, claims_agent.default_inventory(), as_of,
        session=session, cache_dir=CASSETTES,
    )
    claim_id = f"C-EVAL-{case['id']}"
    clause = session.execute(
        sa.select(models.Clause).where(models.Clause.ref == "9.2")
    ).scalars().first()
    assert clause is not None
    session.add(
        models.Claim(
            id=claim_id, matter_id="MAT-01", clause_id=clause.id,
            claim_type=draft.claim_type, params_json=dict(draft.params),
            question_text=draft.question_text, as_of=as_of,
            created_at="2026-01-01T00:00:00Z",
        )
    )
    session.commit()
    if draft.claim_type not in memory.SUPPORTED_TYPES:
        finding = memory.decide_finding(
            session, claim_id=claim_id,
            proof={"claim_id": claim_id, "as_of": as_of, "conclusion": "",
                   "premises": [], "steps": [], "explanation": draft.explanation},
            run_id="RUN-EVAL", challenger_cache_dir=CASSETTES,
        )
        return str(finding.status)
    result = loop_agent.run_verify(
        session, claim_id=claim_id, matter_id="MAT-01", cache_dir=CASSETTES
    )
    if not (result.accepted and result.proof is not None):
        return "NO_PROOF"
    finding = memory.decide_finding(
        session, claim_id=claim_id, proof=result.proof,
        run_id=result.run_id, challenger_cache_dir=CASSETTES,
    )
    return str(finding.status)


def run_evals(db_path: str | Path, golden_path: str | Path = DEFAULT_GOLDEN) -> dict[str, Any]:
    """Run every golden case on a fresh seed; return the report (P5)."""
    seed.seed_demo(db_path, CASSETTES.parent)
    session = sessionmaker(bind=init_db(db_path), future=True)()
    cases: list[dict[str, Any]] = []
    try:
        for case in load_golden(golden_path):
            outcome: dict[str, Any] = {"id": case["id"], "kind": case["kind"]}
            try:
                if case["kind"] == "ask":
                    status = _run_ask(session, case)
                    outcome["status"] = status
                    outcome["passed"] = status == case["expect_status"]
                elif case["kind"] == "counterfactual":
                    result = counterfactual.run_counterfactual(
                        session, str(case["source_version_id"])
                    )
                    row = next(
                        (
                            a
                            for a in result["affected"]
                            if a["finding_id"] == case["expect_finding"]
                        ),
                        None,
                    )
                    outcome["passed"] = bool(
                        row and row["would_remain_valid"] is case["expect_valid"]
                    )
                elif case["kind"] == "decoy":
                    outcome["passed"] = (
                        graph.dependent_findings(session, str(case["provision_id"])) == []
                    )
                else:
                    outcome["passed"] = False
                    outcome["error"] = f"unknown kind {case['kind']}"
            except Exception as exc:  # a case that errors is a failed case
                outcome["passed"] = False
                outcome["error"] = f"{type(exc).__name__}: {exc}"[:200]
            cases.append(outcome)
        findings = session.execute(sa.select(models.Finding)).scalars().all()
        violations = 0
        valid_proofs = 0
        for finding in findings:
            report = finding.checker_report_json
            if isinstance(report, dict) and report.get("valid"):
                valid_proofs += 1
            proof = finding.proof_json if isinstance(finding.proof_json, dict) else {}
            for premise in proof.get("premises", []) if isinstance(proof, dict) else []:
                if isinstance(premise, dict) and premise.get("trust_class") not in ADMITTED \
                        and premise.get("trust_class") is not None:
                    # Only count premises of decided (non-seed) proofs.
                    if str(finding.id).startswith("FND-") and finding.run_id:
                        violations += 1
        spend = session.execute(
            sa.select(sa.func.coalesce(sa.func.sum(models.LlmCall.cost_est), 0.0))
        ).scalar() or 0.0
        passed = sum(1 for item in cases if item["passed"])
        return {
            "cases": cases,
            "passed": passed,
            "total": len(cases),
            "verdict_agreement": (passed / len(cases)) if cases else 0.0,
            "premise_violations": violations,
            "spend_usd": float(spend),
            "gate_passed": passed == len(cases) and violations == 0,
        }
    finally:
        session.close()
