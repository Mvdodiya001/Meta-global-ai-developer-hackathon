import type { DiffResult } from '../api/types'
import { sectionWording } from '../utils/lawyerCopy'
import { IconArrowRight } from './ui/Icons'

type DiffViewProps = {
  diff: DiffResult
}

/**
 * Editorial before/after: two document columns with a hairline between them
 * and inline change highlights, not nested cards.
 */
export function DiffView({ diff }: DiffViewProps) {
  // Show the amended provision named in changed_keys, not the first
  // provision in the list (which is the commencement section).
  const changedKey = diff.changed_keys[0]
  const before =
    diff.before.find((row) => row.key === changedKey) ?? diff.before[0]
  const after = diff.after.find((row) => row.key === changedKey) ?? diff.after[0]
  const heading = sectionWording(changedKey ?? '')

  return (
    <section className="ct-panel space-y-3" aria-labelledby="diff-heading">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2 id="diff-heading" className="ct-panel-title">
            Section change
          </h2>
          <p className="mt-0.5 text-sm text-ct-muted">{heading}</p>
        </div>
        <span className="ct-readonly-chip">Read-only comparison</span>
      </div>
      <div className="grid gap-x-8 gap-y-4 lg:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] lg:items-start">
        <div className="min-w-0">
          <div className="mb-2 flex items-center gap-2">
            <span className="ct-badge">Before</span>
            <span className="text-xs text-ct-muted">In force earlier</span>
          </div>
          <p className="whitespace-pre-wrap border-l-2 border-ct-line pl-3 font-serif text-[0.92rem] leading-relaxed text-ct-soft">
            {before?.text ?? 'No earlier wording'}
          </p>
        </div>
        <div className="hidden items-start justify-center pt-8 lg:flex" aria-hidden="true">
          <IconArrowRight size={18} className="text-ct-faint" />
        </div>
        <div className="min-w-0 lg:border-l lg:border-ct-line lg:pl-8">
          <div className="mb-2 flex items-center gap-2">
            <span className="ct-badge ct-badge--warn">After</span>
            <span className="text-xs text-ct-muted">Amended wording</span>
          </div>
          <p className="whitespace-pre-wrap border-l-2 border-ct-warn bg-ct-warnSoft/50 py-1 pl-3 font-serif text-[0.92rem] leading-relaxed text-ct-ink">
            {after?.text ?? 'No new wording'}
          </p>
        </div>
      </div>
    </section>
  )
}
