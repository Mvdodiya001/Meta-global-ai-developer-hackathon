import type { ReverifyList } from '../../api/types'
import { displayReasonLabel, displayRecheckCaption } from '../../utils/displayFields'
import { StatusBadge } from '../badges/StatusBadge'

type ReverifyListPanelProps = {
  list: ReverifyList | null
  error: string | null
}

export function ReverifyListPanel({ list, error }: ReverifyListPanelProps) {
  return (
    <section className="ct-panel space-y-3 p-4" aria-labelledby="reverify-list-heading">
      <h2 id="reverify-list-heading" className="ct-section-title">
        Re-check queue
      </h2>
      {error ? (
        <p role="alert" className="text-sm font-medium text-rose-800 dark:text-rose-200">
          {error}
        </p>
      ) : null}
      {list && list.findings.length === 0 ? (
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Nothing is waiting for a fresh decision.
        </p>
      ) : null}
      {list && list.findings.length > 0 ? (
        <ul className="space-y-2">
          {list.findings.map((row, index) => (
            <li
              key={`${row.reason}-${index}`}
              className="flex flex-wrap items-center gap-2 text-sm"
            >
              <span>{displayRecheckCaption(row.clause_ref)}</span>
              <StatusBadge
                status={row.reason}
                label={displayReasonLabel(row.reason, row.reason_label)}
              />
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  )
}
