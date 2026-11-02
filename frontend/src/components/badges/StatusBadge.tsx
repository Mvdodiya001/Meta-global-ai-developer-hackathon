import { displayStatusLabel } from '../../utils/displayFields'

const STATUS_META: Record<string, { icon: string; className: string }> = {
  FOLLOWS: {
    icon: '→',
    className:
      'border-emerald-300 bg-emerald-50 text-emerald-900 dark:border-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-100',
  },
  RULED_OUT: {
    icon: '✕',
    className:
      'border-slate-400 bg-slate-100 text-slate-900 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100',
  },
  UNKNOWN: {
    icon: '?',
    className:
      'border-amber-400 bg-amber-50 text-amber-950 dark:border-amber-600 dark:bg-amber-950/40 dark:text-amber-100',
  },
  REQUIRES_REVIEW: {
    icon: '!',
    className:
      'border-rose-400 bg-rose-50 text-rose-950 dark:border-rose-700 dark:bg-rose-950/40 dark:text-rose-100',
  },
  CONFLICTING: {
    icon: '≠',
    className:
      'border-violet-400 bg-violet-50 text-violet-950 dark:border-violet-600 dark:bg-violet-950/40 dark:text-violet-100',
  },
  STALE: {
    icon: '↻',
    className:
      'border-orange-400 bg-orange-50 text-orange-950 dark:border-orange-600 dark:bg-orange-950/40 dark:text-orange-100',
  },
  SUPERSEDED: {
    icon: '↩',
    className:
      'border-slate-400 bg-slate-100 text-slate-800 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100',
  },
}

type StatusBadgeProps = {
  status: string
  state?: string | null
  label?: string | null
}

export function StatusBadge({ status, state, label }: StatusBadgeProps) {
  const key = state === 'STALE' || state === 'SUPERSEDED' ? state : status
  const style = STATUS_META[key] ?? {
    icon: '•',
    className:
      'border-slate-300 bg-slate-50 text-slate-800 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100',
  }
  const text = displayStatusLabel(status, label, state)

  return (
    <span
      className={`inline-flex max-w-xl items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-semibold ${style.className}`}
    >
      <span aria-hidden="true">{style.icon}</span>
      <span>{text}</span>
    </span>
  )
}
