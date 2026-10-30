import { useCallback, useEffect, useRef, useState } from 'react'

import { api } from '../api/client'
import { DEMO_DOCUMENT_ID, DEMO_MATTER_ID } from '../api/config'
import {
  DEMO_CHALLENGER_REPORT,
  parseChallengerReport,
  type ChallengerReportView,
} from '../api/mocks/challenger'
import { DEFAULT_VERIFY_QUESTION } from '../api/mocks/runTrace'
import type { Clause, Fact, Finding, Matter, ToolCall } from '../api/types'
import { AskBox } from '../components/clause-review/AskBox'
import { ClauseList } from '../components/clause-review/ClauseList'
import { PremiseTrace } from '../components/clause-review/PremiseTrace'
import { SourceTrace } from '../components/clause-review/SourceTrace'
import { ToolTracePanel } from '../components/clause-review/ToolTracePanel'
import { WhatWouldChangePanel } from '../components/clause-review/WhatWouldChangePanel'
import { ChallengerPanel } from '../components/ChallengerPanel'
import { FindingCard } from '../components/FindingCard'
import { ProofSyllogism } from '../components/ProofSyllogism'
import {
  buildPremiseTrace,
  buildSourceTrace,
  buildWhatWouldChange,
} from '../utils/findingTraces'

type VerifyPhase = 'idle' | 'running' | 'done'

export function ClauseReviewPage() {
  const [matter, setMatter] = useState<Matter | null>(null)
  const [clauses, setClauses] = useState<Clause[]>([])
  const [facts, setFacts] = useState<Fact[]>([])
  const [selectedClauseId, setSelectedClauseId] = useState<string | null>(null)
  const [question, setQuestion] = useState(DEFAULT_VERIFY_QUESTION)
  const [asOf, setAsOf] = useState('2025-10-01')
  const [phase, setPhase] = useState<VerifyPhase>('idle')
  const [runId, setRunId] = useState<string | null>(null)
  const [traceEvents, setTraceEvents] = useState<ToolCall[]>([])
  const [finding, setFinding] = useState<Finding | null>(null)
  const [lawyerReviewed, setLawyerReviewed] = useState(false)
  const [challengerOn, setChallengerOn] = useState(true)
  const [challengerReport, setChallengerReport] = useState<ChallengerReportView | null>(
    null,
  )
  const [notice, setNotice] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    void (async () => {
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
    setTraceEvents([])
    setFinding(null)
    setLawyerReviewed(false)
    setChallengerReport(null)
    setNotice(null)

    try {
      const created = await api.createClaim({
        clause_id: selectedClauseId,
        question,
        as_of: asOf,
      })
      setRunId(created.run_id)

      await api.pollRunEvents(created.run_id, setTraceEvents, controller.signal)

      const result = await api.currentFinding(created.claim_id)
      setFinding(result)
      setChallengerReport(result ? parseChallengerReport(result.challenger_report) : null)
      if (!result) {
        setNotice('No finding yet. The verification run is still open.')
      }
      setPhase('done')
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        return
      }
      setPhase('idle')
      setNotice(err instanceof Error ? err.message : 'Verification failed')
    }
  }, [asOf, phase, question, selectedClauseId])

  useEffect(() => {
    return () => abortRef.current?.abort()
  }, [])

  const sourceRows = finding ? buildSourceTrace(finding) : []
  const premiseRows = finding ? buildPremiseTrace(finding, facts) : []
  const sensitivity = finding ? buildWhatWouldChange(finding, facts) : []

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6">
      <header>
        <p className="ct-section-title">Screen 1 · Clause review</p>
        <h1 className="text-2xl font-semibold tracking-tight">
          {matter?.title ?? 'Loading matter…'}
        </h1>
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
        disabled={phase === 'running' || !selectedClauseId}
        onQuestionChange={setQuestion}
        onAsOfChange={setAsOf}
        onSubmit={() => void runVerification()}
      />

      <ToolTracePanel events={traceEvents} running={phase === 'running'} runId={runId} />

      {notice ? <p className="text-sm text-slate-600 dark:text-slate-400">{notice}</p> : null}

      {finding ? (
        <>
          <FindingCard finding={finding} lawyerReviewed={lawyerReviewed} />
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium hover:bg-slate-50 dark:border-slate-600 dark:hover:bg-slate-900"
              onClick={() => setLawyerReviewed(true)}
            >
              Mark lawyer-reviewed (demo)
            </button>
          </div>
          <ProofSyllogism proof={finding.proof} />
          <SourceTrace rows={sourceRows} />
          <PremiseTrace rows={premiseRows} />
          <WhatWouldChangePanel hints={sensitivity} />
        </>
      ) : null}

      <ChallengerPanel
        enabled={challengerOn}
        report={challengerReport}
        onToggle={setChallengerOn}
        onRun={() => {
          setChallengerReport(DEMO_CHALLENGER_REPORT)
          setFinding((current) =>
            current
              ? {
                  ...current,
                  status: 'REQUIRES_REVIEW',
                  challenger_report: {
                    model: DEMO_CHALLENGER_REPORT.model,
                    blocking: DEMO_CHALLENGER_REPORT.blocking,
                    objections: DEMO_CHALLENGER_REPORT.objections,
                  },
                }
              : current,
          )
        }}
      />
    </div>
  )
}
