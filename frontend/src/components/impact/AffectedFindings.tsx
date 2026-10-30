import type { ImpactReport } from '../../api/types'
import { StatusBadge } from '../badges/StatusBadge'

type AffectedFindingsProps = {
  impact: ImpactReport
  onReverify: () => void
  reverifying: boolean
  reverified: boolean
}

export function AffectedFindings({
  impact,
  onReverify,
  reverifying,
  reverified,
}: AffectedFindingsProps) {
  const staleCount = impact.affected.filter((row) => row.state === 'STALE').length

  return (
    <section className="ct-panel p-4" aria-labelledby="impact-heading">
      <h2 id="impact-heading" className="mb-3 ct-section-title">
        Affected findings
      </h2>
      {impact.affected.length === 0 ? (
        <p className="text-sm text-slate-600 dark:text-slate-400">
          No findings flagged. A decoy or unrelated source change does not mark dependents stale.
        </p>
      ) : (
        <ul className="space-y-2">
          {impact.affected.map((row) => (
            <li key={row.finding_id} className="flex flex-wrap items-center gap-2 text-sm">
              <span className="font-mono">{row.finding_id}</span>
              <span className="text-slate-500">claim {row.claim_id}</span>
              <StatusBadge status="FOLLOWS" state={row.state} />
            </li>
          ))}
        </ul>
      )}
      <button
        type="button"
        onClick={onReverify}
        disabled={staleCount === 0 || reverifying || reverified}
        className="mt-4 rounded-md bg-blue-800 px-4 py-2 text-sm font-medium text-white hover:bg-blue-900 disabled:opacity-50 dark:bg-blue-700"
      >
        {reverified ? 'Re-verified' : 'Re-verify'}
      </button>
    </section>
  )
}
