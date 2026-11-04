import { DISCLAIMER_TEXT } from '../../content/disclaimer'
import { IconInfo } from '../ui/Icons'

export function DisclaimerBanner() {
  return (
    <aside
      role="note"
      aria-label="Legal disclaimer"
      className="ct-disclaimer"
    >
      <IconInfo size={15} className="mt-0.5 shrink-0" />
      <p className="min-w-0">{DISCLAIMER_TEXT}</p>
    </aside>
  )
}
