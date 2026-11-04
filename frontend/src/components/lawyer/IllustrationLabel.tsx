import { IconInfo } from '../ui/Icons'

export function IllustrationLabel() {
  return (
    <p className="inline-flex items-center gap-1.5 rounded-full border border-ct-line bg-ct-surface3 px-2.5 py-0.5 text-xs font-medium text-ct-muted">
      <IconInfo size={12} />
      Illustration, not a server answer
    </p>
  )
}
