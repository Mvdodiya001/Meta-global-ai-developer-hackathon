import { useCallback, useEffect, useRef, useState } from 'react'

import { api } from '../api/client'
import { DEMO_DOCUMENT_ID, DEMO_MATTER_ID } from '../api/config'
import { parseChallengerReport, type ChallengerReportView } from '../api/mocks/challenger'
import { rememberClaimId } from '../api/demoSession'
import {
  DEFAULT_AS_OF,
  DEFAULT_VERIFY_QUESTION,
  DEMO_AS_OF_OPTIONS,
} from '../api/mocks/runTrace'
import type { Clause, Fact, Finding, Matter } from '../api/types'
import { AskBox } from '../components/clause-review/AskBox'
import { ClauseList } from '../components/clause-review/ClauseList'
import { PremiseTrace } from '../components/clause-review/PremiseTrace'
import { SourceTrace } from '../components/clause-review/SourceTrace'
import { WhatWouldChangePanel } from '../components/clause-review/WhatWouldChangePanel'
import { ChallengerPanel } from '../components/ChallengerPanel'
import { FindingCard } from '../components/FindingCard'
import { ProofSyllogism } from '../components/ProofSyllogism'
import { AiDraftBadge } from '../components/badges/AiDraftBadge'
import { buildWhatWouldChange } from '../utils/findingTraces'
import { lawyerError } from '../utils/lawyerCopy'

type VerifyPhase = 'idle' | 'running' | 'done'

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
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    void (async () => {
      try {
        const docs = await api.documents(DEMO_MATTER_ID)
        const documentId = docs.documents[0]?.id ?? DEMO_DOCUMENT_ID
        const [m, c, f] = await Promise.all([
          api.matter(DEMO_MATTER_ID),
          api.clauses(documentId),
          api.facts(DEMO_MATTER_ID),
        ])
        setMatter(m)
        setClauses(c)
        setFacts(f)
        const clause92 = c.find((clause) => clause.ref === '9.2')
        setSelectedClauseId(clause92?.id ?? c[0]?.id ?? null)
      } catch (err) {
        setNotice(lawyerError(err))
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

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Review a clause</h1>
        <AiDraftBadge label="AI draft — not yet reviewed" />
        <p className="text-sm font-medium">{matter?.title ?? 'Loading…'}</p>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          {matter?.client_name}
        </p>
      </header>

      <section className="ct-panel p-4" aria-labelledby="clauses-heading">
        <h2 id="clauses-heading" className="mb-3 ct-section-title">
          Contract clauses
        </h2>
        <ClauseList
          clauses={clauses}
          selectedId={selectedClauseId}
          onSelect={setSelectedClauseId}
        />
      </section>

      <AskBox
        question={question}
        asOf={asOf}
        asOfOptions={DEMO_AS_OF_OPTIONS}
        disabled={phase === 'running' || !selectedClauseId}
        onQuestionChange={setQuestion}
        onAsOfChange={setAsOf}
        onSubmit={() => void runVerification()}
      />

      {notice ? <p className="text-sm text-slate-600 dark:text-slate-400">{notice}</p> : null}

      {finding ? (
        <>
          <FindingCard finding={finding} lawyerReviewed={lawyerReviewed} />
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={lawyerReviewed || reviewing}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium hover:bg-slate-50 disabled:opacity-50 dark:border-slate-600 dark:hover:bg-slate-900"
              onClick={() => void markLawyerReviewed()}
            >
              {lawyerReviewed
                ? 'Lawyer-reviewed'
                : reviewing
                  ? 'Saving review…'
                  : 'Mark lawyer-reviewed'}
            </button>
          </div>
          <ProofSyllogism finding={finding} />
          <SourceTrace finding={finding} />
          <PremiseTrace finding={finding} />
          <WhatWouldChangePanel hints={sensitivity} />
          <ChallengerPanel report={challengerReport} />
        </>
      ) : null}
    </div>
  )
}
