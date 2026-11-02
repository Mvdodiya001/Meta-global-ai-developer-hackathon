import { useEffect, useState } from 'react'

import { api } from '../../api/client'
import { DEMO_MATTER_ID } from '../../api/config'
import type { Clause, Fact } from '../../api/types'
import { fileToBase64, isWavFile } from '../../utils/fileBase64'
import { lawyerError } from '../../utils/lawyerCopy'
import { asTrustClass } from '../../utils/trustClass'
import { AiDraftBadge } from '../badges/AiDraftBadge'
import { TrustChip } from '../TrustChip'

const FALLBACK_CLAUSE = 'CL-10'

type DictationPanelProps = {
  clauses: Clause[]
  defaultClauseId: string
  onFactProposed: (fact: Fact) => void
  onApprove: (factId: string) => void
}

export function DictationPanel({
  clauses,
  defaultClauseId,
  onFactProposed,
  onApprove,
}: DictationPanelProps) {
  const [clauseId, setClauseId] = useState(defaultClauseId || FALLBACK_CLAUSE)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fact, setFact] = useState<Fact | null>(null)

  useEffect(() => {
    setClauseId(defaultClauseId || FALLBACK_CLAUSE)
  }, [defaultClauseId])

  async function handleFile(file: File | undefined) {
    if (!file) {
      return
    }
    if (!isWavFile(file)) {
      setError('Use a WAV recording.')
      return
    }
    setBusy(true)
    setError(null)
    try {
      const audio_base64 = await fileToBase64(file)
      const next = await api.createDictation({
        matter_id: DEMO_MATTER_ID,
        clause_id: clauseId,
        audio_base64,
      })
      const proposed: Fact = {
        id: next.fact_id,
        matter_id: DEMO_MATTER_ID,
        clause_id: clauseId,
        statement: next.transcript,
        structured: {},
        origin: 'voice_dictation',
        trust_class: next.trust_class,
        trust_label: 'Proposed — not yet approved by you',
        created_at: new Date().toISOString(),
      }
      setFact(proposed)
      onFactProposed(proposed)
    } catch (err) {
      setFact(null)
      setError(lawyerError(err))
    } finally {
      setBusy(false)
    }
  }

  const approved = fact ? asTrustClass(fact.trust_class) === 'lawyer_confirmed' : false

  return (
    <section className="ct-panel space-y-3 p-4" aria-labelledby="dictation-heading">
      <h2 id="dictation-heading" className="ct-section-title">
        Dictate a fact
      </h2>
      <label htmlFor="dictation-clause" className="block text-sm font-medium">
        Clause
      </label>
      <select
        id="dictation-clause"
        value={clauseId}
        onChange={(event) => setClauseId(event.target.value)}
        className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900"
      >
        {clauses.map((clause) => (
          <option key={clause.id} value={clause.id}>
            {clause.ref} {clause.heading}
          </option>
        ))}
        {clauses.every((clause) => clause.id !== clauseId) ? (
          <option value={clauseId}>Current clause</option>
        ) : null}
      </select>
      <label htmlFor="dictation-audio" className="block text-sm font-medium">
        Dictate a fact
      </label>
      <input
        id="dictation-audio"
        type="file"
        accept="audio/wav"
        disabled={busy}
        className="block w-full text-sm file:mr-3 file:rounded-md file:border file:border-slate-300 file:bg-white file:px-3 file:py-1.5 file:text-sm file:font-medium dark:file:border-slate-600 dark:file:bg-slate-900"
        onChange={(event) => {
          void handleFile(event.target.files?.[0])
          event.target.value = ''
        }}
      />
      {busy ? <p className="text-sm">Listening…</p> : null}
      {error ? (
        <p role="alert" className="text-sm font-medium text-rose-800 dark:text-rose-200">
          {error}
        </p>
      ) : null}
      {fact ? (
        <div className="space-y-2 rounded-md border border-slate-200 p-3 dark:border-slate-700">
          <div className="flex flex-wrap items-center gap-2">
            <TrustChip trustClass={asTrustClass(fact.trust_class)} label={fact.trust_label} />
            {approved ? null : <AiDraftBadge label="AI draft — not yet reviewed" />}
          </div>
          <p className="text-sm">{fact.statement}</p>
          {approved ? null : (
            <button
              type="button"
              className="rounded-md border border-slate-300 px-3 py-1 text-xs font-medium hover:bg-slate-50 dark:border-slate-600 dark:hover:bg-slate-800"
              onClick={() => {
                onApprove(fact.id)
                setFact({
                  ...fact,
                  trust_class: 'lawyer_confirmed',
                  trust_label: 'Confirmed by you',
                })
              }}
            >
              Approve
            </button>
          )}
        </div>
      ) : null}
    </section>
  )
}
