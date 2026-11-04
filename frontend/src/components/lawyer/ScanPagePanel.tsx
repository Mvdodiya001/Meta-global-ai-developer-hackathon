import { useState } from 'react'

import { api } from '../../api/client'
import { currentMatterId } from '../../api/demoSession'
import type { ScanResult } from '../../api/types'
import { fileToBase64, scanMediaType } from '../../utils/fileBase64'
import { lawyerError } from '../../utils/lawyerCopy'
import { asTrustClass } from '../../utils/trustClass'
import { AiDraftBadge } from '../badges/AiDraftBadge'
import { TrustChip } from '../TrustChip'
import { IconFile } from '../ui/Icons'
import { StateMessage } from '../ui/StateMessage'

export function ScanPagePanel() {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ScanResult | null>(null)

  async function handleFile(file: File | undefined) {
    if (!file) {
      return
    }
    const mediaType = scanMediaType(file)
    if (!mediaType) {
      setError('Use a PNG or JPEG page.')
      return
    }
    setBusy(true)
    setError(null)
    try {
      const image_base64 = await fileToBase64(file)
      const next = await api.scanPage({
        matter_id: currentMatterId(),
        title: file.name,
        image_base64,
        media_type: mediaType,
      })
      setResult(next)
    } catch (err) {
      setResult(null)
      setError(lawyerError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="ct-panel" aria-labelledby="scan-heading">
      <div className="ct-panel-head">
        <div>
          <h2 id="scan-heading" className="ct-panel-title">
            Add a scanned clause page
          </h2>
          <p className="ct-panel-desc">
            The extract is an AI draft — not yet reviewed, and not legal advice.
          </p>
        </div>
      </div>
      <div className="ct-panel-body space-y-3">
        <div className="ct-field">
          <label htmlFor="scan-page-file" className="ct-label">
            Add a scanned clause page
          </label>
          <input
            id="scan-page-file"
            type="file"
            accept="image/png,image/jpeg"
            disabled={busy}
            className="block w-full text-sm text-ct-soft file:mr-3 file:cursor-pointer file:rounded file:border file:border-ct-lineStrong file:bg-ct-surface file:px-2.5 file:py-1 file:text-xs file:font-semibold file:text-ct-soft"
            onChange={(event) => {
              const file = event.target.files?.[0]
              void handleFile(file)
              event.target.value = ''
            }}
          />
        </div>
        {busy ? (
          <p className="flex items-center gap-2 text-sm text-ct-muted" role="status">
            <span className="ct-spinner" aria-hidden="true" />
            Reading the page…
          </p>
        ) : null}
        {error ? (
          <StateMessage tone="danger" live="alert">
            {error}
          </StateMessage>
        ) : null}
        {result ? (
          <div className="border-t border-ct-line pt-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-semibold text-ct-ink">
                Clause {result.clause.ref}
              </span>
              <TrustChip
                trustClass={asTrustClass(result.fact.trust_class)}
                label={result.fact.trust_label}
              />
              <AiDraftBadge label="AI draft — not yet reviewed" />
            </div>
            <p className="text-sm leading-relaxed text-ct-soft">{result.fact.statement}</p>
          </div>
        ) : (
          <p className="flex items-start gap-2 text-xs text-ct-muted">
            <IconFile size={14} className="mt-0.5 shrink-0" />
            Nothing is added to the matter until you confirm the extracted wording.
          </p>
        )}
      </div>
    </section>
  )
}
