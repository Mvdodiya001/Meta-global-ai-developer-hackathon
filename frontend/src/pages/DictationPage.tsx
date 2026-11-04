import { useEffect, useRef, useState } from 'react'

import { api } from '../api/client'
import { DEMO_MATTER_ID, getApiBase } from '../api/config'
import type { Clause, DictationResult } from '../api/types'
import { PageHeader } from '../components/layout/PageHeader'
import { Button } from '../components/ui/Button'
import { IconCheck, IconMic, IconStop } from '../components/ui/Icons'
import { Panel } from '../components/ui/Panel'
import { StateMessage } from '../components/ui/StateMessage'
import { startLiveWavRecording, startWavRecording, type WavRecorder } from '../utils/wavRecorder'

const STEPS = ['Choose the clause', 'Record the fact', 'Check the transcript', 'Save and confirm'] as const

export function DictationPage() {
  const [clauses, setClauses] = useState<Clause[]>([])
  const [clauseId, setClauseId] = useState('')
  const [recording, setRecording] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [proposed, setProposed] = useState<DictationResult | null>(null)
  const [confirmed, setConfirmed] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  const [noticeTone, setNoticeTone] = useState<'info' | 'danger'>('info')
  const [busy, setBusy] = useState(false)
  const [hasAudio, setHasAudio] = useState(false)
  const [liveEnabled, setLiveEnabled] = useState(false)
  const [liveTranscript, setLiveTranscript] = useState('')
  const recorderRef = useRef<WavRecorder | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const audioRef = useRef<string>('')

  useEffect(() => {
    void (async () => {
      const docs = await api.documents(DEMO_MATTER_ID)
      const documentId = docs.documents[0]?.id
      if (documentId) {
        const list = await api.clauses(documentId)
        setClauses(list)
        setClauseId(list.find((clause) => clause.ref === '9.2')?.id ?? list[0]?.id ?? '')
      }
    })()
  }, [])

  useEffect(() => {
    return () => {
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [])

  function streamUrl(): string {
    const base = getApiBase().replace(/\/$/, '')
    if (base) {
      return `${base.replace(/^http/, 'ws')}/api/transcribe/stream`
    }
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${proto}//${window.location.host}/api/transcribe/stream`
  }

  function handleStreamMessage(event: MessageEvent<string>): void {
    let msg: {
      type: string
      ok?: boolean
      transcript?: string
    }
    try {
      msg = JSON.parse(event.data) as {
        type: string
        ok?: boolean
        transcript?: string
      }
    } catch {
      return
    }
    if ((msg.type === 'interim' || msg.type === 'final') && msg.ok && msg.transcript) {
      setLiveTranscript(msg.transcript)
    }
    if (msg.type === 'error') {
      setNotice('Live transcription unavailable. Your recording will still be transcribed after stop.')
      setNoticeTone('danger')
    }
    if (msg.type === 'final' && !msg.ok) {
      setNotice('Live transcription unavailable. Your recording will still be transcribed after stop.')
      setNoticeTone('danger')
    }
  }

  async function toggleRecording() {
    if (recording) {
      const base64 = await recorderRef.current?.stop()
      recorderRef.current = null
      setRecording(false)
      const socket = wsRef.current
      wsRef.current = null
      if (base64) {
        if (socket && socket.readyState === WebSocket.OPEN) {
          try {
            socket.send(JSON.stringify({ type: 'audio', audio_base64: base64 }))
            socket.send(JSON.stringify({ type: 'finalize' }))
          } catch {
            socket.close()
          }
        } else if (socket) {
          socket.close()
        }
        audioRef.current = base64
        setHasAudio(true)
        setNotice('Listening… writing down what you said')
        setNoticeTone('info')
        try {
          const heard = await api.transcribe({ matter_id: DEMO_MATTER_ID, audio_base64: base64 })
          setTranscript(heard.transcript)
          setNotice(null)
        } catch {
          setNotice('That recording could not be written down. Try again.')
          setNoticeTone('danger')
        }
      } else if (socket) {
        socket.close()
      }
      return
    }
    if (liveEnabled) {
      if (typeof WebSocket === 'undefined') {
        setNotice('Live transcription is not available in this browser. Record normally instead.')
        setNoticeTone('danger')
      } else {
        try {
          const socket = new WebSocket(streamUrl())
          wsRef.current = socket
          setLiveTranscript('')
          socket.onmessage = (event: MessageEvent<string>) => handleStreamMessage(event)
          socket.onerror = () => {
            setNotice(
              'Live transcription unavailable. Your recording will still be transcribed after stop.',
            )
            setNoticeTone('danger')
          }
        } catch {
          wsRef.current = null
          setNotice(
            'Live transcription unavailable. Your recording will still be transcribed after stop.',
          )
          setNoticeTone('danger')
        }
      }
      try {
        const socket = wsRef.current
        recorderRef.current = await startLiveWavRecording((partial) => {
          if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: 'audio', audio_base64: partial }))
          }
        })
        setRecording(true)
        setNotice('Recording… speak the fact, then stop')
        setNoticeTone('info')
      } catch {
        wsRef.current?.close()
        wsRef.current = null
        setNotice('The microphone is not available in this browser.')
        setNoticeTone('danger')
      }
      return
    }
    try {
      recorderRef.current = await startWavRecording()
      setRecording(true)
      setNotice('Recording… speak the fact, then stop')
      setNoticeTone('info')
    } catch {
      setNotice('The microphone is not available in this browser.')
      setNoticeTone('danger')
    }
  }

  async function saveProposed() {
    if (!audioRef.current) {
      setNotice('Record your voice first, then save.')
      setNoticeTone('danger')
      return
    }
    setBusy(true)
    setNotice(null)
    // The server transcribes the recording itself and stores that text
    // as the proposed fact; the preview above is only for reading.
    const result = await api
      .createDictation({
        matter_id: DEMO_MATTER_ID,
        clause_id: clauseId || null,
        audio_base64: audioRef.current,
      })
      .catch(() => null)
    setBusy(false)
    if (result) {
      setProposed(result)
      setConfirmed(false)
      return
    }
    setNotice('The fact could not be saved. Try again.')
    setNoticeTone('danger')
  }

  async function approve() {
    if (!proposed || busy) {
      return
    }
    setBusy(true)
    try {
      await api.approveFact(proposed.fact_id)
      setConfirmed(true)
      setNotice('Confirmed by you. This fact can now support an answer.')
      setNoticeTone('info')
    } catch {
      setNotice('This fact could not be confirmed. Try again.')
      setNoticeTone('danger')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="ct-page">
      <PageHeader
        eyebrow="Drafting"
        title="Dictate a fact"
        description="Speak a fact. It is saved as proposed — not relied on — until you confirm it."
      />

      <ol className="flex flex-wrap gap-x-5 gap-y-1" aria-label="Dictation steps">
        {STEPS.map((step, index) => {
          const active =
            (index === 0 && !hasAudio) ||
            (index === 1 && recording) ||
            (index === 2 && hasAudio && !proposed) ||
            (index === 3 && Boolean(proposed))
          return (
            <li
              key={step}
              className={[
                'flex items-baseline gap-2 text-xs',
                active ? 'font-semibold text-ct-accent' : 'text-ct-muted',
              ].join(' ')}
              aria-current={active ? 'step' : undefined}
            >
              <span className="ct-mono">{String(index + 1).padStart(2, '0')}</span>
              {step}
            </li>
          )
        })}
      </ol>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_20rem] xl:items-start">
        <Panel heading="Your voice" headingId="dictate-heading">
          <div className="ct-field">
            <label htmlFor="dictate-clause" className="ct-label">
              Clause this fact is about
            </label>
            <select
              id="dictate-clause"
              value={clauseId}
              onChange={(event) => setClauseId(event.target.value)}
              className="ct-select"
            >
              {clauses.map((clause) => (
                <option key={clause.id} value={clause.id}>
                  Clause {clause.ref} — {clause.heading}
                </option>
              ))}
            </select>
          </div>

          <div className="border-t border-ct-line pt-3">
            <div className="flex flex-wrap items-center gap-3">
              <Button
                variant={recording ? 'danger' : 'primary'}
                icon={recording ? <IconStop size={14} /> : <IconMic size={14} />}
                onClick={() => void toggleRecording()}
                disabled={busy}
              >
                {recording ? 'Stop recording' : 'Start recording'}
              </Button>
              {recording ? (
                <span className="flex items-center gap-2 text-sm font-medium text-ct-danger">
                  <span className="ct-dot ct-dot--pulse bg-current" aria-hidden="true" />
                  Recording
                </span>
              ) : (
                <span className="text-xs text-ct-muted">
                  The audio never leaves this session except for transcription.
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 pt-2">
              <input
                id="dictate-live"
                type="checkbox"
                checked={liveEnabled}
                disabled={recording || busy}
                onChange={(event) => setLiveEnabled(event.target.checked)}
              />
              <label htmlFor="dictate-live" className="text-xs text-ct-soft">
                Transcribe live
              </label>
            </div>
          </div>

          {liveEnabled ? (
            <div className="ct-field" aria-live="polite">
              <p className="ct-label">Live transcript (draft — not saved)</p>
              <p className="text-sm text-ct-soft">{liveTranscript || 'Listening…'}</p>
            </div>
          ) : null}

          <div className="ct-field">
            <label htmlFor="dictate-transcript" className="ct-label">
              What you said
            </label>
            <textarea
              id="dictate-transcript"
              rows={4}
              value={transcript}
              onChange={(event) => setTranscript(event.target.value)}
              placeholder="Your transcript will appear here after you stop recording."
              className="ct-textarea"
            />
            <p className="ct-help">
              The server stores the recording&rsquo;s own transcript as the proposed fact.
            </p>
          </div>

          {notice ? <StateMessage tone={noticeTone}>{notice}</StateMessage> : null}

          <div className="flex flex-wrap items-center gap-2 border-t border-ct-line pt-3">
            <Button
              variant="primary"
              disabled={!hasAudio || Boolean(proposed)}
              loading={busy && !proposed}
              onClick={() => void saveProposed()}
            >
              Save as proposed fact
            </Button>
            {proposed ? (
              <Button
                variant={confirmed ? 'ghost' : 'secondary'}
                disabled={confirmed}
                loading={busy && Boolean(proposed)}
                icon={confirmed ? <IconCheck size={14} /> : undefined}
                onClick={() => void approve()}
              >
                {confirmed ? 'Confirmed by you' : 'Confirm this fact'}
              </Button>
            ) : null}
          </div>

          {proposed ? (
            <div className="border-t border-ct-line pt-3">
              <p className="text-sm text-ct-soft">
                {confirmed
                  ? 'Confirmed by you. This fact can now support an answer.'
                  : 'Saved as proposed — not yet approved by you. Confirm it before any answer relies on it.'}
              </p>
            </div>
          ) : null}
        </Panel>

        <aside className="space-y-5">
          <Panel heading="What happens next" headingId="dictate-next" tone="quiet">
            <ol className="space-y-3 text-sm text-ct-soft">
              <li>
                <span className="font-semibold text-ct-ink">Proposed.</span> The transcript is
                stored as a proposed fact and cannot support an answer yet.
              </li>
              <li>
                <span className="font-semibold text-ct-ink">Confirmed.</span> Only your explicit
                confirmation lets an answer use it.
              </li>
              <li>
                <span className="font-semibold text-ct-ink">Traceable.</span> Any answer that
                uses the fact lists it under &ldquo;Facts relied on&rdquo;.
              </li>
            </ol>
          </Panel>
          <p className="ct-help">
            Record in a quiet room and check names, dates, and clause numbers in the transcript
            before confirming.
          </p>
        </aside>
      </div>
    </div>
  )
}
