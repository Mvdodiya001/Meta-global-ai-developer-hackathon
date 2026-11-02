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
    <section className="ct-panel space-y-3 p-4" aria-labelledby="asof-heading">
      <h2 id="asof-heading" className="ct-section-title">
        Law version date
      </h2>
      <div className="flex flex-wrap items-end gap-4">
        <div>
          <label htmlFor="as-of" className="mb-1 block text-sm font-medium">
            As-of date
          </label>
          <input
            id="as-of"
            type="date"
            value={asOf}
            disabled={disabled}
            onChange={(event) => onAsOfChange(event.target.value)}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900"
          />
        </div>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Commencement {commencement}. Move the date across it to see whether the section is in force.
        </p>
      </div>
      <p className="text-sm">
        Section 6 is {inForce ? 'in force' : 'not in force'} on {asOf}.
      </p>
      <StatusBadge status={inForce ? 'FOLLOWS' : 'UNKNOWN'} />
      {finding && asOf < commencement ? (
        <>
          <IllustrationLabel />
          <FindingCard finding={finding} title="Answer as of this date" />
        </>
      ) : null}
    </section>
  )
}
