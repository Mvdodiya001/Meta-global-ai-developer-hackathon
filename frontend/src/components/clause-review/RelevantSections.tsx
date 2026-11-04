import { useState } from 'react'

import { api } from '../../api/client'
import type { ProvisionHit } from '../../api/types'
import { Button } from '../ui/Button'

/**
 * Relevant sections (Phase 3): deterministic retrieval over every current
 * law in the corpus, ranked by how strongly the wording matches. Scores
 * are shown so a lawyer can judge the match, not just trust it.
 */
export function RelevantSections({ initialQuery }: { initialQuery: string }) {
  const [text, setText] = useState(initialQuery)
  const [hits, setHits] = useState<ProvisionHit[] | null>(null)
  const [busy, setBusy] = useState(false)
  const [failed, setFailed] = useState(false)
  const [semantic, setSemantic] = useState(true)

  async function search() {
    if (!text.trim() || busy) {
      return
    }
    setBusy(true)
    setFailed(false)
    try {
      const result = await api.searchProvisions(text.trim(), 5, semantic)
      setHits(result.hits)
    } catch {
      setFailed(true)
    } finally {
      setBusy(false)
    }
  }

  const maxScore = hits && hits.length > 0 ? Math.max(...hits.map((hit) => hit.score)) : 0

  return (
    <section className="ct-panel" aria-labelledby="relevant-heading">
      <div className="ct-panel-head">
        <div>
          <h2 id="relevant-heading" className="ct-panel-title">
            Relevant sections
          </h2>
          <p className="ct-panel-desc">
            Every current law in the corpus, ranked by wording match. Check the section
            before relying on it.
          </p>
        </div>
      </div>
      <div className="ct-panel-body space-y-3">
        <div className="flex flex-wrap items-end gap-2">
          <div className="ct-field min-w-[14rem] flex-1">
            <label htmlFor="relevant-query" className="ct-label">
              Clause or question wording
            </label>
            <input
              id="relevant-query"
              className="ct-input"
              value={text}
              onChange={(event) => setText(event.target.value)}
              placeholder="e.g. transfer of personal data outside India"
            />
          </div>
          <Button variant="secondary" disabled={!text.trim() || busy} loading={busy} onClick={() => void search()}>
            Find sections
          </Button>
        </div>
        <label className="flex items-center gap-2 text-xs text-ct-soft">
          <input
            type="checkbox"
            checked={semantic}
            onChange={(event) => setSemantic(event.target.checked)}
          />
          AI re-rank by meaning (suggestion — may be wrong)
        </label>

        {failed ? (
          <p className="ct-notice ct-notice--danger">Sections could not be searched. Try again.</p>
        ) : null}

        {hits !== null && hits.length === 0 ? (
          <p className="ct-empty">No section matches that wording closely.</p>
        ) : null}

        {hits && hits.length > 0 ? (
          <ol className="ct-rows">
            {hits.map((hit) => (
              <li key={hit.provision_id}>
                <div className="flex flex-wrap items-baseline gap-x-2.5 gap-y-1">
                  <span className="font-medium text-ct-ink">
                    {hit.key.replace(/^DPDP-Act-2023_|^IT-Act-2000_|^Copyright-Act-1957_/, '')}
                  </span>
                  <span className="text-xs text-ct-muted">{hit.source_title}</span>
                  <span className="ct-mono text-[0.7rem] text-ct-faint">
                    match {hit.score.toFixed(2)}
                  </span>
                </div>
                <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-ct-surface3">
                  <div
                    className="h-full rounded-full bg-ct-accent"
                    style={{ width: `${Math.max(8, Math.round((hit.score / maxScore) * 100))}%` }}
                  />
                </div>
                <p className="mt-1.5 line-clamp-2 text-sm leading-relaxed text-ct-soft">
                  {hit.text}
                </p>
                {hit.reranked ? (
                  <p className="mt-1 text-xs text-ct-muted">
                    <span className="ct-badge ct-badge--accent mr-1.5">AI re-ranked</span>
                    {hit.why ?? ''}
                  </p>
                ) : null}
              </li>
            ))}
          </ol>
        ) : null}
      </div>
    </section>
  )
}
