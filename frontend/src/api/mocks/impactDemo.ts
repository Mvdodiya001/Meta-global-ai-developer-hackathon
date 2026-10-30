import type {
  AuditTrail,
  Finding,
  GraphSlice,
  ImpactReport,
  SourceVersionList,
} from '../types'

const FINDING_IDS = [
  'FND-001',
  'FND-003',
  'FND-004',
  'FND-005',
  'FND-006',
  'FND-007',
  'FND-008',
  'FND-009',
] as const

const STALE_IDS = new Set(['FND-001', 'FND-003', 'FND-004'])

function findingNode(id: string, stale: boolean) {
  return {
    id,
    kind: 'finding',
    label: id,
    state: stale ? 'STALE' : null,
  }
}

/** Demo graph: 3 of 8 findings stale after the simulated DPDP Act v2 ingest. */
export const demoStaleGraph: GraphSlice = {
  nodes: [
    ...FINDING_IDS.map((id) => findingNode(id, STALE_IDS.has(id))),
    { id: 'RC-01', kind: 'rule_card', label: 'RC-01', state: null },
    { id: 'PRV-SEC-6-V1', kind: 'provision', label: 'Section 6', state: null },
  ],
  edges: [
    { src: 'FND-001', dst: 'RC-01', rel: 'DEPENDS_ON' },
    { src: 'FND-003', dst: 'RC-01', rel: 'DEPENDS_ON' },
    { src: 'FND-004', dst: 'RC-01', rel: 'DEPENDS_ON' },
    { src: 'RC-01', dst: 'PRV-SEC-6-V1', rel: 'DERIVED_FROM' },
  ],
}

export const demoCurrentGraph: GraphSlice = {
  nodes: demoStaleGraph.nodes.map((node) => ({ ...node, state: null })),
  edges: demoStaleGraph.edges,
}

export const demoImpact: ImpactReport = {
  id: 'IMP-01',
  source_version_id: 'SV-02',
  affected: [
    { claim_id: 'C-001', finding_id: 'FND-001', state: 'STALE' },
    { claim_id: 'C-003', finding_id: 'FND-003', state: 'STALE' },
    { claim_id: 'C-004', finding_id: 'FND-004', state: 'STALE' },
  ],
}

export const decoyImpact: ImpactReport = {
  id: 'IMP-DECOY',
  source_version_id: 'SV-DECOY-1',
  affected: [],
}

export const decoyVersions: SourceVersionList = {
  versions: [
    {
      id: 'SV-DECOY-1',
      source_id: 'SRC-DECOY',
      version_label: 'v1',
      published_on: '2024-06-01',
      effective_from: '2024-06-01',
      effective_until: null,
      content_sha256: 'stub-sha256-decoy',
      is_simulated: false,
      supersedes_id: null,
    },
  ],
}

export function afterFindingFrom(before: Finding): Finding {
  return {
    ...before,
    id: 'FND-002',
    version_no: 2,
    status: 'UNKNOWN',
    confidence_band: 'not computed',
    state: 'CURRENT',
    source_version_ids: ['SV-02'],
    supersedes_finding_id: before.id,
    run_id: 'RUN-02',
    created_at: '2026-10-28T10:12:00Z',
    proof: {
      ...before.proof,
      conclusion: 'unknown',
    },
  }
}

export function reverifyAudit(base: AuditTrail): AuditTrail {
  return {
    rows: [
      {
        id: 'AUD-03',
        ts: '2026-10-28T10:12:00Z',
        actor_type: 'system',
        actor_id: 'system',
        event: 'finding.superseded',
        object_type: 'finding',
        object_id: 'FND-001',
        details: { replacement: 'FND-002', source_version_id: 'SV-02' },
      },
      ...base.rows,
    ],
  }
}
