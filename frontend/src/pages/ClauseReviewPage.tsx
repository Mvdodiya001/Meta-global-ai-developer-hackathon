import { useCallback, useEffect, useRef, useState } from 'react'

import { api } from '../api/client'
import { DEMO_DOCUMENT_ID } from '../api/config'
import { parseChallengerReport, type ChallengerReportView } from '../api/mocks/challenger'
import { currentMatterId, preferredDocumentId, rememberClaimId } from '../api/demoSession'
import {
  DEFAULT_AS_OF,
  DEFAULT_VERIFY_QUESTION,
  DEMO_AS_OF_OPTIONS,
} from '../api/mocks/runTrace'
import type { Clause, Fact, Finding, Matter } from '../api/types'
import { AskBox } from '../components/clause-review/AskBox'
import { ClauseList } from '../components/clause-review/ClauseList'
import { PremiseTrace } from '../components/clause-review/PremiseTrace'
import { RelevantSections } from '../components/clause-review/RelevantSections'
import { SourceTrace } from '../components/clause-review/SourceTrace'
import { WhatWouldChangePanel } from '../components/clause-review/WhatWouldChangePanel'
import { ChallengerPanel } from '../components/ChallengerPanel'
import { FindingCard } from '../components/FindingCard'
import { PageHeader } from '../components/layout/PageHeader'
import { ProofSyllogism } from '../components/ProofSyllogism'
import { Button } from '../components/ui/Button'
import { IconCheck, IconSearch } from '../components/ui/Icons'
import { PanelSkeleton, Skeleton } from '../components/ui/Skeleton'
import { StateMessage } from '../components/ui/StateMessage'
import { clauseTags } from '../utils/clauseTags'
import { buildWhatWouldChange } from '../utils/findingTraces'
import { lawyerError } from '../utils/lawyerCopy'

type VerifyPhase = 'idle' | 'running' | 'done'

const PROGRESS_STEPS = [
  'Reading the selected clause',
  'Fixing the law version for that date',
  'Testing the requirement against the facts',
  'Drafting the proof for your review',
] as const

export function ClauseReviewPage() {
  const [matter, setMatter] = useState<Matter | null>(null)
  const [clauses, setClauses] = useState<Clause[]>([])
  const [facts, setFacts] = useState<Fact[]>([])
  const [selectedClauseId, setSelectedClauseId] = useState<string | null>(null)
  const [question, setQuestion] = useState(DEFAULT_VERIFY_QUESTION)
  const [asOf, setAsOf] = useState(DEFAULT_AS_OF)
  const [phase, setPhase] = useState<VerifyPhase>('idle')
  const [finding, setFinding] = useState<Finding | null>(null)
  const [lawyerReviewed, setLawyerReviewed] = useState(false)
  const [reviewing, setReviewing] = useState(false)
  const [challengerReport, setChallengerReport] = useState<ChallengerReportView | null>(
    null,
  )
  const [notice, setNotice] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')
  const [tagFilter, setTagFilter] = useState('')
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    void (async () => {
      try {
        const docs = await api.documents(currentMatterId())
        const documentId =
          preferredDocumentId(docs.documents.map((doc) => doc.id)) ?? DEMO_DOCUMENT_ID
        const [m, c, f] = await Promise.all([
          api.matter(currentMatterId()),
          api.clauses(documentId),
          api.facts(currentMatterId()),
        ])
        setMatter(m)
        setClauses(c)
        setFacts(f)
        const clause92 = c.find((clause) => clause.ref === '9.2')
        setSelectedClauseId(clause92?.id ?? c[0]?.id ?? null)
      } catch (err) {
        setNotice(lawyerError(err))
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  const runVerification = useCallback(async () => {
    if (!selectedClauseId || phase === 'running') {
      return
    }
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setPhase('running')
    setFinding(null)
    setLawyerReviewed(false)
    setReviewing(false)
    setChallengerReport(null)
    setNotice(null)

    try {
      const created = await api.createClaim({
        clause_id: selectedClauseId,
        question,
        as_of: asOf,
      })
      rememberClaimId(created.claim_id)

      await api.pollRunEvents(created.run_id, () => undefined, controller.signal)

      const result = await api.currentFinding(created.claim_id)
      setFinding(result)
      setChallengerReport(result ? parseChallengerReport(result.challenger_report) : null)
      if (!result) {
        setNotice('No answer yet. The check is still open.')
      }
      setPhase('done')
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        return
      }
      setPhase('idle')
      setNotice(lawyerError(err))
    }
  }, [asOf, phase, question, selectedClauseId])

  async function markLawyerReviewed() {
    if (!finding || lawyerReviewed || reviewing) {
      return
    }
    setReviewing(true)
    setNotice(null)
    try {
      const result = await api.reviewFinding(finding.id, { action: 'approve' })
      let next = finding
      try {
        next = await api.findingById(finding.id)
      } catch {
        next = finding
      }
      setFinding({
        ...next,
        state: result.state || 'REVIEWED',
        ai_draft_label: 'Reviewed by lawyer',
      })
      setLawyerReviewed(true)
    } catch (err) {
      setNotice(lawyerError(err))
    } finally {
      setReviewing(false)
    }
  }

  useEffect(() => {
    return () => abortRef.current?.abort()
  }, [])

  const sensitivity = finding ? buildWhatWouldChange(finding, facts) : []
  const allTags = [...new Set(clauses.flatMap((clause) => clauseTags(clause)))].sort()
  const visibleClauses = clauses.filter((clause) => {
    if (tagFilter && !clauseTags(clause).includes(tagFilter)) {
      return false
    }
    const term = filter.trim().toLowerCase()
    if (!term) {
      return true
    }
    return (
      clause.ref.toLowerCase().includes(term) ||
      clause.heading.toLowerCase().includes(term) ||
      clause.text.toLowerCase().includes(term)
    )
  })

  return (
    <div className="ct-page">
      <PageHeader
        eyebrow="Review"
        title="Review a clause"
        description={
          matter ? (
            <>
              <span className="font-medium text-ct-soft">{matter.title}</span>
              <span className="mx-1.5 text-ct-lineStrong" aria-hidden="true">
                /
              </span>
              {matter.client_name}
            </>
          ) : (
            'Select a clause, ask a question, and read the proof behind the answer.'
          )
        }
      />

      <div className="grid gap-5 lg:grid-cols-[minmax(0,15rem)_minmax(0,1fr)] lg:items-start">
        <aside className="min-w-0 lg:sticky lg:top-4" aria-labelledby="clauses-heading">
          <div className="border-b border-ct-line pb-3">
            <div className="flex items-center justify-between gap-2">
              <h2 id="clauses-heading" className="ct-panel-title">
                Contract clauses
              </h2>
              <span className="ct-badge">{clauses.length}</span>
            </div>
            <div className="relative mt-2">
              <IconSearch
                size={14}
                className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-ct-faint"
              />
              <input
                type="search"
                aria-label="Find a clause"
                placeholder="Find a clause"
                value={filter}
                onChange={(event) => setFilter(event.target.value)}
                className="ct-input py-1.5 pl-8 text-xs"
              />
            </div>
            {allTags.length > 0 ? (
              <div className="mt-2 flex flex-wrap gap-1" aria-label="Filter clauses by topic">
                <button
                  type="button"
                  className={tagFilter === '' ? 'ct-badge ct-badge--accent' : 'ct-badge'}
                  onClick={() => setTagFilter('')}
                >
                  All topics
                </button>
                {allTags.map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    className={tagFilter === tag ? 'ct-badge ct-badge--accent' : 'ct-badge'}
                    onClick={() => setTagFilter(tag === tagFilter ? '' : tag)}
                  >
                    {tag}
                  </button>
                ))}
              </div>
            ) : null}
          </div>
          <div className="ct-scroll-fade max-h-[26rem] overflow-y-auto py-2">
            {loading ? (
              <Skeleton lines={5} label="Loading clauses" />
            ) : visibleClauses.length === 0 ? (
              <p className="ct-empty">No clause matches that search.</p>
            ) : (
              <ClauseList
                clauses={visibleClauses}
                selectedId={selectedClauseId}
                onSelect={setSelectedClauseId}
              />
            )}
          </div>
        </aside>

        <div className="ct-enter min-w-0 space-y-5">
          <AskBox
            question={question}
            asOf={asOf}
            asOfOptions={DEMO_AS_OF_OPTIONS}
            disabled={phase === 'running' || !selectedClauseId}
            onQuestionChange={setQuestion}
            onAsOfChange={setAsOf}
            onSubmit={() => void runVerification()}
          />

          <RelevantSections initialQuery={question} />

          {notice ? <StateMessage tone="warn">{notice}</StateMessage> : null}

          {phase === 'running' ? (
            <section className="ct-panel" aria-live="polite" aria-label="Checking the clause">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-semibold text-ct-ink">Checking the clause</p>
                <span className="ct-badge ct-badge--accent">
                  <span className="ct-dot ct-dot--pulse" aria-hidden="true" />
                  Working
                </span>
              </div>
              <div className="ct-progress mt-3" role="presentation">
                <div className="ct-progress-bar" />
              </div>
              <ol className="mt-3 space-y-2">
                {PROGRESS_STEPS.map((step, index) => (
                  <li key={step} className="flex items-center gap-2 text-sm text-ct-muted">
                    <span
                      className={[
                        'flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[0.65rem]',
                        index === 0
                          ? 'border-ct-accent bg-ct-accentSoft text-ct-accent'
                          : 'border-ct-line bg-ct-surface2 text-ct-faint',
                      ].join(' ')}
                      aria-hidden="true"
                    >
                      {index + 1}
                    </span>
                    {step}
                  </li>
                ))}
              </ol>
            </section>
          ) : null}

          {phase === 'idle' && !finding ? (
            <div className="ct-empty">
              <p className="font-medium text-ct-soft">No answer yet</p>
              <p>
                Choose a clause and ask a question. The answer will appear here with the
                clause, the law version, the facts relied on, and what could change it.
              </p>
            </div>
          ) : null}

          {loading && !finding ? <PanelSkeleton label="Loading review workspace" /> : null}

          {finding ? (
            <div className="space-y-5">
              <FindingCard finding={finding} lawyerReviewed={lawyerReviewed} />

              <div className="flex flex-wrap items-center justify-between gap-3 border-y border-ct-line py-3">
                <div>
                  <p className="text-sm font-semibold text-ct-ink">
                    {lawyerReviewed ? 'Reviewed by you' : 'Ready for your review'}
                  </p>
                  <p className="mt-0.5 text-xs text-ct-muted">
                    {lawyerReviewed
                      ? 'This answer is marked lawyer-reviewed for this matter.'
                      : 'Confirm the draft only after checking the quotes and facts below.'}
                  </p>
                </div>
                <Button
                  variant={lawyerReviewed ? 'ghost' : 'primary'}
                  disabled={lawyerReviewed || reviewing}
                  loading={reviewing}
                  icon={lawyerReviewed ? <IconCheck size={15} /> : undefined}
                  onClick={() => void markLawyerReviewed()}
                >
                  {lawyerReviewed
                    ? 'Lawyer-reviewed'
                    : reviewing
                      ? 'Saving review…'
                      : 'Mark lawyer-reviewed'}
                </Button>
              </div>

              <div className="grid gap-5 xl:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)] xl:items-start">
                <div className="min-w-0 space-y-5">
                  <ProofSyllogism finding={finding} />
                  <SourceTrace finding={finding} />
                  <PremiseTrace finding={finding} />
                </div>
                <div className="min-w-0 space-y-5">
                  <WhatWouldChangePanel hints={sensitivity} />
                  <ChallengerPanel report={challengerReport} />
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}
