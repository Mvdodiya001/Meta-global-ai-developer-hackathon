import { DEMO_SOURCE_ID, getApiBase, mocksEnabled } from './config'
import {
  fetchMockAudit,
  fetchMockClauses,
  fetchMockDiff,
  fetchMockDocuments,
  fetchMockFacts,
  fetchMockFinding,
  fetchMockFindingById,
  fetchMockGraph,
  fetchMockImpact,
  fetchMockCreateMatter,
  fetchMockCardDrafts,
  fetchMockAuditExport,
  fetchMockCompare,
  fetchMockCoverage,
  fetchMockFlagPair,
  fetchMockConfirmCard,
  fetchMockDraftCard,
  fetchMockMatter,
  fetchMockProvisions,
  fetchMockSearchProvisions,
  fetchMockRejectCard,
  fetchMockMatters,
  fetchMockApproveFact,
  fetchMockChallengeFact,
  fetchMockExplainDocument,
  fetchMockRejectFact,
  fetchMockSummarizeDocument,
  fetchMockCreateClaim,
  fetchMockUnknownFinding,
  fetchMockHistory,
  fetchMockIngest,
  fetchMockReverify,
  fetchMockRunEvents,
  fetchMockSourceVersions,
  fetchMockSources,
  fetchMockReviewFinding,
  fetchMockVerifyProof,
  fetchMockCounterfactual,
  fetchMockReverifyList,
  fetchMockScan,
  fetchMockDictation,
  fetchMockTranscribe,
  fetchMockUpdateClause,
  fetchMockUploadDocument,
  fetchMockJob,
  fetchMockDocumentPages,
  fetchMockAuth,
  pollMockRunEvents,
} from './mocks'
import type {
  AuditTrail,
  AuthResult,
  ClaimCreated,
  DocumentPages,
  IntakeJob,
  TranscribeResult,
  UploadResult,
  FindingHistory,
  AuditExport,
  Clause,
  CompareReport,
  CoverageReport,
  FlagResult,
  CounterfactualBody,
  CounterfactualResult,
  DictationRequest,
  DictationResult,
  DiffResult,
  DocumentList,
  Fact,
  ExplainResult,
  FactAction,
  SummaryResult,
  Finding,
  GraphSlice,
  ImpactReport,
  IngestResult,
  IngestVersionBody,
  Matter,
  MatterList,
  MatterSummary,
  Proof,
  ProofVerifyResult,
  ProvisionList,
  ProvisionSearchResult,
  ReviewBody,
  RuleCardDraftList,
  RuleCardSummary,
  ReviewResult,
  ReverifyList,
  ReverifyResult,
  Run,
  RunEvents,
  ScanRequest,
  ScanResult,
  SourceList,
  SourceVersionList,
  ToolCall,
} from './types'

const POLL_MS = 400
const POLL_ATTEMPTS = 20

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

type ErrorEnvelope = {
  error?: { code?: string; message?: string }
}

async function readError(response: Response, path: string): Promise<ApiError> {
  const fallback = `API ${path} failed: ${response.status}`
  try {
    const body = (await response.json()) as ErrorEnvelope
    return new ApiError(
      response.status,
      body.error?.code ?? 'HTTP_ERROR',
      body.error?.message ?? fallback,
    )
  } catch {
    return new ApiError(response.status, 'HTTP_ERROR', fallback)
  }
}

const TOKEN_KEY = 'clausetrace.token'

export function storedToken(): string | null {
  try {
    return window.localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function storeToken(token: string | null): void {
  try {
    if (token) {
      window.localStorage.setItem(TOKEN_KEY, token)
    } else {
      window.localStorage.removeItem(TOKEN_KEY)
    }
  } catch {
    // storage unavailable (tests); sign-in still works for the session
  }
}

function authHeaders(): Record<string, string> {
  const token = storedToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function getJson<T>(path: string): Promise<T> {
  const url = `${getApiBase()}${path}`
  const response = await fetch(url, { headers: authHeaders() })
  if (!response.ok) {
    if (response.status === 401) {
      // Stale token (e.g. issued by another backend): drop it so the
      // UI can show the sign-in prompt instead of a load error.
      storeToken(null)
    }
    throw await readError(response, path)
  }
  return response.json() as Promise<T>
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const url = `${getApiBase()}${path}`
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    if (response.status === 401) {
      // Stale token (e.g. issued by another backend): drop it so the
      // UI can show the sign-in prompt instead of a load error.
      storeToken(null)
    }
    throw await readError(response, path)
  }
  return response.json() as Promise<T>
}

async function optionalGet<T>(path: string): Promise<T | null> {
  try {
    return await getJson<T>(path)
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      return null
    }
    throw err
  }
}

function query(params: Record<string, string | undefined>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value) {
      search.set(key, value)
    }
  }
  const encoded = search.toString()
  return encoded ? `?${encoded}` : ''
}

function delay(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const timer = window.setTimeout(resolve, ms)
    const onAbort = () => {
      window.clearTimeout(timer)
      reject(new DOMException('Aborted', 'AbortError'))
    }
    if (signal?.aborted) {
      onAbort()
      return
    }
    signal?.addEventListener('abort', onAbort, { once: true })
  })
}

async function pollLiveRunEvents(
  runId: string,
  onEvent: (events: ToolCall[]) => void,
  signal?: AbortSignal,
): Promise<ToolCall[]> {
  let events: ToolCall[] = []
  for (let attempt = 0; attempt < POLL_ATTEMPTS; attempt += 1) {
    if (signal?.aborted) {
      throw new DOMException('Aborted', 'AbortError')
    }
    const payload = await getJson<RunEvents>(`/api/runs/${encodeURIComponent(runId)}/events`)
    events = payload.events
    onEvent(events)
    const run = await getJson<Run>(`/api/runs/${encodeURIComponent(runId)}`)
    if (run.status !== 'running') {
      return events
    }
    await delay(POLL_MS, signal)
  }
  return events
}

/** HTTP client for contract v8. Tests keep mocks (`MODE=test`). */
export const api = {
  matters: (): Promise<MatterList> =>
    mocksEnabled()
      ? fetchMockMatters()
      : getJson<MatterList>('/api/matters'),
  createMatter: (body: { title: string; client_name: string }): Promise<MatterSummary> =>
    mocksEnabled()
      ? fetchMockCreateMatter(body)
      : postJson<MatterSummary>('/api/matters', body),
  matter: (id: string): Promise<Matter> =>
    mocksEnabled() ? fetchMockMatter() : getJson<Matter>(`/api/matters/${encodeURIComponent(id)}`),
  documents: (matterId: string): Promise<DocumentList> =>
    mocksEnabled()
      ? fetchMockDocuments(matterId)
      : getJson<DocumentList>(`/api/matters/${encodeURIComponent(matterId)}/documents`),
  clauses: (documentId: string): Promise<Clause[]> =>
    mocksEnabled()
      ? fetchMockClauses()
      : getJson<{ clauses: Clause[] }>(
          `/api/documents/${encodeURIComponent(documentId)}/clauses`,
        ).then((r) => r.clauses),
  finding: (claimId: string): Promise<Finding> =>
    mocksEnabled()
      ? fetchMockFinding()
      : getJson<Finding>(`/api/claims/${encodeURIComponent(claimId)}/current`),
  currentFinding: (claimId: string): Promise<Finding | null> =>
    mocksEnabled()
      ? claimId === 'C-UNK'
        ? fetchMockUnknownFinding()
        : fetchMockFinding()
      : optionalGet<Finding>(`/api/claims/${encodeURIComponent(claimId)}/current`),
  findingById: (findingId: string): Promise<Finding> =>
    mocksEnabled()
      ? fetchMockFindingById(findingId)
      : getJson<Finding>(`/api/findings/${encodeURIComponent(findingId)}`),
  findingHistory: (claimId: string): Promise<Finding[]> =>
    mocksEnabled()
      ? fetchMockHistory(claimId)
      : getJson<FindingHistory>(`/api/claims/${encodeURIComponent(claimId)}/history`).then(
          (r) => r.versions,
        ),
  facts: (matterId: string): Promise<Fact[]> =>
    mocksEnabled()
      ? fetchMockFacts()
      : getJson<{ facts: Fact[] }>(
          `/api/matters/${encodeURIComponent(matterId)}/facts`,
        ).then((r) => r.facts),
  diff: (
    currentVersionId: string,
    againstVersionId: string,
    sourceIdForMock = DEMO_SOURCE_ID,
  ): Promise<DiffResult> =>
    mocksEnabled()
      ? fetchMockDiff(sourceIdForMock, againstVersionId)
      : getJson<DiffResult>(
          `/api/source-versions/${encodeURIComponent(currentVersionId)}/diff${query({
            against: againstVersionId,
          })}`,
        ),
  graph: (matterId: string, sourceIdForMock = DEMO_SOURCE_ID): Promise<GraphSlice> =>
    mocksEnabled()
      ? fetchMockGraph(sourceIdForMock)
      : getJson<GraphSlice>(`/api/graph${query({ matter_id: matterId })}`),
  audit: (matterId: string): Promise<AuditTrail> =>
    mocksEnabled()
      ? fetchMockAudit()
      : getJson<AuditTrail>(`/api/audit${query({ matter_id: matterId })}`),
  sourceVersions: (sourceId: string): Promise<SourceVersionList> =>
    mocksEnabled()
      ? fetchMockSourceVersions(sourceId)
      : getJson<SourceVersionList>(`/api/sources/${encodeURIComponent(sourceId)}/versions`),
  impact: (reportId: string): Promise<ImpactReport> =>
    mocksEnabled()
      ? fetchMockImpact(reportId)
      : getJson<ImpactReport>(`/api/impact/${encodeURIComponent(reportId)}`),
  sources: (): Promise<SourceList> =>
    mocksEnabled() ? fetchMockSources() : getJson<SourceList>('/api/sources'),
  auditExport: (matterId: string): Promise<AuditExport> =>
    mocksEnabled()
      ? fetchMockAuditExport(matterId)
      : getJson<AuditExport>(`/api/matters/${encodeURIComponent(matterId)}/audit-export`),
  compareDocuments: (matterId: string, a: string, b: string): Promise<CompareReport> =>
    mocksEnabled()
      ? fetchMockCompare()
      : getJson<CompareReport>(
          `/api/matters/${encodeURIComponent(matterId)}/compare${query({ a, b })}`,
        ),
  flagClausePair: (matterId: string, clauseRef: string): Promise<FlagResult> =>
    mocksEnabled()
      ? fetchMockFlagPair()
      : postJson<FlagResult>(`/api/matters/${encodeURIComponent(matterId)}/compare/flag`, {
          clause_ref: clauseRef,
        }),
  documentCoverage: (documentId: string): Promise<CoverageReport> =>
    mocksEnabled()
      ? fetchMockCoverage()
      : getJson<CoverageReport>(`/api/documents/${encodeURIComponent(documentId)}/coverage`),
  searchProvisions: (q: string, limit = 5, rerank = false): Promise<ProvisionSearchResult> =>
    mocksEnabled()
      ? fetchMockSearchProvisions(q)
      : getJson<ProvisionSearchResult>(
          `/api/provisions/search${query({
            q,
            limit: String(limit),
            rerank: rerank ? 'true' : undefined,
          })}`,
        ),
  provisions: (versionId: string): Promise<ProvisionList> =>
    mocksEnabled()
      ? fetchMockProvisions()
      : getJson<ProvisionList>(
          `/api/source-versions/${encodeURIComponent(versionId)}/provisions`,
        ),
  cardDrafts: (): Promise<RuleCardDraftList> =>
    mocksEnabled() ? fetchMockCardDrafts() : getJson<RuleCardDraftList>('/api/rule-cards/drafts'),
  draftCard: (provisionId: string): Promise<RuleCardSummary> =>
    mocksEnabled()
      ? fetchMockDraftCard()
      : postJson<RuleCardSummary>('/api/rule-cards/draft', { provision_id: provisionId }),
  confirmCard: (
    cardId: string,
    body: { interpretation?: string; claim_type?: string },
  ): Promise<RuleCardSummary> =>
    mocksEnabled()
      ? fetchMockConfirmCard(cardId)
      : postJson<RuleCardSummary>(`/api/rule-cards/${encodeURIComponent(cardId)}/confirm`, body),
  rejectCard: (cardId: string): Promise<RuleCardSummary> =>
    mocksEnabled()
      ? fetchMockRejectCard(cardId)
      : postJson<RuleCardSummary>(`/api/rule-cards/${encodeURIComponent(cardId)}/reject`, {}),
  ingest: (sourceId: string, version?: IngestVersionBody): Promise<IngestResult> =>
    mocksEnabled()
      ? fetchMockIngest(sourceId)
      : postJson<IngestResult>(`/api/sources/${encodeURIComponent(sourceId)}/ingest`, {
          version,
        }),
  reverify: (reportId: string): Promise<ReverifyResult> =>
    mocksEnabled()
      ? fetchMockReverify()
      : postJson<ReverifyResult>(`/api/impact/${encodeURIComponent(reportId)}/reverify`, {}),
  createClaim: (body: {
    clause_id: string
    question: string
    as_of: string
  }): Promise<ClaimCreated> =>
    mocksEnabled() ? fetchMockCreateClaim(body) : postJson<ClaimCreated>('/api/claims', body),
  runEvents: (runId: string): Promise<ToolCall[]> =>
    mocksEnabled()
      ? fetchMockRunEvents(runId)
      : getJson<RunEvents>(`/api/runs/${encodeURIComponent(runId)}/events`).then(
          (r) => r.events,
        ),
  pollRunEvents: mocksEnabled() ? pollMockRunEvents : pollLiveRunEvents,
  approveFact: (factId: string): Promise<FactAction> =>
    mocksEnabled()
      ? fetchMockApproveFact(factId)
      : postJson<FactAction>(`/api/facts/${encodeURIComponent(factId)}/approve`, {}),
  challengeFact: (factId: string): Promise<FactAction> =>
    mocksEnabled()
      ? fetchMockChallengeFact(factId)
      : postJson<FactAction>(`/api/facts/${encodeURIComponent(factId)}/challenge`, {
          reason: 'Lawyer challenge',
        }),
  rejectFact: (factId: string): Promise<FactAction> =>
    mocksEnabled()
      ? fetchMockRejectFact(factId)
      : postJson<FactAction>(`/api/facts/${encodeURIComponent(factId)}/reject`, {}),
  explainDocument: (documentId: string): Promise<ExplainResult> =>
    mocksEnabled()
      ? fetchMockExplainDocument()
      : postJson<ExplainResult>(`/api/documents/${encodeURIComponent(documentId)}/explain`, {}),
  summarizeDocument: (documentId: string): Promise<SummaryResult> =>
    mocksEnabled()
      ? fetchMockSummarizeDocument()
      : postJson<SummaryResult>(
          `/api/documents/${encodeURIComponent(documentId)}/summarize`,
          {},
        ),
  verifyProof: (claimId: string, proof: Proof): Promise<ProofVerifyResult> =>
    mocksEnabled()
      ? fetchMockVerifyProof({ claim_id: claimId, proof })
      : postJson<ProofVerifyResult>('/api/proofs/verify', { claim_id: claimId, proof }),
  reviewFinding: (findingId: string, body: ReviewBody): Promise<ReviewResult> =>
    mocksEnabled()
      ? fetchMockReviewFinding(findingId)
      : postJson<ReviewResult>(`/api/findings/${encodeURIComponent(findingId)}/review`, body),
  counterfactual: (body: CounterfactualBody): Promise<CounterfactualResult> =>
    mocksEnabled()
      ? fetchMockCounterfactual(body)
      : postJson<CounterfactualResult>('/api/counterfactual', body),
  reverifyList: (matterId: string): Promise<ReverifyList> =>
    mocksEnabled()
      ? fetchMockReverifyList(matterId)
      : getJson<ReverifyList>(`/api/reverify-list${query({ matter_id: matterId })}`),
  scanPage: (body: ScanRequest): Promise<ScanResult> =>
    mocksEnabled() ? fetchMockScan(body) : postJson<ScanResult>('/api/scans', body),
  createDictation: (body: DictationRequest): Promise<DictationResult> =>
    mocksEnabled()
      ? fetchMockDictation(body)
      : postJson<DictationResult>('/api/dictations', body),
  transcribe: (body: DictationRequest): Promise<TranscribeResult> =>
    mocksEnabled()
      ? fetchMockTranscribe(body)
      : postJson<TranscribeResult>('/api/transcribe', body),
  updateClause: (
    documentId: string,
    clauseId: string,
    body: { text: string; heading?: string },
  ): Promise<Clause> =>
    mocksEnabled()
      ? fetchMockUpdateClause(documentId, clauseId, body)
      : postJson<Clause>(
          `/api/documents/${encodeURIComponent(documentId)}/clauses/${encodeURIComponent(clauseId)}/update`,
          body,
        ),
  uploadDocument: (
    matterId: string,
    body: { title: string; file_base64: string; media_type: string },
  ): Promise<UploadResult> =>
    mocksEnabled()
      ? fetchMockUploadDocument()
      : postJson<UploadResult>(
          `/api/matters/${encodeURIComponent(matterId)}/documents/upload`,
          body,
        ),
  jobStatus: (jobId: string): Promise<IntakeJob> =>
    mocksEnabled()
      ? fetchMockJob()
      : getJson<IntakeJob>(`/api/jobs/${encodeURIComponent(jobId)}`),
  documentPages: (documentId: string): Promise<DocumentPages> =>
    mocksEnabled()
      ? fetchMockDocumentPages()
      : getJson<DocumentPages>(
          `/api/documents/${encodeURIComponent(documentId)}/pages`,
        ),
  register: (body: { email: string; password: string; name: string }): Promise<AuthResult> =>
    mocksEnabled()
      ? fetchMockAuth(body.email, body.name)
      : postJson<AuthResult>('/api/auth/register', body),
  login: (body: { email: string; password: string }): Promise<AuthResult> =>
    mocksEnabled()
      ? fetchMockAuth(body.email, '')
      : postJson<AuthResult>('/api/auth/login', body),
  me: (): Promise<AuthResult> =>
    mocksEnabled() ? fetchMockAuth('lawyer@example.com', 'Lawyer') : getJson<AuthResult>('/api/me'),
}
