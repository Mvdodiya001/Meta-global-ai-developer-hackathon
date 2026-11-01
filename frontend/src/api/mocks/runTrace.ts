import type { ToolCall } from '../types'

/** Demo tool trace aligned with DEMO_AND_SUBMISSION.md (mock layer; v0 example has 2 events). */
export const DEMO_RUN_EVENTS: ToolCall[] = [
  {
    seq: 1,
    tool: 'lookup_source',
    args: { source_id: 'SRC-DPDP-ACT', as_of: '2025-10-01' },
    result: { source_version_id: 'SV-01', version_label: 'v1' },
    ok: true,
  },
  {
    seq: 2,
    tool: 'get_premise',
    args: { fact_id: 'F-001' },
    result: { fact_id: 'F-001', trust_class: 'document_extracted' },
    ok: true,
  },
  {
    seq: 3,
    tool: 'get_premise',
    args: { fact_id: 'F-002' },
    result: { fact_id: 'F-002', trust_class: 'lawyer_confirmed' },
    ok: true,
  },
  {
    seq: 4,
    tool: 'verify_derivation',
    args: { claim_id: 'C-001' },
    result: { valid: true },
    ok: true,
  },
  {
    seq: 5,
    tool: 'propose_finding',
    args: { claim_id: 'C-001', status: 'FOLLOWS' },
    result: { finding_id: 'FND-001' },
    ok: true,
  },
]

export const DEFAULT_VERIFY_QUESTION =
  'Does clause 9.2 require Nimbus to keep transfer logs?'

/** Recorded replay dates. Default is the canonical ask-flow cassette. */
export const DEFAULT_AS_OF = '2026-11-20'
export const SECONDARY_AS_OF = '2025-10-17'
export const DEMO_AS_OF_OPTIONS = [DEFAULT_AS_OF, SECONDARY_AS_OF] as const
