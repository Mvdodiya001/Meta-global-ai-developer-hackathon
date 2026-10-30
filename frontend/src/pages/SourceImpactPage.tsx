import { useCallback, useEffect, useState } from 'react'

import { api } from '../api/client'
import { DEMO_MATTER_ID, DEMO_SOURCE_ID } from '../api/config'
import type {
  AuditTrail,
  DiffResult,
  Finding,
  GraphSlice,
  ImpactReport,
  IngestVersionBody,
  SourceList,
  SourceVersion,
} from '../api/types'
import { AuditList } from '../components/AuditList'
import { DiffView } from '../components/DiffView'
import { StaleGraph } from '../components/StaleGraph'
import { AffectedFindings } from '../components/impact/AffectedFindings'
import { BeforeAfterSplit } from '../components/impact/BeforeAfterSplit'
import { VersionPicker } from '../components/impact/VersionPicker'

function ingestBody(version: SourceVersion, diff: DiffResult): IngestVersionBody {
  return {
    version_label: version.version_label,
    published_on: version.published_on,
    effective_from: version.effective_from,
    provisions: diff.after.map((row) => ({
      key: row.key,
      text: row.text,
      effective_from: row.effective_from,
      effective_until: row.effective_until ?? null,
    })),
  }
}

export function SourceImpactPage() {
  const [sources, setSources] = useState<SourceList['sources']>([])
  const [versions, setVersions] = useState<SourceVersion[]>([])
  const [sourceId, setSourceId] = useState(DEMO_SOURCE_ID)
  const [versionId, setVersionId] = useState('')
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
    const current = list.versions.find((version) => version.id === preferred)
    const againstId =
      current?.supersedes_id ??
      list.versions.find((version) => version.id !== preferred)?.id ??
      preferred
    const [nextDiff, nextGraph, trail, report] = await Promise.all([
      preferred ? api.diff(preferred, againstId, nextSource) : Promise.resolve(null),
      api.graph(DEMO_MATTER_ID, nextSource),
      api.audit(DEMO_MATTER_ID),
      preferred ? api.impact(`IMP-${preferred}`) : Promise.resolve(null),
    ])
    setVersions(list.versions)
    setVersionId(preferred)
    setDiff(nextDiff)
    setGraph(nextGraph)
    setAudit(trail)
    setImpact(report)
    setAfter(null)
    setReverified(false)
    const firstId = report?.affected[0]?.finding_id
    setBefore(firstId ? await api.findingById(firstId) : null)
  }, [])

  useEffect(() => {
    void api.sources().then((sourceList) => {
      setSources(sourceList.sources)
      const initial =
        sourceList.sources.find((row) => row.id === DEMO_SOURCE_ID)?.id ??
        sourceList.sources[0]?.id
      if (initial) {
        setSourceId(initial)
        void loadSource(initial)
      }
    })
  }, [loadSource])

  async function handleSourceChange(next: string) {
    setSourceId(next)
    await loadSource(next)
  }

  async function handleIngest() {
    const selected = versions.find((version) => version.id === versionId)
    if (!selected || !diff) {
      return
    }
    const result = await api.ingest(sourceId, ingestBody(selected, diff))
    const [report, slice, trail] = await Promise.all([
      api.impact(result.impact_report_id),
      api.graph(DEMO_MATTER_ID, sourceId),
      api.audit(DEMO_MATTER_ID),
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
    const result = await api.reverify(impact.id)
    const nextId = result.current[0]
    const [nextFinding, trail] = await Promise.all([
      nextId ? api.findingById(nextId) : Promise.resolve(null),
      api.audit(DEMO_MATTER_ID),
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
