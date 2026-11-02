import type { Fact, TrustClass } from '../../api/types'
import { asTrustClass } from '../../utils/trustClass'
import { TrustChip } from '../TrustChip'
import { LawyerReviewedBadge } from '../badges/LawyerReviewedBadge'

type FactTrustListProps = {
  facts: Fact[]
  reviewedIds: string[]
  disabled?: boolean
  onApprove: (factId: string) => void
  onChallenge: (factId: string) => void
}

function sortFacts(facts: Fact[]): Fact[] {
  return [...facts].sort((a, b) => {
    const aProposed = asTrustClass(a.trust_class) === 'ai_inferred' ? 1 : 0
    const bProposed = asTrustClass(b.trust_class) === 'ai_inferred' ? 1 : 0
    return aProposed - bProposed
  })
}

export function FactTrustList({
  facts,
  reviewedIds,
  disabled = false,
  onApprove,
  onChallenge,
}: FactTrustListProps) {
  const ordered = sortFacts(facts)

  return (
    <section className="ct-panel p-4" aria-labelledby="facts-heading">
      <h2 id="facts-heading" className="mb-3 ct-section-title">
        Facts awaiting your approval
      </h2>
      {ordered.length === 0 ? (
        <p className="text-sm text-slate-600 dark:text-slate-400">
          No facts are listed yet.
        </p>
      ) : null}
      <ul className="space-y-3">
        {ordered.map((fact) => {
          const trust = fact.trust_class as TrustClass
          const proposed = trust === 'ai_inferred'
          return (
            <li
              key={fact.id}
              aria-label={fact.statement}
              className="rounded-md border border-slate-200 p-4 dark:border-slate-700"
            >
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <TrustChip trustClass={trust} label={fact.trust_label} />
                {reviewedIds.includes(fact.id) ? <LawyerReviewedBadge /> : null}
                {proposed ? (
                  <span className="text-xs text-slate-500">Not relied on</span>
                ) : null}
              </div>
              <p className="text-sm">{fact.statement}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={disabled}
                  className="rounded-md border border-slate-300 px-3 py-1 text-xs font-medium hover:bg-slate-50 disabled:opacity-50 dark:border-slate-600 dark:hover:bg-slate-800"
                  onClick={() => onApprove(fact.id)}
                >
                  Approve
                </button>
                <button
                  type="button"
                  disabled={disabled}
                  className="rounded-md border border-rose-300 px-3 py-1 text-xs font-medium text-rose-900 hover:bg-rose-50 disabled:opacity-50 dark:border-rose-700 dark:text-rose-100 dark:hover:bg-rose-950/40"
                  onClick={() => onChallenge(fact.id)}
                >
                  Challenge
                </button>
              </div>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
