import { useEffect, useState } from 'react'

import { api } from '../api/client'
import type { AuditTrail, DiffResult, GraphSlice, ImpactReport } from '../api/types'
import { AuditList } from '../components/AuditList'
import { DiffView } from '../components/DiffView'
import { StaleGraph } from '../components/StaleGraph'
import { SimulatedBadge } from '../components/badges/SimulatedBadge'
import { StatusBadge } from '../components/badges/StatusBadge'

export function SourceImpactPage() {
  const [diff, setDiff] = useState<DiffResult | null>(null)
  const [graph, setGraph] = useState<GraphSlice | null>(null)
  const [audit, setAudit] = useState<AuditTrail | null>(null)
  const [impact, setImpact] = useState<ImpactReport | null>(null)
  const [selectedVersion, setSelectedVersion] = useState('SV-02')

  useEffect(() => {
    void Promise.all([
      api.sourceVersions('SRC-DPDP-ACT'),
      api.diff('SRC-DPDP-ACT', 'SV-02'),
      api.graph('FND-001'),
      api.audit('MAT-01'),
      api.impact('IMP-01'),
    ]).then(([versions, d, g, a, i]) => {
      setDiff(d)
      setGraph(g)
      setAudit(a)
      setImpact(i)
      const simulated = versions.versions.find((v) => v.is_simulated)
      if (simulated) {
        setSelectedVersion(simulated.id)
      }
    })
  }, [])

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6">
      <header>
        <p className="ct-section-title">Screen 2 · Source change &amp; impact</p>
        <h1 className="text-2xl font-semibold tracking-tight">Amendment impact</h1>
      </header>

      <section className="ct-panel flex flex-wrap items-center gap-3 p-4">
        <label htmlFor="version-picker" className="text-sm font-medium">
          Compare against version
        </label>
        <select
          id="version-picker"
          value={selectedVersion}
          onChange={(event) => setSelectedVersion(event.target.value)}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900"
        >
          <option value="SV-02">SV-02 (simulated amendment)</option>
          <option value="SV-01">SV-01 (current)</option>
        </select>
        <SimulatedBadge />
      </section>

      {diff ? <DiffView diff={diff} /> : null}

      {graph ? <StaleGraph graph={graph} /> : null}

      {impact ? (
        <section className="ct-panel p-4" aria-labelledby="impact-heading">
          <h2 id="impact-heading" className="mb-3 ct-section-title">
            Affected findings
          </h2>
          <ul className="space-y-2">
            {impact.affected.map((row) => (
              <li
                key={row.finding_id}
                className="flex flex-wrap items-center gap-2 text-sm"
              >
                <span className="font-mono">{row.finding_id}</span>
                <span className="text-slate-500">claim {row.claim_id}</span>
                <StatusBadge status="FOLLOWS" state={row.state} />
              </li>
            ))}
          </ul>
          <button
            type="button"
            className="mt-4 rounded-md bg-blue-800 px-4 py-2 text-sm font-medium text-white hover:bg-blue-900 dark:bg-blue-700"
          >
            Re-verify (mock)
          </button>
        </section>
      ) : null}

      {audit ? <AuditList audit={audit} /> : null}
    </div>
  )
}
