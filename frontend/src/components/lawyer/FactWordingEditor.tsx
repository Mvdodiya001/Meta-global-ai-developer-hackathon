import { FACT_MISMATCH } from '../../content/glossary'
import type { ProofVerifyResult } from '../../api/types'

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
    <section className="ct-panel space-y-3 p-4" aria-labelledby="wording-heading">
      <h2 id="wording-heading" className="ct-section-title">
        Fact wording
      </h2>
      <p className="text-sm text-slate-600 dark:text-slate-400">
        Change one listed fact and re-check whether it still matches the document.
      </p>
      <label htmlFor="fact-sentence" className="block text-sm font-medium">
        Fact sentence
      </label>
      <textarea
        id="fact-sentence"
        rows={3}
        value={sentence}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900"
      />
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onRecheck}
          disabled={disabled}
          className="rounded-md bg-blue-800 px-4 py-2 text-sm font-medium text-white hover:bg-blue-900 disabled:opacity-50 dark:bg-blue-700"
        >
          Re-check
        </button>
        <button
          type="button"
          onClick={onReset}
          disabled={disabled}
          className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium disabled:opacity-50 dark:border-slate-600"
        >
          Restore wording
        </button>
      </div>
      {result && !result.valid ? (
        <p className="text-sm font-medium">{FACT_MISMATCH}</p>
      ) : null}
      {result?.valid ? (
        <p className="text-sm">This fact still matches the document.</p>
      ) : null}
    </section>
  )
}
