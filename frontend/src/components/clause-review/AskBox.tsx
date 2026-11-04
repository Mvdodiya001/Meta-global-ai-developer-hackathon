import { IconArrowRight, IconSearch } from '../ui/Icons'

type AskBoxProps = {
  question: string
  asOf: string
  asOfOptions: readonly string[]
  disabled: boolean
  onQuestionChange: (value: string) => void
  onAsOfChange: (value: string) => void
  onSubmit: () => void
}

/** Editorial question block: an open rule, not a boxed form. */
export function AskBox({
  question,
  asOf,
  asOfOptions,
  disabled,
  onQuestionChange,
  onAsOfChange,
  onSubmit,
}: AskBoxProps) {
  return (
    <form
      className="ct-panel"
      aria-labelledby="ask-heading"
      onSubmit={(event) => {
        event.preventDefault()
        onSubmit()
      }}
    >
      <div className="ct-panel-head">
        <div>
          <h2 id="ask-heading" className="ct-panel-title">
            Ask about a clause
          </h2>
          <p className="ct-panel-desc">
            A question, plus the date that fixes which version of the law applies.
          </p>
        </div>
        <span className="ct-badge">
          <IconSearch size={12} />
          Verified against recorded sources
        </span>
      </div>
      <div className="ct-panel-body space-y-3">
        <div className="ct-field">
          <label className="ct-label" htmlFor="verify-question">
            Legal question
          </label>
          <textarea
            id="verify-question"
            rows={3}
            value={question}
            disabled={disabled}
            onChange={(event) => onQuestionChange(event.target.value)}
            className="ct-textarea"
          />
        </div>
        <div className="flex flex-wrap items-end justify-between gap-3 border-t border-ct-line pt-3">
          <div className="ct-field">
            <label className="ct-label" htmlFor="verify-as-of">
              As-of date
            </label>
            <select
              id="verify-as-of"
              value={asOf}
              disabled={disabled}
              onChange={(event) => onAsOfChange(event.target.value)}
              className="ct-select w-auto"
            >
              {asOfOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            disabled={disabled || question.trim().length === 0}
            className="ct-btn ct-btn--primary ct-btn--lg"
          >
            Ask
            <IconArrowRight size={15} />
          </button>
        </div>
      </div>
    </form>
  )
}
