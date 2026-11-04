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

/**
 * Numbered editorial reasoning: each step is a headed section separated by
 * hairlines, with the quoted source set as document text.
 */
export function ProofSyllogism({ finding }: ProofSyllogismProps) {
  const facts = displayFactLines(finding)
  const steps = [
    { title: 'Clause', quote: displayClauseQuote(finding) },
    { title: 'Section', quote: displaySectionQuote(finding) },
  ]

  return (
    <section className="ct-panel" aria-labelledby="reasoning-heading">
      <div className="ct-panel-head">
        <div>
          <h2 id="reasoning-heading" className="ct-panel-title">
            Reasoning
          </h2>
          <p className="ct-panel-desc">
            Each step is drawn from a quoted source or an accepted fact.
          </p>
        </div>
      </div>
      <div className="ct-panel-body">
        <ol className="ct-rows !gap-0">
          {steps.map((step, index) => (
            <li key={step.title}>
              <p className="ct-mono text-xs font-semibold tracking-wide text-ct-accent">
                {String(index + 1).padStart(2, '0')}
              </p>
              <p className="mt-1 font-serif text-lg font-semibold tracking-tight text-ct-ink">
                {step.title}
              </p>
              <blockquote className="ct-quote mt-2">{step.quote}</blockquote>
            </li>
          ))}
          {facts.map((line, index) => (
            <li key={`${line.label}-${index}`}>
              <p className="ct-mono text-xs font-semibold tracking-wide text-ct-accent">
                {String(index + 3).padStart(2, '0')}
              </p>
              <div className="mt-1 flex flex-wrap items-center gap-2">
                <TrustChip trustClass={line.trustClass} label={line.trustLabel} />
                {line.proposed ? (
                  <span className="text-xs font-medium text-ct-warn">Not relied on</span>
                ) : null}
              </div>
              <blockquote className="ct-quote mt-2">{line.label}</blockquote>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}
