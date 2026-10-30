import { useEffect, useState } from 'react'

import { api } from '../api/client'
import { DEMO_MATTER_ID } from '../api/config'
import {
  COMMENCEMENT_DATE,
  UNKNOWN_QUESTION,
  applyFactAction,
  asOfFinding,
  challengedFinding,
  unknownFinding,
} from '../api/mocks/lawyerControl'
import type { Fact, Finding, Proof, ProofVerifyResult } from '../api/types'
import { DEMO_CHALLENGER_REPORT } from '../api/mocks/challenger'
import { ChallengerPanel } from '../components/ChallengerPanel'
import { FindingCard } from '../components/FindingCard'
import { AsOfPanel } from '../components/lawyer/AsOfPanel'
import { FactTrustList } from '../components/lawyer/FactTrustList'
import { ProofEditor } from '../components/lawyer/ProofEditor'
import { UnknownClaimDemo } from '../components/lawyer/UnknownClaimDemo'
import { AiDraftBadge } from '../components/badges/AiDraftBadge'

export function LawyerControlPage() {
  const [facts, setFacts] = useState<Fact[]>([])
  const [baseFinding, setBaseFinding] = useState<Finding | null>(null)
  const [reviewedIds, setReviewedIds] = useState<string[]>([])
  const [dependent, setDependent] = useState<Finding | null>(null)
  const [recomputed, setRecomputed] = useState(false)
  const [asOf, setAsOf] = useState(COMMENCEMENT_DATE)
  const [asOfResult, setAsOfResult] = useState<Finding | null>(null)
  const [unknownQ, setUnknownQ] = useState(UNKNOWN_QUESTION)
  const [unknownResult, setUnknownResult] = useState<Finding | null>(null)
  const [proofText, setProofText] = useState('')
  const [verifyResult, setVerifyResult] = useState<ProofVerifyResult | null>(null)

  useEffect(() => {
    void (async () => {
      const nextFacts = await api.facts(DEMO_MATTER_ID)
      setFacts(nextFacts)
      setReviewedIds(
        nextFacts
          .filter((fact) => fact.trust_class === 'lawyer_confirmed')
          .map((fact) => fact.id),
      )
      const finding = await api.currentFinding('C-001')
      if (finding) {
        setBaseFinding(finding)
        setDependent(finding)
        setProofText(JSON.stringify(finding.proof, null, 2))
      }
    })()
  }, [])

  async function handleApprove(factId: string) {
    const action = await api.approveFact(factId)
    setFacts((current) => applyFactAction(current, action))
    setReviewedIds((ids) => (ids.includes(factId) ? ids : [...ids, factId]))
  }

  async function handleChallenge(factId: string) {
    const action = await api.challengeFact(factId)
    setFacts((current) => applyFactAction(current, action))
    setRecomputed(true)
    if (baseFinding) {
      setDependent(challengedFinding(baseFinding))
    }
  }

  function handleAsOf(next: string) {
    setAsOf(next)
    if (baseFinding) {
      setAsOfResult(asOfFinding(baseFinding, next))
    }
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6">
      <header>
        <p className="ct-section-title">Screen 3 · Lawyer control</p>
        <h1 className="text-2xl font-semibold tracking-tight">Premises &amp; trust</h1>
        <AiDraftBadge label="AI draft — not yet reviewed" />
      </header>

      <FactTrustList
        facts={facts}
        reviewedIds={reviewedIds}
        onApprove={(id) => void handleApprove(id)}
        onChallenge={(id) => void handleChallenge(id)}
      />

      {recomputed ? (
        <p className="text-sm font-medium">Dependents recomputed after the trust-class change.</p>
      ) : null}
      {dependent ? <FindingCard finding={dependent} /> : null}

      <AsOfPanel
        asOf={asOf}
        commencement={COMMENCEMENT_DATE}
        finding={asOfResult}
        onAsOfChange={handleAsOf}
      />

      <UnknownClaimDemo
        question={unknownQ}
        finding={unknownResult}
        onQuestionChange={setUnknownQ}
        onAsk={() => setUnknownResult(unknownFinding())}
      />

      <ProofEditor
        value={proofText}
        result={verifyResult}
        onChange={setProofText}
        onReset={() => {
          if (baseFinding) {
            setProofText(JSON.stringify(baseFinding.proof, null, 2))
            setVerifyResult(null)
          }
        }}
        onVerify={() => {
          void (async () => {
            try {
              const parsed = JSON.parse(proofText) as Proof
              const claimId = baseFinding?.claim_id ?? 'C-001'
              setVerifyResult(await api.verifyProof(claimId, parsed))
            } catch {
              setVerifyResult({
                valid: false,
                cited_source_versions: [],
                errors: [
                  {
                    code: 'PREMISE_MISMATCH',
                    message: 'Proof JSON is not valid.',
                  },
                ],
              })
            }
          })()
        }}
      />

      <ChallengerPanel
        enabled
        report={verifyResult && !verifyResult.valid ? DEMO_CHALLENGER_REPORT : null}
      />
    </div>
  )
}
