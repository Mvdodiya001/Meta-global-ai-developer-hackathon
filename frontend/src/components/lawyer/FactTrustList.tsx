import { useState } from 'react'

import type { Fact, TrustClass } from '../../api/types'
import { asTrustClass } from '../../utils/trustClass'
import { TrustChip } from '../TrustChip'
import { LawyerReviewedBadge } from '../badges/LawyerReviewedBadge'
import { Button } from '../ui/Button'

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

/** Clean rows: trust label and inline actions, separated by hairlines. */
export function FactTrustList({
  facts,
  reviewedIds,
  disabled = false,
  onApprove,
  onChallenge,
}: FactTrustListProps) {
  const [expanded, setExpanded] = useState(false)
  const ordered = sortFacts(facts)
  const proposed = ordered.filter((fact) => asTrustClass(fact.trust_class) === 'ai_inferred').length
  const LIMIT = 6
  const visible = expanded ? ordered : ordered.slice(0, LIMIT)

  return (
    <section className="ct-panel" aria-labelledby="facts-heading">
      <div className="ct-panel-head">
        <div>
          <h2 id="facts-heading" className="ct-panel-title">
            Facts awaiting your approval
          </h2>
          <p className="ct-panel-desc">
            Proposed facts are not relied on. Confirm only what the document or your own
            knowledge supports.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {proposed > 0 ? <span className="ct-badge ct-badge--warn">{proposed} proposed</span> : null}
          <span className="ct-badge">{ordered.length}</span>
        </div>
      </div>
      <div className="ct-panel-body">
        {ordered.length === 0 ? (
          <p className="ct-empty">No facts are listed yet.</p>
        ) : (
          <ul className="ct-rows">
            {visible.map((fact) => {
              const trust = fact.trust_class as TrustClass
              const isProposed = trust === 'ai_inferred'
              return (
                <li key={fact.id} aria-label={fact.statement}>
                  <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                    <TrustChip trustClass={trust} label={fact.trust_label} />
                    {reviewedIds.includes(fact.id) ? <LawyerReviewedBadge /> : null}
                    {isProposed ? (
                      <span className="text-xs font-medium text-ct-warn">Not relied on</span>
                    ) : null}
                  </div>
                  <p className="mt-1.5 text-sm leading-relaxed text-ct-ink">{fact.statement}</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <Button
                      size="sm"
                      variant="secondary"
                      disabled={disabled}
                      onClick={() => onApprove(fact.id)}
                    >
                      Approve
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      disabled={disabled}
                      onClick={() => onChallenge(fact.id)}
                    >
                      Challenge
                    </Button>
                  </div>
                </li>
              )
            })}
          </ul>
        )}
        {ordered.length > LIMIT ? (
          <button
            type="button"
            className="ct-btn ct-btn--secondary ct-btn--sm mt-3"
            onClick={() => setExpanded((value) => !value)}
          >
            {expanded ? 'Show fewer facts' : `Show all ${ordered.length} facts`}
          </button>
        ) : null}
      </div>
    </section>
  )
}
