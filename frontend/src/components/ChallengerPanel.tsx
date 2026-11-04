import { SECOND_REVIEW_BLOCKING } from '../content/glossary'
import type { ChallengerReportView } from '../api/mocks/challenger'
import { isLawyerSafeText } from '../utils/lawyerCopy'
import { IconAlert, IconQuote } from './ui/Icons'
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
    <section className="ct-panel" aria-labelledby="second-review-heading">
      <div className="ct-panel-head">
        <div>
          <h2 id="second-review-heading" className="ct-panel-title">
            Second-review pass
          </h2>
          <p className="ct-panel-desc">
            An independent pass over the same proof, looking for a reason to withhold it.
          </p>
        </div>
        {report.blocking ? <StatusBadge status="REQUIRES_REVIEW" /> : null}
      </div>
      <div className="ct-panel-body space-y-3">
        {report.blocking ? (
          <div className="flex items-start gap-2.5 rounded-md border border-ct-dangerLine bg-ct-dangerSoft p-3 text-ct-danger">
            <IconAlert size={16} className="mt-0.5 shrink-0" />
            <p className="text-sm font-semibold">{SECOND_REVIEW_BLOCKING}</p>
          </div>
        ) : reasons.length === 0 ? (
          <p className="text-sm text-ct-muted">The second review did not flag this draft.</p>
        ) : null}
        {reasons.length > 0 ? (
          <ul className="ct-rows">
            {reasons.map((reason, index) => (
              <li
                key={`${index}-${reason.slice(0, 24)}`}
                className="text-sm leading-relaxed text-ct-soft"
              >
                {reason}
              </li>
            ))}
          </ul>
        ) : null}
        {quotes.length > 0 ? (
          <ul className="space-y-2">
            {quotes.map((quote, index) => (
              <li key={`${index}-${quote.slice(0, 24)}`} className="flex gap-2">
                <IconQuote size={14} className="mt-1 shrink-0 text-ct-muted" />
                <blockquote className="ct-quote text-sm">{quote}</blockquote>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </section>
  )
}
