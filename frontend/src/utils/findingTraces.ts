import type { Fact, Finding } from '../api/types'

export type SourceTraceRow = {
  id: string
  sourceVersionId: string
  provisionId: string
  span: string
  sha256: string
}

export function buildSourceTrace(finding: Finding): SourceTraceRow[] {
  const rows: SourceTraceRow[] = []
  for (const step of finding.proof.steps) {
    if (step.citation) {
      rows.push({
        id: `${step.rule_card_id ?? 'step'}-${rows.length}`,
        sourceVersionId: step.citation.source_version_id,
        provisionId: step.citation.provision_id,
        span: step.citation.span.join('–'),
        sha256: step.citation.sha256.slice(0, 12),
      })
    }
  }
  for (const versionId of finding.source_version_ids) {
    if (!rows.some((row) => row.sourceVersionId === versionId)) {
      rows.push({
        id: `sv-${versionId}`,
        sourceVersionId: versionId,
        provisionId: '—',
        span: '—',
        sha256: '—',
      })
    }
  }
  return rows
}

export type PremiseTraceRow = {
  factId: string
  statement: string
  trustClass: string
  inProof: boolean
}

export function buildPremiseTrace(finding: Finding, facts: Fact[]): PremiseTraceRow[] {
  const byId = new Map(facts.map((fact) => [fact.id, fact]))
  return finding.premise_ids.map((factId) => {
    const fact = byId.get(factId)
    return {
      factId,
      statement: fact?.statement ?? 'Premise text unavailable in mock.',
      trustClass: fact?.trust_class ?? 'unknown',
      inProof: finding.proof.premises.some((p) => p.fact_id === factId),
    }
  })
}

export type SensitivityHint = {
  id: string
  label: string
  detail: string
}

export function buildWhatWouldChange(finding: Finding, facts: Fact[]): SensitivityHint[] {
  const hints: SensitivityHint[] = []
  for (const premise of finding.proof.premises) {
    if (premise.trust_class !== 'lawyer_confirmed') {
      hints.push({
        id: `premise-${premise.fact_id}`,
        label: `Challenge ${premise.fact_id}`,
        detail:
          'If this premise were disputed or downgraded, the checker may reject the proof or the finding may move to REQUIRES_REVIEW.',
      })
    }
  }
  hints.push({
    id: 'source-version',
    label: 'Amend the cited source version',
    detail:
      'A new source version that changes Section 6 would mark this finding stale until the agent runs a fresh lookup_source.',
  })
  hints.push({
    id: 'as-of',
    label: 'Move the as-of date',
    detail: `In-force checks use as-of ${finding.as_of}; an earlier date may fail commencement gates.`,
  })
  const disputed = facts.filter((f) => f.trust_class === 'disputed')
  if (disputed.length === 0) {
    hints.push({
      id: 'unknown-premise',
      label: 'Add an unverified premise',
      detail:
        'Introducing ai_inferred or disputed premises without lawyer confirmation blocks a FOLLOWS conclusion.',
    })
  }
  return hints
}
