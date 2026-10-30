import type { ProofVerifyResult } from '../../api/types'

type ProofEditorProps = {
  value: string
  result: ProofVerifyResult | null
  onChange: (value: string) => void
  onVerify: () => void
  onReset: () => void
}

export function ProofEditor({ value, result, onChange, onVerify, onReset }: ProofEditorProps) {
  const codes = result?.errors
    .map((error) => String(error.code ?? ''))
    .filter(Boolean)
    .join(', ')

  return (
    <section className="ct-panel space-y-3 p-4" aria-labelledby="proof-editor-heading">
      <h2 id="proof-editor-heading" className="ct-section-title">
        Proof editor (tamper demo)
      </h2>
      <p className="text-sm text-slate-600 dark:text-slate-400">
        The checker has no model in it. Edit a premise and verify.
      </p>
      <label htmlFor="proof-json" className="block text-sm font-medium">
        Proof JSON
      </label>
      <textarea
        id="proof-json"
        rows={10}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 font-mono text-xs dark:border-slate-600 dark:bg-slate-900"
      />
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onVerify}
          className="rounded-md bg-blue-800 px-4 py-2 text-sm font-medium text-white hover:bg-blue-900 dark:bg-blue-700"
        >
          Verify proof
        </button>
        <button
          type="button"
          onClick={onReset}
          className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium dark:border-slate-600"
        >
          Reset proof
        </button>
      </div>
      {result ? (
        <div className="rounded-md border border-slate-200 p-3 text-sm dark:border-slate-700">
          {result.valid ? (
            <p>Checker: valid proof (PASS)</p>
          ) : (
            <>
              <p>Checker rejects this proof.</p>
              <p className="font-mono text-xs">{codes || 'invalid'}</p>
            </>
          )}
        </div>
      ) : null}
    </section>
  )
}
