import type { Finding } from '../api/types'
import { AiDraftBadge } from './badges/AiDraftBadge'
import { LawyerReviewedBadge } from './badges/LawyerReviewedBadge'
import { StatusBadge } from './badges/StatusBadge'

type FindingCardProps = {
  finding: Finding
  lawyerReviewed?: boolean
}

export function FindingCard({ finding, lawyerReviewed = false }: FindingCardProps) {
  return (
    <article
      className="ct-panel space-y-3 p-4"
      aria-label={`Finding ${finding.id}`}
    >
      <div className="flex flex-wrap items-center gap-2">
        <h2 id={`finding-${finding.id}`} className="text-lg font-semibold">
          Finding {finding.id}
        </h2>
        <StatusBadge status={finding.status} state={finding.state} />
        {lawyerReviewed ? (
          <LawyerReviewedBadge />
        ) : (
          <AiDraftBadge label={finding.ai_draft_label} />
        )}
      </div>
      <dl className="grid gap-2 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-slate-500">Claim</dt>
          <dd className="font-mono">{finding.claim_id}</dd>
        </div>
        <div>
          <dt className="text-slate-500">As of</dt>
          <dd>{finding.as_of}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Conclusion</dt>
          <dd className="capitalize">{finding.proof.conclusion}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Confidence</dt>
          <dd className="capitalize">{finding.confidence_band}</dd>
        </div>
      </dl>
      <p className="text-sm text-slate-600 dark:text-slate-400">
        Checker: {finding.checker_report.valid ? 'valid proof' : 'invalid proof'}
        {finding.checker_report.errors.length > 0
          ? ` (${finding.checker_report.errors.length} issues)`
          : ''}
      </p>
    </article>
  )
}
