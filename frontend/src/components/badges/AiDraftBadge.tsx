import { IconClause } from '../ui/Icons'

type AiDraftBadgeProps = {
  label: string
}

export function AiDraftBadge({ label }: AiDraftBadgeProps) {
  return (
    <span className="ct-badge ct-badge--accent">
      <IconClause size={12} />
      <span>{label}</span>
    </span>
  )
}
