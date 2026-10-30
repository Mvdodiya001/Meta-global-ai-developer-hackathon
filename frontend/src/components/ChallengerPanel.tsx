import type { ChallengerReportView } from '../api/mocks/challenger'
import { StatusBadge } from './badges/StatusBadge'

type ChallengerPanelProps = {
  enabled: boolean
  report: ChallengerReportView | null
  onToggle?: (enabled: boolean) => void
  onRun?: () => void
}

export function ChallengerPanel({
  enabled,
  report,
  onToggle,
  onRun,
}: ChallengerPanelProps) {
  return (
    <section className="ct-panel space-y-3 p-4" aria-labelledby="challenger-heading">
      <div className="flex flex-wrap items-center gap-3">
        <h2 id="challenger-heading" className="ct-section-title">
          Challenger
        </h2>
        {onToggle ? (
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={enabled}
              onChange={(event) => onToggle(event.target.checked)}
            />
            Challenger on
          </label>
        ) : null}
        {onRun && enabled ? (
          <button
            type="button"
            onClick={onRun}
            className="rounded-md border border-slate-300 px-3 py-1 text-xs font-medium hover:bg-slate-50 dark:border-slate-600 dark:hover:bg-slate-900"
          >
            Run challenger (demo)
          </button>
        ) : null}
      </div>
      <p className="text-sm text-slate-600 dark:text-slate-400">
        Second Muse Spark pass (<span className="font-mono">muse-spark-1.2</span>
        ), different prompt from the drafter. It reviews; the checker has no
        model in it. Set <span className="font-mono">CHALLENGER=off</span> to skip.
      </p>
      {!enabled ? (
        <p className="text-sm">Challenger is off. No second pass is sent.</p>
      ) : report == null ? (
        <p className="text-sm">No challenger report on this finding yet.</p>
      ) : report.objections.length === 0 ? (
        <p className="text-sm">No objections. The reviewer endorsed the draft.</p>
      ) : (
        <>
          {report.blocking ? (
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge status="REQUIRES_REVIEW" />
              <span className="text-sm">Blocking objection forces Requires review.</span>
            </div>
          ) : null}
          <p className="font-mono text-xs text-slate-500">model {report.model}</p>
          <ul className="space-y-2">
            {report.objections.map((objection, index) => (
              <li
                key={`${objection.severity}-${index}`}
                className="rounded-md border border-slate-200 p-3 text-sm dark:border-slate-700"
              >
                <p className="font-medium">
                  {objection.severity === 'blocking' ? 'Blocking' : 'Note'}
                </p>
                <p>{objection.reason}</p>
                {objection.quote ? (
                  <blockquote className="mt-1 font-mono text-xs text-slate-600 dark:text-slate-400">
                    {objection.quote}
                  </blockquote>
                ) : null}
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  )
}
