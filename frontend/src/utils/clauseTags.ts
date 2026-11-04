import type { Clause } from '../api/types'

const RULES: [RegExp, string][] = [
  [/transfer|outside india|cross-border/i, 'Cross-border'],
  [/breach|intimat/i, 'Breach notice'],
  [/retain|retention|erase|erasure|delet/i, 'Retention & erasure'],
  [/encrypt|security|safeguard|access control/i, 'Security'],
  [/consent/i, 'Consent'],
  [/purpose|only for|scope of processing/i, 'Purpose'],
  [/sub-?processor/i, 'Sub-processors'],
  [/audit|logs?\b/i, 'Audit & logs'],
  [/children|child/i, 'Children'],
  [/grievance|complaint/i, 'Grievance'],
]

/** Deterministic taxonomy tags from clause heading + text (Phase 1). */
export function clauseTags(clause: Clause): string[] {
  const haystack = `${clause.heading} ${clause.text}`
  const tags: string[] = []
  for (const [pattern, tag] of RULES) {
    if (pattern.test(haystack) && !tags.includes(tag)) {
      tags.push(tag)
    }
    if (tags.length >= 2) {
      break
    }
  }
  return tags
}
