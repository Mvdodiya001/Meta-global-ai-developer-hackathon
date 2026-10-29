import { DISCLAIMER_TEXT } from '../../content/disclaimer'

export function DisclaimerBanner() {
  return (
    <aside
      role="note"
      aria-label="Legal disclaimer"
      className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/40 dark:text-amber-100"
    >
      {DISCLAIMER_TEXT}
    </aside>
  )
}
