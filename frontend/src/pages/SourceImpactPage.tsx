import { useCallback, useEffect, useState } from 'react'

import { api } from '../api/client'
import { DEMO_SOURCE_ID } from '../api/config'
import { currentMatterId } from '../api/demoSession'
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
import { PageHeader } from '../components/layout/PageHeader'
import { PanelSkeleton } from '../components/ui/Skeleton'
import { StateMessage } from '../components/ui/StateMessage'
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
  const [rechecking, setRechecking] = useState(false)
  const [ingesting, setIngesting] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [whatIf, setWhatIf] = useState<CounterfactualResult | null>(null)
  const [whatIfBusy, setWhatIfBusy] = useState(false)
  const [whatIfError, setWhatIfError] = useState<string | null>(null)
  const [reverifyList, setReverifyList] = useState<ReverifyList | null>(null)
  const [reverifyListError, setReverifyListError] = useState<string | null>(null)
  const [wording, setWording] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)

  const loadSource = useCallback(async (nextSource: string) => {
    setLoading(true)
    setActionError(null)
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
      api.graph(currentMatterId(), nextSource),
      api.audit(currentMatterId()),
      preferred ? api.impact(`IMP-${preferred}`) : Promise.resolve(null),
      api.reverifyList(currentMatterId()).catch((err: unknown) => {
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
    setRechecking(false)
    setWhatIf(null)
    setWhatIfError(null)
    setWording(captions)
    if (waiting) {
      setReverifyList(waiting)
      setReverifyListError(null)
    }
    const firstId = report?.affected[0]?.finding_id
    setBefore(firstId ? await api.findingById(firstId) : null)
    setLoading(false)
  }, [])

  useEffect(() => {
    void api
      .sources()
      .then((sourceList) => {
        setSources(sourceList.sources)
        const initial =
          sourceList.sources.find((row) => row.id === DEMO_SOURCE_ID)?.id ??
          sourceList.sources[0]?.id
        if (initial) {
          setSourceId(initial)
          void loadSource(initial).catch((err: unknown) => {
            setActionError(lawyerError(err))
            setLoading(false)
          })
        } else {
          setLoading(false)
        }
      })
      .catch((err: unknown) => {
        setActionError(lawyerError(err))
        setLoading(false)
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
    try {
      await loadSource(next)
    } catch (err) {
      setActionError(lawyerError(err))
      setLoading(false)
    }
  }

  async function handleIngest() {
    const selected = versions.find((version) => version.id === versionId)
    if (!selected || !diff || ingesting) {
      return
    }
    setIngesting(true)
    setActionError(null)
    try {
      const result = await api.ingest(sourceId, ingestBody(selected, diff))
      const [report, slice, trail] = await Promise.all([
        api.impact(result.impact_report_id),
        api.graph(currentMatterId(), sourceId),
        api.audit(currentMatterId()),
      ])
      const captions = await wordingFor(report.affected.map((row) => row.finding_id))
      setImpact(report)
      setGraph(slice)
      setAudit(trail)
      setAfter(null)
      setReverified(false)
      setWording((current) => ({ ...current, ...captions }))
      // The Before/After comparison anchors on the first affected answer.
      // At page load nothing is affected yet, so capture it here — after
      // applying the change — or the split never renders post-recheck.
      const firstAffectedId = report.affected[0]?.finding_id
      if (firstAffectedId) {
        try {
          const first = await api.findingById(firstAffectedId)
          setBefore((prev) => prev ?? first)
        } catch {
          // Comparison is best-effort; the re-check queue already rendered.
        }
      }
    } catch (err) {
      setActionError(lawyerError(err))
    } finally {
      setIngesting(false)
    }
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
    if (!impact || rechecking) {
      return
    }
    setRechecking(true)
    setActionError(null)
    try {
      const result = await api.reverify(impact.id)
      const nextId = result.current[0]
      const [nextFinding, trail] = await Promise.all([
        nextId ? api.findingById(nextId) : Promise.resolve(null),
        api.audit(currentMatterId()),
      ])
      setAfter(nextFinding)
      setAudit(trail)
      setReverified(true)
    } catch (err) {
      setActionError(lawyerError(err))
    } finally {
      setRechecking(false)
    }
  }

  return (
    <div className="ct-page">
      <PageHeader
        eyebrow="Change analysis"
        title="Law changes"
        description="See which earlier answers depended on a section that has changed, and re-check only what needs a fresh decision."
      />

      {actionError ? (
        <StateMessage tone="danger" live="alert">
          {actionError}
        </StateMessage>
      ) : null}

      <VersionPicker
        sources={sources}
        versions={versions}
        sourceId={sourceId}
        versionId={versionId}
        onSourceChange={(id) => void handleSourceChange(id)}
        onVersionChange={setVersionId}
        onIngest={() => void handleIngest()}
        onWhatIf={() => void handleWhatIf()}
        whatIfBusy={whatIfBusy || ingesting}
      />

      {loading ? <PanelSkeleton label="Loading the change analysis" /> : null}

      {whatIf || whatIfError ? (
        <div className="grid gap-5 xl:grid-cols-2 xl:items-start">
          <WhatIfPanel
            result={whatIf}
            error={whatIfError}
            changedWording={changedWording}
            affectedWording={wording}
          />
          <ReverifyListPanel list={reverifyList} error={reverifyListError} />
        </div>
      ) : (
        <ReverifyListPanel list={reverifyList} error={reverifyListError} />
      )}

      {diff ? <DiffView diff={diff} /> : null}
      {graph ? <StaleGraph graph={graph} /> : null}

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] xl:items-start">
        {impact ? (
          <AffectedFindings
            rows={queueRows}
            onRecheck={() => void handleReverify()}
            rechecking={rechecking}
            rechecked={reverified}
          />
        ) : null}
        {audit ? <AuditList audit={audit} /> : null}
      </div>

      {before ? <BeforeAfterSplit before={before} after={after} /> : null}
    </div>
  )
}
