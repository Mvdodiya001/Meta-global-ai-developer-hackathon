import type { Finding } from '../../api/types'
import { FindingCard } from '../FindingCard'
import { IconInfo } from '../ui/Icons'

type UnknownClaimDemoProps = {
  question: string
  finding: Finding | null
  disabled?: boolean
  error?: string | null
  onQuestionChange: (value: string) => void
  onAsk: () => void
}

export function UnknownClaimDemo({
  question,
  finding,
  disabled = false,
  error = null,
  onQuestionChange,
  onAsk,
}: UnknownClaimDemoProps) {
  return (
    <section className="ct-panel" aria-labelledby="unknown-heading">
      <div className="ct-panel-head">
        <div>
          <h2 id="unknown-heading" className="ct-panel-title">
            When the file does not cover it
          </h2>
          <p className="ct-panel-desc">
            A question outside the material should return an honest unknown, with no invented
            citations.
          </p>
        </div>
      </div>
      <div className="ct-panel-body space-y-3">
        <div className="ct-field">
          <label htmlFor="unknown-question" className="ct-label">
            Question this file does not cover
          </label>
          <textarea
            id="unknown-question"
            rows={3}
            value={question}
            disabled={disabled}
            onChange={(event) => onQuestionChange(event.target.value)}
            className="ct-textarea"
          />
        </div>
        <button type="button" onClick={onAsk} disabled={disabled} className="ct-btn ct-btn--primary">
          Ask a question this file does not cover
        </button>
        {error ? (
          <div className="ct-notice ct-notice--danger" role="status">
            <IconInfo size={16} className="mt-0.5 shrink-0" />
            <p className="text-sm font-medium">{error}</p>
          </div>
        ) : null}
        {finding ? (
          <>
            <p className="text-sm text-ct-soft">
              No source on file covers this. No citations were invented.
            </p>
            <FindingCard finding={finding} title="Answer that cannot be determined" />
          </>
        ) : null}
      </div>
    </section>
  )
}
