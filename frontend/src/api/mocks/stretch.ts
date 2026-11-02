import type {
  Clause,
  CounterfactualBody,
  CounterfactualResult,
  DictationRequest,
  DictationResult,
  Fact,
  ReverifyList,
  ScanRequest,
  ScanResult,
} from '../types'
import { ANSWER_WOULD_NOT_FOLLOW, STATUS_LABELS, TRUST_LABELS } from '../../content/glossary'

const SCAN_CLAUSE: Clause = {
  id: 'CL-SCAN-9.2',
  document_version_id: 'DOCV-SCAN-01',
  ref: '9.2',
  heading: 'Cross-border transfer for fraud screening',
  text: 'Nimbus may transfer order data to its analytics cluster outside India for fraud screening.',
  span_start: 0,
  span_end: 89,
}

const SCAN_FACT: Fact = {
  id: 'F-SCAN-01',
  matter_id: 'MAT-01',
  clause_id: 'CL-SCAN-9.2',
  statement: 'Scanned page states Nimbus may transfer order data outside India for fraud screening.',
  structured: { transfer_outside_india: true },
  origin: 'scan',
  trust_class: 'document_extracted',
  trust_label: TRUST_LABELS.document_extracted,
  created_at: '2026-11-02T08:00:00Z',
}

export const MOCK_COUNTERFACTUAL: CounterfactualResult = {
  available: true,
  note: 'Read-only what-if. Nothing was ingested and no finding was marked stale.',
  source_version_id: 'SV-02',
  changed_keys: ['DPDP-Act-2023_s8(6)'],
  affected: [
    {
      finding_id: 'FND-RC-CT3-BREACH-01',
      claim_id: 'C-REC-ASK',
      would_remain_valid: false,
      would_follow_label: ANSWER_WOULD_NOT_FOLLOW,
      logic: {
        valid: false,
        consistent: true,
        counterexample: {
          rule_RC_CT3_BREACH_01: false,
          conclusion_holds: false,
        },
        atoms: ['rule_RC_CT3_BREACH_01', 'conclusion_holds'],
      },
    },
  ],
  reverify_list: ['FND-RC-CT3-BREACH-01'],
  nodes: [],
  edges: [],
}

export const MOCK_REVERIFY_LIST: ReverifyList = {
  findings: [
    {
      finding_id: 'FND-RC-CT3-BREACH-01',
      claim_id: 'C-REC-ASK',
      reason: 'STALE',
      reason_label: STATUS_LABELS.STALE,
      clause_ref: '9.2',
    },
    {
      finding_id: 'FND-CONFLICT-01',
      claim_id: 'C-CONFLICT',
      reason: 'CONFLICTING',
      reason_label: STATUS_LABELS.CONFLICTING,
      clause_ref: '10',
    },
  ],
}

export const MOCK_SCAN: ScanResult = {
  document_id: 'DOC-SCAN-01',
  clause: SCAN_CLAUSE,
  fact: SCAN_FACT,
}

export const MOCK_DICTATION: DictationResult = {
  fact_id: 'F-DICT-01',
  transcript: 'Nimbus keeps transfer logs for review.',
  trust_class: 'ai_inferred',
}

export async function fetchMockCounterfactual(
  _body: CounterfactualBody,
): Promise<CounterfactualResult> {
  return MOCK_COUNTERFACTUAL
}

export async function fetchMockReverifyList(_matterId: string): Promise<ReverifyList> {
  return MOCK_REVERIFY_LIST
}

export async function fetchMockScan(_body: ScanRequest): Promise<ScanResult> {
  return MOCK_SCAN
}

export async function fetchMockDictation(_body: DictationRequest): Promise<DictationResult> {
  return MOCK_DICTATION
}
