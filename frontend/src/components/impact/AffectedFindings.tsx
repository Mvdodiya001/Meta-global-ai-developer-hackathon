import { displayClauseRef, displayStatusLabel } from '../../utils/displayFields'
import { IconRefresh } from '../ui/Icons'
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

/** Simple structured list: one row per answer with a single re-check action. */
export function AffectedFindings({
  rows,
  onRecheck,
  rechecking,
  rechecked,
}: AffectedFindingsProps) {
  const staleCount = rows.filter((row) => row.state === 'STALE').length

  return (
    <section className="ct-panel" aria-labelledby="impact-heading">
      <div className="ct-panel-head">
        <div>
          <h2 id="impact-heading" className="ct-panel-title">
            Answers to re-check
          </h2>
          <p className="ct-panel-desc">
            Re-checking drafts a new answer against the current law. The earlier answer stays
            on file.
          </p>
        </div>
        <span className="ct-badge">{staleCount} waiting</span>
      </div>
      <div className="ct-panel-body">
        {rows.length === 0 ? (
          <p className="ct-empty">No answers need re-check for this law change.</p>
        ) : (
          <ul className="ct-rows">
            {rows.map((row) => (
              <li
                key={row.key}
                className="flex flex-wrap items-center gap-x-3 gap-y-1.5 text-sm"
              >
                <span className="font-medium text-ct-ink">
                  {displayClauseRef(row.clauseRef)}
                </span>
                <StatusBadge
                  status="FOLLOWS"
                  state={row.state}
                  label={displayStatusLabel('FOLLOWS', row.statusLabel, row.state)}
                />
              </li>
            ))}
          </ul>
        )}
        <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-ct-line pt-4">
          <button
            type="button"
            onClick={onRecheck}
            disabled={staleCount === 0 || rechecking || rechecked}
            className="ct-btn ct-btn--primary"
          >
            {rechecked ? (
              'Re-checked'
            ) : rechecking ? (
              <>
                <span className="ct-spinner" aria-hidden="true" />
                Re-checking…
              </>
            ) : (
              <>
                <IconRefresh size={15} />
                Re-check
              </>
            )}
          </button>
          {rechecked ? (
            <span className="text-xs text-ct-muted">
              The new answer is shown under Before / after.
            </span>
          ) : null}
        </div>
      </div>
    </section>
  )
}
