import type { CounterfactualResult } from '../../api/types'
import { PREVIEW_LAW_CHANGE } from '../../content/glossary'
import { displayWouldFollow } from '../../utils/displayFields'
import { isLawyerSafeText, lawyerError } from '../../utils/lawyerCopy'

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
    <section className="ct-panel space-y-3 p-4" aria-labelledby="whatif-heading">
      <h2 id="whatif-heading" className="ct-section-title">
        Preview
      </h2>
      <p className="text-sm text-slate-700 dark:text-slate-300">{PREVIEW_LAW_CHANGE}</p>
      {error ? (
        <p role="alert" className="text-sm font-medium text-rose-800 dark:text-rose-200">
          {lawyerError(new Error(error))}
        </p>
      ) : null}
      {result && !result.available ? (
        <p role="alert" className="text-sm font-medium">
          {note}
        </p>
      ) : null}
      {result ? (
        <>
          <div>
            <h3 className="text-sm font-semibold">Sections that would change</h3>
            {changedWording.length === 0 ? (
              <p className="text-sm text-slate-600 dark:text-slate-400">None.</p>
            ) : (
              <ul className="mt-1 list-disc pl-5 text-sm">
                {changedWording.map((text) => (
                  <li key={text}>{text}</li>
                ))}
              </ul>
            )}
          </div>
          <div>
            <h3 className="text-sm font-semibold">Answers that would be affected</h3>
            {result.affected.length === 0 ? (
              <p className="text-sm text-slate-600 dark:text-slate-400">None.</p>
            ) : (
              <ul className="mt-1 space-y-2">
                {result.affected.map((row, index) => (
                  <li key={`${row.claim_id}-${index}`} className="text-sm">
                    <p>{affectedWording[row.finding_id] ?? 'An answer that relied on this section'}</p>
                    <p className="font-medium">{displayWouldFollow(row)}</p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      ) : null}
    </section>
  )
}
