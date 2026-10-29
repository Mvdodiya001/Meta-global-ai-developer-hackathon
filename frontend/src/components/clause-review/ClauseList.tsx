import type { Clause } from '../../api/types'

type ClauseListProps = {
  clauses: Clause[]
  selectedId: string | null
  onSelect: (clauseId: string) => void
}

export function ClauseList({ clauses, selectedId, onSelect }: ClauseListProps) {
  return (
    <ul className="space-y-2" aria-label="Contract clauses">
      {clauses.map((clause) => {
        const selected = clause.id === selectedId
        return (
          <li key={clause.id}>
            <button
              type="button"
              onClick={() => onSelect(clause.id)}
              aria-pressed={selected}
              className={[
                'w-full rounded-md border p-3 text-left transition-colors',
                selected
                  ? 'border-blue-500 bg-blue-50 dark:border-blue-600 dark:bg-blue-950/40'
                  : 'border-slate-200 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-900',
              ].join(' ')}
            >
              <div className="mb-1 flex items-baseline gap-2">
                <span className="font-mono text-sm font-semibold">{clause.ref}</span>
                <span className="text-sm font-medium">{clause.heading}</span>
              </div>
              <p className="line-clamp-2 text-sm text-slate-700 dark:text-slate-300">
                {clause.text}
              </p>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
