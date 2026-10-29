type AiDraftBadgeProps = {
  label: string
}

export function AiDraftBadge({ label }: AiDraftBadgeProps) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-violet-300 bg-violet-50 px-2 py-0.5 text-xs font-medium text-violet-900 dark:border-violet-700 dark:bg-violet-950/50 dark:text-violet-100">
      <span aria-hidden="true">✎</span>
      <span>{label}</span>
    </span>
  )
}
