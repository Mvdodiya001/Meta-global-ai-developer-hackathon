import type { Finding } from '../../api/types'
import {
  displayLawVersionDate,
  displayLawVersionLabel,
  displaySectionLabel,
  displaySectionQuote,
} from '../../utils/displayFields'
import { IconBook, IconClock } from '../ui/Icons'

type SourceTraceProps = {
  finding: Finding
}

export function SourceTrace({ finding }: SourceTraceProps) {
  const heading = displaySectionLabel(finding)

  return (
    <section className="ct-panel" aria-labelledby="source-trace-heading">
      <div className="ct-panel-head">
        <div>
          <h2 id="source-trace-heading" className="ct-panel-title">
            Section
          </h2>
          <p className="ct-panel-desc">The exact provision this answer was tested against.</p>
        </div>
        <span className="ct-badge">
          <IconClock size={12} />
          {displayLawVersionDate(finding)}
        </span>
      </div>
      <div className="ct-panel-body space-y-3">
        <p className="flex items-center gap-1.5 text-xs text-ct-muted">
          <IconBook size={13} />
          {displayLawVersionLabel(finding)}
        </p>
        {heading ? <p className="text-sm font-semibold text-ct-ink">{heading}</p> : null}
        <blockquote className="ct-quote">{displaySectionQuote(finding)}</blockquote>
      </div>
    </section>
  )
}
