import { getApiBase } from './config'
import {
  fetchMockAudit,
  fetchMockClauses,
  fetchMockDiff,
  fetchMockFacts,
  fetchMockFinding,
  fetchMockGraph,
  fetchMockImpact,
  fetchMockMatter,
  fetchMockAfterFinding,
  fetchMockCreateClaim,
  fetchMockIngest,
  fetchMockReverify,
  fetchMockReverifyAudit,
  fetchMockRunEvents,
  fetchMockSourceVersions,
  fetchMockSources,
  pollMockRunEvents,
} from './mocks'
import type {
  AuditTrail,
  ClaimCreated,
  Clause,
  DiffResult,
  Fact,
  Finding,
  GraphSlice,
  ImpactReport,
  IngestResult,
  Matter,
  ReverifyResult,
  SourceList,
  SourceVersionList,
  ToolCall,
} from './types'

const useLiveApi = import.meta.env.VITE_USE_LIVE_API === '1'

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${getApiBase()}${path}`)
  if (!response.ok) {
    throw new Error(`API ${path} failed: ${response.status}`)
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
    throw new Error(`API ${path} failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}

/** Client reads openapi examples unless `VITE_USE_LIVE_API=1` (backend with API_STUB=1). */
export const api = {
  matter: (_id: string): Promise<Matter> =>
    useLiveApi ? getJson<Matter>(`/api/matters/${_id}`) : fetchMockMatter(),
  clauses: (_documentId: string): Promise<Clause[]> =>
    useLiveApi
      ? getJson<{ clauses: Clause[] }>(`/api/documents/${_documentId}/clauses`).then(
          (r) => r.clauses,
        )
      : fetchMockClauses(),
  finding: (_claimId: string): Promise<Finding> =>
    useLiveApi
      ? getJson<Finding>(`/api/claims/${_claimId}/current`)
      : fetchMockFinding(),
  facts: (_matterId: string): Promise<Fact[]> =>
    useLiveApi
      ? getJson<{ facts: Fact[] }>(`/api/matters/${_matterId}/facts`).then((r) => r.facts)
      : fetchMockFacts(),
  diff: (sourceId: string, against: string): Promise<DiffResult> =>
    useLiveApi
      ? getJson<DiffResult>(
          `/api/sources/${sourceId}/diff?against=${encodeURIComponent(against)}`,
        )
      : fetchMockDiff(sourceId, against),
  graph: (_findingId: string, sourceId = 'SRC-DPDP-ACT'): Promise<GraphSlice> =>
    useLiveApi
      ? getJson<GraphSlice>(`/api/findings/${_findingId}/graph`)
      : fetchMockGraph(sourceId),
  audit: (_matterId: string): Promise<AuditTrail> =>
    useLiveApi
      ? getJson<AuditTrail>(`/api/matters/${_matterId}/audit`)
      : fetchMockAudit(),
  sourceVersions: (sourceId: string): Promise<SourceVersionList> =>
    useLiveApi
      ? getJson<SourceVersionList>(`/api/sources/${sourceId}/versions`)
      : fetchMockSourceVersions(sourceId),
  impact: (reportId: string): Promise<ImpactReport> =>
    useLiveApi
      ? getJson<ImpactReport>(`/api/impact/${reportId}`)
      : fetchMockImpact(reportId),
  sources: (): Promise<SourceList> =>
    useLiveApi ? getJson<SourceList>('/api/sources') : fetchMockSources(),
  ingest: (sourceId: string): Promise<IngestResult> =>
    useLiveApi
      ? postJson<IngestResult>(`/api/sources/${sourceId}/ingest`, { fixture: true })
      : fetchMockIngest(sourceId),
  reverify: (reportId: string): Promise<ReverifyResult> =>
    useLiveApi
      ? postJson<ReverifyResult>(`/api/impact/${reportId}/reverify`, {})
      : fetchMockReverify(),
  afterFinding: (): Promise<Finding> =>
    useLiveApi
      ? getJson<Finding>('/api/findings/FND-002')
      : fetchMockAfterFinding(),
  reverifyAudit: (): Promise<AuditTrail> =>
    useLiveApi
      ? getJson<AuditTrail>('/api/matters/MAT-01/audit')
      : fetchMockReverifyAudit(),
  createClaim: (_body: {
    clause_id: string
    question: string
    as_of: string
  }): Promise<ClaimCreated> =>
    useLiveApi
      ? postJson<ClaimCreated>('/api/claims', _body)
      : fetchMockCreateClaim(),
  runEvents: (runId: string): Promise<ToolCall[]> =>
    useLiveApi
      ? getJson<{ events: ToolCall[] }>(`/api/runs/${runId}/events`).then((r) => r.events)
      : fetchMockRunEvents(runId),
  pollRunEvents: pollMockRunEvents,
}
