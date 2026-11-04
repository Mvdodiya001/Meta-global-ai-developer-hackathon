import type { ReactNode } from 'react'

type PanelProps = {
  heading: string
  headingId: string
  children: ReactNode
  description?: ReactNode
  actions?: ReactNode
  tone?: 'default' | 'flat' | 'quiet' | 'surface'
  className?: string
}

/**
 * Shared section for lawyer-facing pages (P4 design system).
 * Default is an open editorial section; `surface` adds a boundary for
 * genuinely grouped interactions such as upload or evidence panels.
 */
export function Panel({
  heading,
  headingId,
  children,
  description,
  actions,
  tone = 'default',
  className = '',
}: PanelProps) {
  return (
    <section
      className={[
        'ct-panel',
        tone === 'flat' ? 'ct-panel--flat' : '',
        tone === 'quiet' ? 'ct-panel--quiet' : '',
        tone === 'surface' ? 'ct-panel--surface' : '',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      aria-labelledby={headingId}
    >
      <div className="ct-panel-head">
        <div className="min-w-0">
          <h2 id={headingId} className="ct-panel-title">
            {heading}
          </h2>
          {description ? <p className="ct-panel-desc">{description}</p> : null}
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
      </div>
      <div className="ct-panel-body">{children}</div>
    </section>
  )
}
