import { useCallback, useEffect, useRef, useState } from 'react'

import { api } from '../api/client'
import { DEFAULT_VERIFY_QUESTION } from '../api/mocks/runTrace'
import type { Clause, Fact, Finding, Matter, ToolCall } from '../api/types'
import { AskBox } from '../components/clause-review/AskBox'
import { ClauseList } from '../components/clause-review/ClauseList'
import { PremiseTrace } from '../components/clause-review/PremiseTrace'
import { SourceTrace } from '../components/clause-review/SourceTrace'
import { ToolTracePanel } from '../components/clause-review/ToolTracePanel'
import { WhatWouldChangePanel } from '../components/clause-review/WhatWouldChangePanel'
import { FindingCard } from '../components/FindingCard'
import { ProofSyllogism } from '../components/ProofSyllogism'
import {
  buildPremiseTrace,
  buildSourceTrace,
  buildWhatWouldChange,
} from '../lib/findingTraces'

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
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    void Promise.all([
      api.matter('MAT-01'),
      api.clauses('DOCV-01'),
      api.facts('MAT-01'),
    ]).then(([m, c, f]) => {
      setMatter(m)
      setClauses(c)
      setFacts(f)
      const clause92 = c.find((clause) => clause.ref === '9.2')
      setSelectedClauseId(clause92?.id ?? c[0]?.id ?? null)
    })
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

    const created = await api.createClaim({
      clause_id: selectedClauseId,
      question,
      as_of: asOf,
    })
    setRunId(created.run_id)

    await api.pollRunEvents(
      created.run_id,
      setTraceEvents,
      controller.signal,
    )

    const result = await api.finding(created.claim_id)
    setFinding(result)
    setPhase('done')
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
    </div>
  )
}
