import type { ToolCall } from '../../api/types'

type ToolTracePanelProps = {
  events: ToolCall[]
  running: boolean
  runId: string | null
}

/** Vertical timeline of bounded tool calls, in Quiet Sage tones. */
export function ToolTracePanel({ events, running, runId }: ToolTracePanelProps) {
  return (
    <section className="ct-panel" aria-labelledby="tool-trace-heading">
      <div className="mb-1 flex flex-wrap items-baseline gap-2">
        <h2 id="tool-trace-heading" className="ct-section-title">
          Tool trace
        </h2>
        {runId ? <span className="ct-mono text-xs text-ct-faint">{runId}</span> : null}
        {running ? (
          <span className="text-xs font-medium text-ct-accent">Running…</span>
        ) : null}
      </div>
      {events.length === 0 ? (
        <p className="ct-empty">Submit a question to watch the six bounded tools.</p>
      ) : (
        <ol className="relative ml-1 border-l border-ct-line">
          {events.map((event) => (
            <li key={event.seq} className="relative pb-4 pl-5 last:pb-1">
              <span
                className={[
                  'absolute -left-[5px] top-1.5 h-2 w-2 rounded-full',
                  event.ok ? 'bg-ct-ok' : 'bg-ct-danger',
                ].join(' ')}
                aria-hidden="true"
              />
              <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
                <span className="ct-mono text-[0.7rem] text-ct-faint">#{event.seq}</span>
                <span className="text-sm font-semibold text-ct-ink">{event.tool}</span>
                <span
                  className={
                    event.ok
                      ? 'text-xs font-medium text-ct-ok'
                      : 'text-xs font-medium text-ct-danger'
                  }
                >
                  {event.ok ? 'ok' : 'failed'}
                </span>
              </div>
              <pre className="ct-mono mt-1 overflow-x-auto whitespace-pre-wrap text-[0.72rem] leading-relaxed text-ct-muted">
                {JSON.stringify(event.args)}
              </pre>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}
