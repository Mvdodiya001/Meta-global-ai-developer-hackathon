import { FACT_MISMATCH } from '../../content/glossary'
import type { ProofVerifyResult } from '../../api/types'
import { IconAlert, IconCheck } from '../ui/Icons'

type FactWordingEditorProps = {
  sentence: string
  result: ProofVerifyResult | null
  disabled?: boolean
  onChange: (value: string) => void
  onRecheck: () => void
  onReset: () => void
}

export function FactWordingEditor({
  sentence,
  result,
  disabled = false,
  onChange,
  onRecheck,
  onReset,
}: FactWordingEditorProps) {
  return (
    <section className="ct-panel" aria-labelledby="wording-heading">
      <div className="ct-panel-head">
        <div>
          <h2 id="wording-heading" className="ct-panel-title">
            Fact wording
          </h2>
          <p className="ct-panel-desc">
            Change one listed fact and re-check whether it still matches the document.
          </p>
        </div>
      </div>
      <div className="ct-panel-body space-y-3">
        <div className="ct-field">
          <label htmlFor="fact-sentence" className="ct-label">
            Fact sentence
          </label>
          <textarea
            id="fact-sentence"
            rows={3}
            value={sentence}
            disabled={disabled}
            onChange={(event) => onChange(event.target.value)}
            className="ct-textarea"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={onRecheck}
            disabled={disabled}
            className="ct-btn ct-btn--primary"
          >
            Re-check
          </button>
          <button
            type="button"
            onClick={onReset}
            disabled={disabled}
            className="ct-btn ct-btn--secondary"
          >
            Restore wording
          </button>
        </div>
        {result && !result.valid ? (
          <div className="ct-notice ct-notice--danger" role="alert">
            <IconAlert size={16} className="mt-0.5 shrink-0" />
            <p className="text-sm font-semibold">{FACT_MISMATCH}</p>
          </div>
        ) : null}
        {result?.valid ? (
          <div className="ct-notice">
            <IconCheck size={16} className="mt-0.5 shrink-0 text-ct-ok" />
            <p className="text-sm">This fact still matches the document.</p>
          </div>
        ) : null}
      </div>
    </section>
  )
}
