import type { Fact, Finding } from '../api/types'

export type SourceTraceRow = {
  id: string
  sourceVersionId: string
  provisionId: string
  span: string
  sha256: string
  quote: string | null
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
        quote: step.quote ?? null,
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
        quote: null,
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
      statement: fact?.statement ?? 'This fact is not on the list yet.',
      trustClass: fact?.trust_class ?? 'ai_inferred',
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
        label: 'If you dispute a listed fact',
        detail:
          'The answer may need your review before it can be relied on.',
      })
    }
  }
  hints.push({
    id: 'source-version',
    label: 'If the cited law is amended',
    detail: 'This answer would need a re-check against the new wording.',
  })
  hints.push({
    id: 'as-of',
    label: 'If you move the law version date',
    detail: `In-force reading uses ${finding.as_of}. An earlier date may put the section out of force.`,
  })
  const disputed = facts.filter((f) => f.trust_class === 'disputed')
  if (disputed.length === 0) {
    hints.push({
      id: 'unknown-premise',
      label: 'If you add a fact you have not confirmed',
      detail: 'A proposed fact is not relied on until you approve it.',
    })
  }
  return hints
}
