import type { DiffResult } from '../api/types'

type DiffViewProps = {
  diff: DiffResult
}

export function DiffView({ diff }: DiffViewProps) {
  const before = diff.before[0]
  const after = diff.after[0]

  return (
    <section className="space-y-3" aria-labelledby="diff-heading">
      <h2 id="diff-heading" className="ct-section-title">
        Provision diff ({diff.changed_keys.join(', ')})
      </h2>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="ct-panel p-4">
          <h3 className="mb-2 text-sm font-medium">
            Before · {before?.key ?? '—'}
          </h3>
          <p className="whitespace-pre-wrap font-mono text-xs leading-relaxed">
            {before?.text ?? 'No prior text'}
          </p>
        </div>
        <div className="ct-panel border-l-4 border-l-orange-400 p-4">
          <h3 className="mb-2 text-sm font-medium">
            After · {after?.key ?? '—'}
          </h3>
          <p className="whitespace-pre-wrap font-mono text-xs leading-relaxed">
            {after?.text ?? 'No new text'}
          </p>
        </div>
      </div>
    </section>
  )
}
