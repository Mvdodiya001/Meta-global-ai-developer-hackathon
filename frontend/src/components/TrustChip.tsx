import type { TrustClass } from '../api/types'
import { displayTrustLabel } from '../utils/displayFields'
import { IconAlert, IconCheck, IconFile, IconUser } from './ui/Icons'

const TRUST_STYLES: Record<TrustClass, { className: string; Icon: typeof IconCheck }> = {
  document_extracted: { className: 'ct-badge--info', Icon: IconFile },
  lawyer_confirmed: { className: 'ct-badge--ok', Icon: IconCheck },
  ai_inferred: { className: 'ct-badge--accent', Icon: IconUser },
  disputed: { className: 'ct-badge--danger', Icon: IconAlert },
}

type TrustChipProps = {
  trustClass: TrustClass
  label?: string | null
}

export function TrustChip({ trustClass, label }: TrustChipProps) {
  const meta = TRUST_STYLES[trustClass]
  return (
    <span className={['ct-badge', meta.className].join(' ')}>
      <meta.Icon size={12} />
      <span>{displayTrustLabel(trustClass, label)}</span>
    </span>
  )
}
