import { useEffect, useState } from 'react'

import { api } from '../api/client'
import { DEMO_MATTER_ID } from '../api/config'
import { lastClaimId } from '../api/demoSession'
import {
  COMMENCEMENT_DATE,
  UNKNOWN_QUESTION,
  applyFactAction,
  asOfFinding,
  challengedFinding,
} from '../api/mocks/lawyerControl'
import type { Clause, Fact, Finding, Proof, ProofVerifyResult } from '../api/types'
import { parseChallengerReport } from '../api/mocks/challenger'
import { ChallengerPanel } from '../components/ChallengerPanel'
import { FindingCard } from '../components/FindingCard'
import { PageHeader } from '../components/layout/PageHeader'
import { AsOfPanel } from '../components/lawyer/AsOfPanel'
import { DictationPanel } from '../components/lawyer/DictationPanel'
import { FactTrustList } from '../components/lawyer/FactTrustList'
import { FactWordingEditor } from '../components/lawyer/FactWordingEditor'
import { IllustrationLabel } from '../components/lawyer/IllustrationLabel'
import { ScanPagePanel } from '../components/lawyer/ScanPagePanel'
import { UnknownClaimDemo } from '../components/lawyer/UnknownClaimDemo'
import { Skeleton } from '../components/ui/Skeleton'
import { StateMessage } from '../components/ui/StateMessage'

export function LawyerControlPage() {
  const [claimId, setClaimId] = useState<string | null>(null)
  const [clauses, setClauses] = useState<Clause[]>([])
  const [facts, setFacts] = useState<Fact[]>([])
  const [baseFinding, setBaseFinding] = useState<Finding | null>(null)
  const [reviewedIds, setReviewedIds] = useState<string[]>([])
  const [dependent, setDependent] = useState<Finding | null>(null)
  const [recomputed, setRecomputed] = useState(false)
  const [asOf, setAsOf] = useState(COMMENCEMENT_DATE)
  const [asOfResult, setAsOfResult] = useState<Finding | null>(null)
  const [unknownQ, setUnknownQ] = useState(UNKNOWN_QUESTION)
  const [unknownResult, setUnknownResult] = useState<Finding | null>(null)
  const [factSentence, setFactSentence] = useState('')
  const [verifyResult, setVerifyResult] = useState<ProofVerifyResult | null>(null)
  const [approveNotice, setApproveNotice] = useState<string | null>(null)
  const [unknownBusy, setUnknownBusy] = useState(false)
  const [unknownError, setUnknownError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const stored = lastClaimId()
    setClaimId(stored)
    void (async () => {
      try {
        const docs = await api.documents(DEMO_MATTER_ID)
        const documentId = docs.documents[0]?.id
        if (documentId) {
          setClauses(await api.clauses(documentId))
        }
        const nextFacts = await api.facts(DEMO_MATTER_ID)
        setFacts(nextFacts)
        setReviewedIds(
          nextFacts
            .filter((fact) => fact.trust_class === 'lawyer_confirmed')
            .map((fact) => fact.id),
        )
        if (!stored) {
          return
        }
        const finding = await api.currentFinding(stored)
        if (finding) {
          setBaseFinding(finding)
          setDependent(finding)
          setFactSentence(finding.proof.premises[0]?.statement ?? '')
        }
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  const actionsEnabled = Boolean(claimId)
  const defaultClauseId =
    facts.find((fact) => baseFinding?.premise_ids.includes(fact.id) && fact.clause_id)
      ?.clause_id ?? 'CL-10'

  async function handleApprove(factId: string): Promise<boolean> {
    const fact = facts.find((row) => row.id === factId)
    if (reviewedIds.includes(factId) || fact?.trust_class === 'lawyer_confirmed') {
      setApproveNotice('Already confirmed')
      return false
    }
    try {
      const action = await api.approveFact(factId)
      setFacts((current) => applyFactAction(current, action))
      setReviewedIds((ids) => (ids.includes(factId) ? ids : [...ids, factId]))
      setApproveNotice(null)
      return true
    } catch {
      // A second confirm lands on the superseded row server-side.
      setApproveNotice('Already confirmed')
      return false
    }
  }

  async function handleUnknownAsk() {
    if (!actionsEnabled || unknownBusy) {
      return
    }
    setUnknownBusy(true)
    setUnknownError(null)
    try {
      const clause92 = clauses.find((clause) => clause.ref === '9.2')
      const created = await api.createClaim({
        clause_id: clause92?.id ?? defaultClauseId,
        question: unknownQ,
        as_of: COMMENCEMENT_DATE,
      })
      const finding = created.claim_id
        ? await api.currentFinding(created.claim_id)
        : null
      setUnknownResult(finding)
      if (!finding) {
        setUnknownError('No answer came back. Try again.')
      }
    } catch {
      setUnknownResult(null)
      setUnknownError('That question could not be answered. Try again.')
    } finally {
      setUnknownBusy(false)
    }
  }

  async function handleChallenge(factId: string) {
    if (!actionsEnabled) {
      return
    }
    const action = await api.challengeFact(factId)
    setFacts((current) => applyFactAction(current, action))
    setRecomputed(true)
    if (baseFinding) {
      setDependent(challengedFinding(baseFinding))
    }
  }

  function handleAsOf(next: string) {
    if (!actionsEnabled) {
      return
    }
    setAsOf(next)
    if (baseFinding) {
      setAsOfResult(asOfFinding(baseFinding, next))
    }
  }

  function proofFromSentence(base: Proof, sentence: string): Proof {
    const premises = base.premises.map((premise, index) =>
      index === 0 ? { ...premise, statement: sentence } : premise,
    )
    return { ...base, premises }
  }

  return (
    <div className="ct-page">
      <PageHeader
        eyebrow="Governance"
        title="Your control room"
        description="Approve the facts behind an answer, test the wording, and see how a changed premise or date affects what follows."
      />

      {!actionsEnabled ? (
        <div className="ct-notice ct-notice--info">
          <span className="ct-dot mt-1.5" aria-hidden="true" />
          <div>
            <p className="text-sm font-semibold">Ask about a clause first</p>
            <p className="mt-0.5 text-sm">
              The approval queue and validity checks open once there is an answer in this
              session. Review a clause, then come back.
            </p>
          </div>
        </div>
      ) : null}

      {loading ? (
        <div className="space-y-2" role="status" aria-label="Loading the control room">
          <Skeleton lines={4} label="Loading the control room" />
        </div>
      ) : null}

      <div className="grid gap-5 xl:grid-cols-2 xl:items-start">
        <ScanPagePanel />
        <DictationPanel
          clauses={clauses}
          defaultClauseId={defaultClauseId}
          onFactProposed={(fact) => {
            setFacts((current) => [fact, ...current.filter((row) => row.id !== fact.id)])
          }}
          onApprove={handleApprove}
        />
      </div>

      <FactTrustList
        facts={facts}
        reviewedIds={reviewedIds}
        disabled={!actionsEnabled}
        onApprove={(id) => void handleApprove(id)}
        onChallenge={(id) => void handleChallenge(id)}
      />

      {approveNotice ? <StateMessage tone="info">{approveNotice}</StateMessage> : null}

      {recomputed ? (
        <p className="text-sm font-medium text-ct-ink">
          Related answers were updated after you changed this fact.
        </p>
      ) : null}
      {dependent ? (
        <div className="space-y-2">
          {recomputed ? <IllustrationLabel /> : null}
          <FindingCard finding={dependent} title="Current answer" />
        </div>
      ) : null}

      <div className="grid gap-5 xl:grid-cols-2 xl:items-start">
        <AsOfPanel
          asOf={asOf}
          commencement={COMMENCEMENT_DATE}
          finding={asOfResult}
          disabled={!actionsEnabled}
          onAsOfChange={handleAsOf}
        />

        <UnknownClaimDemo
          question={unknownQ}
          finding={unknownResult}
          disabled={!actionsEnabled || unknownBusy}
          error={unknownError}
          onQuestionChange={setUnknownQ}
          onAsk={() => void handleUnknownAsk()}
        />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)] xl:items-start">
        <FactWordingEditor
          sentence={factSentence}
          result={verifyResult}
          disabled={!actionsEnabled}
          onChange={setFactSentence}
          onReset={() => {
            if (baseFinding) {
              setFactSentence(baseFinding.proof.premises[0]?.statement ?? '')
              setVerifyResult(null)
            }
          }}
          onRecheck={() => {
            if (!claimId || !baseFinding) {
              return
            }
            void (async () => {
              const proof = proofFromSentence(baseFinding.proof, factSentence)
              setVerifyResult(await api.verifyProof(claimId, proof))
            })()
          }}
        />

        <ChallengerPanel
          report={
            verifyResult && !verifyResult.valid
              ? parseChallengerReport({
                  blocking: true,
                  objections: [
                    {
                      severity: 'blocking',
                      reason: 'Cited premise text does not match the admitted fact statement, so the proof is not using an admitted premise.',
                    },
                  ],
                })
              : null
          }
        />
      </div>
    </div>
  )
}
