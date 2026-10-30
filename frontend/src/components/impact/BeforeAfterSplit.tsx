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
      <h2 id="split-heading" className="ct-section-title">
        Before / after
      </h2>
      <p className="text-sm text-slate-600 dark:text-slate-400">
        Old findings stay on file. Re-verify writes a new row; it does not overwrite history.
      </p>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="space-y-2">
          <h3 className="text-sm font-medium">Before · {before.id}</h3>
          <FindingCard finding={before} />
        </div>
        <div className="space-y-2">
          <h3 className="text-sm font-medium">After · {after?.id ?? 'pending'}</h3>
          {after ? (
            <FindingCard finding={after} />
          ) : (
            <div className="ct-panel p-4 text-sm text-slate-600 dark:text-slate-400">
              Run Re-verify to draft a new finding against the new source version.
              <div className="mt-2">
                <StatusBadge status="UNKNOWN" />
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
