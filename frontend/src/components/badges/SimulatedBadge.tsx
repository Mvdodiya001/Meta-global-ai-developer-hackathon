export function SimulatedBadge() {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-orange-400 bg-orange-50 px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-orange-900 dark:border-orange-600 dark:bg-orange-950/40 dark:text-orange-100">
      <span aria-hidden="true">⚠</span>
      <span>Simulated</span>
    </span>
  )
}
