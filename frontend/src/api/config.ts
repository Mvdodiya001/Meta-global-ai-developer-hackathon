const apiBase = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

/** Base URL for ClauseTrace REST API (use API_STUB=1 on backend during development). */
export function getApiBase(): string {
  return apiBase.replace(/\/$/, '')
}
