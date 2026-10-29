import { useEffect, useState } from 'react'

import { api } from '../api/client'
import type { Clause, Finding, Matter } from '../api/types'
import { FindingCard } from '../components/FindingCard'
import { ProofSyllogism } from '../components/ProofSyllogism'

export function ClauseReviewPage() {
  const [matter, setMatter] = useState<Matter | null>(null)
  const [clauses, setClauses] = useState<Clause[]>([])
  const [finding, setFinding] = useState<Finding | null>(null)

  useEffect(() => {
    void Promise.all([
      api.matter('MAT-01'),
      api.clauses('DOCV-01'),
      api.finding('C-001'),
    ]).then(([m, c, f]) => {
      setMatter(m)
      setClauses(c)
      setFinding(f)
    })
  }, [])

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
        <ul className="space-y-3">
          {clauses.map((clause) => (
            <li
              key={clause.id}
              className="rounded-md border border-slate-200 p-3 dark:border-slate-700"
            >
              <div className="mb-1 flex items-baseline gap-2">
                <span className="font-mono text-sm font-semibold">{clause.ref}</span>
                <span className="text-sm font-medium">{clause.heading}</span>
              </div>
              <p className="text-sm text-slate-700 dark:text-slate-300">{clause.text}</p>
            </li>
          ))}
        </ul>
      </section>

      {finding ? (
        <>
          <FindingCard finding={finding} />
          <ProofSyllogism proof={finding.proof} />
        </>
      ) : (
        <p className="text-sm text-slate-500">Loading finding…</p>
      )}
    </div>
  )
}
