import type { DiffResult } from '../api/types'
import { sectionWording } from '../utils/lawyerCopy'

type DiffViewProps = {
  diff: DiffResult
}

export function DiffView({ diff }: DiffViewProps) {
  // Show the amended provision named in changed_keys, not the first
  // provision in the list (which is the commencement section).
  const changedKey = diff.changed_keys[0]
  const before =
    diff.before.find((row) => row.key === changedKey) ?? diff.before[0]
  const after = diff.after.find((row) => row.key === changedKey) ?? diff.after[0]
  const heading = sectionWording(changedKey ?? '')

  return (
    <section className="space-y-3" aria-labelledby="diff-heading">
      <h2 id="diff-heading" className="ct-section-title">
        Section change
      </h2>
      <p className="text-sm text-slate-600 dark:text-slate-400">{heading}</p>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="ct-panel p-4">
          <h3 className="mb-2 text-sm font-medium">Before</h3>
          <p className="whitespace-pre-wrap text-sm leading-relaxed">
            {before?.text ?? 'No earlier wording'}
          </p>
        </div>
        <div className="ct-panel border-l-4 border-l-orange-400 p-4">
          <h3 className="mb-2 text-sm font-medium">After</h3>
          <p className="whitespace-pre-wrap text-sm leading-relaxed">
            {after?.text ?? 'No new wording'}
          </p>
        </div>
      </div>
    </section>
  )
}
