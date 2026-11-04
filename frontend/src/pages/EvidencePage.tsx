import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { api } from '../api/client'
import type { Finding } from '../api/types'
import { FindingCard } from '../components/FindingCard'
import { PageHeader } from '../components/layout/PageHeader'
import { ProofSyllogism } from '../components/ProofSyllogism'
import { TrustChip } from '../components/TrustChip'
import { Button } from '../components/ui/Button'
import { IconClock } from '../components/ui/Icons'
import { Panel } from '../components/ui/Panel'
import { QueueList } from '../components/ui/QueueList'
import { PanelSkeleton } from '../components/ui/Skeleton'
import { StateMessage } from '../components/ui/StateMessage'
import { displayFactLines } from '../utils/displayFields'

export function EvidencePage() {
  const { findingId = '' } = useParams()
  const [finding, setFinding] = useState<Finding | null>(null)
  const [versions, setVersions] = useState<Finding[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const current = await api.findingById(findingId)
      setFinding(current)
      setVersions(await api.findingHistory(current.claim_id))
    } catch {
      setError('This answer could not be loaded.')
    } finally {
      setLoading(false)
    }
  }, [findingId])

  useEffect(() => {
    void load()
  }, [load])

  const factLines = finding ? displayFactLines(finding) : []
  const otherVersions = finding ? versions.filter((version) => version.id !== finding.id) : []

  return (
    <div className="ct-page">
      <PageHeader
        eyebrow="Evidence"
        title="Evidence for this answer"
        description="The quotes, facts, and version history behind one finding — kept together so the reasoning can be checked later."
      />

      {error ? (
        <StateMessage tone="danger" live="alert">
          <p>{error}</p>
          <Button variant="secondary" size="sm" className="mt-2" onClick={() => void load()}>
            Try again
          </Button>
        </StateMessage>
      ) : null}

      {loading ? <PanelSkeleton label="Loading the evidence" /> : null}

      {finding ? (
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)] xl:items-start">
          <div className="min-w-0 space-y-5">
            <FindingCard finding={finding} title="Answer" showEvidenceLink={false} />
            <ProofSyllogism finding={finding} />
          </div>

          <div className="min-w-0 space-y-5">
            <Panel
              heading="Facts relied on"
              headingId="evidence-facts"
              description="Only confirmed or document-extracted facts can support this answer."
            >
              {factLines.length === 0 ? (
                <p className="ct-empty">No facts were relied on for this answer.</p>
              ) : (
                <ul className="ct-rows">
                  {factLines.map((line, index) => (
                    <li
                      key={`${line.label}-${index}`}
                    >
                      <div className="mb-1.5 flex flex-wrap items-center gap-2">
                        <TrustChip trustClass={line.trustClass} label={line.trustLabel} />
                        {line.proposed ? (
                          <span className="text-xs font-medium text-ct-warn">Not relied on</span>
                        ) : null}
                      </div>
                      <p className="text-sm leading-relaxed text-ct-ink">{line.label}</p>
                      {line.confirmedBy ? (
                        <p className="mt-1 text-xs text-ct-muted">
                          Confirmed by {line.confirmedBy}
                        </p>
                      ) : null}
                    </li>
                  ))}
                </ul>
              )}
            </Panel>

            <QueueList
              heading="Version history"
              headingId="evidence-history"
              emptyText="No other versions of this answer."
              isEmpty={otherVersions.length === 0}
              description="Every re-check is appended; nothing is replaced."
            >
              {otherVersions.map((version) => (
                <li
                  key={version.id}
                  className="flex items-start gap-2.5 text-sm"
                >
                  <IconClock size={14} className="mt-0.5 shrink-0 text-ct-muted" />
                  <div className="min-w-0 flex-1">
                    <p className="text-ct-soft">
                      <span className="ct-readonly-chip mr-1.5">
                        Version {version.version_no}
                      </span>
                      {version.status_label}
                    </p>
                    <p className="mt-0.5 text-xs text-ct-muted">{version.law_version_label}</p>
                    <p className="ct-mono mt-0.5 text-[0.7rem] text-ct-faint">
                      {version.law_version_date}
                    </p>
                  </div>
                  <Link to={`/evidence/${version.id}`} className="ct-link shrink-0 text-xs">
                    View
                  </Link>
                </li>
              ))}
            </QueueList>
          </div>
        </div>
      ) : null}
    </div>
  )
}
