import { useEffect, useState } from 'react'

import { api } from '../../api/client'
import { currentMatterId, preferredDocumentId } from '../../api/demoSession'
import type { Fact } from '../../api/types'
import { Button } from '../ui/Button'

type UnderstandingKind = 'parties' | 'obligations' | 'defined_terms' | 'key_dates'

function kindOf(fact: Fact): UnderstandingKind | null {
  const kind = (fact.structured as { kind?: unknown } | undefined)?.kind
  return kind === 'parties' || kind === 'obligations' || kind === 'defined_terms' || kind === 'key_dates'
    ? kind
    : null
}

function field(fact: Fact, name: string): string {
  const value = (fact.structured as Record<string, unknown> | undefined)?.[name]
  return typeof value === 'string' ? value : ''
}

/**
 * Contract understanding (Phase 1): parties, obligations, defined terms
 * and key dates extracted from the working document. Everything here is
 * AI-suggested and proposed — not relied on — until a lawyer confirms it
 * in the Control room.
 */
export function UnderstandingPanel() {
  const [facts, setFacts] = useState<Fact[]>([])
  const [loaded, setLoaded] = useState(false)
  const [documentId, setDocumentId] = useState('')
  const [summarizing, setSummarizing] = useState(false)

  const load = async () => {
    try {
      const [list, docs] = await Promise.all([
        api.facts(currentMatterId()),
        api.documents(currentMatterId()),
      ])
      setFacts(list)
      setDocumentId(preferredDocumentId(docs.documents.map((doc) => doc.id)) ?? '')
    } catch {
      setFacts([])
    } finally {
      setLoaded(true)
    }
  }

  useEffect(() => {
    void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function summarize() {
    if (!documentId || summarizing) {
      return
    }
    setSummarizing(true)
    try {
      await api.summarizeDocument(documentId)
      await load()
    } catch {
      // Summary is additive; the rest of the panel still stands.
    } finally {
      setSummarizing(false)
    }
  }

  const summary = facts
    .filter((fact) => (fact.structured as { kind?: unknown } | undefined)?.kind === 'summary')
    .sort((a, b) => b.created_at.localeCompare(a.created_at))[0]

  const byKind = (kind: UnderstandingKind) =>
    facts.filter((fact) => kindOf(fact) === kind)
  const parties = byKind('parties')
  const obligations = byKind('obligations')
  const terms = byKind('defined_terms')
  const dates = byKind('key_dates')
  const actors = [...new Set(obligations.map((fact) => field(fact, 'actor')).filter(Boolean))]

  return (
    <section className="ct-panel" aria-labelledby="understanding-heading">
      <div className="ct-panel-head">
        <div>
          <h2 id="understanding-heading" className="ct-panel-title">
            Contract understanding
          </h2>
          <p className="ct-panel-desc">
            AI suggestion — may be wrong. This is not legal advice. Parties, obligations,
            terms and dates extracted from your document; proposed until you confirm them
            in Your control room.
          </p>
        </div>
        <span className="ct-badge ct-badge--accent">AI draft — not yet reviewed</span>
      </div>
      <div className="ct-panel-body space-y-4">
        <div>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="ct-section-title">Document summary</h3>
            <Button
              variant="secondary"
              size="sm"
              disabled={!documentId || summarizing}
              loading={summarizing}
              onClick={() => void summarize()}
            >
              {summary ? 'Refresh summary' : 'Summarise this document'}
            </Button>
          </div>
          {summary ? (
            <p className="mt-1.5 text-sm leading-relaxed text-ct-soft">
              {summary.statement.replace(/^Document summary:\s*/, '')}
            </p>
          ) : (
            <p className="ct-help mt-1.5">
              No summary yet. Generate one and it will appear here as a suggestion to check.
            </p>
          )}
        </div>

        {!loaded ? (
          <p className="ct-empty">Loading the understanding…</p>
        ) : parties.length + obligations.length + terms.length + dates.length === 0 ? (
          <p className="ct-empty">
            Nothing extracted yet. Upload a document and its parties and obligations will
            appear here as proposed items.
          </p>
        ) : (
          <>
            {parties.length > 0 ? (
              <div>
                <h3 className="ct-section-title">Parties</h3>
                <ul className="ct-rows mt-1.5">
                  {parties.map((fact) => (
                    <li key={fact.id} className="flex flex-wrap items-baseline gap-x-3 !py-2 text-sm">
                      <span className="font-medium text-ct-ink">{field(fact, 'name') || fact.statement}</span>
                      <span className="text-ct-muted">{field(fact, 'role')}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {obligations.length > 0 ? (
              <div>
                <h3 className="ct-section-title">Obligations</h3>
                {actors.map((actor) => (
                  <div key={actor} className="mt-2">
                    <p className="text-sm font-semibold text-ct-ink">{actor}</p>
                    <ul className="ct-rows mt-1">
                      {obligations
                        .filter((fact) => field(fact, 'actor') === actor)
                        .map((fact) => (
                          <li key={fact.id} className="!py-2 text-sm text-ct-soft">
                            {fact.statement}
                            {field(fact, 'clause_ref') ? (
                              <span className="ct-mono ml-2 text-xs text-ct-faint">
                                clause {field(fact, 'clause_ref')}
                              </span>
                            ) : null}
                          </li>
                        ))}
                    </ul>
                  </div>
                ))}
              </div>
            ) : null}

            {terms.length > 0 ? (
              <div>
                <h3 className="ct-section-title">Defined terms</h3>
                <ul className="ct-rows mt-1.5">
                  {terms.map((fact) => (
                    <li key={fact.id} className="!py-2 text-sm">
                      <span className="font-medium text-ct-ink">{field(fact, 'term')}</span>
                      <span className="text-ct-muted"> — {field(fact, 'definition')}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {dates.length > 0 ? (
              <div>
                <h3 className="ct-section-title">Key dates</h3>
                <ul className="ct-rows mt-1.5">
                  {dates.map((fact) => (
                    <li key={fact.id} className="flex flex-wrap gap-x-3 !py-2 text-sm">
                      <span className="ct-mono text-ct-soft">{field(fact, 'date')}</span>
                      <span className="text-ct-muted">{field(fact, 'label')}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </>
        )}
      </div>
    </section>
  )
}
