const STATUS_META: Record<
  string,
  { label: string; icon: string; className: string }
> = {
  FOLLOWS: {
    label: 'Follows',
    icon: '→',
    className:
      'border-emerald-300 bg-emerald-50 text-emerald-900 dark:border-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-100',
  },
  RULED_OUT: {
    label: 'Ruled out',
    icon: '✕',
    className:
      'border-slate-400 bg-slate-100 text-slate-900 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100',
  },
  UNKNOWN: {
    label: 'Unknown',
    icon: '?',
    className:
      'border-amber-400 bg-amber-50 text-amber-950 dark:border-amber-600 dark:bg-amber-950/40 dark:text-amber-100',
  },
  REQUIRES_REVIEW: {
    label: 'Requires review',
    icon: '!',
    className:
      'border-rose-400 bg-rose-50 text-rose-950 dark:border-rose-700 dark:bg-rose-950/40 dark:text-rose-100',
  },
  STALE: {
    label: 'Stale',
    icon: '↻',
    className:
      'border-orange-400 bg-orange-50 text-orange-950 dark:border-orange-600 dark:bg-orange-950/40 dark:text-orange-100',
  },
  SUPERSEDED: {
    label: 'Superseded',
    icon: '↩',
    className:
      'border-slate-400 bg-slate-100 text-slate-800 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100',
  },
}

type StatusBadgeProps = {
  status: string
  state?: string | null
}

export function StatusBadge({ status, state }: StatusBadgeProps) {
  const key = state === 'STALE' || state === 'SUPERSEDED' ? state : status
  const meta = STATUS_META[key] ?? {
    label: status,
    icon: '•',
    className:
      'border-slate-300 bg-slate-50 text-slate-800 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100',
  }

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-semibold ${meta.className}`}
    >
      <span aria-hidden="true">{meta.icon}</span>
      <span>{meta.label}</span>
    </span>
  )
}
