import type { Finding } from '../api/types'
import {
  displayClauseQuote,
  displayLawVersionDate,
  displayLawVersionLabel,
  displaySectionQuote,
} from '../utils/displayFields'
import { AiDraftBadge } from './badges/AiDraftBadge'
import { LawyerReviewedBadge } from './badges/LawyerReviewedBadge'
import { StatusBadge } from './badges/StatusBadge'

type FindingCardProps = {
  finding: Finding
  lawyerReviewed?: boolean
  title?: string
}

function isLawyerReviewed(finding: Finding, flagged: boolean): boolean {
  if (flagged || finding.state === 'REVIEWED') {
    return true
  }
  return finding.ai_draft_label.toLowerCase().includes('reviewed by lawyer')
}

export function FindingCard({
  finding,
  lawyerReviewed = false,
  title = 'Legal test',
}: FindingCardProps) {
  const reviewed = isLawyerReviewed(finding, lawyerReviewed)

  return (
    <article className="ct-panel space-y-3 p-4" aria-label={title}>
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="text-lg font-semibold">{title}</h2>
        <StatusBadge
          status={finding.status}
          state={finding.state}
          label={finding.status_label}
        />
        {reviewed ? (
          <LawyerReviewedBadge />
        ) : (
          <AiDraftBadge label={finding.ai_draft_label} />
        )}
      </div>
      <p className="text-sm text-slate-600 dark:text-slate-400">
        {displayLawVersionLabel(finding)} · {displayLawVersionDate(finding)}
      </p>
      <blockquote className="border-l-2 border-slate-300 pl-3 text-sm dark:border-slate-600">
        {displayClauseQuote(finding)}
      </blockquote>
      <blockquote className="border-l-2 border-slate-300 pl-3 text-sm dark:border-slate-600">
        {displaySectionQuote(finding)}
      </blockquote>
    </article>
  )
}
