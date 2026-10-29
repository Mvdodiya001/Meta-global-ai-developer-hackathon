import type { AuditTrail } from '../api/types'

type AuditListProps = {
  audit: AuditTrail
}

export function AuditList({ audit }: AuditListProps) {
  return (
    <section className="ct-panel overflow-hidden" aria-labelledby="audit-heading">
      <h2 id="audit-heading" className="border-b border-slate-200 px-4 py-3 text-sm font-semibold dark:border-slate-700">
        Audit trail
      </h2>
      <ul className="divide-y divide-slate-200 dark:divide-slate-800">
        {audit.rows.map((row) => (
          <li key={row.id} className="px-4 py-3 text-sm">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs text-slate-500">{row.ts}</span>
              <span className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs dark:bg-slate-800">
                {row.event}
              </span>
            </div>
            <p className="mt-1 text-slate-700 dark:text-slate-300">
              {row.object_type} {row.object_id} · {row.actor_type} {row.actor_id}
            </p>
          </li>
        ))}
      </ul>
    </section>
  )
}
