import type { AuditTrail } from '../api/types'
import { IconClock } from './ui/Icons'

type AuditListProps = {
  audit: AuditTrail
}

function eventLabel(event: string): string {
  if (event.includes('stale')) {
    return 'An earlier answer needs re-check because the law changed'
  }
  if (event.includes('proposed')) {
    return 'A draft answer was recorded'
  }
  if (event.includes('review')) {
    return 'You reviewed an answer'
  }
  return 'A record was added'
}

function displayTime(ts: string): { date: string; time: string } {
  const [date = ts, time = ''] = ts.split('T')
  return { date, time: time.replace('Z', '').slice(0, 8) }
}

/** Chronological timeline: a rail with dated entries, no boxes. */
export function AuditList({ audit }: AuditListProps) {
  return (
    <section className="ct-panel" aria-labelledby="audit-heading">
      <div className="ct-panel-head">
        <div>
          <h2 id="audit-heading" className="ct-panel-title">
            History
          </h2>
          <p className="ct-panel-desc">Every state change is appended; nothing is overwritten.</p>
        </div>
      </div>
      {audit.rows.length === 0 ? (
        <div className="ct-panel-body">
          <p className="ct-empty">No history has been recorded yet.</p>
        </div>
      ) : (
        <ol className="relative ml-1 space-y-0 border-l border-ct-line pl-0">
          {audit.rows.map((row) => {
            const { date, time } = displayTime(row.ts)
            return (
              <li key={row.id} className="relative pb-5 pl-6 last:pb-1">
                <span
                  className="absolute -left-[9px] top-1 flex h-[17px] w-[17px] items-center justify-center rounded-full border border-ct-line bg-ct-bg text-ct-muted"
                  aria-hidden="true"
                >
                  <IconClock size={10} />
                </span>
                <p className="text-sm leading-relaxed text-ct-soft">{eventLabel(row.event)}</p>
                <p className="ct-mono mt-0.5 text-[0.7rem] text-ct-faint">
                  {date}
                  {time ? ` · ${time}` : ''}
                </p>
              </li>
            )
          })}
        </ol>
      )}
    </section>
  )
}
