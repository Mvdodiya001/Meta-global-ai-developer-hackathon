import type { TrustClass } from '../api/types'
import { displayTrustLabel } from '../utils/displayFields'

const TRUST_STYLES: Record<TrustClass, string> = {
  document_extracted:
    'border-sky-300 bg-sky-50 text-sky-900 dark:border-sky-700 dark:bg-sky-950/40 dark:text-sky-100',
  lawyer_confirmed:
    'border-emerald-300 bg-emerald-50 text-emerald-900 dark:border-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-100',
  ai_inferred:
    'border-violet-300 bg-violet-50 text-violet-900 dark:border-violet-700 dark:bg-violet-950/40 dark:text-violet-100',
  disputed:
    'border-rose-400 bg-rose-50 text-rose-950 dark:border-rose-700 dark:bg-rose-950/40 dark:text-rose-100',
}

type TrustChipProps = {
  trustClass: TrustClass
  label?: string | null
}

export function TrustChip({ trustClass, label }: TrustChipProps) {
  return (
    <span
      className={`inline-flex rounded-md border px-2 py-0.5 text-xs font-medium ${TRUST_STYLES[trustClass]}`}
    >
      {displayTrustLabel(trustClass, label)}
    </span>
  )
}
