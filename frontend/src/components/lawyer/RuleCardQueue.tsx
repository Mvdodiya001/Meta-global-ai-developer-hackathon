import { useCallback, useEffect, useState } from 'react'

import { api } from '../../api/client'
import { DEMO_SOURCE_ID } from '../../api/config'
import type { ProvisionSummary, RuleCardSummary } from '../../api/types'
import { Button } from '../ui/Button'
import { StateMessage } from '../ui/StateMessage'

/**
 * Legal-test drafting queue (Phase 2a): the model drafts a card from a
 * provision; only a lawyer's Confirm makes it relied-on. Drafts are
 * labelled AI-suggested and may be wrong.
 */
export function RuleCardQueue() {
  const [provisions, setProvisions] = useState<ProvisionSummary[]>([])
  const [provisionId, setProvisionId] = useState('')
  const [drafts, setDrafts] = useState<RuleCardSummary[]>([])
  const [edits, setEdits] = useState<Record<string, { interpretation: string; claim_type: string }>>({})
  const [notice, setNotice] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const loadDrafts = useCallback(async () => {
    try {
      const list = await api.cardDrafts()
      setDrafts(list.drafts)
      setEdits((current) => {
        const next = { ...current }
        for (const draft of list.drafts) {
          if (!next[draft.id]) {
            next[draft.id] = {
              interpretation: draft.interpretation,
              claim_type: draft.claim_type,
            }
          }
        }
        return next
      })
    } catch {
      setNotice('The draft queue could not be loaded.')
    }
  }, [])

  useEffect(() => {
    void (async () => {
      try {
        const versions = await api.sourceVersions(DEMO_SOURCE_ID)
        const current = versions.versions.find((v) => !v.is_simulated) ?? versions.versions[0]
        if (current) {
          const list = await api.provisions(current.id)
          setProvisions(list.provisions)
          setProvisionId(list.provisions[0]?.id ?? '')
        }
      } catch {
        setNotice('Provisions could not be loaded.')
      }
      await loadDrafts()
    })()
  }, [loadDrafts])

  async function draft() {
    if (!provisionId || busy) {
      return
    }
    setBusy(true)
    setNotice(null)
    try {
      await api.draftCard(provisionId)
      await loadDrafts()
      setNotice('Draft added below. It is not relied on until you confirm it.')
    } catch {
      setNotice('A draft could not be created for that provision.')
    } finally {
      setBusy(false)
    }
  }

  async function confirm(card: RuleCardSummary) {
    setBusy(true)
    try {
      await api.confirmCard(card.id, edits[card.id] ?? {})
      await loadDrafts()
      setNotice('Confirmed. This legal test can now be relied on.')
    } catch {
      setNotice('That draft could not be confirmed.')
    } finally {
      setBusy(false)
    }
  }

  async function reject(card: RuleCardSummary) {
    setBusy(true)
    try {
      await api.rejectCard(card.id)
      await loadDrafts()
      setNotice('Draft rejected.')
    } catch {
      setNotice('That draft could not be rejected.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="ct-panel" aria-labelledby="card-queue-heading">
      <div className="ct-panel-head">
        <div>
          <h2 id="card-queue-heading" className="ct-panel-title">
            Legal test drafts
          </h2>
          <p className="ct-panel-desc">
            AI suggestion — may be wrong. This is not legal advice. A drafted test is not
            relied on until you confirm it.
          </p>
        </div>
        <span className="ct-badge ct-badge--warn">{drafts.length} awaiting review</span>
      </div>
      <div className="ct-panel-body space-y-3">
        <div className="flex flex-wrap items-end gap-2">
          <div className="ct-field min-w-[14rem] flex-1">
            <label htmlFor="draft-provision" className="ct-label">
              Provision to draft a test for
            </label>
            <select
              id="draft-provision"
              className="ct-select"
              value={provisionId}
              onChange={(event) => setProvisionId(event.target.value)}
            >
              {provisions.map((provision) => (
                <option key={provision.id} value={provision.id}>
                  {provision.key}
                </option>
              ))}
            </select>
          </div>
          <Button variant="secondary" disabled={!provisionId || busy} loading={busy} onClick={() => void draft()}>
            Draft a legal test
          </Button>
        </div>

        {notice ? <StateMessage tone="info">{notice}</StateMessage> : null}

        {drafts.length === 0 ? (
          <p className="ct-empty">No drafts awaiting review.</p>
        ) : (
          <ul className="ct-rows">
            {drafts.map((card) => (
              <li key={card.id}>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="ct-badge ct-badge--accent">AI draft — not yet reviewed</span>
                  <span className="text-xs text-ct-muted">{card.provision_key}</span>
                </div>
                <blockquote className="ct-quote mt-2 text-sm">{card.span_text}</blockquote>
                <div className="ct-field mt-2">
                  <label htmlFor={`card-type-${card.id}`} className="ct-label">
                    Claim type
                  </label>
                  <input
                    id={`card-type-${card.id}`}
                    className="ct-input max-w-[10rem]"
                    value={edits[card.id]?.claim_type ?? card.claim_type}
                    onChange={(event) =>
                      setEdits((current) => ({
                        ...current,
                        [card.id]: {
                          interpretation: current[card.id]?.interpretation ?? card.interpretation,
                          claim_type: event.target.value,
                        },
                      }))
                    }
                  />
                </div>
                <div className="ct-field mt-2">
                  <label htmlFor={`card-text-${card.id}`} className="ct-label">
                    What the test requires
                  </label>
                  <textarea
                    id={`card-text-${card.id}`}
                    className="ct-textarea"
                    rows={3}
                    value={edits[card.id]?.interpretation ?? card.interpretation}
                    onChange={(event) =>
                      setEdits((current) => ({
                        ...current,
                        [card.id]: {
                          interpretation: event.target.value,
                          claim_type: current[card.id]?.claim_type ?? card.claim_type,
                        },
                      }))
                    }
                  />
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  <Button size="sm" variant="primary" disabled={busy} onClick={() => void confirm(card)}>
                    Confirm this test
                  </Button>
                  <Button size="sm" variant="ghost" disabled={busy} onClick={() => void reject(card)}>
                    Reject
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
