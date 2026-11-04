import type { ComponentType } from 'react'

import { displayStatusLabel } from '../../utils/displayFields'
import {
  IconAlert,
  IconCheck,
  IconClock,
  IconInfo,
  IconRefresh,
  IconScale,
  IconX,
} from '../ui/Icons'

type StatusMeta = {
  Icon: ComponentType<{ size?: number }>
  className: string
}

const STATUS_META: Record<string, StatusMeta> = {
  FOLLOWS: { Icon: IconCheck, className: 'ct-badge--ok' },
  RULED_OUT: { Icon: IconX, className: '' },
  UNKNOWN: { Icon: IconInfo, className: 'ct-badge--warn' },
  REQUIRES_REVIEW: { Icon: IconAlert, className: 'ct-badge--danger' },
  CONFLICTING: { Icon: IconScale, className: 'ct-badge--warn' },
  STALE: { Icon: IconRefresh, className: 'ct-badge--warn' },
  SUPERSEDED: { Icon: IconClock, className: '' },
}

type StatusBadgeProps = {
  status: string
  state?: string | null
  label?: string | null
}

export function StatusBadge({ status, state, label }: StatusBadgeProps) {
  const key = state === 'STALE' || state === 'SUPERSEDED' ? state : status
  const meta: StatusMeta = STATUS_META[key] ?? {
    Icon: IconInfo,
    className: '',
  }
  const text = displayStatusLabel(status, label, state)

  return (
    <span
      className={['ct-badge max-w-xl items-start text-left', meta.className]
        .filter(Boolean)
        .join(' ')}
      data-status={key}
    >
      <meta.Icon size={13} />
      <span>{text}</span>
    </span>
  )
}
