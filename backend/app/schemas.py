"""T0.7: Pydantic response models for every DATA_MODEL_API §7 endpoint (contract v0)."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class Health(BaseModel):
    """Liveness probe (DATA_MODEL_API §7)."""

    status: str


class MatterContext(BaseModel):
    """Static demo panel row (F18)."""

    id: str
    matter_id: str
    kind: str
    title: str
    due_at: str
    source_label: str


class Matter(BaseModel):
    """Matter plus context panel (F18)."""

    id: str
    client_name: str
    title: str
    context: list[MatterContext]


class Document(BaseModel):
    """A contract document (F3)."""

    id: str
    matter_id: str
    title: str
    kind: str


class DocumentList(BaseModel):
    """Clause-list parent response (F3)."""

    documents: list[Document]


class Clause(BaseModel):
    """One extracted clause (F3)."""

    id: str
    document_version_id: str
    ref: str
    heading: str
    text: str
    span_start: int
    span_end: int


class ClauseList(BaseModel):
    """Stub: clause list example (T0.7)."""

    clauses: list[Clause]


class Fact(BaseModel):
    """A premise candidate with trust class (F8)."""

    id: str
    matter_id: str
    clause_id: str | None
    statement: str
    structured: dict[str, Any]
    origin: str
    trust_class: str
    trust_label: str = ""
    created_at: str


class FactList(BaseModel):
    """Stub: facts with trust classes example (T0.7)."""

    facts: list[Fact]


class FactAction(BaseModel):
    """Lawyer trust action result (F15)."""

    fact_id: str
    trust_class: str
    supersedes_id: str | None = None


class ExtractResult(BaseModel):
    """Extraction result: clauses plus candidate facts (F3)."""

    clauses: list[Clause]
    facts: list[Fact]


class ScanRequest(BaseModel):
    """One scanned page as base64 JSON (no multipart dependency) (T7.2)."""

    matter_id: str
    title: str
    image_base64: str
    media_type: str = "image/png"


class ScanResult(BaseModel):
    """A scanned page stored as a new document with clause + fact (T7.2)."""

    document_id: str
    clause: Clause
    fact: Fact


class DictationRequest(BaseModel):
    """One dictated clip as base64 WAV JSON (T7.1)."""

    matter_id: str
    clause_id: str | None = None
    audio_base64: str


class DictationResult(BaseModel):
    """A transcript stored as a proposed (ai_inferred) fact (T7.1)."""

    fact_id: str
    transcript: str
    trust_class: str


class ClaimCreated(BaseModel):
    """Structured claim plus run handle, loop finding when accepted (F4, F5)."""

    claim_id: str
    run_id: str
    finding_id: str | None = None
    status: str | None = None


class ToolCall(BaseModel):
    """One logged tool call (F5)."""

    seq: int
    tool: str
    args: dict[str, Any]
    result: dict[str, Any]
    ok: bool


class Run(BaseModel):
    """Agent run status (F5)."""

    id: str
    trigger: str
    claim_id: str
    status: str


class RunEvents(BaseModel):
    """Stub: live tool-call trace example; SSE lands after v0 (F5)."""

    events: list[ToolCall]


class Citation(BaseModel):
    """A (source_version_id, provision_id, span, sha256) citation."""

    source_version_id: str
    provision_id: str
    span: list[int]
    sha256: str


class ProofPremise(BaseModel):
    """A premise cited by a proof."""

    fact_id: str
    statement: str
    trust_class: str


class ProofStep(BaseModel):
    """One checker step (kinds land fully in T3.2).

    Gate fix: carries every checker step field (compare/evidence/role
    included) and allows future kinds, so a proof read back from the API
    round-trips into /api/proofs/verify without losing its evidence.
    """

    model_config = ConfigDict(extra="allow")

    kind: str
    fact_id: str | None = None
    rule_card_id: str | None = None
    citation: Citation | None = None
    provision_id: str | None = None
    as_of: str | None = None
    conclusion: str | None = None
    clause_id: str | None = None
    quote: str | None = None
    value: float | None = None
    op: str | None = None
    bound: float | None = None
    party: str | None = None
    role: str | None = None


class Proof(BaseModel):
    """A structured proof draft over accepted premises."""

    claim_id: str
    as_of: str
    premises: list[ProofPremise]
    steps: list[ProofStep]
    conclusion: str


class CheckerReport(BaseModel):
    """Deterministic checker verdict (F9)."""

    valid: bool
    errors: list[dict[str, Any]]
    cited_source_versions: list[str]


class FactLine(BaseModel):
    """One fact a finding relies on, in lawyer wording (contract v9)."""

    label: str
    trust_label: str = ""
    confirmed_by: str | None = None


class Finding(BaseModel):
    """A finding with proof, traces and reports (F7, F9)."""

    id: str
    claim_id: str
    version_no: int
    status: str
    status_label: str = ""
    clause_ref: str = ""
    clause_quote: str = ""
    section_label: str = ""
    section_quote: str = ""
    law_version_label: str = ""
    law_version_date: str = ""
    fact_lines: list[FactLine] = []
    confidence_band: str
    proof: Proof
    as_of: str
    source_version_ids: list[str]
    premise_ids: list[str]
    rule_card_ids: list[str]
    checker_report: CheckerReport | None = None
    challenger_report: dict[str, Any] | None = None
    run_id: str
    created_at: str
    supersedes_finding_id: str | None = None
    state: str
    ai_draft_label: str


class ClaimRequest(BaseModel):
    """Structure-claim request body (F4)."""

    clause_id: str
    question: str
    as_of: str


class FactActionBody(BaseModel):
    """Lawyer trust-action request body (F15)."""

    reason: str | None = None
    reviewer: str | None = None
    note: str | None = None


class ReviewBody(BaseModel):
    """Finding review request body (F16)."""

    action: str
    note: str | None = None
    reviewer: str | None = None


class IngestVersionBody(BaseModel):
    """Inline new-version payload for ingest (F11)."""

    version_label: str
    published_on: str
    effective_from: str
    provisions: list[dict[str, Any]]


class IngestBody(BaseModel):
    """Ingest request body (F11)."""

    version: IngestVersionBody | None = None
    fixture: str | None = None
    url: str | None = None


class ReverifyBody(BaseModel):
    """Re-verify request body; proofs keyed by stale finding id (F12)."""

    proofs: dict[str, dict[str, Any]] = {}


class ProofVerifyBody(BaseModel):
    """Tamper-demo checker request body (G8)."""

    claim_id: str
    proof: dict[str, Any]


class FindingHistory(BaseModel):
    """All finding versions for a claim (F12)."""

    versions: list[Finding]


class ReviewResult(BaseModel):
    """Lawyer review outcome (F16)."""

    finding_id: str
    state: str


class Source(BaseModel):
    """A legal source in the registry (F1)."""

    id: str
    key: str
    title: str
    publisher: str
    url: str
    jurisdiction: str


class SourceList(BaseModel):
    """Source registry response (F1)."""

    sources: list[Source]


class SourceVersion(BaseModel):
    """One hashed source snapshot (F1, F11)."""

    id: str
    source_id: str
    version_label: str
    published_on: str
    effective_from: str
    effective_until: str | None = None
    content_sha256: str
    is_simulated: bool
    supersedes_id: str | None = None


class SourceVersionList(BaseModel):
    """Version registry response (F1)."""

    versions: list[SourceVersion]


class Provision(BaseModel):
    """One provision inside a source version (F2)."""

    id: str
    source_version_id: str
    key: str
    text: str
    text_sha256: str
    effective_from: str
    effective_until: str | None = None


class DiffResult(BaseModel):
    """Side-by-side diff data between two versions (F11)."""

    against: str
    current: str
    changed_keys: list[str]
    before: list[Provision]
    after: list[Provision]


class IngestResult(BaseModel):
    """New version plus impact report handle (F11)."""

    source_version_id: str
    impact_report_id: str


class AffectedFinding(BaseModel):
    """One finding flagged by the impact engine (F11)."""

    claim_id: str
    finding_id: str
    state: str
    status_label: str = ""
    clause_ref: str = ""


class ImpactReport(BaseModel):
    """Stub: impact report example (T0.7)."""

    id: str
    source_version_id: str
    affected: list[AffectedFinding]


class ReverifyResult(BaseModel):
    """Re-run outcome for stale findings (F12)."""

    superseded: list[str]
    current: list[str]
    skipped: list[str] = []


class GraphNode(BaseModel):
    """One React Flow node (F10)."""

    id: str
    kind: str
    label: str
    state: str | None = None


class GraphEdge(BaseModel):
    """One React Flow edge (F10)."""

    src: str
    dst: str
    rel: str


class GraphSlice(BaseModel):
    """Stub: graph slice example (T0.7)."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]


class AuditRow(BaseModel):
    """One append-only audit row (F14)."""

    id: str
    ts: str
    actor_type: str
    actor_id: str
    event: str
    object_type: str
    object_id: str
    details: dict[str, Any]


class AuditTrail(BaseModel):
    """Stub: audit rows example (T0.7)."""

    rows: list[AuditRow]


class ProofVerifyResult(BaseModel):
    """Tamper-demo checker verdict (G8)."""

    valid: bool
    errors: list[dict[str, Any]]
    cited_source_versions: list[str]


class CounterfactualAffected(BaseModel):
    """One finding under a counterfactual change (T7.3)."""

    finding_id: str
    claim_id: str
    would_remain_valid: bool
    would_follow_label: str = ""
    logic: dict[str, Any]


class CounterfactualResult(BaseModel):
    """Read-only what-if traversal (F19, stretch T7.3)."""

    available: bool
    note: str
    source_version_id: str | None = None
    changed_keys: list[str] = []
    affected: list[CounterfactualAffected] = []
    reverify_list: list[str] = []
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []


class ReverifyListItem(BaseModel):
    """One finding awaiting re-verification (T7.3)."""

    finding_id: str
    claim_id: str
    reason: str
    reason_label: str = ""
    clause_ref: str = ""


class ReverifyList(BaseModel):
    """Findings awaiting re-verification for a matter (T7.3)."""

    findings: list[ReverifyListItem] = []


class DemoResetResult(BaseModel):
    """Seed reset acknowledgement (demo only)."""

    reset: bool
    matter_id: str


class DemoScenarioResult(BaseModel):
    """Scenario seed acknowledgement (demo only)."""

    scenario: str
    steps: list[str]


class ErrorDetail(BaseModel):
    """Error shape from DATA_MODEL_API §7."""

    code: str
    message: str
    details: dict[str, Any] = {}


class ErrorResponse(BaseModel):
    """Error envelope from DATA_MODEL_API §7."""

    error: ErrorDetail
