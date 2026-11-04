import type { FactLine, Finding, TrustClass } from '../api/types'
import {
  ANSWER_WOULD_NOT_FOLLOW,
  STATUS_LABELS,
  TRUST_LABELS,
  WOULD_STILL_FOLLOW,
} from '../content/glossary'
import { isLawyerSafeText } from './lawyerCopy'
import { asTrustClass } from './trustClass'

const CITED_CLAUSE = 'A cited clause'
const CITED_SECTION = 'A cited section of the law'
const LAW_VERSION = 'Law version'
const ANSWER_RELIED = 'An answer that relied on this section'
const ANSWER_NEEDS_RECHECK = 'An answer that needs re-check'

export type DisplayFactLine = {
  label: string
  trustLabel: string
  trustClass: TrustClass
  confirmedBy: string | null
  proposed: boolean
}

function safe(text: string | null | undefined, fallback: string): string {
  const trimmed = text?.trim() ?? ''
  if (trimmed && isLawyerSafeText(trimmed)) {
    return trimmed
  }
  return fallback
}

export function trustClassFromLabel(label: string): TrustClass {
  const match = (Object.entries(TRUST_LABELS) as [TrustClass, string][]).find(
    ([, value]) => value === label,
  )
  return match?.[0] ?? 'document_extracted'
}

export function displayStatusLabel(
  status: string,
  label?: string | null,
  state?: string | null,
): string {
  const key = state === 'STALE' || state === 'SUPERSEDED' ? state : status
  // A superseded answer keeps its old status label in the record, but the
  // label must not imply it is still the current answer.
  if (state === 'SUPERSEDED') {
    return STATUS_LABELS.SUPERSEDED
  }
  return safe(label, STATUS_LABELS[key] ?? STATUS_LABELS.REQUIRES_REVIEW)
}

export function displayClauseQuote(finding: Finding): string {
  return safe(finding.clause_quote, CITED_CLAUSE)
}

export function displaySectionQuote(finding: Finding): string {
  return safe(finding.section_quote, CITED_SECTION)
}

export function displaySectionLabel(finding: Finding): string {
  return safe(finding.section_label, '')
}

export function displayLawVersionLabel(finding: Finding): string {
  return safe(finding.law_version_label, LAW_VERSION)
}

export function displayLawVersionDate(finding: Finding): string {
  return safe(finding.law_version_date, finding.as_of)
}

export function displayClauseRef(
  ref?: string | null,
  fallback: string = ANSWER_RELIED,
): string {
  const trimmed = ref?.trim() ?? ''
  if (!trimmed || !isLawyerSafeText(trimmed)) {
    return fallback
  }
  if (/^clause\b/i.test(trimmed)) {
    return trimmed
  }
  return `Clause ${trimmed}`
}

export function displayAnswerCaption(finding: Finding): string {
  if (finding.clause_ref?.trim()) {
    return displayClauseRef(finding.clause_ref)
  }
  return safe(finding.clause_quote, ANSWER_RELIED)
}

export function displayReasonLabel(reason: string, label?: string | null): string {
  return safe(label, STATUS_LABELS[reason] ?? STATUS_LABELS.STALE)
}

export function displayWouldFollow(row: {
  would_remain_valid: boolean
  would_follow_label?: string | null
}): string {
  const fallback = row.would_remain_valid ? WOULD_STILL_FOLLOW : ANSWER_WOULD_NOT_FOLLOW
  return safe(row.would_follow_label, fallback)
}

export function displayRecheckCaption(ref?: string | null): string {
  return displayClauseRef(ref, ANSWER_NEEDS_RECHECK)
}

function lineFromPremise(
  statement: string,
  trustClass: string,
  confirmedBy: string | null,
): DisplayFactLine {
  const trust = asTrustClass(trustClass)
  return {
    label: statement,
    trustClass: trust,
    trustLabel: TRUST_LABELS[trust],
    confirmedBy,
    proposed: trust === 'ai_inferred',
  }
}

export function displayFactLines(finding: Finding): DisplayFactLine[] {
  const fromApi: DisplayFactLine[] = (finding.fact_lines ?? []).map((line: FactLine) => {
    const trust = trustClassFromLabel(line.trust_label)
    const confirmed =
      line.confirmed_by && isLawyerSafeText(line.confirmed_by) ? line.confirmed_by : null
    return {
      label: safe(line.label, 'A listed fact'),
      trustClass: trust,
      trustLabel: safe(line.trust_label, TRUST_LABELS[trust]),
      confirmedBy: confirmed,
      proposed: trust === 'ai_inferred',
    }
  })
  const lines =
    fromApi.length > 0
      ? fromApi
      : finding.proof.premises.map((premise) =>
          lineFromPremise(premise.statement, premise.trust_class, null),
        )
  return [...lines].sort((a, b) => Number(a.proposed) - Number(b.proposed))
}

export function displayTrustLabel(trustClass: TrustClass, label?: string | null): string {
  return safe(label, TRUST_LABELS[trustClass])
}
