import { useState } from 'react'

import { api } from '../../api/client'
import { DEMO_MATTER_ID } from '../../api/config'
import type { ScanResult } from '../../api/types'
import { fileToBase64, scanMediaType } from '../../utils/fileBase64'
import { lawyerError } from '../../utils/lawyerCopy'
import { asTrustClass } from '../../utils/trustClass'
import { AiDraftBadge } from '../badges/AiDraftBadge'
import { TrustChip } from '../TrustChip'

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
        matter_id: DEMO_MATTER_ID,
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
    <section className="ct-panel space-y-3 p-4" aria-labelledby="scan-heading">
      <h2 id="scan-heading" className="ct-section-title">
        Add a scanned clause page
      </h2>
      <p className="text-sm text-slate-700 dark:text-slate-300">
        The extract is an AI draft — not yet reviewed, and not legal advice.
      </p>
      <label htmlFor="scan-page-file" className="block text-sm font-medium">
        Add a scanned clause page
      </label>
      <input
        id="scan-page-file"
        type="file"
        accept="image/png,image/jpeg"
        disabled={busy}
        className="block w-full text-sm file:mr-3 file:rounded-md file:border file:border-slate-300 file:bg-white file:px-3 file:py-1.5 file:text-sm file:font-medium dark:file:border-slate-600 dark:file:bg-slate-900"
        onChange={(event) => {
          const file = event.target.files?.[0]
          void handleFile(file)
          event.target.value = ''
        }}
      />
      {busy ? <p className="text-sm">Reading the page…</p> : null}
      {error ? (
        <p role="alert" className="text-sm font-medium text-rose-800 dark:text-rose-200">
          {error}
        </p>
      ) : null}
      {result ? (
        <div className="space-y-2 rounded-md border border-slate-200 p-3 dark:border-slate-700">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium">Clause {result.clause.ref}</span>
            <TrustChip
              trustClass={asTrustClass(result.fact.trust_class)}
              label={result.fact.trust_label}
            />
            <AiDraftBadge label="AI draft — not yet reviewed" />
          </div>
          <p className="text-sm">{result.fact.statement}</p>
        </div>
      ) : null}
    </section>
  )
}
