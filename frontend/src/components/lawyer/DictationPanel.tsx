import { useEffect, useState } from 'react'

import { api } from '../../api/client'
import { currentMatterId } from '../../api/demoSession'
import type { Clause, Fact } from '../../api/types'
import { fileToBase64, isWavFile } from '../../utils/fileBase64'
import { lawyerError } from '../../utils/lawyerCopy'
import { asTrustClass } from '../../utils/trustClass'
import { AiDraftBadge } from '../badges/AiDraftBadge'
import { TrustChip } from '../TrustChip'
import { Button } from '../ui/Button'
import { StateMessage } from '../ui/StateMessage'

const FALLBACK_CLAUSE = 'CL-10'

type DictationPanelProps = {
  clauses: Clause[]
  defaultClauseId: string
  onFactProposed: (fact: Fact) => void
  onApprove: (factId: string) => Promise<boolean>
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
  const [approving, setApproving] = useState(false)

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
        matter_id: currentMatterId(),
        clause_id: clauseId,
        audio_base64,
      })
      const proposed: Fact = {
        id: next.fact_id,
        matter_id: currentMatterId(),
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
    <section className="ct-panel" aria-labelledby="dictation-heading">
      <div className="ct-panel-head">
        <div>
          <h2 id="dictation-heading" className="ct-panel-title">
            Dictate a fact
          </h2>
          <p className="ct-panel-desc">
            A recording becomes a proposed fact. It is not relied on until you approve it.
          </p>
        </div>
      </div>
      <div className="ct-panel-body space-y-3">
        <div className="ct-field">
          <label htmlFor="dictation-clause" className="ct-label">
            Clause
          </label>
          <select
            id="dictation-clause"
            value={clauseId}
            onChange={(event) => setClauseId(event.target.value)}
            className="ct-select"
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
        </div>
        <div className="ct-field">
          <label htmlFor="dictation-audio" className="ct-label">
            Dictate a fact
          </label>
          <input
            id="dictation-audio"
            type="file"
            accept="audio/wav"
            disabled={busy}
            className="block w-full text-sm text-ct-soft file:mr-3 file:cursor-pointer file:rounded file:border file:border-ct-lineStrong file:bg-ct-surface file:px-2.5 file:py-1 file:text-xs file:font-semibold file:text-ct-soft"
            onChange={(event) => {
              void handleFile(event.target.files?.[0])
              event.target.value = ''
            }}
          />
        </div>
        {busy ? (
          <p className="flex items-center gap-2 text-sm text-ct-muted" role="status">
            <span className="ct-spinner" aria-hidden="true" />
            Listening…
          </p>
        ) : null}
        {error ? (
          <StateMessage tone="danger" live="alert">
            {error}
          </StateMessage>
        ) : null}
        {fact ? (
          <div className="border-t border-ct-line pt-3">
            <div className="flex flex-wrap items-center gap-2">
              <TrustChip trustClass={asTrustClass(fact.trust_class)} label={fact.trust_label} />
              {approved ? null : <AiDraftBadge label="AI draft — not yet reviewed" />}
            </div>
            <p className="text-sm leading-relaxed text-ct-soft">{fact.statement}</p>
            {approved ? null : (
              <Button
                size="sm"
                variant="secondary"
                loading={approving}
                onClick={() => {
                  setApproving(true)
                  void onApprove(fact.id)
                    .then((ok) => {
                      if (ok) {
                        setFact({
                          ...fact,
                          trust_class: 'lawyer_confirmed',
                          trust_label: 'Confirmed by you',
                        })
                      }
                    })
                    .finally(() => setApproving(false))
                }}
              >
                Approve
              </Button>
            )}
          </div>
        ) : null}
      </div>
    </section>
  )
}
