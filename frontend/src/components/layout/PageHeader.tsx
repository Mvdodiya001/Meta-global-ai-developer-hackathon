import type { ReactNode } from 'react'

import { AiDraftBadge } from '../badges/AiDraftBadge'

type PageHeaderProps = {
  title: string
  eyebrow?: string
  description?: ReactNode
  actions?: ReactNode
  /** Show the product-required draft indicator (default: yes). */
  draftBadge?: boolean
  extraBadges?: ReactNode
}

/**
 * The one page header for every route. Keeps the mandatory
 * "AI draft — not yet reviewed" indicator visible without burying it.
 */
export function PageHeader({
  title,
  eyebrow,
  description,
  actions,
  draftBadge = true,
  extraBadges,
}: PageHeaderProps) {
  return (
    <header className="ct-page-header">
      <div className="min-w-0">
        {eyebrow ? <p className="ct-eyebrow">{eyebrow}</p> : null}
        <h1 className="ct-page-title">{title}</h1>
        {description ? <p className="ct-page-desc">{description}</p> : null}
        {draftBadge || extraBadges ? (
          <div className="ct-page-badges">
            {draftBadge ? <AiDraftBadge label="AI draft — not yet reviewed" /> : null}
            {extraBadges}
          </div>
        ) : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  )
}
