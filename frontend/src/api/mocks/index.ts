import auditJson from '../../../../openapi/examples/audit.json'
import clausesJson from '../../../../openapi/examples/clauses.json'
import diffJson from '../../../../openapi/examples/diff.json'
import factsJson from '../../../../openapi/examples/facts.json'
import findingJson from '../../../../openapi/examples/finding_current.json'
import graphJson from '../../../../openapi/examples/graph.json'
import impactJson from '../../../../openapi/examples/impact.json'
import matterJson from '../../../../openapi/examples/matter.json'
import sourceVersionsJson from '../../../../openapi/examples/source_versions.json'

import type {
  AuditTrail,
  ClaimCreated,
  Clause,
  DiffResult,
  Fact,
  Finding,
  GraphSlice,
  ImpactReport,
  Matter,
  SourceVersionList,
  ToolCall,
} from '../types'
import { DEMO_RUN_EVENTS } from './runTrace'

/** Example payloads from `openapi/examples/` (contract v0). */
export const mockData = {
  matter: matterJson as Matter,
  clauses: clausesJson as { clauses: Clause[] },
  finding: findingJson as Finding,
  facts: factsJson as { facts: Fact[] },
  diff: diffJson as DiffResult,
  graph: graphJson as GraphSlice,
  audit: auditJson as AuditTrail,
  sourceVersions: sourceVersionsJson as SourceVersionList,
  impact: impactJson as ImpactReport,
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

export async function fetchMockDiff(): Promise<DiffResult> {
  return mockData.diff
}

export async function fetchMockGraph(): Promise<GraphSlice> {
  return mockData.graph
}

export async function fetchMockAudit(): Promise<AuditTrail> {
  return mockData.audit
}

export async function fetchMockSourceVersions(): Promise<SourceVersionList> {
  return mockData.sourceVersions
}

export async function fetchMockImpact(): Promise<ImpactReport> {
  return mockData.impact
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
