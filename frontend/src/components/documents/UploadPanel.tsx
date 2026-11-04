import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { api } from '../../api/client'
import { currentMatterId, rememberDocumentId } from '../../api/demoSession'
import type { DocumentPages, IntakeJob } from '../../api/types'
import { fileToBase64 } from '../../utils/fileBase64'
import { isLawyerSafeText } from '../../utils/lawyerCopy'
import { Button } from '../ui/Button'
import { IconArrowRight, IconCheck, IconUpload } from '../ui/Icons'
import { StateMessage } from '../ui/StateMessage'

const ACCEPTED: Record<string, string> = {
  'application/pdf': '.pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
  'text/plain': '.txt',
}

function mediaTypeFor(file: File): string | null {
  if (file.type && file.type in ACCEPTED) {
    return file.type
  }
  const name = file.name.toLowerCase()
  if (name.endsWith('.pdf')) return 'application/pdf'
  if (name.endsWith('.docx')) {
    return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  }
  if (name.endsWith('.txt')) return 'text/plain'
  return null
}

function pageOriginLabel(source: string): string {
  return source === 'vision' ? 'transcribed from a scan' : 'read from the file'
}

function stageLabel(job: IntakeJob): string {
  if (job.status === 'queued') {
    return 'Waiting to start'
  }
  const stage = job.stage?.trim()
  return stage && isLawyerSafeText(stage) ? stage : 'Working through the document'
}

/**
 * One prominent document dropzone: title plus a single dashed surface for
 * the file. Progress and page origins read as document metadata below it.
 */
export function UploadPanel() {
  const [title, setTitle] = useState('')
  const [fileName, setFileName] = useState('')
  const [payload, setPayload] = useState<{ base64: string; mediaType: string } | null>(null)
  const [job, setJob] = useState<IntakeJob | null>(null)
  const [pages, setPages] = useState<DocumentPages | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [noticeTone, setNoticeTone] = useState<'danger' | 'info'>('info')
  const [busy, setBusy] = useState(false)
  const [dragging, setDragging] = useState(false)
  const pollRef = useRef<number | null>(null)

  useEffect(
    () => () => {
      if (pollRef.current !== null) {
        window.clearInterval(pollRef.current)
      }
    },
    [],
  )

  async function choose(file: File | undefined) {
    if (!file) {
      return
    }
    const mediaType = mediaTypeFor(file)
    if (!mediaType) {
      setNotice('That file type is not supported. Upload a PDF, DOCX, or text file.')
      setNoticeTone('danger')
      return
    }
    setFileName(file.name)
    setNotice(null)
    try {
      setPayload({ base64: await fileToBase64(file), mediaType })
    } catch {
      setNotice('That file could not be read. Try again.')
      setNoticeTone('danger')
    }
  }

  async function upload() {
    if (!payload || busy) {
      return
    }
    setBusy(true)
    setNotice(null)
    setJob(null)
    setPages(null)
    try {
      const created = await api.uploadDocument(currentMatterId(), {
        title: title.trim() || fileName || 'Uploaded document',
        file_base64: payload.base64,
        media_type: payload.mediaType,
      })
      // From here on, every screen works on this document.
      rememberDocumentId(created.document_id)
      const poll = async () => {
        const status = await api.jobStatus(created.job_id)
        setJob(status)
        if (status.status === 'done' || status.status === 'failed') {
          if (pollRef.current !== null) {
            window.clearInterval(pollRef.current)
            pollRef.current = null
          }
          setBusy(false)
          if (status.status === 'failed') {
            const reason = status.error ?? ''
            const offline = /no cassette|cassette/i.test(reason)
            setNotice(
              offline
                ? 'This file is fine, but the demo is offline: it can only replay files it has seen before. Run the server with LLM_MODE=live to process new files.'
                : 'Processing failed. The file may be unreadable.',
            )
            setNoticeTone('danger')
          } else {
            setPages(await api.documentPages(created.document_id))
          }
        }
      }
      await poll()
      if (pollRef.current !== null) {
        window.clearInterval(pollRef.current)
      }
      pollRef.current = window.setInterval(() => {
        void poll().catch(() => {
          /* polling continues until done */
        })
      }, 1500)
    } catch {
      setBusy(false)
      setNotice('The upload could not be completed. Try again.')
      setNoticeTone('danger')
    }
  }

  const doneCount =
    job?.result && typeof job.result === 'object' && 'clauses' in job.result
      ? String((job.result as { clauses: unknown }).clauses)
      : '?'

  return (
    <section className="ct-panel ct-panel--surface" aria-labelledby="upload-heading">
      <div className="ct-panel-head">
        <div>
          <h2 id="upload-heading" className="ct-panel-title">
            Upload a document
          </h2>
          <p className="ct-panel-desc">
            PDF, DOCX, or text. Scanned pages are transcribed, and you can check where each
            page came from before relying on the answers.
          </p>
        </div>
        <div className="flex flex-wrap gap-1.5" aria-hidden="true">
          {['PDF', 'DOCX', 'TXT'].map((format) => (
            <span key={format} className="ct-badge ct-mono text-[0.66rem]">
              {format}
            </span>
          ))}
        </div>
      </div>

      <div className="ct-panel-body">
        <div className="ct-field">
          <label htmlFor="upload-title" className="ct-label">
            Title
          </label>
          <input
            id="upload-title"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="e.g. Vendor DPA — March"
            className="ct-input max-w-md"
          />
          <p className="ct-help">Optional. A clear title makes the document easier to find.</p>
        </div>

        <label
          htmlFor="upload-file"
          onDragOver={(event) => {
            event.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault()
            setDragging(false)
            void choose(event.dataTransfer.files?.[0])
          }}
          className={[
            'mt-1 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-md border border-dashed px-6 py-9 text-center transition-colors',
            dragging
              ? 'border-ct-accent bg-ct-accentSoft/60'
              : 'border-ct-lineStrong bg-ct-surface2 hover:border-ct-accent hover:bg-ct-accentSoft/40',
          ].join(' ')}
        >
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-ct-accentSoft text-ct-accent">
            <IconUpload size={18} />
          </span>
          <span className="text-sm font-semibold text-ct-ink">
            {fileName || 'Drop a document here, or choose a file'}
          </span>
          <span className="ct-help">
            PDF, DOCX, or text. Nothing is relied on until you review the extracted clauses.
          </span>
          <input
            id="upload-file"
            type="file"
            aria-label="File"
            accept=".pdf,.docx,.txt"
            onChange={(event) => void choose(event.target.files?.[0])}
            className="sr-only"
          />
          <span className="ct-btn ct-btn--secondary ct-btn--sm pointer-events-none" aria-hidden="true">
            Choose a file
          </span>
        </label>

        {notice ? (
          <StateMessage tone={noticeTone} live="status">
            {notice}
          </StateMessage>
        ) : null}

        <div className="mt-1 flex flex-wrap items-center gap-3">
          <Button
            variant="primary"
            disabled={!payload || busy}
            loading={busy}
            icon={<IconUpload size={15} />}
            onClick={() => void upload()}
          >
            {busy ? 'Processing…' : 'Upload and extract'}
          </Button>
        </div>

        {job ? (
          <div className="border-t border-ct-line pt-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-medium text-ct-ink" role="status">
                {job.status === 'done'
                  ? `Done — ${doneCount} clauses extracted.`
                  : stageLabel(job)}
              </p>
              {job.status !== 'done' && job.status !== 'failed' ? (
                <span className="ct-badge ct-badge--accent">
                  <span className="ct-dot ct-dot--pulse" aria-hidden="true" />
                  In progress
                </span>
              ) : null}
              {job.status === 'done' ? (
                <span className="ct-badge ct-badge--ok">
                  <IconCheck size={12} />
                  Ready
                </span>
              ) : null}
            </div>
            {job.status !== 'done' && job.status !== 'failed' ? (
              <div className="ct-progress mt-2" role="presentation">
                <div className="ct-progress-bar" />
              </div>
            ) : null}
          </div>
        ) : null}

        {pages && pages.pages.length > 0 ? (
          <div>
            <h3 className="ct-section-title">Page origins</h3>
            <ul className="ct-rows mt-2">
              {pages.pages.map((page) => (
                <li
                  key={page.page}
                  className="flex items-baseline gap-2.5 !py-2 text-sm"
                >
                  <span className="ct-mono text-xs text-ct-faint">
                    {String(page.page).padStart(2, '0')}
                  </span>
                  <span className="text-ct-soft">
                    Page {page.page} — {pageOriginLabel(page.source)}
                  </span>
                  {page.confidence === 'low' ? (
                    <span className="ct-badge ct-badge--warn">Check this page</span>
                  ) : null}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {job?.status === 'done' && job.document_id ? (
          <Link to="/clauses" className="ct-link inline-flex items-center gap-1 text-sm">
            Review its clauses
            <IconArrowRight size={14} />
          </Link>
        ) : null}
      </div>
    </section>
  )
}
