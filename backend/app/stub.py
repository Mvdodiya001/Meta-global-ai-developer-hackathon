"""T0.7: stub-mode router serving the checked-in example payloads (`API_STUB=1`).

Every handler returns its `openapi/examples/*.json` file verbatim, validated
against the contract response model. Path and query values are accepted but
ignored: the stub always serves the fixture. Real implementations replace
these handlers from T4.5 on; the route paths stay identical.
"""

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app import schemas

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "openapi" / "examples"


def example(name: str) -> Any:
    """Load one example payload by stem (T0.7)."""
    return json.loads((EXAMPLES_DIR / f"{name}.json").read_text())


def demo_forbidden() -> JSONResponse:
    """Error envelope for demo routes when `DEMO_MODE != 1` (DATA_MODEL_API §7)."""
    error = {"code": "DEMO_DISABLED", "message": "demo routes need DEMO_MODE=1", "details": {}}
    return JSONResponse(status_code=403, content={"error": error})


router = APIRouter()


@router.get("/api/matters", response_model=schemas.MatterList)
def list_matters() -> Any:
    """Matter list stub (Phase 0)."""
    return example("matters")


@router.post("/api/matters", response_model=schemas.MatterSummary)
def create_matter(payload: dict[str, Any] | None = None) -> Any:
    """Create-matter stub (Phase 0)."""
    return example("matter_created")


@router.get("/api/matters/{id}", response_model=schemas.Matter)
def get_matter(id: str) -> Any:
    """Matter plus context panel (F18)."""
    return example("matter")


@router.get("/api/matters/{id}/documents", response_model=schemas.DocumentList)
def list_documents(id: str) -> Any:
    """Document list for a matter (F3)."""
    return example("documents")


@router.get("/api/documents/{id}/clauses", response_model=schemas.ClauseList)
def list_clauses(id: str) -> Any:
    """Stub: clause list example (T0.7)."""
    return example("clauses")


@router.post("/api/documents/{id}/explain", response_model=schemas.ExplainResult)
def explain_document(id: str, payload: dict[str, Any] | None = None) -> Any:
    """Explanation-generation stub (Phase 4)."""
    return example("explain_result")


@router.post("/api/documents/{id}/summarize", response_model=schemas.SummaryResult)
def summarize_document(id: str, payload: dict[str, Any] | None = None) -> Any:
    """Document-summary stub (Phase 4)."""
    return example("summary_result")


@router.post("/api/documents/{id}/extract", response_model=schemas.ExtractResult)
def extract_document(id: str, payload: dict[str, Any] | None = None) -> Any:
    """Extraction result stub: clauses plus candidate facts (F3)."""
    return example("extract_result")


@router.get("/api/matters/{id}/facts", response_model=schemas.FactList)
def list_facts(id: str) -> Any:
    """Stub: facts with trust classes example (T0.7)."""
    return example("facts")


@router.post("/api/facts/{id}/approve", response_model=schemas.FactAction)
def approve_fact(id: str, payload: dict[str, Any] | None = None) -> Any:
    """Lawyer approve stub (F15)."""
    return example("fact_action")


@router.post("/api/facts/{id}/challenge", response_model=schemas.FactAction)
def challenge_fact(id: str, payload: dict[str, Any] | None = None) -> Any:
    """Lawyer challenge stub (F15)."""
    return example("fact_action")


@router.post("/api/facts/{id}/reject", response_model=schemas.FactAction)
def reject_fact(id: str, payload: dict[str, Any] | None = None) -> Any:
    """Lawyer reject stub (F15)."""
    return example("fact_action")


@router.post("/api/claims", response_model=schemas.ClaimCreated)
def create_claim(payload: dict[str, Any] | None = None) -> Any:
    """Structure-claim stub (F4, F5)."""
    return example("claim_created")


@router.get("/api/runs/{id}", response_model=schemas.Run)
def get_run(id: str) -> Any:
    """Run status stub (F5)."""
    return example("run")


@router.get("/api/runs/{id}/events", response_model=schemas.RunEvents)
def get_run_events(id: str) -> Any:
    """Tool-call trace stub; SSE streaming lands after v0 (F5)."""
    return example("run_events")


@router.get("/api/claims/{id}/current", response_model=schemas.Finding)
def get_current_finding(id: str) -> Any:
    """Stub: finding with proof example (T0.7)."""
    return example("finding_current")


@router.get("/api/claims/{id}/history", response_model=schemas.FindingHistory)
def get_finding_history(id: str) -> Any:
    """All finding versions stub (F12)."""
    return example("finding_history")


@router.get("/api/findings/{id}", response_model=schemas.Finding)
def get_finding(id: str) -> Any:
    """Proof, traces and reports stub (F9)."""
    return example("finding")


@router.post("/api/findings/{id}/review", response_model=schemas.ReviewResult)
def review_finding(id: str, payload: dict[str, Any] | None = None) -> Any:
    """Lawyer review stub (F16)."""
    return example("review_result")


@router.get("/api/sources", response_model=schemas.SourceList)
def list_sources() -> Any:
    """Source registry stub (F1)."""
    return example("sources")


@router.get("/api/sources/{id}/versions", response_model=schemas.SourceVersionList)
def list_source_versions(id: str) -> Any:
    """Version registry stub (F1)."""
    return example("source_versions")


@router.get("/api/source-versions/{id}/provisions", response_model=schemas.ProvisionList)
def list_provisions(id: str) -> Any:
    """Provision list stub (Phase 2a)."""
    return example("provisions")


@router.get("/api/matters/{id}/audit-export", response_model=schemas.AuditExport)
def audit_export(id: str) -> Any:
    """Audit export stub (Phase 6)."""
    return example("audit_export")


@router.get("/api/matters/{id}/compare", response_model=schemas.CompareReport)
def compare_documents(id: str, a: str = "", b: str = "") -> Any:
    """Document comparison stub (Phase 5)."""
    return example("compare_report")


@router.post("/api/matters/{id}/compare/flag", response_model=schemas.FlagResult)
def flag_clause_pair(id: str, payload: dict[str, Any] | None = None) -> Any:
    """Compare-flag stub (Phase 5)."""
    return example("flag_result")


@router.get("/api/documents/{id}/coverage", response_model=schemas.CoverageReport)
def document_coverage(id: str) -> Any:
    """Coverage roll-up stub (Phase 5)."""
    return example("coverage_report")


@router.get("/api/provisions/search", response_model=schemas.ProvisionSearchResult)
def search_provisions(q: str = "") -> Any:
    """Provision retrieval stub (Phase 3)."""
    return example("provision_search")


@router.get("/api/rule-cards/drafts", response_model=schemas.RuleCardDraftList)
def list_card_drafts() -> Any:
    """Card draft queue stub (Phase 2a)."""
    return example("rule_card_drafts")


@router.post("/api/rule-cards/draft", response_model=schemas.RuleCardSummary)
def draft_card(payload: dict[str, Any] | None = None) -> Any:
    """Draft-a-card stub (Phase 2a)."""
    return example("rule_card")


@router.post("/api/rule-cards/{id}/confirm", response_model=schemas.RuleCardSummary)
def confirm_card(id: str, payload: dict[str, Any] | None = None) -> Any:
    """Confirm-a-card stub (Phase 2a)."""
    return example("rule_card")


@router.post("/api/rule-cards/{id}/reject", response_model=schemas.RuleCardSummary)
def reject_card(id: str, payload: dict[str, Any] | None = None) -> Any:
    """Reject-a-card stub (Phase 2a)."""
    return example("rule_card")


@router.get("/api/source-versions/{id}/diff", response_model=schemas.DiffResult)
def diff_versions(id: str, against: str) -> Any:
    """Side-by-side diff stub (F11)."""
    return example("diff")


@router.post("/api/sources/{id}/ingest", response_model=schemas.IngestResult)
def ingest_source(id: str, payload: dict[str, Any] | None = None) -> Any:
    """Ingest stub: new version plus impact report handle (F11)."""
    return example("ingest_result")


@router.get("/api/impact/{id}", response_model=schemas.ImpactReport)
def get_impact(id: str) -> Any:
    """Stub: impact report example (T0.7)."""
    return example("impact")


@router.post("/api/impact/{id}/reverify", response_model=schemas.ReverifyResult)
def reverify_impact(id: str, payload: dict[str, Any] | None = None) -> Any:
    """Re-run stub for stale findings (F12)."""
    return example("reverify_result")


@router.get("/api/graph", response_model=schemas.GraphSlice)
def get_graph(matter_id: str | None = None, focus: str | None = None) -> Any:
    """Stub: graph slice example (T0.7)."""
    return example("graph")


@router.get("/api/audit", response_model=schemas.AuditTrail)
def get_audit(matter_id: str | None = None) -> Any:
    """Stub: audit rows example (T0.7)."""
    return example("audit")


@router.post("/api/proofs/verify", response_model=schemas.ProofVerifyResult)
def verify_proof(payload: dict[str, Any] | None = None) -> Any:
    """Tamper-demo checker stub (G8)."""
    return example("proofs_verify")


@router.post("/api/counterfactual", response_model=schemas.CounterfactualResult)
def counterfactual(payload: dict[str, Any] | None = None) -> Any:
    """What-if stub; the traversal itself is stretch (F19)."""
    return example("counterfactual")


@router.post("/api/demo/reset")
def demo_reset(payload: dict[str, Any] | None = None) -> JSONResponse:
    """Seed reset; only if `DEMO_MODE=1` (DATA_MODEL_API §7)."""
    if os.getenv("DEMO_MODE", "0") != "1":
        return demo_forbidden()
    return JSONResponse(status_code=200, content=example("demo_reset"))


@router.post("/api/demo/scenario/{name}")
def demo_scenario(name: str, payload: dict[str, Any] | None = None) -> JSONResponse:
    """Scenario seed; only if `DEMO_MODE=1` (DATA_MODEL_API §7)."""
    if os.getenv("DEMO_MODE", "0") != "1":
        return demo_forbidden()
    return JSONResponse(status_code=200, content=example("demo_scenario"))


@router.get("/api/models", response_model=schemas.ModelsResult)
def list_models() -> Any:
    """Available models stub (v15)."""
    return example("models")


@router.get("/api/v1/models", response_model=schemas.ModelsResult, include_in_schema=False)
def list_models_v1() -> Any:
    """Version-prefixed alias stub (v15)."""
    return example("models")
