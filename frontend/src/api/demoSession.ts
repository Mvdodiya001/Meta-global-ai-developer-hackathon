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
