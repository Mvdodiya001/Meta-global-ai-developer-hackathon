import type { TrustClass } from '../../api/types'
import { TrustChip } from '../TrustChip'
import type { PremiseTraceRow } from '../../lib/findingTraces'

type PremiseTraceProps = {
  rows: PremiseTraceRow[]
}

export function PremiseTrace({ rows }: PremiseTraceProps) {
  return (
    <section className="ct-panel p-4" aria-labelledby="premise-trace-heading">
      <h2 id="premise-trace-heading" className="mb-3 ct-section-title">
        Premise trace
      </h2>
      <ul className="space-y-2">
        {rows.map((row) => (
          <li
            key={row.factId}
            className="rounded-md border border-slate-200 p-3 dark:border-slate-700"
          >
            <div className="mb-1 flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs">{row.factId}</span>
              <TrustChip trustClass={row.trustClass as TrustClass} />
              {row.inProof ? (
                <span className="text-xs text-slate-500">Used in proof</span>
              ) : null}
            </div>
            <p className="text-sm">{row.statement}</p>
          </li>
        ))}
      </ul>
    </section>
  )
}
