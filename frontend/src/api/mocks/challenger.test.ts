import { describe, expect, it } from 'vitest'

import { parseChallengerReport } from './challenger'

describe('parseChallengerReport', () => {
  it('returns null for a missing report', () => {
    expect(parseChallengerReport(null)).toBeNull()
  })

  it('treats a blocking objection as blocking', () => {
    const report = parseChallengerReport({
      model: 'muse-spark-1.2',
      objections: [{ severity: 'blocking', reason: 'Premise mismatch.' }],
    })
    expect(report?.blocking).toBe(true)
    expect(report?.objections).toHaveLength(1)
  })
})
