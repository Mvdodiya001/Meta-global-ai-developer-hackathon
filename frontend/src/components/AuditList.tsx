import type { AuditTrail } from '../api/types'

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

export function AuditList({ audit }: AuditListProps) {
  return (
    <section className="ct-panel overflow-hidden" aria-labelledby="audit-heading">
      <h2 id="audit-heading" className="border-b border-slate-200 px-4 py-3 text-sm font-semibold dark:border-slate-700">
        History
      </h2>
      <ul className="divide-y divide-slate-200 dark:divide-slate-800">
        {audit.rows.map((row) => (
          <li key={row.id} className="px-4 py-3 text-sm">
            <p className="text-slate-500">{row.ts}</p>
            <p className="mt-1 text-slate-700 dark:text-slate-300">{eventLabel(row.event)}</p>
          </li>
        ))}
      </ul>
    </section>
  )
}
