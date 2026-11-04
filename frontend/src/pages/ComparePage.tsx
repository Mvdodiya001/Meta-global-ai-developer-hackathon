import { useEffect, useState } from 'react'

import { api } from '../api/client'
import { currentMatterId } from '../api/demoSession'
import type { CompareReport, CoverageReport, DocumentList } from '../api/types'
import { PageHeader } from '../components/layout/PageHeader'
import { Button } from '../components/ui/Button'
import { StateMessage } from '../components/ui/StateMessage'

/**
 * Compare documents (Phase 5): clause alignment between two documents of
 * the matter, differing pairs flaggable for lawyer review, and a
 * contract-vs-law coverage roll-up for the first document.
 */
export function ComparePage() {
  const [documents, setDocuments] = useState<DocumentList['documents']>([])
  const [a, setA] = useState('')
  const [b, setB] = useState('')
  const [report, setReport] = useState<CompareReport | null>(null)
  const [coverage, setCoverage] = useState<CoverageReport | null>(null)
  const [flagged, setFlagged] = useState<Set<string>>(new Set())
  const [busy, setBusy] = useState(false)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    void (async () => {
      try {
        const list = await api.documents(currentMatterId())
        setDocuments(list.documents)
        setA(list.documents[0]?.id ?? '')
        setB(list.documents[1]?.id ?? list.documents[0]?.id ?? '')
      } catch {
        setFailed(true)
      }
    })()
  }, [])

  async function compare() {
    if (!a || !b || busy) {
      return
    }
    setBusy(true)
    setFailed(false)
    try {
      const [nextReport, nextCoverage] = await Promise.all([
        api.compareDocuments(currentMatterId(), a, b),
        api.documentCoverage(a),
      ])
      setReport(nextReport)
      setCoverage(nextCoverage)
      setFlagged(new Set())
    } catch {
      setFailed(true)
    } finally {
      setBusy(false)
    }
  }

  async function flag(ref: string) {
    try {
      await api.flagClausePair(currentMatterId(), ref)
      setFlagged((current) => new Set(current).add(ref))
    } catch {
      setFailed(true)
    }
  }

  return (
    <div className="ct-page">
      <PageHeader
        eyebrow="Comparison"
        title="Compare documents"
        description="Align two documents clause by clause, flag what differs for a lawyer, and see which law each clause touches."
      />

      {failed ? (
        <StateMessage tone="danger" live="alert">
          The comparison could not be loaded. Try again.
        </StateMessage>
      ) : null}

      <section className="ct-panel" aria-labelledby="compare-heading">
        <div className="ct-panel-head">
          <div>
            <h2 id="compare-heading" className="ct-panel-title">
              Two documents
            </h2>
            <p className="ct-panel-desc">Clauses are aligned by their reference number.</p>
          </div>
        </div>
        <div className="ct-panel-body space-y-3">
          <div className="grid gap-3 md:grid-cols-2">
            <div className="ct-field">
              <label htmlFor="compare-a" className="ct-label">
                First document
              </label>
              <select id="compare-a" className="ct-select" value={a} onChange={(e) => setA(e.target.value)}>
                {documents.map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    {doc.title}
                  </option>
                ))}
              </select>
            </div>
            <div className="ct-field">
              <label htmlFor="compare-b" className="ct-label">
                Second document
              </label>
              <select id="compare-b" className="ct-select" value={b} onChange={(e) => setB(e.target.value)}>
                {documents.map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    {doc.title}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <Button variant="primary" disabled={!a || !b || busy} loading={busy} onClick={() => void compare()}>
            Compare documents
          </Button>
        </div>
      </section>

      {report ? (
        <section className="ct-panel" aria-labelledby="compare-result-heading">
          <div className="ct-panel-head">
            <div>
              <h2 id="compare-result-heading" className="ct-panel-title">
                Aligned clauses
              </h2>
              <p className="ct-panel-desc">
                {report.pairs.filter((pair) => pair.changed).length} of {report.pairs.length}{' '}
                shared clauses differ in wording.
              </p>
            </div>
          </div>
          <div className="ct-panel-body">
            {report.pairs.length === 0 ? (
              <p className="ct-empty">These documents share no clause references.</p>
            ) : (
              <ul className="ct-rows">
                {report.pairs.map((pair) => (
                  <li key={pair.ref}>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium text-ct-ink">Clause {pair.ref}</span>
                      {pair.changed ? (
                        <span className="ct-badge ct-badge--warn">Wording differs</span>
                      ) : (
                        <span className="ct-badge ct-badge--ok">Same wording</span>
                      )}
                      {pair.changed ? (
                        flagged.has(pair.ref) ? (
                          <span className="ct-badge">Flagged for review</span>
                        ) : (
                          <Button size="sm" variant="ghost" onClick={() => void flag(pair.ref)}>
                            Flag for review
                          </Button>
                        )
                      ) : null}
                    </div>
                    {pair.changed ? (
                      <div className="mt-1.5 grid gap-3 md:grid-cols-2">
                        <p className="border-l-2 border-ct-line pl-3 font-serif text-sm leading-relaxed text-ct-soft">
                          {pair.a_text}
                        </p>
                        <p className="border-l-2 border-ct-warn bg-ct-warnSoft/50 py-1 pl-3 font-serif text-sm leading-relaxed text-ct-ink">
                          {pair.b_text}
                        </p>
                      </div>
                    ) : null}
                  </li>
                ))}
              </ul>
            )}
            {report.only_a.length + report.only_b.length > 0 ? (
              <p className="ct-help mt-2">
                Only in the first: {report.only_a.join(', ') || 'none'} · Only in the
                second: {report.only_b.join(', ') || 'none'}
              </p>
            ) : null}
          </div>
        </section>
      ) : null}

      {coverage ? (
        <section className="ct-panel" aria-labelledby="coverage-heading">
          <div className="ct-panel-head">
            <div>
              <h2 id="coverage-heading" className="ct-panel-title">
                Which law each clause touches
              </h2>
              <p className="ct-panel-desc">
                Strongest matching section per clause, with the latest answer state.
              </p>
            </div>
          </div>
          <div className="ct-panel-body">
            <ul className="ct-rows">
              {coverage.rows.map((row) => (
                <li key={row.clause_id} className="flex flex-wrap items-baseline gap-x-2.5 !py-2 text-sm">
                  <span className="font-medium text-ct-ink">Clause {row.ref}</span>
                  <span className="text-ct-muted">{row.heading}</span>
                  <span className="ct-mono text-xs text-ct-faint">
                    {row.provision_key.replace(/^DPDP-Act-2023_|^IT-Act-2000_|^Copyright-Act-1957_/, '')}
                  </span>
                  <span className="text-xs text-ct-muted">{row.source_title}</span>
                  {row.finding_status ? (
                    <span className="ct-badge">{row.finding_status}</span>
                  ) : (
                    <span className="text-xs text-ct-faint">no answer yet</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </section>
      ) : null}
    </div>
  )
}
