import type { Fact, TrustClass } from '../../api/types'
import { TrustChip } from '../TrustChip'
import { LawyerReviewedBadge } from '../badges/LawyerReviewedBadge'

type FactTrustListProps = {
  facts: Fact[]
  reviewedIds: string[]
  onApprove: (factId: string) => void
  onChallenge: (factId: string) => void
}

export function FactTrustList({
  facts,
  reviewedIds,
  onApprove,
  onChallenge,
}: FactTrustListProps) {
  return (
    <section className="ct-panel p-4" aria-labelledby="facts-heading">
      <h2 id="facts-heading" className="mb-3 ct-section-title">
        Matter facts
      </h2>
      {facts.length === 0 ? (
        <p className="text-sm text-slate-600 dark:text-slate-400">
          No facts on this matter yet.
        </p>
      ) : null}
      <ul className="space-y-3">
        {facts.map((fact) => (
          <li
            key={fact.id}
            aria-label={`Fact ${fact.id}`}
            className="rounded-md border border-slate-200 p-4 dark:border-slate-700"
          >
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs text-slate-500">{fact.id}</span>
              <TrustChip trustClass={fact.trust_class as TrustClass} />
              {reviewedIds.includes(fact.id) ? <LawyerReviewedBadge /> : null}
            </div>
            <p className="text-sm">{fact.statement}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                className="rounded-md border border-slate-300 px-3 py-1 text-xs font-medium hover:bg-slate-50 dark:border-slate-600 dark:hover:bg-slate-800"
                onClick={() => onApprove(fact.id)}
              >
                Approve
              </button>
              <button
                type="button"
                className="rounded-md border border-rose-300 px-3 py-1 text-xs font-medium text-rose-900 hover:bg-rose-50 dark:border-rose-700 dark:text-rose-100 dark:hover:bg-rose-950/40"
                onClick={() => onChallenge(fact.id)}
              >
                Challenge
              </button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}
