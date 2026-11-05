import auditJson from '../../../../openapi/examples/audit.json'
import clausesJson from '../../../../openapi/examples/clauses.json'
import diffJson from '../../../../openapi/examples/diff.json'
import factsJson from '../../../../openapi/examples/facts.json'
import findingJson from '../../../../openapi/examples/finding_current.json'
import ingestJson from '../../../../openapi/examples/ingest_result.json'
import matterJson from '../../../../openapi/examples/matter.json'
import reverifyJson from '../../../../openapi/examples/reverify_result.json'
import sourcesJson from '../../../../openapi/examples/sources.json'
import compareReportJson from '../../../../openapi/examples/compare_report.json'
import coverageReportJson from '../../../../openapi/examples/coverage_report.json'
import flagResultJson from '../../../../openapi/examples/flag_result.json'
import provisionSearchJson from '../../../../openapi/examples/provision_search.json'
import provisionsJson from '../../../../openapi/examples/provisions.json'
import ruleCardJson from '../../../../openapi/examples/rule_card.json'
import ruleCardDraftsJson from '../../../../openapi/examples/rule_card_drafts.json'
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
  AdminOverview,
  AuditExport,
  CompareReport,
  CoverageReport,
  FlagResult,
  ProvisionList,
  ProvisionSearchResult,
  ReviewResult,
  RuleCardDraftList,
  RuleCardSummary,
  ReverifyResult,
  SourceList,
  SourceVersionList,
  ToolCall,
  TrustClass,
} from '../types'
import { STATUS_LABELS, TRUST_LABELS } from '../../content/glossary'
import {
  fetchMockAuth,
  fetchMockCounterfactual,
  fetchMockDictation,
  fetchMockDocumentPages,
  fetchMockJob,
  fetchMockReverifyList,
  fetchMockScan,
  fetchMockTranscribe,
  fetchMockUpdateClause,
  fetchMockUploadDocument,
} from './stretch'
import {
  afterFindingFrom,
  decoyImpact,
  decoyVersions,
  demoCurrentGraph,
  demoImpact,
  demoStaleGraph,
  reverifyAudit,
} from './impactDemo'
import { approveFact, challengeFact, unknownFinding, verifyProof } from './lawyerControl'
import { DEMO_RUN_EVENTS } from './runTrace'

function withDisplayFields(finding: Finding): Finding {
  return {
    ...finding,
    status_label: finding.status_label || STATUS_LABELS[finding.status] || '',
    clause_ref: finding.clause_ref || '9.2',
    clause_quote:
      finding.clause_quote ||
      'Nimbus may transfer order data to its analytics cluster outside India for fraud screening.',
    section_label: finding.section_label || 'Digital Personal Data Protection Act, 2023, s 8(6)',
    section_quote:
      finding.section_quote ||
      'Personal data may be transferred outside India except to notified countries',
    law_version_label:
      finding.law_version_label || 'Digital Personal Data Protection Act, 2023, version v1',
    law_version_date: finding.law_version_date || finding.as_of,
    fact_lines:
      finding.fact_lines.length > 0
        ? finding.fact_lines
        : finding.proof.premises.map((premise) => ({
            label: premise.statement,
            trust_label: TRUST_LABELS[premise.trust_class as TrustClass] ?? '',
            confirmed_by: premise.trust_class === 'lawyer_confirmed' ? 'You' : null,
          })),
  }
}

function withTrustLabels(facts: Fact[]): Fact[] {
  return facts.map((fact) => ({
    ...fact,
    trust_label: fact.trust_label || TRUST_LABELS[fact.trust_class as TrustClass] || '',
  }))
}

/** Example payloads from `openapi/examples/` plus v9 display fields for the UI. */
export const mockData = {
  matter: matterJson as Matter,
  clauses: clausesJson as { clauses: Clause[] },
  finding: withDisplayFields(findingJson as Finding),
  facts: { facts: withTrustLabels((factsJson as { facts: Fact[] }).facts) },
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

export async function fetchMockProvisions(): Promise<ProvisionList> {
  return provisionsJson as ProvisionList
}

const mockDrafts: RuleCardSummary[] = [
  ...(ruleCardDraftsJson as RuleCardDraftList).drafts,
]

export async function fetchMockCardDrafts(): Promise<RuleCardDraftList> {
  return { drafts: [...mockDrafts] }
}

export async function fetchMockDraftCard(): Promise<RuleCardSummary> {
  const card = ruleCardJson as RuleCardSummary
  if (!mockDrafts.some((draft) => draft.id === card.id)) {
    mockDrafts.push(card)
  }
  return card
}

export async function fetchMockConfirmCard(id: string): Promise<RuleCardSummary> {
  const index = mockDrafts.findIndex((draft) => draft.id === id)
  const base = index >= 0 ? mockDrafts[index] : (ruleCardJson as RuleCardSummary)
  if (index >= 0) {
    mockDrafts.splice(index, 1)
  }
  return { ...base, id: 'RC-CONFIRMED-01', trust_class: 'lawyer_confirmed' }
}

export async function fetchMockRejectCard(id: string): Promise<RuleCardSummary> {
  const index = mockDrafts.findIndex((draft) => draft.id === id)
  const base = index >= 0 ? mockDrafts[index] : (ruleCardJson as RuleCardSummary)
  if (index >= 0) {
    mockDrafts.splice(index, 1)
  }
  return base
}

const mockMatters: { id: string; client_name: string; title: string }[] = [
  {
    id: mockData.matter.id,
    client_name: mockData.matter.client_name,
    title: mockData.matter.title,
  },
]

export async function fetchMockMatters(): Promise<{ matters: typeof mockMatters }> {
  return { matters: [...mockMatters] }
}

export async function fetchMockCreateMatter(body: {
  title: string
  client_name: string
}): Promise<{ id: string; client_name: string; title: string }> {
  const created = {
    id: `MAT-${String(mockMatters.length + 1).padStart(2, '0')}`,
    client_name: body.client_name,
    title: body.title,
  }
  mockMatters.push(created)
  return created
}

export async function fetchMockRunEvents(_runId: string): Promise<ToolCall[]> {
  return DEMO_RUN_EVENTS
}

export async function fetchMockCreateClaim(body?: {
  question?: string
}): Promise<ClaimCreated> {
  const question = body?.question ?? ''
  if (/telecom|fairness opinion/i.test(question)) {
    return {
      claim_id: 'C-UNK',
      run_id: 'RUN-UNK',
      finding_id: 'FND-UNK',
      status: 'UNKNOWN',
    }
  }
  return { claim_id: 'C-001', run_id: 'RUN-01' }
}

export async function fetchMockUnknownFinding(): Promise<Finding> {
  return unknownFinding()
}

export async function fetchMockHistory(claimId: string): Promise<Finding[]> {
  if (claimId === 'C-UNK') {
    return [unknownFinding()]
  }
  return [mockData.finding]
}

export async function fetchMockApproveFact(factId: string): Promise<FactAction> {
  const fact = mockData.facts.facts.find((row) => row.id === factId)
  if (fact) {
    return approveFact(fact)
  }
  return { fact_id: factId, trust_class: 'lawyer_confirmed', supersedes_id: factId }
}

export async function fetchMockAdminOverview(): Promise<AdminOverview> {
  return {
    tenant_id: 'demo',
    matters: 2,
    findings_by_status: { FOLLOWS: 3, REQUIRES_REVIEW: 1, UNKNOWN: 1 },
    facts_by_trust: { lawyer_confirmed: 4, document_extracted: 25, ai_inferred: 36 },
    spend_usd: 0.42,
    jobs: { done: 5 },
  }
}

export async function fetchMockAuditExport(matterId: string): Promise<AuditExport> {
  return {
    matter_id: matterId,
    exported_at: '2026-01-01T00:00:00Z',
    rows: mockData.audit.rows,
  }
}

export async function fetchMockCompare(): Promise<CompareReport> {
  return compareReportJson as CompareReport
}

export async function fetchMockCoverage(): Promise<CoverageReport> {
  return coverageReportJson as CoverageReport
}

export async function fetchMockFlagPair(): Promise<FlagResult> {
  return flagResultJson as FlagResult
}

export async function fetchMockSearchProvisions(
  query: string,
): Promise<ProvisionSearchResult> {
  const example = provisionSearchJson as ProvisionSearchResult
  return { query, hits: example.hits }
}

export async function fetchMockExplainDocument(): Promise<{ explained: number }> {
  return { explained: 12 }
}

export async function fetchMockSummarizeDocument(): Promise<{
  fact_id: string
  summary: string
}> {
  return {
    fact_id: 'F-E01',
    summary:
      'Document summary: This agreement appears to set out how Nimbus processes personal data for Acme.',
  }
}

export async function fetchMockRejectFact(factId: string): Promise<FactAction> {
  return { fact_id: factId, trust_class: 'disputed', supersedes_id: factId }
}

export async function fetchMockChallengeFact(factId: string): Promise<FactAction> {
  const fact = mockData.facts.facts.find((row) => row.id === factId) ?? mockData.facts.facts[0]
  return challengeFact(fact)
}

export async function fetchMockVerifyProof(body: ProofVerifyBody): Promise<ProofVerifyResult> {
  return verifyProof(mockData.finding.proof, body.proof as Proof)
}

export async function fetchMockReviewFinding(findingId: string): Promise<ReviewResult> {
  return { finding_id: findingId, state: 'REVIEWED' }
}

export {
  fetchMockAuth,
  fetchMockCounterfactual,
  fetchMockDictation,
  fetchMockDocumentPages,
  fetchMockJob,
  fetchMockReverifyList,
  fetchMockScan,
  fetchMockTranscribe,
  fetchMockUpdateClause,
  fetchMockUploadDocument,
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
