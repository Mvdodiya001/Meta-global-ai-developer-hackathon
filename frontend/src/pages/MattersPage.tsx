import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { api } from '../api/client'
import { preferredMatterId } from '../api/demoSession'
import type { Matter } from '../api/types'
import { UnderstandingPanel } from '../components/documents/UnderstandingPanel'
import { UploadPanel } from '../components/documents/UploadPanel'
import { PageHeader } from '../components/layout/PageHeader'
import { Button } from '../components/ui/Button'
import { IconArrowRight, IconControl, IconImpact, IconMatters, IconReview } from '../components/ui/Icons'
import { Skeleton } from '../components/ui/Skeleton'
import { StateMessage } from '../components/ui/StateMessage'

const WORKFLOWS = [
  {
    to: '/review',
    label: 'Review a clause',
    hint: 'Ask whether a clause meets a requirement, and read the proof behind the answer.',
    Icon: IconReview,
  },
  {
    to: '/impact',
    label: 'Law changes',
    hint: 'See which earlier answers depended on a section that has since changed.',
    Icon: IconImpact,
  },
  {
    to: '/control',
    label: 'Your control room',
    hint: 'Approve facts, inspect trust, and test what would change an answer.',
    Icon: IconControl,
  },
] as const

export function MattersPage() {
  const [matter, setMatter] = useState<Matter | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const list = await api.matters()
      const picked =
        preferredMatterId(list.matters.map((row) => row.id)) ?? list.matters[0]?.id
      if (picked) {
        setMatter(await api.matter(picked))
      }
    } catch {
      setError('The matter could not be loaded.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div className="ct-page">
      <PageHeader
        eyebrow="Workspace"
        title="Your matters"
        description="One place to check a contract clause against a stated version of the law, then keep the reasoning on file."
      />

      {error ? (
        <StateMessage tone="danger" live="alert">
          <p>{error}</p>
          <Button variant="secondary" size="sm" className="mt-2" onClick={() => void load()}>
            Try again
          </Button>
        </StateMessage>
      ) : null}

      {loading && !matter ? (
        <div className="space-y-2" role="status" aria-label="Loading matter">
          <Skeleton lines={2} label="Loading matter" />
        </div>
      ) : null}

      {matter ? (
        <section aria-labelledby="matter-heading">
          <p className="ct-eyebrow flex items-center gap-2">
            <IconMatters size={14} />
            Current matter
          </p>
          <h2
            id="matter-heading"
            className="mt-2 font-serif text-3xl font-semibold leading-tight tracking-tight text-ct-ink"
          >
            {matter.title}
          </h2>
          <p className="mt-2 text-sm text-ct-muted">
            <span className="font-medium text-ct-soft">Client</span>
            <span className="mx-2 text-ct-lineStrong" aria-hidden="true">
              /
            </span>
            {matter.client_name}
          </p>
          <p className="mt-4 max-w-2xl border-t border-ct-line pt-4 text-sm leading-relaxed text-ct-muted">
            Every answer is conditional on the premises you accept and the law version
            in force on the as-of date. Earlier answers stay on file.
          </p>
        </section>
      ) : null}

      <section className="space-y-3" aria-labelledby="workflow-heading">
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 id="workflow-heading" className="text-base font-semibold tracking-tight">
              Start a review
            </h2>
            <p className="mt-0.5 text-sm text-ct-muted">
              Follow the same order a supervising lawyer would: check, re-check, then govern.
            </p>
          </div>
        </div>
        <ol className="grid gap-x-8 gap-y-2 md:grid-cols-3">
          {WORKFLOWS.map((flow, index) => (
            <li key={flow.to} className="border-t-2 border-ct-line pt-3">
              <Link
                to={flow.to}
                className="group flex h-full flex-col gap-2 no-underline"
              >
                <span className="flex items-center justify-between">
                  <span className="text-ct-accent">
                    <flow.Icon size={18} />
                  </span>
                  <span className="ct-mono text-xs text-ct-faint">
                    {String(index + 1).padStart(2, '0')}
                  </span>
                </span>
                <span className="block">
                  <span className="block text-sm font-semibold text-ct-ink">{flow.label}</span>
                  <span className="mt-1 block text-sm leading-relaxed text-ct-muted">
                    {flow.hint}
                  </span>
                </span>
                <span className="mt-auto inline-flex items-center gap-1 text-xs font-semibold text-ct-accent">
                  Open
                  <IconArrowRight
                    size={13}
                    className="transition-transform duration-150 group-hover:translate-x-0.5"
                  />
                </span>
              </Link>
            </li>
          ))}
        </ol>
      </section>

      {matter ? <UploadPanel /> : null}

      {matter ? <UnderstandingPanel /> : null}
    </div>
  )
}
