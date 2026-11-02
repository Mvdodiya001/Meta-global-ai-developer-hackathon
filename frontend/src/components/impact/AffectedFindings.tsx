import { displayClauseRef, displayStatusLabel } from '../../utils/displayFields'
import { StatusBadge } from '../badges/StatusBadge'

export type RecheckRow = {
  key: string
  clauseRef: string
  state: string | null
  statusLabel?: string | null
}

type AffectedFindingsProps = {
  rows: RecheckRow[]
  onRecheck: () => void
  rechecking: boolean
  rechecked: boolean
}

export function AffectedFindings({
  rows,
  onRecheck,
  rechecking,
  rechecked,
}: AffectedFindingsProps) {
  const staleCount = rows.filter((row) => row.state === 'STALE').length

  return (
    <section className="ct-panel p-4" aria-labelledby="impact-heading">
      <h2 id="impact-heading" className="mb-3 ct-section-title">
        Re-check queue
      </h2>
      {rows.length === 0 ? (
        <p className="text-sm text-slate-600 dark:text-slate-400">
          No answers need re-check for this law change.
        </p>
      ) : (
        <ul className="space-y-2">
          {rows.map((row) => (
            <li key={row.key} className="flex flex-wrap items-center gap-2 text-sm">
              <span>{displayClauseRef(row.clauseRef)}</span>
              <StatusBadge
                status="FOLLOWS"
                state={row.state}
                label={displayStatusLabel('FOLLOWS', row.statusLabel, row.state)}
              />
            </li>
          ))}
        </ul>
      )}
      <button
        type="button"
        onClick={onRecheck}
        disabled={staleCount === 0 || rechecking || rechecked}
        className="mt-4 rounded-md bg-blue-800 px-4 py-2 text-sm font-medium text-white hover:bg-blue-900 disabled:opacity-50 dark:bg-blue-700"
      >
        {rechecked ? 'Re-checked' : 'Re-check'}
      </button>
    </section>
  )
}
