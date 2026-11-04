import type { ReactNode } from 'react'

import { IconAlert, IconCheck, IconInfo } from './Icons'

type StateMessageProps = {
  tone?: 'info' | 'warn' | 'danger' | 'success' | 'neutral'
  children: ReactNode
  /** Use "alert" only for genuine failures that need attention. */
  live?: 'status' | 'alert'
  className?: string
}

const ICONS = {
  info: IconInfo,
  warn: IconAlert,
  danger: IconAlert,
  success: IconCheck,
  neutral: IconInfo,
} as const

const TONES = {
  info: 'ct-notice--info',
  warn: 'ct-notice--warn',
  danger: 'ct-notice--danger',
  success: 'ct-notice--info',
  neutral: '',
} as const

/** Inline outcome/notice with an icon and readable text (not colour alone). */
export function StateMessage({
  tone = 'neutral',
  children,
  live = 'status',
  className = '',
}: StateMessageProps) {
  const Icon = ICONS[tone]
  return (
    <div
      role={live}
      className={['ct-notice', TONES[tone], className].filter(Boolean).join(' ')}
    >
      <Icon size={16} className="mt-0.5 shrink-0" />
      <div className="min-w-0">{children}</div>
    </div>
  )
}
