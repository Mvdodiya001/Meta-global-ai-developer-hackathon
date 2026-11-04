import { useCallback, useEffect, useRef, useState } from 'react'

import { api } from '../api/client'
import { currentMatterId, preferredDocumentId } from '../api/demoSession'
import type { Clause, DocumentPages, Fact } from '../api/types'
import { PageHeader } from '../components/layout/PageHeader'
import { Button } from '../components/ui/Button'
import { IconFile, IconMic, IconStop } from '../components/ui/Icons'
import { Panel } from '../components/ui/Panel'
import { Skeleton } from '../components/ui/Skeleton'
import { StateMessage } from '../components/ui/StateMessage'
import { startWavRecording, type WavRecorder } from '../utils/wavRecorder'

export function ClausesPage() {
  const [clauses, setClauses] = useState<Clause[]>([])
  const [documentId, setDocumentId] = useState('')
  const [pages, setPages] = useState<DocumentPages | null>(null)
  const [selectedId, setSelectedId] = useState('')
  const [text, setText] = useState('')
  const [recording, setRecording] = useState(false)
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(true)
  const [notice, setNotice] = useState<string | null>(null)
  const [noticeTone, setNoticeTone] = useState<'info' | 'danger'>('info')
  const [explanations, setExplanations] = useState<Fact[]>([])
  const [explaining, setExplaining] = useState(false)
  const recorderRef = useRef<WavRecorder | null>(null)

  const loadExplanations = useCallback(async (clauseIds: string[]) => {
    try {
      const facts = await api.facts(currentMatterId())
      // Confirming mints a successor fact; the draft it supersedes (and
      // any dismissed/disputed copy) leaves the reading list.
      const superseded = new Set(
        facts
          .map((fact) => fact.supersedes_id)
          .filter((id): id is string => typeof id === 'string'),
      )
      setExplanations(
        facts.filter(
          (fact) =>
            (fact.structured as { kind?: unknown } | undefined)?.kind === 'explanation' &&
            fact.clause_id !== null &&
            clauseIds.includes(fact.clause_id) &&
            fact.trust_class !== 'disputed' &&
            !superseded.has(fact.id),
        ),
      )
    } catch {
      setExplanations([])
    }
  }, [])

  useEffect(() => {
    void (async () => {
      try {
        const docs = await api.documents(currentMatterId())
        const id = preferredDocumentId(docs.documents.map((doc) => doc.id)) ?? ''
        setDocumentId(id)
        if (id) {
          const list = await api.clauses(id)
          setClauses(list)
          try {
            setPages(await api.documentPages(id))
          } catch {
            setPages(null)
          }
          const first = list.find((clause) => clause.ref === '9.2') ?? list[0]
          if (first) {
            setSelectedId(first.id)
            setText(first.text)
          }
          await loadExplanations(list.map((clause) => clause.id))
        }
      } catch {
        setNotice('The clause list could not be loaded. Try again.')
        setNoticeTone('danger')
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  const selected = clauses.find((clause) => clause.id === selectedId)
  const original = selected?.text ?? ''

  function choose(clause: Clause) {
    setSelectedId(clause.id)
    setText(clause.text)
    setNotice(null)
  }

  const toggleRecording = useCallback(async () => {
    if (recording) {
      const base64 = await recorderRef.current?.stop()
      setRecording(false)
      if (base64) {
        try {
          const heard = await api.transcribe({
            matter_id: currentMatterId(),
            audio_base64: base64,
          })
          setText(heard.transcript)
          setNotice('Wording written down from your voice. Check it, then save.')
          setNoticeTone('info')
        } catch {
          setNotice('That recording could not be written down. Try again.')
          setNoticeTone('danger')
        }
      }
      return
    }
    try {
      recorderRef.current = await startWavRecording()
      setRecording(true)
      setNotice('Recording… dictate the new wording, then stop')
      setNoticeTone('info')
    } catch {
      setNotice('The microphone is not available in this browser.')
      setNoticeTone('danger')
    }
  }, [recording])

  async function save() {
    if (!selected || !documentId || saving) {
      return
    }
    setSaving(true)
    setNotice(null)
    const updated = await api
      .updateClause(documentId, selected.id, { text })
      .catch(() => null)
    if (!updated) {
      setSaving(false)
      setNotice('The new wording could not be saved. Try again.')
      setNoticeTone('danger')
      return
    }
    const list = await api.clauses(documentId)
    setClauses(list)
    setSelectedId(updated.id)
    setText(updated.text)
    setSaving(false)
    setNotice('Saved as a new version. The earlier wording stays on record.')
    setNoticeTone('info')
  }

  const changed = Boolean(selected) && text.trim() !== original.trim()

  async function generateExplanations() {
    if (!documentId || explaining) {
      return
    }
    setExplaining(true)
    try {
      await api.explainDocument(documentId)
      await loadExplanations(clauses.map((clause) => clause.id))
      setNotice('Explanations drafted below. They are suggestions — check each one.')
      setNoticeTone('info')
    } catch {
      setNotice('Explanations could not be drafted. Try again.')
      setNoticeTone('danger')
    } finally {
      setExplaining(false)
    }
  }

  async function confirmExplanation(fact: Fact) {
    await api.approveFact(fact.id).catch(() => null)
    await loadExplanations(clauses.map((clause) => clause.id))
  }

  async function dismissExplanation(fact: Fact) {
    await api.rejectFact(fact.id).catch(() => null)
    await loadExplanations(clauses.map((clause) => clause.id))
  }

  return (
    <div className="ct-page">
      <PageHeader
        eyebrow="Drafting"
        title="Update clause wording"
        description="Edit or dictate new wording. Saving writes a new version — the earlier wording stays on record, and facts recorded against it stay as they are."
      />

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_20rem] xl:items-start">
        <Panel
          heading="Clause wording"
          headingId="clauses-heading"
          description="One clause at a time. Nothing is overwritten."
          actions={
            selected ? (
              <span className="ct-badge">Clause {selected.ref}</span>
            ) : undefined
          }
        >
          {loading ? (
            <Skeleton lines={5} label="Loading clause wording" />
          ) : (
            <>
              <div className="ct-field">
                <label htmlFor="clause-picker" className="ct-label">
                  Clause
                </label>
                <select
                  id="clause-picker"
                  value={selectedId}
                  onChange={(event) => {
                    const clause = clauses.find((row) => row.id === event.target.value)
                    if (clause) choose(clause)
                  }}
                  className="ct-select"
                >
                  {clauses.map((clause) => (
                    <option key={clause.id} value={clause.id}>
                      Clause {clause.ref} — {clause.heading}
                    </option>
                  ))}
                </select>
              </div>

              <div className="ct-field">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <label htmlFor="clause-text" className="ct-label">
                    Wording of clause {selected?.ref ?? ''}
                  </label>
                  <span className="text-xs text-ct-faint">
                    {text.trim().length} characters
                  </span>
                </div>
                <textarea
                  id="clause-text"
                  rows={9}
                  value={text}
                  onChange={(event) => setText(event.target.value)}
                  className="ct-textarea font-serif text-[0.95rem] leading-relaxed"
                />
              </div>

              {notice ? (
                <StateMessage tone={noticeTone}>{notice}</StateMessage>
              ) : null}

              <div className="flex flex-wrap items-center gap-2 border-t border-ct-line pt-3">
                <Button
                  variant={recording ? 'danger' : 'secondary'}
                  icon={recording ? <IconStop size={14} /> : <IconMic size={14} />}
                  onClick={() => void toggleRecording()}
                >
                  {recording ? 'Stop recording' : 'Dictate the wording'}
                </Button>
                <Button
                  variant="primary"
                  disabled={!text.trim() || !changed}
                  loading={saving}
                  onClick={() => void save()}
                >
                  Save new wording
                </Button>
                {changed ? (
                  <span className="text-xs text-ct-warn">Unsaved changes</span>
                ) : (
                  <span className="ct-help">No changes to save</span>
                )}
              </div>
            </>
          )}
        </Panel>

        <div className="space-y-5">
          <Panel
            heading="Versioning"
            headingId="clauses-versioning"
            tone="quiet"
          >
            <ul className="space-y-2.5 text-sm text-ct-soft">
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-ct-accent" />
                Saving creates a new version with its own wording.
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-ct-accent" />
                The earlier version stays available for comparison.
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-ct-accent" />
                Answers already made are not rewritten retroactively.
              </li>
            </ul>
          </Panel>

          {pages && pages.pages.length > 0 ? (
            <Panel
              heading="Where each page came from"
              headingId="clauses-pages"
              description="Transcribed pages deserve a closer look before you rely on their wording."
            >
              <ul className="ct-rows">
                {pages.pages.map((page) => (
                  <li
                    key={page.page}
                    className="flex items-center gap-2 !py-2 text-sm"
                  >
                    <IconFile size={14} className="shrink-0 text-ct-muted" />
                    <span className="text-ct-soft">
                      Page {page.page} —{' '}
                      {page.source === 'vision'
                        ? 'transcribed from a scan'
                        : 'read from the file'}
                    </span>
                    {page.confidence === 'low' ? (
                      <span className="ct-badge ct-badge--warn">Check this page</span>
                    ) : null}
                  </li>
                ))}
              </ul>
            </Panel>
          ) : null}
        </div>
      </div>

      <Panel
        heading="Plain-language explanations"
        headingId="clauses-explain"
        description="AI suggestion — may be wrong. This is not legal advice. Confirm only what you have checked against the clause."
        actions={
          <Button
            variant="secondary"
            size="sm"
            disabled={!documentId || explaining}
            loading={explaining}
            onClick={() => void generateExplanations()}
          >
            Explain all clauses
          </Button>
        }
      >
        {explanations.length === 0 ? (
          <p className="ct-empty">
            No explanations yet. Draft them and each clause gets a plain-language reading
            you can confirm or dismiss.
          </p>
        ) : (
          <ul className="ct-rows">
            {explanations.map((fact) => {
              const structured = fact.structured as Record<string, string>
              const confirmed = fact.trust_class === 'lawyer_confirmed'
              return (
                <li key={fact.id}>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-medium text-ct-ink">
                      Clause {structured.clause_ref ?? ''}
                    </span>
                    {confirmed ? (
                      <span className="ct-badge ct-badge--ok">Confirmed by you</span>
                    ) : (
                      <span className="ct-badge ct-badge--accent">
                        AI draft — not yet reviewed
                      </span>
                    )}
                  </div>
                  <dl className="mt-1.5 space-y-1 text-sm text-ct-soft">
                    <div>
                      <dt className="font-semibold text-ct-ink">What this says</dt>
                      <dd>{structured.says}</dd>
                    </div>
                    <div>
                      <dt className="font-semibold text-ct-ink">Who it binds</dt>
                      <dd>{structured.binds}</dd>
                    </div>
                    <div>
                      <dt className="font-semibold text-ct-ink">What triggers it</dt>
                      <dd>{structured.triggers}</dd>
                    </div>
                    <div>
                      <dt className="font-semibold text-ct-ink">Worth checking</dt>
                      <dd>{structured.check}</dd>
                    </div>
                  </dl>
                  {!confirmed ? (
                    <div className="mt-2 flex flex-wrap gap-2">
                      <Button size="sm" variant="primary" onClick={() => void confirmExplanation(fact)}>
                        Confirm
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => void dismissExplanation(fact)}>
                        Dismiss
                      </Button>
                    </div>
                  ) : null}
                </li>
              )
            })}
          </ul>
        )}
      </Panel>
    </div>
  )
}
