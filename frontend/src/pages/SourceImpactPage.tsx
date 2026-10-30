import { useCallback, useEffect, useState } from 'react'

import { api } from '../api/client'
import type {
  AuditTrail,
  DiffResult,
  Finding,
  GraphSlice,
  ImpactReport,
  SourceList,
  SourceVersion,
} from '../api/types'
import { AuditList } from '../components/AuditList'
import { DiffView } from '../components/DiffView'
import { StaleGraph } from '../components/StaleGraph'
import { AffectedFindings } from '../components/impact/AffectedFindings'
import { BeforeAfterSplit } from '../components/impact/BeforeAfterSplit'
import { VersionPicker } from '../components/impact/VersionPicker'

export function SourceImpactPage() {
  const [sources, setSources] = useState<SourceList['sources']>([])
  const [versions, setVersions] = useState<SourceVersion[]>([])
  const [sourceId, setSourceId] = useState('SRC-DPDP-ACT')
  const [versionId, setVersionId] = useState('SV-02')
  const [diff, setDiff] = useState<DiffResult | null>(null)
  const [graph, setGraph] = useState<GraphSlice | null>(null)
  const [audit, setAudit] = useState<AuditTrail | null>(null)
  const [impact, setImpact] = useState<ImpactReport | null>(null)
  const [before, setBefore] = useState<Finding | null>(null)
  const [after, setAfter] = useState<Finding | null>(null)
  const [reverified, setReverified] = useState(false)

  const loadSource = useCallback(async (nextSource: string, against?: string) => {
    const list = await api.sourceVersions(nextSource)
    const preferred =
      against ??
      list.versions.find((version) => version.is_simulated)?.id ??
      list.versions[0]?.id ??
      ''
    const [d, g] = await Promise.all([
      api.diff(nextSource, preferred),
      api.graph('FND-001', nextSource),
    ])
    setVersions(list.versions)
    setVersionId(preferred)
    setDiff(d)
    setGraph(g)
    setAfter(null)
    setReverified(false)
  }, [])

  useEffect(() => {
    void Promise.all([
      api.sources(),
      api.finding('C-001'),
      api.audit('MAT-01'),
      api.impact('IMP-01'),
    ]).then(([sourceList, finding, trail, report]) => {
      setSources(sourceList.sources)
      setBefore(finding)
      setAudit(trail)
      setImpact(report)
    })
    void loadSource('SRC-DPDP-ACT', 'SV-02')
  }, [loadSource])

  async function handleSourceChange(next: string) {
    setSourceId(next)
    await loadSource(next)
    if (next === 'SRC-DECOY') {
      setImpact({ id: 'IMP-DECOY', source_version_id: 'SV-DECOY-1', affected: [] })
    }
  }

  async function handleIngest() {
    const result = await api.ingest(sourceId)
    const [report, slice, trail] = await Promise.all([
      api.impact(result.impact_report_id),
      api.graph('FND-001', sourceId),
      api.audit('MAT-01'),
    ])
    setImpact(report)
    setGraph(slice)
    setAudit(trail)
    setAfter(null)
    setReverified(false)
  }

  async function handleReverify() {
    if (!impact) {
      return
    }
    await api.reverify(impact.id)
    const [nextFinding, trail] = await Promise.all([
      api.afterFinding(),
      api.reverifyAudit(),
    ])
    setAfter(nextFinding)
    setAudit(trail)
    setReverified(true)
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6">
      <header>
        <p className="ct-section-title">Screen 2 · Source change &amp; impact</p>
        <h1 className="text-2xl font-semibold tracking-tight">Amendment impact</h1>
      </header>

      <VersionPicker
        sources={sources}
        versions={versions}
        sourceId={sourceId}
        versionId={versionId}
        onSourceChange={(id) => void handleSourceChange(id)}
        onVersionChange={setVersionId}
        onIngest={() => void handleIngest()}
      />

      {diff ? <DiffView diff={diff} /> : null}
      {graph ? <StaleGraph graph={graph} /> : null}

      {impact ? (
        <AffectedFindings
          impact={impact}
          onReverify={() => void handleReverify()}
          reverifying={false}
          reverified={reverified}
        />
      ) : null}

      {before ? <BeforeAfterSplit before={before} after={after} /> : null}
      {audit ? <AuditList audit={audit} /> : null}
    </div>
  )
}
