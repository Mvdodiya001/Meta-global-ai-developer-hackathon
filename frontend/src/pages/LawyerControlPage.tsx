import { useEffect, useState } from 'react'

import { api } from '../api/client'
import type { Fact, TrustClass } from '../api/types'
import { TrustChip } from '../components/TrustChip'
import { AiDraftBadge } from '../components/badges/AiDraftBadge'
import { LawyerReviewedBadge } from '../components/badges/LawyerReviewedBadge'

export function LawyerControlPage() {
  const [facts, setFacts] = useState<Fact[]>([])
  const [asOf, setAsOf] = useState('2025-10-01')
  const [reviewedFactId, setReviewedFactId] = useState<string | null>('F-002')

  useEffect(() => {
    void api.facts('MAT-01').then(setFacts)
  }, [])

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6">
      <header>
        <p className="ct-section-title">Screen 3 · Lawyer control</p>
        <h1 className="text-2xl font-semibold tracking-tight">Premises &amp; trust</h1>
      </header>

      <section className="ct-panel flex flex-wrap items-end gap-4 p-4">
        <div>
          <label htmlFor="as-of" className="mb-1 block text-sm font-medium">
            As-of date
          </label>
          <input
            id="as-of"
            type="date"
            value={asOf}
            onChange={(event) => setAsOf(event.target.value)}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900"
          />
        </div>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Move across commencement dates to see in-force rules change (demo).
        </p>
      </section>

      <section className="ct-panel p-4" aria-labelledby="facts-heading">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <h2 id="facts-heading" className="ct-section-title">
            Matter facts
          </h2>
          <AiDraftBadge label="AI draft — not yet reviewed" />
        </div>
        <ul className="space-y-3">
          {facts.map((fact) => (
            <li
              key={fact.id}
              className="rounded-md border border-slate-200 p-4 dark:border-slate-700"
            >
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <span className="font-mono text-xs text-slate-500">{fact.id}</span>
                <TrustChip trustClass={fact.trust_class as TrustClass} />
                {reviewedFactId === fact.id ? <LawyerReviewedBadge /> : null}
              </div>
              <p className="text-sm">{fact.statement}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="rounded-md border border-slate-300 px-3 py-1 text-xs font-medium hover:bg-slate-50 dark:border-slate-600 dark:hover:bg-slate-800"
                  onClick={() => setReviewedFactId(fact.id)}
                >
                  Approve (demo)
                </button>
                <button
                  type="button"
                  className="rounded-md border border-rose-300 px-3 py-1 text-xs font-medium text-rose-900 hover:bg-rose-50 dark:border-rose-700 dark:text-rose-100 dark:hover:bg-rose-950/40"
                >
                  Challenge (mock)
                </button>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
