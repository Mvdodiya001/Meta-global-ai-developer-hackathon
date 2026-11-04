import type { Finding } from '../../api/types'
import { FindingCard } from '../FindingCard'
import { StatusBadge } from '../badges/StatusBadge'
import { IllustrationLabel } from './IllustrationLabel'

type AsOfPanelProps = {
  asOf: string
  commencement: string
  finding: Finding | null
  disabled?: boolean
  onAsOfChange: (value: string) => void
}

export function AsOfPanel({
  asOf,
  commencement,
  finding,
  disabled = false,
  onAsOfChange,
}: AsOfPanelProps) {
  const inForce = asOf >= commencement

  return (
    <section className="ct-panel" aria-labelledby="asof-heading">
      <div className="ct-panel-head">
        <div>
          <h2 id="asof-heading" className="ct-panel-title">
            Law version date
          </h2>
          <p className="ct-panel-desc">
            Move the date across commencement to see whether the section is in force.
          </p>
        </div>
      </div>
      <div className="ct-panel-body space-y-3">
        <div className="flex flex-wrap items-end gap-4">
          <div className="ct-field">
            <label htmlFor="as-of" className="ct-label">
              As-of date
            </label>
            <input
              id="as-of"
              type="date"
              value={asOf}
              disabled={disabled}
              onChange={(event) => onAsOfChange(event.target.value)}
              className="ct-input w-auto"
            />
          </div>
          <p className="text-xs text-ct-muted">Commencement {commencement}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-sm text-ct-soft">
            Section 6 is {inForce ? 'in force' : 'not in force'} on {asOf}.
          </p>
          <StatusBadge status={inForce ? 'FOLLOWS' : 'UNKNOWN'} />
        </div>
        {finding && asOf < commencement ? (
          <div className="space-y-2 pt-1">
            <IllustrationLabel />
            <FindingCard finding={finding} title="Answer as of this date" />
          </div>
        ) : null}
      </div>
    </section>
  )
}
