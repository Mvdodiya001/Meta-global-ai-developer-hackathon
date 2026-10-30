export type ChallengerObjection = {
  severity: 'blocking' | 'note'
  reason: string
  quote?: string
}

export type ChallengerReportView = {
  model: string
  blocking: boolean
  note: boolean
  objections: ChallengerObjection[]
}

/** Demo report aligned with the T6.1 recorded second pass (muse-spark-1.2). */
export const DEMO_CHALLENGER_REPORT: ChallengerReportView = {
  model: 'muse-spark-1.2',
  blocking: true,
  note: false,
  objections: [
    {
      severity: 'blocking',
      reason:
        'Cited premise text does not match the admitted fact statement, so the proof is not using an admitted premise.',
      quote: 'Clause 9.2 forbids all cross-border transfers.',
    },
    {
      severity: 'blocking',
      reason:
        'The conclude step does not follow from the cited steps. A second Muse Spark pass is a reviewer, not a replacement for the checker.',
      quote: "kind: conclude, conclusion: holds",
    },
  ],
}

export const EMPTY_CHALLENGER_REPORT: ChallengerReportView = {
  model: 'muse-spark-1.2',
  blocking: false,
  note: false,
  objections: [],
}

export function parseChallengerReport(
  raw: { [key: string]: unknown } | null | undefined,
): ChallengerReportView | null {
  if (raw == null) {
    return null
  }
  const objectionsRaw = raw.objections
  const objections: ChallengerObjection[] = Array.isArray(objectionsRaw)
    ? objectionsRaw.flatMap((item) => {
        if (typeof item !== 'object' || item == null) {
          return []
        }
        const row = item as { [key: string]: unknown }
        const severity = row.severity === 'note' ? 'note' : 'blocking'
        const reason = typeof row.reason === 'string' ? row.reason : ''
        if (!reason) {
          return []
        }
        const quote = typeof row.quote === 'string' ? row.quote : undefined
        return [{ severity, reason, quote }]
      })
    : []
  return {
    model: typeof raw.model === 'string' && raw.model ? raw.model : 'muse-spark-1.2',
    blocking: raw.blocking === true || objections.some((row) => row.severity === 'blocking'),
    note: raw.note === true || objections.some((row) => row.severity === 'note'),
    objections,
  }
}
