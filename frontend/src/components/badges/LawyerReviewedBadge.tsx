import { IconCheck } from '../ui/Icons'

export function LawyerReviewedBadge() {
  return (
    <span className="ct-badge ct-badge--ok">
      <IconCheck size={12} />
      <span>Lawyer-reviewed</span>
    </span>
  )
}
