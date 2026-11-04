const CLAIM_KEY = 'clausetrace.claim_id'

/** Persist the claim created on Screen 1 for later screens. */
export function rememberClaimId(claimId: string): void {
  sessionStorage.setItem(CLAIM_KEY, claimId)
}

/** Claim id from the last Screen 1 verification, if any. */
export function lastClaimId(): string | null {
  return sessionStorage.getItem(CLAIM_KEY)
}

export function clearClaimId(): void {
  sessionStorage.removeItem(CLAIM_KEY)
}

const MATTER_KEY = 'clausetrace.matter_id'

/** Persist the matter selected in the sidebar for every screen. */
export function rememberMatterId(matterId: string): void {
  sessionStorage.setItem(MATTER_KEY, matterId)
}

/** Matter id selected in this session, if any. */
export function lastMatterId(): string | null {
  return sessionStorage.getItem(MATTER_KEY)
}

export function clearMatterId(): void {
  sessionStorage.removeItem(MATTER_KEY)
}

/**
 * The working matter: the sidebar selection when it is in the visible
 * list, else the first visible matter (the seeded demo by default).
 */
export function preferredMatterId(ids: string[]): string | null {
  const remembered = lastMatterId()
  if (remembered && ids.includes(remembered)) {
    return remembered
  }
  return ids[0] ?? null
}

/** Selected matter id, falling back to the seeded demo matter. */
export function currentMatterId(): string {
  return lastMatterId() ?? 'MAT-01'
}

const DOCUMENT_KEY = 'clausetrace.document_id'

/** Persist the document the lawyer uploaded so every screen works on it. */
export function rememberDocumentId(documentId: string): void {
  sessionStorage.setItem(DOCUMENT_KEY, documentId)
}

/** Document id from the last upload in this session, if any. */
export function lastDocumentId(): string | null {
  return sessionStorage.getItem(DOCUMENT_KEY)
}

export function clearDocumentId(): void {
  sessionStorage.removeItem(DOCUMENT_KEY)
}

/**
 * The working document for this session: the uploaded one when it is in
 * the matter's document list, else the first (seeded) document.
 */
export function preferredDocumentId(ids: string[]): string | null {
  const remembered = lastDocumentId()
  if (remembered && ids.includes(remembered)) {
    return remembered
  }
  return ids[0] ?? null
}
