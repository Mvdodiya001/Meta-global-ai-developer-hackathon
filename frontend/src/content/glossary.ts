export const STATUS_LABELS: Record<string, string> = {
  FOLLOWS: 'Meets the requirement — on the facts and law listed below',
  RULED_OUT: 'Does not meet the requirement, on the material listed',
  UNKNOWN: 'Cannot be determined from the available material',
  REQUIRES_REVIEW: 'Needs your review before it can be relied on',
  CONFLICTING: 'Two readings of the law conflict — your call',
  STALE: 'Needs re-check: the law it relied on has changed',
  SUPERSEDED: 'Replaced by a later answer',
}

export const TRUST_LABELS = {
  lawyer_confirmed: 'Confirmed by you',
  document_extracted: 'Taken from the document',
  ai_inferred: 'Proposed — not yet approved by you',
  disputed: 'Disputed by you',
} as const

export const SECOND_REVIEW_BLOCKING =
  'A second review flagged this — needs your review'

export const FACT_MISMATCH = 'This fact no longer matches the document'

export const PREVIEW_LAW_CHANGE = 'Preview a law change — nothing is saved'

export const ANSWER_WOULD_NOT_FOLLOW = 'This answer would no longer follow'

export const WOULD_STILL_FOLLOW = 'Would still meet the requirement'
