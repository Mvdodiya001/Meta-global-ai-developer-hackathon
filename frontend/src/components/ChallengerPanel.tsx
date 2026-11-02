import { SECOND_REVIEW_BLOCKING } from '../content/glossary'
import type { ChallengerReportView } from '../api/mocks/challenger'
import { isLawyerSafeText } from '../utils/lawyerCopy'
import { StatusBadge } from './badges/StatusBadge'

type ChallengerPanelProps = {
  report: ChallengerReportView | null
}

export function ChallengerPanel({ report }: ChallengerPanelProps) {
  if (report == null) {
    return null
  }

  const reasons = report.objections
    .map((row) => row.reason)
    .filter((reason) => isLawyerSafeText(reason))
  const quotes = report.objections
    .map((row) => row.quote)
    .filter((quote): quote is string => Boolean(quote && isLawyerSafeText(quote)))

  return (
    <section className="ct-panel space-y-3 p-4" aria-labelledby="second-review-heading">
      <h2 id="second-review-heading" className="ct-section-title">
        Second-review pass
      </h2>
      {report.blocking ? (
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge status="REQUIRES_REVIEW" />
          <p className="text-sm font-medium">{SECOND_REVIEW_BLOCKING}</p>
        </div>
      ) : reasons.length === 0 ? (
        <p className="text-sm">The second review did not flag this draft.</p>
      ) : null}
      {reasons.length > 0 ? (
        <ul className="space-y-2">
          {reasons.map((reason, index) => (
            <li
              key={`${index}-${reason.slice(0, 24)}`}
              className="rounded-md border border-slate-200 p-3 text-sm dark:border-slate-700"
            >
              {reason}
            </li>
          ))}
        </ul>
      ) : null}
      {quotes.length > 0 ? (
        <ul className="space-y-2">
          {quotes.map((quote, index) => (
            <li key={`${index}-${quote.slice(0, 24)}`}>
              <blockquote className="border-l-2 border-slate-300 pl-3 text-sm dark:border-slate-600">
                {quote}
              </blockquote>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  )
}
