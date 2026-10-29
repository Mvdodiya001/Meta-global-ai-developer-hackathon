import type { SourceTraceRow } from '../../utils/findingTraces'

type SourceTraceProps = {
  rows: SourceTraceRow[]
}

export function SourceTrace({ rows }: SourceTraceProps) {
  return (
    <section className="ct-panel p-4" aria-labelledby="source-trace-heading">
      <h2 id="source-trace-heading" className="mb-3 ct-section-title">
        Source trace
      </h2>
      <ul className="space-y-2 text-sm">
        {rows.map((row) => (
          <li
            key={row.id}
            className="rounded-md border border-slate-200 p-3 dark:border-slate-700"
          >
            <div className="font-mono text-xs text-slate-500">
              {row.sourceVersionId} · {row.provisionId}
            </div>
            <p>
              Span {row.span} · sha256 prefix {row.sha256}
            </p>
          </li>
        ))}
      </ul>
    </section>
  )
}
