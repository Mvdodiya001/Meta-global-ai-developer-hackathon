import type { ToolCall } from '../../api/types'

type ToolTracePanelProps = {
  events: ToolCall[]
  running: boolean
  runId: string | null
}

export function ToolTracePanel({ events, running, runId }: ToolTracePanelProps) {
  return (
    <section className="ct-panel p-4" aria-labelledby="tool-trace-heading">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <h2 id="tool-trace-heading" className="ct-section-title">
          Tool trace
        </h2>
        {runId ? (
          <span className="font-mono text-xs text-slate-500">{runId}</span>
        ) : null}
        {running ? (
          <span className="text-xs font-medium text-blue-700 dark:text-blue-300">
            Running…
          </span>
        ) : null}
      </div>
      {events.length === 0 ? (
        <p className="text-sm text-slate-500">
          Submit a question to watch the six bounded tools (mock polling).
        </p>
      ) : (
        <ol className="space-y-2">
          {events.map((event) => (
            <li
              key={event.seq}
              className="rounded-md border border-slate-200 px-3 py-2 font-mono text-xs dark:border-slate-700"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-slate-500">#{event.seq}</span>
                <span className="font-semibold text-slate-900 dark:text-slate-100">
                  {event.tool}
                </span>
                <span
                  className={
                    event.ok
                      ? 'text-emerald-700 dark:text-emerald-300'
                      : 'text-rose-700 dark:text-rose-300'
                  }
                >
                  {event.ok ? 'ok' : 'failed'}
                </span>
              </div>
              <pre className="mt-1 overflow-x-auto whitespace-pre-wrap text-slate-600 dark:text-slate-400">
                {JSON.stringify(event.args)}
              </pre>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}
