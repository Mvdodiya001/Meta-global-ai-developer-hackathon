import type { Finding } from '../../api/types'
import { FindingCard } from '../FindingCard'

type UnknownClaimDemoProps = {
  question: string
  finding: Finding | null
  disabled?: boolean
  onQuestionChange: (value: string) => void
  onAsk: () => void
}

export function UnknownClaimDemo({
  question,
  finding,
  disabled = false,
  onQuestionChange,
  onAsk,
}: UnknownClaimDemoProps) {
  return (
    <section className="ct-panel space-y-3 p-4" aria-labelledby="unknown-heading">
      <h2 id="unknown-heading" className="ct-section-title">
        Honest unknown
      </h2>
      <label htmlFor="unknown-question" className="block text-sm font-medium">
        Out-of-corpus question
      </label>
      <textarea
        id="unknown-question"
        rows={3}
        value={question}
        disabled={disabled}
        onChange={(event) => onQuestionChange(event.target.value)}
        className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900"
      />
      <button
        type="button"
        onClick={onAsk}
        disabled={disabled}
        className="rounded-md bg-blue-800 px-4 py-2 text-sm font-medium text-white hover:bg-blue-900 disabled:opacity-50 dark:bg-blue-700"
      >
        Ask out-of-corpus claim
      </button>
      {finding ? (
        <>
          <p className="text-sm text-slate-700 dark:text-slate-300">
            No source on file covers this. Zero citations invented.
          </p>
          <FindingCard finding={finding} />
        </>
      ) : null}
    </section>
  )
}
