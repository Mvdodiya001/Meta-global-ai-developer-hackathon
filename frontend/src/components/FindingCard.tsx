import { Link } from 'react-router-dom'

import type { Finding } from '../api/types'
import {
  displayClauseQuote,
  displayLawVersionDate,
  displayLawVersionLabel,
  displaySectionQuote,
} from '../utils/displayFields'
import { IconArrowRight, IconBook, IconQuote } from './ui/Icons'
import { AiDraftBadge } from './badges/AiDraftBadge'
import { LawyerReviewedBadge } from './badges/LawyerReviewedBadge'
import { StatusBadge } from './badges/StatusBadge'

type FindingCardProps = {
  finding: Finding
  lawyerReviewed?: boolean
  title?: string
  /** Hide the self-referential link when the card is already the evidence page. */
  showEvidenceLink?: boolean
}

function isLawyerReviewed(finding: Finding, flagged: boolean): boolean {
  if (flagged || finding.state === 'REVIEWED') {
    return true
  }
  return finding.ai_draft_label.toLowerCase().includes('reviewed by lawyer')
}

/**
 * A finding reads like a short legal document: a status line, the two
 * quoted sources side by side, and a closing note. It is deliberately not a
 * card, so the quotes stay the focus of the page.
 */
export function FindingCard({
  finding,
  lawyerReviewed = false,
  title = 'Legal test',
  showEvidenceLink = true,
}: FindingCardProps) {
  const reviewed = isLawyerReviewed(finding, lawyerReviewed)

  return (
    <article className="ct-doc ct-enter" aria-label={title}>
      <div className="space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="ct-eyebrow">Finding</p>
            <h2 className="mt-1 font-serif text-2xl font-semibold leading-tight tracking-tight text-ct-ink">
              {title}
            </h2>
          </div>
          <div className="flex flex-wrap items-center gap-1.5">
            {reviewed ? (
              <LawyerReviewedBadge />
            ) : (
              <AiDraftBadge label={finding.ai_draft_label} />
            )}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
          <StatusBadge
            status={finding.status}
            state={finding.state}
            label={finding.status_label}
          />
          <p className="flex flex-wrap items-center gap-1.5 text-xs text-ct-muted">
            <IconBook size={13} />
            <span>{`${displayLawVersionLabel(finding)} · ${displayLawVersionDate(finding)}`}</span>
          </p>
        </div>

        <div className="grid gap-x-7 gap-y-4 md:grid-cols-2">
          <figure className="min-w-0">
            <figcaption className="ct-readonly-chip mb-1.5">
              <IconQuote size={12} />
              The clause
            </figcaption>
            <blockquote className="ct-quote text-[0.92rem]">
              {displayClauseQuote(finding)}
            </blockquote>
          </figure>
          <figure className="min-w-0 md:border-l md:border-ct-line md:pl-7">
            <figcaption className="ct-readonly-chip mb-1.5">
              <IconBook size={12} />
              The law
            </figcaption>
            <blockquote className="ct-quote ct-quote--gold text-[0.92rem]">
              {displaySectionQuote(finding)}
            </blockquote>
          </figure>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 border-t border-ct-line pt-3">
          <p className="text-xs text-ct-muted">
            {reviewed
              ? 'A lawyer has reviewed this answer.'
              : 'This draft has not been reviewed by a lawyer.'}
          </p>
          {showEvidenceLink ? (
            <Link
              to={`/evidence/${finding.id}`}
              className="ct-link inline-flex items-center gap-1 text-sm"
            >
              Open evidence
              <IconArrowRight size={14} />
            </Link>
          ) : null}
        </div>
      </div>
    </article>
  )
}
