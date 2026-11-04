import type { CounterfactualResult } from '../../api/types'
import { PREVIEW_LAW_CHANGE } from '../../content/glossary'
import { displayWouldFollow } from '../../utils/displayFields'
import { isLawyerSafeText, lawyerError } from '../../utils/lawyerCopy'
import { IconAlert, IconCheck } from '../ui/Icons'

type WhatIfPanelProps = {
  result: CounterfactualResult | null
  error: string | null
  changedWording: string[]
  affectedWording: Record<string, string>
}

export function WhatIfPanel({
  result,
  error,
  changedWording,
  affectedWording,
}: WhatIfPanelProps) {
  if (!result && !error) {
    return null
  }

  const note =
    result?.note && isLawyerSafeText(result.note) ? result.note : PREVIEW_LAW_CHANGE

  return (
    <section className="ct-panel" aria-labelledby="whatif-heading">
      <div className="ct-panel-head">
        <div>
          <h2 id="whatif-heading" className="ct-panel-title">
            Preview
          </h2>
          <p className="ct-panel-desc">
            A dry run against the selected version. Your findings are not modified.
          </p>
        </div>
        <span className="ct-badge ct-badge--info">Read-only</span>
      </div>
      <div className="ct-panel-body space-y-3">
        {error ? (
          <p role="alert" className="ct-notice ct-notice--danger">
            {lawyerError(new Error(error))}
          </p>
        ) : null}
        {result && !result.available ? (
          <p role="alert" className="ct-notice ct-notice--warn">
            {note}
          </p>
        ) : null}
        {result ? (
          <>
            <div>
              <h3 className="text-sm font-semibold text-ct-ink">Sections that would change</h3>
              {changedWording.length === 0 ? (
                <p className="mt-1 text-sm text-ct-muted">None.</p>
              ) : (
                <ul className="mt-1.5 space-y-1.5 text-sm text-ct-soft">
                  {changedWording.map((text) => (
                    <li key={text} className="flex gap-2">
                      <IconAlert size={14} className="mt-0.5 shrink-0 text-ct-warn" />
                      <span>{text}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div>
              <h3 className="text-sm font-semibold text-ct-ink">Answers that would be affected</h3>
              {result.affected.length === 0 ? (
                <p className="mt-1 text-sm text-ct-muted">None.</p>
              ) : (
                <ul className="ct-rows mt-1.5">
                  {result.affected.map((row, index) => (
                    <li
                      key={`${row.claim_id}-${index}`}
                      className="text-sm"
                    >
                      <p className="text-ct-soft">
                        {affectedWording[row.finding_id] ??
                          'An answer that relied on this section'}
                      </p>
                      <p className="mt-1 flex items-center gap-1.5 font-medium text-ct-ink">
                        {row.would_remain_valid ? (
                          <IconCheck size={14} className="text-ct-ok" />
                        ) : (
                          <IconAlert size={14} className="text-ct-warn" />
                        )}
                        {displayWouldFollow(row)}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </>
        ) : null}
        <p className="ct-help border-t border-ct-line pt-2.5">{PREVIEW_LAW_CHANGE}</p>
      </div>
    </section>
  )
}
