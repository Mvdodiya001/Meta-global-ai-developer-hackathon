import { describe, expect, it, vi } from 'vitest'

import { api } from './client'
import { mocksEnabled } from './config'

describe('api client', () => {
  it('keeps openapi example mocks in test mode', async () => {
    expect(mocksEnabled()).toBe(true)
    const spy = vi.spyOn(globalThis, 'fetch')
    const matter = await api.matter('MAT-01')
    expect(matter.id).toBe('MAT-01')
    expect(spy).not.toHaveBeenCalled()
    spy.mockRestore()
  })
})
