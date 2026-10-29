import type { Proof, TrustClass } from '../api/types'
import { TrustChip } from './TrustChip'

type ProofSyllogismProps = {
  proof: Proof
}

export function ProofSyllogism({ proof }: ProofSyllogismProps) {
  return (
    <section className="ct-panel space-y-4 p-4" aria-labelledby="proof-heading">
      <h2 id="proof-heading" className="ct-section-title">
        Proof syllogism
      </h2>
      <div>
        <h3 className="mb-2 text-sm font-medium text-slate-700 dark:text-slate-300">
          Premises
        </h3>
        <ol className="space-y-2">
          {proof.premises.map((premise, index) => (
            <li
              key={premise.fact_id}
              className="rounded-md border border-slate-200 p-3 dark:border-slate-700"
            >
              <div className="mb-1 flex flex-wrap items-center gap-2">
                <span className="font-mono text-xs text-slate-500">
                  P{index + 1} · {premise.fact_id}
                </span>
                <TrustChip trustClass={premise.trust_class as TrustClass} />
              </div>
              <p className="text-sm">{premise.statement}</p>
            </li>
          ))}
        </ol>
      </div>
      <div>
        <h3 className="mb-2 text-sm font-medium text-slate-700 dark:text-slate-300">
          Steps
        </h3>
        <ol className="space-y-1 font-mono text-xs text-slate-700 dark:text-slate-300">
          {proof.steps.map((step, index) => (
            <li key={`${step.kind}-${index}`}>
              {index + 1}. {step.kind}
              {step.rule_card_id ? ` · ${step.rule_card_id}` : ''}
              {step.conclusion ? ` → ${step.conclusion}` : ''}
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}
