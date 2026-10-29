type AskBoxProps = {
  question: string
  asOf: string
  disabled: boolean
  onQuestionChange: (value: string) => void
  onAsOfChange: (value: string) => void
  onSubmit: () => void
}

export function AskBox({
  question,
  asOf,
  disabled,
  onQuestionChange,
  onAsOfChange,
  onSubmit,
}: AskBoxProps) {
  return (
    <form
      className="ct-panel space-y-3 p-4"
      aria-labelledby="ask-heading"
      onSubmit={(event) => {
        event.preventDefault()
        onSubmit()
      }}
    >
      <h2 id="ask-heading" className="ct-section-title">
        Ask about the selected clause
      </h2>
      <label className="block text-sm font-medium" htmlFor="verify-question">
        Legal question
      </label>
      <textarea
        id="verify-question"
        rows={3}
        value={question}
        disabled={disabled}
        onChange={(event) => onQuestionChange(event.target.value)}
        className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900"
      />
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className="mb-1 block text-sm font-medium" htmlFor="verify-as-of">
            As-of date
          </label>
          <input
            id="verify-as-of"
            type="date"
            value={asOf}
            disabled={disabled}
            onChange={(event) => onAsOfChange(event.target.value)}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900"
          />
        </div>
        <button
          type="submit"
          disabled={disabled || question.trim().length === 0}
          className="rounded-md bg-blue-800 px-4 py-2 text-sm font-medium text-white hover:bg-blue-900 disabled:opacity-50 dark:bg-blue-700"
        >
          Run verification
        </button>
      </div>
    </form>
  )
}
