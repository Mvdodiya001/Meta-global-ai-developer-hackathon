import type { ReverifyList } from '../../api/types'
import { displayReasonLabel, displayRecheckCaption } from '../../utils/displayFields'
import { StatusBadge } from '../badges/StatusBadge'

type ReverifyListPanelProps = {
  list: ReverifyList | null
  error: string | null
}

export function ReverifyListPanel({ list, error }: ReverifyListPanelProps) {
  return (
    <section className="ct-panel" aria-labelledby="reverify-list-heading">
      <div className="ct-panel-head">
        <div>
          <h2 id="reverify-list-heading" className="ct-panel-title">
            Waiting for a fresh decision
          </h2>
          <p className="ct-panel-desc">
            These answers already knew their source had changed.
          </p>
        </div>
        {list ? <span className="ct-badge">{list.findings.length}</span> : null}
      </div>
      <div className="ct-panel-body">
        {error ? (
          <p role="alert" className="ct-notice ct-notice--danger">
            {error}
          </p>
        ) : null}
        {list && list.findings.length === 0 ? (
          <p className="ct-empty">Nothing is waiting for a fresh decision.</p>
        ) : null}
        {list && list.findings.length > 0 ? (
          <ul className="ct-rows">
            {list.findings.map((row, index) => (
              <li
                key={`${row.reason}-${index}`}
                className="flex flex-wrap items-center gap-2 text-sm"
              >
                <span className="font-medium text-ct-ink">
                  {displayRecheckCaption(row.clause_ref)}
                </span>
                <StatusBadge
                  status={row.reason}
                  label={displayReasonLabel(row.reason, row.reason_label)}
                />
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </section>
  )
}
