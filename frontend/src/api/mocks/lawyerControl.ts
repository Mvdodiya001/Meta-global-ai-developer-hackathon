import type { Fact, FactAction, Finding, Proof, ProofVerifyResult } from '../types'

export const COMMENCEMENT_DATE = '2025-10-01'

export const UNKNOWN_QUESTION =
  'Does this clause require a fairness opinion from an unrelated telecom circular?'

export function approveFact(fact: Fact): FactAction {
  return {
    fact_id: fact.id,
    trust_class: 'lawyer_confirmed',
    supersedes_id: fact.id,
  }
}

export function challengeFact(fact: Fact): FactAction {
  return {
    fact_id: fact.id,
    trust_class: 'disputed',
    supersedes_id: fact.id,
  }
}

export function applyFactAction(facts: Fact[], action: FactAction): Fact[] {
  return facts.map((fact) =>
    fact.id === action.fact_id || fact.id === action.supersedes_id
      ? { ...fact, trust_class: action.trust_class, origin: 'lawyer' }
      : fact,
  )
}

export function unknownFinding(): Finding {
  return {
    id: 'FND-UNK',
    claim_id: 'C-UNK',
    version_no: 1,
    status: 'UNKNOWN',
    confidence_band: 'not computed',
    as_of: COMMENCEMENT_DATE,
    source_version_ids: [],
    premise_ids: [],
    rule_card_ids: [],
    checker_report: null,
    challenger_report: null,
    run_id: 'RUN-UNK',
    created_at: '2026-10-30T12:00:00Z',
    supersedes_finding_id: null,
    state: 'CURRENT',
    ai_draft_label: 'AI draft — not yet reviewed',
    proof: {
      as_of: COMMENCEMENT_DATE,
      claim_id: 'C-UNK',
      conclusion: 'unknown',
      premises: [],
      steps: [],
    },
  }
}

export function asOfFinding(base: Finding, asOf: string): Finding {
  const inForce = asOf >= COMMENCEMENT_DATE
  return {
    ...base,
    id: 'FND-ASOF',
    as_of: asOf,
    status: inForce ? 'FOLLOWS' : 'UNKNOWN',
    confidence_band: inForce ? base.confidence_band : 'not computed',
    checker_report: inForce ? base.checker_report : null,
    proof: {
      ...base.proof,
      as_of: asOf,
      conclusion: inForce ? base.proof.conclusion : 'unknown',
    },
  }
}

export function challengedFinding(base: Finding): Finding {
  return {
    ...base,
    status: 'UNKNOWN',
    confidence_band: 'not computed',
    checker_report: null,
    proof: { ...base.proof, conclusion: 'unknown' },
  }
}

export function verifyProof(original: Proof, candidate: Proof): ProofVerifyResult {
  const originalText = original.premises.map((p) => p.statement).join('\n')
  const candidateText = candidate.premises?.map((p) => p.statement).join('\n') ?? ''
  if (candidateText !== originalText) {
    return {
      valid: false,
      cited_source_versions: original.steps
        .map((step) => step.citation?.source_version_id)
        .filter((id): id is string => Boolean(id)),
      errors: [
        {
          step: 0,
          code: 'PREMISE_MISMATCH',
          message: 'Edited premise text does not match the stored fact.',
        },
      ],
    }
  }
  return {
    valid: true,
    errors: [],
    cited_source_versions: ['SV-01'],
  }
}
