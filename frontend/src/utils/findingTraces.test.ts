import { describe, expect, it } from 'vitest'

import { mockData } from '../api/mocks'
import {
  buildPremiseTrace,
  buildSourceTrace,
  buildWhatWouldChange,
} from './findingTraces'

describe('findingTraces', () => {
  it('builds source rows from proof citations', () => {
    const rows = buildSourceTrace(mockData.finding)
    expect(rows.length).toBeGreaterThan(0)
    expect(rows[0]?.sourceVersionId).toBe('SV-01')
  })

  it('maps premise ids to fact statements', () => {
    const rows = buildPremiseTrace(mockData.finding, mockData.facts.facts)
    expect(rows).toHaveLength(2)
    expect(rows[0]?.factId).toBe('F-001')
  })

  it('lists sensitivity hints', () => {
    const hints = buildWhatWouldChange(mockData.finding, mockData.facts.facts)
    expect(hints.some((h) => h.label.includes('Amend'))).toBe(true)
  })
})
