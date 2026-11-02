import { useCallback, useEffect, useState } from 'react'

import { api } from '../api/client'
import { DEMO_MATTER_ID, DEMO_SOURCE_ID } from '../api/config'
import type {
  AuditTrail,
  CounterfactualResult,
  DiffResult,
  Finding,
  GraphSlice,
  ImpactReport,
  IngestVersionBody,
  ReverifyList,
  SourceList,
  SourceVersion,
} from '../api/types'
import { AuditList } from '../components/AuditList'
import { DiffView } from '../components/DiffView'
import { StaleGraph } from '../components/StaleGraph'
import { AffectedFindings, type RecheckRow } from '../components/impact/AffectedFindings'
import { BeforeAfterSplit } from '../components/impact/BeforeAfterSplit'
import { ReverifyListPanel } from '../components/impact/ReverifyListPanel'
import { VersionPicker } from '../components/impact/VersionPicker'
import { WhatIfPanel } from '../components/impact/WhatIfPanel'
import { AiDraftBadge } from '../components/badges/AiDraftBadge'
import { displayAnswerCaption } from '../utils/displayFields'
import { lawyerError, sectionWording } from '../utils/lawyerCopy'

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

async function wordingFor(ids: string[]): Promise<Record<string, string>> {
  const entries = await Promise.all(
    ids.map(async (id) => {
      try {
        const finding = await api.findingById(id)
        return [id, displayAnswerCaption(finding)] as const
      } catch {
        return [id, 'An answer that relied on this section'] as const
      }
    }),
  )
  return Object.fromEntries(entries)
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
  const [whatIf, setWhatIf] = useState<CounterfactualResult | null>(null)
  const [whatIfBusy, setWhatIfBusy] = useState(false)
  const [whatIfError, setWhatIfError] = useState<string | null>(null)
  const [reverifyList, setReverifyList] = useState<ReverifyList | null>(null)
  const [reverifyListError, setReverifyListError] = useState<string | null>(null)
  const [wording, setWording] = useState<Record<string, string>>({})

  const loadSource = useCallback(async (nextSource: string) => {
    const list = await api.sourceVersions(nextSource)
    const preferred =
      list.versions.find((version) => version.is_simulated)?.id ??
      list.versions[0]?.id ??
      ''
    const current = list.versions.find((version) => version.id === preferred)
    const againstId =
      current?.supersedes_id ??
      list.versions.find((version) => version.id !== preferred)?.id ??
      preferred
    const [nextDiff, nextGraph, trail, report, waiting] = await Promise.all([
      preferred ? api.diff(preferred, againstId, nextSource) : Promise.resolve(null),
      api.graph(DEMO_MATTER_ID, nextSource),
      api.audit(DEMO_MATTER_ID),
      preferred ? api.impact(`IMP-${preferred}`) : Promise.resolve(null),
      api.reverifyList(DEMO_MATTER_ID).catch((err: unknown) => {
        setReverifyListError(lawyerError(err))
        return null
      }),
    ])
    const ids = [
      ...(report?.affected.map((row) => row.finding_id) ?? []),
      ...(waiting?.findings.map((row) => row.finding_id) ?? []),
    ]
    const captions = await wordingFor([...new Set(ids)])
    setVersions(list.versions)
    setVersionId(preferred)
    setDiff(nextDiff)
    setGraph(nextGraph)
    setAudit(trail)
    setImpact(report)
    setAfter(null)
    setReverified(false)
    setWhatIf(null)
    setWhatIfError(null)
    setWording(captions)
    if (waiting) {
      setReverifyList(waiting)
      setReverifyListError(null)
    }
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

  const queueRows: RecheckRow[] =
    impact?.affected.map((row, index) => ({
      key: `${row.state}-${index}`,
      clauseRef: row.clause_ref,
      state: row.state,
      statusLabel: row.status_label,
    })) ?? []

  const changedWording = (whatIf?.changed_keys ?? []).map((key) =>
    sectionWording(key, diff?.after.find((row) => row.key === key)?.text ?? diff?.after[0]?.text),
  )

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
    const captions = await wordingFor(report.affected.map((row) => row.finding_id))
    setImpact(report)
    setGraph(slice)
    setAudit(trail)
    setAfter(null)
    setReverified(false)
    setWording((current) => ({ ...current, ...captions }))
  }

  async function handleWhatIf() {
    if (!versionId || whatIfBusy) {
      return
    }
    setWhatIfBusy(true)
    setWhatIfError(null)
    try {
      const result = await api.counterfactual({ source_version_id: versionId })
      const captions = await wordingFor(result.affected.map((row) => row.finding_id))
      setWording((current) => ({ ...current, ...captions }))
      setWhatIf(result)
    } catch (err) {
      setWhatIf(null)
      setWhatIfError(lawyerError(err))
    } finally {
      setWhatIfBusy(false)
    }
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
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Law changes</h1>
        <AiDraftBadge label="AI draft — not yet reviewed" />
        <p className="text-sm text-slate-600 dark:text-slate-400">
          See which answers need a re-check when the law changes.
        </p>
      </header>

      <VersionPicker
        sources={sources}
        versions={versions}
        sourceId={sourceId}
        versionId={versionId}
        onSourceChange={(id) => void handleSourceChange(id)}
        onVersionChange={setVersionId}
        onIngest={() => void handleIngest()}
        onWhatIf={() => void handleWhatIf()}
        whatIfBusy={whatIfBusy}
      />

      <WhatIfPanel
        result={whatIf}
        error={whatIfError}
        changedWording={changedWording}
        affectedWording={wording}
      />
      <ReverifyListPanel list={reverifyList} error={reverifyListError} />

      {diff ? <DiffView diff={diff} /> : null}
      {graph ? <StaleGraph graph={graph} /> : null}

      {impact ? (
        <AffectedFindings
          rows={queueRows}
          onRecheck={() => void handleReverify()}
          rechecking={false}
          rechecked={reverified}
        />
      ) : null}

      {before ? <BeforeAfterSplit before={before} after={after} /> : null}
      {audit ? <AuditList audit={audit} /> : null}
    </div>
  )
}
