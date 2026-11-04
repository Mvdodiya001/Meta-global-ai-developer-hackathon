import type { Clause } from '../../api/types'
import { IconCheck } from '../ui/Icons'

type ClauseListProps = {
  clauses: Clause[]
  selectedId: string | null
  onSelect: (clauseId: string) => void
}

/** Compact navigational list: a hairline index with a clear active state. */
export function ClauseList({ clauses, selectedId, onSelect }: ClauseListProps) {
  return (
    <ul className="ct-rows" aria-label="Contract clauses">
      {clauses.map((clause) => {
        const selected = clause.id === selectedId
        return (
          <li key={clause.id} className="!py-0">
            <button
              type="button"
              onClick={() => onSelect(clause.id)}
              aria-pressed={selected}
              aria-current={selected ? 'true' : undefined}
              className={[
                'group flex w-full min-w-0 flex-col gap-1 rounded-sm px-2 py-2.5 text-left',
                'border-l-2 transition-colors',
                selected
                  ? 'border-ct-accent bg-ct-accentSoft/60'
                  : 'border-transparent hover:border-ct-lineStrong hover:bg-ct-surface2',
              ].join(' ')}
            >
              <span className="flex min-w-0 items-baseline gap-2">
                <span className="ct-mono text-xs font-semibold text-ct-accent">
                  {clause.ref}
                </span>
                <span className="min-w-0 flex-1 truncate text-sm font-medium text-ct-ink">
                  {clause.heading}
                </span>
                {selected ? <IconCheck size={13} className="shrink-0 text-ct-accent" /> : null}
              </span>
              <span className="line-clamp-2 min-w-0 max-w-full break-words text-xs leading-relaxed text-ct-muted">
                {clause.text}
              </span>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
