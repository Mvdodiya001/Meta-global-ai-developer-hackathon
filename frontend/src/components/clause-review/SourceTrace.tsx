import type { Finding } from '../../api/types'
import {
  displayLawVersionDate,
  displayLawVersionLabel,
  displaySectionLabel,
  displaySectionQuote,
} from '../../utils/displayFields'

type SourceTraceProps = {
  finding: Finding
}

export function SourceTrace({ finding }: SourceTraceProps) {
  const heading = displaySectionLabel(finding)

  return (
    <section className="ct-panel p-4" aria-labelledby="source-trace-heading">
      <h2 id="source-trace-heading" className="mb-3 ct-section-title">
        Section
      </h2>
      <p className="mb-3 text-sm text-slate-600 dark:text-slate-400">
        {displayLawVersionLabel(finding)} · {displayLawVersionDate(finding)}
      </p>
      {heading ? <p className="mb-2 text-sm font-medium">{heading}</p> : null}
      <blockquote className="border-l-2 border-slate-300 pl-3 text-sm dark:border-slate-600">
        {displaySectionQuote(finding)}
      </blockquote>
    </section>
  )
}
