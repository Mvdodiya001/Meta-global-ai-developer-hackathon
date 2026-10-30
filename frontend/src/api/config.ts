const apiBase = import.meta.env.VITE_API_BASE ?? ''

/** Seeded demo matter (`scripts/seed_demo.py`). */
export const DEMO_MATTER_ID = 'MAT-01'

/** Seeded demo document id (not a document-version id). */
export const DEMO_DOCUMENT_ID = 'DOC-01'

/** Default legal source for Screen 2. */
export const DEMO_SOURCE_ID = 'SRC-DPDP-ACT'

/** Base URL for ClauseTrace REST API. Empty uses the Vite `/api` proxy in `npm run dev`. */
export function getApiBase(): string {
  return apiBase.replace(/\/$/, '')
}

/**
 * Demo and production talk to the real v1 API.
 * Bundled `openapi/examples` mocks stay for Vitest (`MODE=test`) or `VITE_USE_MOCKS=1`.
 */
export function mocksEnabled(): boolean {
  return import.meta.env.MODE === 'test' || import.meta.env.VITE_USE_MOCKS === '1'
}
