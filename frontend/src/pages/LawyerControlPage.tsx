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
  unknownFinding,
} from '../api/mocks/lawyerControl'
import type { Clause, Fact, Finding, Proof, ProofVerifyResult } from '../api/types'
import { parseChallengerReport } from '../api/mocks/challenger'
import { ChallengerPanel } from '../components/ChallengerPanel'
import { FindingCard } from '../components/FindingCard'
import { AsOfPanel } from '../components/lawyer/AsOfPanel'
import { DictationPanel } from '../components/lawyer/DictationPanel'
import { FactTrustList } from '../components/lawyer/FactTrustList'
import { FactWordingEditor } from '../components/lawyer/FactWordingEditor'
import { ScanPagePanel } from '../components/lawyer/ScanPagePanel'
import { UnknownClaimDemo } from '../components/lawyer/UnknownClaimDemo'
import { AiDraftBadge } from '../components/badges/AiDraftBadge'

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

  useEffect(() => {
    const stored = lastClaimId()
    setClaimId(stored)
    void (async () => {
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
    })()
  }, [])

  const actionsEnabled = Boolean(claimId)
  const defaultClauseId =
    facts.find((fact) => baseFinding?.premise_ids.includes(fact.id) && fact.clause_id)
      ?.clause_id ?? 'CL-10'

  async function handleApprove(factId: string) {
    const action = await api.approveFact(factId)
    setFacts((current) => applyFactAction(current, action))
    setReviewedIds((ids) => (ids.includes(factId) ? ids : [...ids, factId]))
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
    <div className="mx-auto flex max-w-5xl flex-col gap-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Your control room</h1>
        <AiDraftBadge label="AI draft — not yet reviewed" />
      </header>

      {!actionsEnabled ? (
        <p className="ct-panel p-4 text-sm font-medium">Ask about a clause first</p>
      ) : null}

      <ScanPagePanel />
      <DictationPanel
        clauses={clauses}
        defaultClauseId={defaultClauseId}
        onFactProposed={(fact) => {
          setFacts((current) => [fact, ...current.filter((row) => row.id !== fact.id)])
        }}
        onApprove={(id) => void handleApprove(id)}
      />

      <FactTrustList
        facts={facts}
        reviewedIds={reviewedIds}
        disabled={!actionsEnabled}
        onApprove={(id) => void handleApprove(id)}
        onChallenge={(id) => void handleChallenge(id)}
      />

      {recomputed ? (
        <p className="text-sm font-medium">
          Related answers were updated after you changed this fact.
        </p>
      ) : null}
      {dependent ? <FindingCard finding={dependent} title="Current answer" /> : null}

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
        disabled={!actionsEnabled}
        onQuestionChange={setUnknownQ}
        onAsk={() => {
          if (actionsEnabled) {
            setUnknownResult(unknownFinding())
          }
        }}
      />

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
  )
}
