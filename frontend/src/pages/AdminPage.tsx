import { useEffect, useState } from 'react'

import type { AdminOverview } from '../api/types'
import { STATUS_LABELS, TRUST_LABELS } from '../content/glossary'
import { PageHeader } from '../components/layout/PageHeader'
import { Button } from '../components/ui/Button'
import { Panel } from '../components/ui/Panel'
import { PanelSkeleton } from '../components/ui/Skeleton'
import { StateMessage } from '../components/ui/StateMessage'

function labelFor(map: Record<string, string>, key: string): string {
  return map[key] ?? 'Other'
}

function CountRows({
  entries,
  labels,
}: {
  entries: [string, number][]
  labels: Record<string, string>
}) {
  const total = Math.max(
    1,
    entries.reduce((sum, [, count]) => sum + count, 0),
  )
  return (
    <ul className="space-y-3">
      {entries.map(([key, count]) => (
        <li key={key}>
          <div className="mb-1 flex items-baseline justify-between gap-3">
            <span className="text-sm text-ct-soft">{labelFor(labels, key)}</span>
            <span className="ct-mono text-sm font-semibold text-ct-ink">{count}</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-ct-surface3">
            <div
              className="h-full rounded-full bg-ct-accent"
              style={{ width: `${Math.round((count / total) * 100)}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  )
}

export function AdminPage() {
  const [overview, setOverview] = useState<AdminOverview | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/admin/overview')
      if (!response.ok) {
        throw new Error('failed')
      }
      setOverview((await response.json()) as AdminOverview)
    } catch {
      setError('The internal overview could not be loaded.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  return (
    <div className="ct-page">
      <PageHeader
        eyebrow="Staff only"
        title="Internal overview"
        description="For the team running ClauseTrace. Not part of the lawyer workflow."
      />

      {error ? (
        <StateMessage tone="danger" live="alert">
          <p>{error}</p>
          <Button variant="secondary" size="sm" className="mt-2" onClick={() => void load()}>
            Try again
          </Button>
        </StateMessage>
      ) : null}

      {loading ? <PanelSkeleton label="Loading the internal overview" /> : null}

      {overview ? (
        <>
          <dl className="grid gap-x-8 gap-y-3 border-y border-ct-line py-4 sm:grid-cols-3">
            <div>
              <dt className="ct-stat-label">Matters</dt>
              <dd className="ct-stat-value mt-1">{overview.matters}</dd>
            </div>
            <div className="sm:border-l sm:border-ct-line sm:pl-8">
              <dt className="ct-stat-label">Estimated model spend</dt>
              <dd className="ct-stat-value mt-1">${overview.spend_usd.toFixed(4)}</dd>
            </div>
            <div className="sm:border-l sm:border-ct-line sm:pl-8">
              <dt className="ct-stat-label">Answer states</dt>
              <dd className="ct-stat-value mt-1">
                {Object.values(overview.findings_by_status).reduce(
                  (sum, count) => sum + count,
                  0,
                )}
              </dd>
            </div>
          </dl>

          <div className="grid gap-5 lg:grid-cols-2 lg:items-start">
            <Panel heading="Answers so far" headingId="admin-findings">
              <CountRows
                entries={Object.entries(overview.findings_by_status)}
                labels={STATUS_LABELS}
              />
            </Panel>
            <Panel heading="Facts by confirmation state" headingId="admin-facts">
              <CountRows
                entries={Object.entries(overview.facts_by_trust)}
                labels={TRUST_LABELS}
              />
            </Panel>
          </div>

          <p className="ct-help">
            This page is intentionally absent from lawyer navigation.
          </p>
        </>
      ) : null}
    </div>
  )
}
