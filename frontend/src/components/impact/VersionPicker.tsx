import type { SourceList, SourceVersion } from '../../api/types'
import { IconArrowRight, IconBook, IconRefresh } from '../ui/Icons'
import { SimulatedBadge } from '../badges/SimulatedBadge'

type VersionPickerProps = {
  sources: SourceList['sources']
  versions: SourceVersion[]
  sourceId: string
  versionId: string
  whatIfBusy?: boolean
  onSourceChange: (sourceId: string) => void
  onVersionChange: (versionId: string) => void
  onIngest: () => void
  onWhatIf: () => void
}

export function VersionPicker({
  sources,
  versions,
  sourceId,
  versionId,
  whatIfBusy = false,
  onSourceChange,
  onVersionChange,
  onIngest,
  onWhatIf,
}: VersionPickerProps) {
  const selected = versions.find((version) => version.id === versionId)

  return (
    <section className="ct-panel" aria-labelledby="version-picker-heading">
      <div className="ct-panel-head">
        <div className="flex items-start gap-2.5">
          <span className="mt-0.5 text-ct-muted" aria-hidden="true">
            <IconBook size={17} />
          </span>
          <div>
            <h2 id="version-picker-heading" className="ct-panel-title">
              Compare a law version
            </h2>
            <p className="ct-panel-desc">
              Preview first, then apply. Previewing never saves anything.
            </p>
          </div>
        </div>
        {selected?.is_simulated ? <SimulatedBadge /> : null}
      </div>
      <div className="ct-panel-body">
        <div className="grid gap-3 md:grid-cols-2">
          <div className="ct-field">
            <label htmlFor="source-picker" className="ct-label">
              Legal source
            </label>
            <select
              id="source-picker"
              value={sourceId}
              onChange={(event) => onSourceChange(event.target.value)}
              className="ct-select"
            >
              {sources.map((source) => (
                <option key={source.id} value={source.id}>
                  {source.title}
                </option>
              ))}
            </select>
          </div>
          <div className="ct-field">
            <label htmlFor="version-picker" className="ct-label">
              Law version
            </label>
            <select
              id="version-picker"
              value={versionId}
              onChange={(event) => onVersionChange(event.target.value)}
              className="ct-select"
            >
              {versions.map((version) => (
                <option key={version.id} value={version.id}>
                  {version.version_label} · from {version.effective_from}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-ct-line pt-3">
          <button
            type="button"
            onClick={onWhatIf}
            disabled={!versionId || whatIfBusy}
            aria-label="Preview a law change — nothing is saved"
            className="ct-btn ct-btn--secondary"
          >
            <IconRefresh size={15} />
            {whatIfBusy ? 'Previewing…' : 'Preview a law change — nothing is saved'}
          </button>
          <button type="button" onClick={onIngest} className="ct-btn ct-btn--primary">
            Apply this law change
            <IconArrowRight size={15} />
          </button>
        </div>
      </div>
    </section>
  )
}
