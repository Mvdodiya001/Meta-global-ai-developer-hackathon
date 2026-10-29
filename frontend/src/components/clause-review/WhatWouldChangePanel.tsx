import type { SensitivityHint } from '../../utils/findingTraces'

type WhatWouldChangePanelProps = {
  hints: SensitivityHint[]
}

export function WhatWouldChangePanel({ hints }: WhatWouldChangePanelProps) {
  return (
    <section className="ct-panel p-4" aria-labelledby="wwc-heading">
      <h2 id="wwc-heading" className="mb-2 ct-section-title">
        What would change my answer?
      </h2>
      <p className="mb-3 text-sm text-slate-600 dark:text-slate-400">
        Sensitivity hints from accepted premises and cited sources (mock derivation).
      </p>
      <ul className="space-y-2">
        {hints.map((hint) => (
          <li
            key={hint.id}
            className="rounded-md border border-slate-200 p-3 dark:border-slate-700"
          >
            <p className="text-sm font-medium">{hint.label}</p>
            <p className="text-sm text-slate-600 dark:text-slate-400">{hint.detail}</p>
          </li>
        ))}
      </ul>
    </section>
  )
}
