import auditJson from '../../../../openapi/examples/audit.json'
import clausesJson from '../../../../openapi/examples/clauses.json'
import diffJson from '../../../../openapi/examples/diff.json'
import factsJson from '../../../../openapi/examples/facts.json'
import findingJson from '../../../../openapi/examples/finding_current.json'
import ingestJson from '../../../../openapi/examples/ingest_result.json'
import matterJson from '../../../../openapi/examples/matter.json'
import reverifyJson from '../../../../openapi/examples/reverify_result.json'
import sourcesJson from '../../../../openapi/examples/sources.json'
import sourceVersionsJson from '../../../../openapi/examples/source_versions.json'

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
  Matter,
  Proof,
  ProofVerifyBody,
  ProofVerifyResult,
  ReverifyResult,
  SourceList,
  SourceVersionList,
  ToolCall,
} from '../types'
import {
  afterFindingFrom,
  decoyImpact,
  decoyVersions,
  demoCurrentGraph,
  demoImpact,
  demoStaleGraph,
  reverifyAudit,
} from './impactDemo'
import { approveFact, challengeFact, verifyProof } from './lawyerControl'
import { DEMO_RUN_EVENTS } from './runTrace'

/** Example payloads from `openapi/examples/` (contract v1 compatible stubs). */
export const mockData = {
  matter: matterJson as Matter,
  clauses: clausesJson as { clauses: Clause[] },
  finding: findingJson as Finding,
  facts: factsJson as { facts: Fact[] },
  diff: diffJson as DiffResult,
  audit: auditJson as AuditTrail,
  sourceVersions: sourceVersionsJson as SourceVersionList,
  impact: demoImpact,
  sources: sourcesJson as SourceList,
  ingest: ingestJson as IngestResult,
  reverify: reverifyJson as ReverifyResult,
}

export async function fetchMockClauses(): Promise<Clause[]> {
  return mockData.clauses.clauses
}

export async function fetchMockFinding(): Promise<Finding> {
  return mockData.finding
}

export async function fetchMockFacts(): Promise<Fact[]> {
  return mockData.facts.facts
}

export async function fetchMockDiff(
  _sourceId: string,
  against: string,
): Promise<DiffResult> {
  if (against === 'SV-DECOY-1' || _sourceId === 'SRC-DECOY') {
    const sample = mockData.diff.before[0]
    return {
      ...mockData.diff,
      against: 'SV-DECOY-1',
      current: 'SV-DECOY-1',
      changed_keys: [],
      before: sample ? [sample] : [],
      after: sample ? [sample] : [],
    }
  }
  return mockData.diff
}

export async function fetchMockGraph(sourceId = 'SRC-DPDP-ACT'): Promise<GraphSlice> {
  return sourceId === 'SRC-DECOY' ? demoCurrentGraph : demoStaleGraph
}

export async function fetchMockAudit(): Promise<AuditTrail> {
  return mockData.audit
}

export async function fetchMockSourceVersions(
  sourceId: string,
): Promise<SourceVersionList> {
  return sourceId === 'SRC-DECOY' ? decoyVersions : mockData.sourceVersions
}

export async function fetchMockImpact(reportId: string): Promise<ImpactReport> {
  return reportId.includes('DECOY') ? decoyImpact : mockData.impact
}

export async function fetchMockDocuments(matterId: string): Promise<DocumentList> {
  return {
    documents: [
      {
        id: 'DOC-01',
        matter_id: matterId,
        title: mockData.matter.title,
        kind: 'dpa',
      },
    ],
  }
}

export async function fetchMockFindingById(id: string): Promise<Finding> {
  if (id === 'FND-002') {
    return fetchMockAfterFinding()
  }
  return fetchMockFinding()
}

export async function fetchMockSources(): Promise<SourceList> {
  return mockData.sources
}

export async function fetchMockIngest(sourceId: string): Promise<IngestResult> {
  if (sourceId === 'SRC-DECOY') {
    return { source_version_id: 'SV-DECOY-1', impact_report_id: 'IMP-DECOY' }
  }
  return mockData.ingest
}

export async function fetchMockReverify(): Promise<ReverifyResult> {
  return mockData.reverify
}

export async function fetchMockAfterFinding(): Promise<Finding> {
  return afterFindingFrom(mockData.finding)
}

export async function fetchMockReverifyAudit(): Promise<AuditTrail> {
  return reverifyAudit(mockData.audit)
}

export async function fetchMockMatter(): Promise<Matter> {
  return mockData.matter
}

export async function fetchMockRunEvents(_runId: string): Promise<ToolCall[]> {
  return DEMO_RUN_EVENTS
}

export async function fetchMockCreateClaim(): Promise<ClaimCreated> {
  return { claim_id: 'C-001', run_id: 'RUN-01' }
}

export async function fetchMockApproveFact(factId: string): Promise<FactAction> {
  const fact = mockData.facts.facts.find((row) => row.id === factId) ?? mockData.facts.facts[0]
  return approveFact(fact)
}

export async function fetchMockChallengeFact(factId: string): Promise<FactAction> {
  const fact = mockData.facts.facts.find((row) => row.id === factId) ?? mockData.facts.facts[0]
  return challengeFact(fact)
}

export async function fetchMockVerifyProof(body: ProofVerifyBody): Promise<ProofVerifyResult> {
  return verifyProof(mockData.finding.proof, body.proof as Proof)
}

export async function pollMockRunEvents(
  runId: string,
  onEvent: (events: ToolCall[]) => void,
  signal?: AbortSignal,
): Promise<ToolCall[]> {
  const all = await fetchMockRunEvents(runId)
  let index = 0
  return new Promise((resolve, reject) => {
    const tick = () => {
      if (signal?.aborted) {
        reject(new DOMException('Aborted', 'AbortError'))
        return
      }
      index += 1
      const slice = all.slice(0, index)
      onEvent(slice)
      if (index >= all.length) {
        resolve(all)
        return
      }
      window.setTimeout(tick, 350)
    }
    tick()
  })
}
