import { IconAlert } from '../ui/Icons'

export function SimulatedBadge() {
  return (
    <span className="ct-badge ct-badge--warn uppercase tracking-wide">
      <IconAlert size={12} />
      <span>Simulated</span>
    </span>
  )
}
