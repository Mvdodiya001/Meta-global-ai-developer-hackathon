import type { Finding } from '../../api/types'
import { FindingCard } from '../FindingCard'
import { StatusBadge } from '../badges/StatusBadge'

type BeforeAfterSplitProps = {
  before: Finding
  after: Finding | null
}

export function BeforeAfterSplit({ before, after }: BeforeAfterSplitProps) {
  return (
    <section className="space-y-3" aria-labelledby="split-heading">
      <div>
        <h2 id="split-heading" className="ct-panel-title">
          Before / after
        </h2>
        <p className="mt-0.5 text-sm text-ct-muted">
          Earlier answers stay on file. A re-check writes a new answer; it does not overwrite
          history.
        </p>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="space-y-2">
          <h3 className="ct-section-title">Before</h3>
          <FindingCard finding={before} title="Earlier answer" />
        </div>
        <div className="space-y-2">
          <h3 className="ct-section-title">After</h3>
          {after ? (
            <FindingCard finding={after} title="Later answer" />
          ) : (
            <div className="flex min-h-[12rem] flex-col items-start justify-center gap-2 border-t border-ct-line pt-4">
              <div className="flex items-center gap-2">
                <StatusBadge status="UNKNOWN" />
              </div>
              <p className="text-sm text-ct-muted">
                Run Re-check to draft a new answer against the new law version.
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
