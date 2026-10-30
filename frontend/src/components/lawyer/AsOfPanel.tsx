import type { Finding } from '../../api/types'
import { FindingCard } from '../FindingCard'
import { StatusBadge } from '../badges/StatusBadge'

type AsOfPanelProps = {
  asOf: string
  commencement: string
  finding: Finding | null
  onAsOfChange: (value: string) => void
}

export function AsOfPanel({ asOf, commencement, finding, onAsOfChange }: AsOfPanelProps) {
  const inForce = asOf >= commencement

  return (
    <section className="ct-panel space-y-3 p-4" aria-labelledby="asof-heading">
      <h2 id="asof-heading" className="ct-section-title">
        As-of applicability
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
            onChange={(event) => onAsOfChange(event.target.value)}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900"
          />
        </div>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Commencement {commencement}. Move the date across it to flip in-force.
        </p>
      </div>
      <p className="text-sm">
        Section 6 is {inForce ? 'in force' : 'not in force'} on {asOf}.
      </p>
      <StatusBadge status={inForce ? 'FOLLOWS' : 'UNKNOWN'} />
      {finding && asOf < commencement ? <FindingCard finding={finding} /> : null}
    </section>
  )
}
