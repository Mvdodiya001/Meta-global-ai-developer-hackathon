import type { Finding } from '../../api/types'
import { displayFactLines } from '../../utils/displayFields'
import { TrustChip } from '../TrustChip'

type PremiseTraceProps = {
  finding: Finding
}

export function PremiseTrace({ finding }: PremiseTraceProps) {
  const lines = displayFactLines(finding)

  return (
    <section className="ct-panel p-4" aria-labelledby="premise-trace-heading">
      <h2 id="premise-trace-heading" className="mb-3 ct-section-title">
        Facts
      </h2>
      <ul className="space-y-2">
        {lines.map((line, index) => (
          <li
            key={`${line.label}-${index}`}
            aria-label={line.label}
            className="rounded-md border border-slate-200 p-3 dark:border-slate-700"
          >
            <div className="mb-1 flex flex-wrap items-center gap-2">
              <TrustChip trustClass={line.trustClass} label={line.trustLabel} />
              {line.proposed ? (
                <span className="text-xs text-slate-500">Not relied on</span>
              ) : null}
            </div>
            <p className="text-sm">{line.label}</p>
            {line.confirmedBy ? (
              <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">
                Confirmed by {line.confirmedBy}
              </p>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  )
}
