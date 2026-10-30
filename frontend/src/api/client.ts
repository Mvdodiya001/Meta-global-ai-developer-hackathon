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
  fetchMockMatter,
  fetchMockApproveFact,
  fetchMockChallengeFact,
  fetchMockCreateClaim,
  fetchMockIngest,
  fetchMockReverify,
  fetchMockRunEvents,
  fetchMockSourceVersions,
  fetchMockSources,
  fetchMockVerifyProof,
  pollMockRunEvents,
} from './mocks'
import type {
  AuditTrail,
  ClaimCreated,
  Clause,
  DiffResult,
  DocumentList,
  Fact,
  FactAction,
  Finding,
  GraphSlice,
  ImpactReport,
  IngestResult,
  IngestVersionBody,
  Matter,
  Proof,
  ProofVerifyResult,
  ReverifyResult,
  Run,
  RunEvents,
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

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${getApiBase()}${path}`)
  if (!response.ok) {
    throw await readError(response, path)
  }
  return response.json() as Promise<T>
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${getApiBase()}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
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

/** HTTP client for contract v1. Tests keep `openapi/examples` mocks. */
export const api = {
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
      ? fetchMockFinding()
      : optionalGet<Finding>(`/api/claims/${encodeURIComponent(claimId)}/current`),
  findingById: (findingId: string): Promise<Finding> =>
    mocksEnabled()
      ? fetchMockFindingById(findingId)
      : getJson<Finding>(`/api/findings/${encodeURIComponent(findingId)}`),
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
    mocksEnabled() ? fetchMockCreateClaim() : postJson<ClaimCreated>('/api/claims', body),
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
  verifyProof: (claimId: string, proof: Proof): Promise<ProofVerifyResult> =>
    mocksEnabled()
      ? fetchMockVerifyProof({ claim_id: claimId, proof })
      : postJson<ProofVerifyResult>('/api/proofs/verify', { claim_id: claimId, proof }),
}
