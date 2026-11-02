const FORBIDDEN: RegExp[] = [
  /\bFND-/,
  /\bC-[A-Z0-9]/,
  /\bCL-/,
  /\bSV-/,
  /\bRC-/,
  /\bIMP-/,
  /\bMAT-/,
  /\bDOC-/,
  /sha256/i,
  /\bhash\b/i,
  /\bJSON\b/i,
  /\{/,
  /\bcassette\b/i,
  /\breplay\b/i,
  /\bmode\b/i,
  /\b502\b/,
  /MODEL_/,
  /lookup_source/,
  /get_premise/,
  /verify_derivation/,
  /propose_finding/,
  /list_dependent_claims/,
  /request_lawyer_review/,
  /six bounded tools/i,
  /Proof JSON/i,
  /\bchecker\b/i,
  /\bAPI\b/,
]

const FALLBACK = 'This request could not be completed. Try again.'

export function isLawyerSafeText(text: string): boolean {
  return !FORBIDDEN.some((pattern) => pattern.test(text))
}

export function lawyerError(err: unknown): string {
  const raw = err instanceof Error ? err.message : FALLBACK
  return isLawyerSafeText(raw) ? raw : FALLBACK
}

export function plainWords(value: unknown): string | null {
  if (typeof value !== 'string') {
    return null
  }
  const trimmed = value.trim()
  if (!trimmed || !isLawyerSafeText(trimmed) || /_/.test(trimmed)) {
    return null
  }
  return trimmed
}

export function sectionWording(key: string, text?: string | null): string {
  if (text && isLawyerSafeText(text)) {
    return text
  }
  const match = key.match(/s(\d+(?:\([^)]+\))?)/i)
  if (match) {
    return `Section ${match[1]}`
  }
  return 'A cited section'
}

export function answerWording(statement: string | null | undefined): string {
  if (statement && isLawyerSafeText(statement)) {
    return statement
  }
  return 'An answer that relied on this section'
}
