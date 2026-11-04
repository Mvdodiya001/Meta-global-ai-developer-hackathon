import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('./config', () => ({
  DEMO_MATTER_ID: 'MAT-01',
  DEMO_DOCUMENT_ID: 'DOC-01',
  DEMO_SOURCE_ID: 'SRC-DPDP-ACT',
  getApiBase: () => '',
  mocksEnabled: () => false,
}))

import { api, clearApiCache, storeToken } from './client'

type FetchCall = [string, RequestInit | undefined]
const calls: FetchCall[] = []

function installFetch() {
  calls.length = 0
  const impl = async (url: string, init?: RequestInit) => {
    calls.push([url, init])
    const payload = url.includes('/api/sources') ? { sources: [] } : { matters: [] }
    return {
      ok: true,
      status: 200,
      json: async () => payload,
    } as Response
  }
  vi.stubGlobal('fetch', vi.fn(impl))
}

const getCount = (path: string) =>
  calls.filter(([url, init]) => url === path && init?.method !== 'POST').length

describe('api read cache', () => {
  beforeEach(() => {
    installFetch()
    window.sessionStorage.clear()
    window.localStorage.clear()
    clearApiCache()
  })

  it('serves repeated reads from cache instead of refetching', async () => {
    await api.matters()
    await api.matters()
    expect(getCount('/api/matters')).toBe(1)
  })

  it('dedupes concurrent identical reads into one fetch', async () => {
    await Promise.all([api.matters(), api.matters(), api.matters()])
    expect(getCount('/api/matters')).toBe(1)
  })

  it('clears cached reads after a successful mutation', async () => {
    await api.matters()
    await api.createMatter({ title: 'New', client_name: 'Client' })
    await api.matters()
    expect(getCount('/api/matters')).toBe(2)
  })

  it('clears cached reads when the signed-in user changes', async () => {
    await api.matters()
    storeToken('token-for-another-user')
    await api.matters()
    expect(getCount('/api/matters')).toBe(2)
  })

  it('persists static law reads to sessionStorage for reloads', async () => {
    await api.sources()
    expect(window.sessionStorage.getItem('ct-cache:/api/sources')).not.toBeNull()
    expect(window.sessionStorage.getItem('ct-cache:/api/matters')).toBeNull()
    await api.sources()
    expect(getCount('/api/sources')).toBe(1)
  })
})
