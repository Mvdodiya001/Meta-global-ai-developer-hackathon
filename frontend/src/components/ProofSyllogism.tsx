import type { Finding } from '../api/types'
import {
  displayClauseQuote,
  displayFactLines,
  displaySectionQuote,
} from '../utils/displayFields'
import { TrustChip } from './TrustChip'

type ProofSyllogismProps = {
  finding: Finding
}

export function ProofSyllogism({ finding }: ProofSyllogismProps) {
  const facts = displayFactLines(finding)
  const steps = [
    { title: 'Clause', quote: displayClauseQuote(finding) },
    { title: 'Section', quote: displaySectionQuote(finding) },
  ]

  return (
    <section className="ct-panel space-y-4 p-4" aria-labelledby="reasoning-heading">
      <h2 id="reasoning-heading" className="ct-section-title">
        Reasoning
      </h2>
      <ol className="space-y-3">
        {steps.map((step, index) => (
          <li key={step.title} className="text-sm">
            <p className="font-medium">
              {index + 1}. {step.title}
            </p>
            <blockquote className="mt-1 border-l-2 border-slate-300 pl-3 dark:border-slate-600">
              {step.quote}
            </blockquote>
          </li>
        ))}
        {facts.map((line, index) => (
          <li key={`${line.label}-${index}`} className="text-sm">
            <p className="font-medium">{index + 3}.</p>
            <div className="mt-1 flex flex-wrap items-center gap-2">
              <TrustChip trustClass={line.trustClass} label={line.trustLabel} />
              {line.proposed ? (
                <span className="text-xs text-slate-500">Not relied on</span>
              ) : null}
            </div>
            <blockquote className="mt-1 border-l-2 border-slate-300 pl-3 dark:border-slate-600">
              {line.label}
            </blockquote>
          </li>
        ))}
      </ol>
    </section>
  )
}
