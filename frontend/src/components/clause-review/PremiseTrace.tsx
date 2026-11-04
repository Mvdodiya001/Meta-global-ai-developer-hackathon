import type { Finding } from '../../api/types'
import { displayFactLines } from '../../utils/displayFields'
import { TrustChip } from '../TrustChip'

type PremiseTraceProps = {
  finding: Finding
}

export function PremiseTrace({ finding }: PremiseTraceProps) {
  const lines = displayFactLines(finding)

  return (
    <section className="ct-panel" aria-labelledby="premise-trace-heading">
      <div className="ct-panel-head">
        <div>
          <h2 id="premise-trace-heading" className="ct-panel-title">
            Facts
          </h2>
          <p className="ct-panel-desc">
            Only confirmed or document-extracted facts can support an answer.
          </p>
        </div>
        <span className="ct-badge">{lines.length}</span>
      </div>
      <div className="ct-panel-body">
        <ul className="ct-rows">
          {lines.map((line, index) => (
            <li
              key={`${line.label}-${index}`}
              aria-label={line.label}
            >
              <div className="mb-1.5 flex flex-wrap items-center gap-2">
                <TrustChip trustClass={line.trustClass} label={line.trustLabel} />
                {line.proposed ? (
                  <span className="text-xs font-medium text-ct-warn">Not relied on</span>
                ) : null}
              </div>
              <p className="text-sm leading-relaxed text-ct-ink">{line.label}</p>
              {line.confirmedBy ? (
                <p className="mt-1 text-xs text-ct-muted">Confirmed by {line.confirmedBy}</p>
              ) : null}
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
