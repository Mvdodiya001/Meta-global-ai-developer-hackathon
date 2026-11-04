import type { SensitivityHint } from '../../utils/findingTraces'
import { IconRefresh } from '../ui/Icons'

type WhatWouldChangePanelProps = {
  hints: SensitivityHint[]
}

export function WhatWouldChangePanel({ hints }: WhatWouldChangePanelProps) {
  if (hints.length === 0) {
    return null
  }

  return (
    <section className="ct-panel" aria-labelledby="wwc-heading">
      <div className="ct-panel-head">
        <div>
          <h2 id="wwc-heading" className="ct-panel-title">
            What would change this answer?
          </h2>
          <p className="ct-panel-desc">
            Check these before relying on the finding.
          </p>
        </div>
      </div>
      <div className="ct-panel-body">
        <ul className="ct-rows">
          {hints.map((hint) => (
            <li
              key={hint.id}
              className="flex gap-2.5"
            >
              <IconRefresh size={15} className="mt-0.5 shrink-0 text-ct-muted" />
              <div className="min-w-0">
                <p className="text-sm font-semibold text-ct-ink">{hint.label}</p>
                <p className="mt-0.5 text-sm leading-relaxed text-ct-muted">{hint.detail}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
