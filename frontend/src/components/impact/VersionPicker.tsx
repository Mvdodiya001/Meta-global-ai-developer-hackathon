import type { SourceList, SourceVersion } from '../../api/types'
import { SimulatedBadge } from '../badges/SimulatedBadge'

type VersionPickerProps = {
  sources: SourceList['sources']
  versions: SourceVersion[]
  sourceId: string
  versionId: string
  onSourceChange: (sourceId: string) => void
  onVersionChange: (versionId: string) => void
  onIngest: () => void
}

export function VersionPicker({
  sources,
  versions,
  sourceId,
  versionId,
  onSourceChange,
  onVersionChange,
  onIngest,
}: VersionPickerProps) {
  const selected = versions.find((version) => version.id === versionId)

  return (
    <section className="ct-panel flex flex-wrap items-end gap-3 p-4">
      <div>
        <label htmlFor="source-picker" className="mb-1 block text-sm font-medium">
          Legal source
        </label>
        <select
          id="source-picker"
          value={sourceId}
          onChange={(event) => onSourceChange(event.target.value)}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900"
        >
          {sources.map((source) => (
            <option key={source.id} value={source.id}>
              {source.title}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="version-picker" className="mb-1 block text-sm font-medium">
          Compare against version
        </label>
        <select
          id="version-picker"
          value={versionId}
          onChange={(event) => onVersionChange(event.target.value)}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900"
        >
          {versions.map((version) => (
            <option key={version.id} value={version.id}>
              {version.version_label} ({version.id})
            </option>
          ))}
        </select>
      </div>
      {selected?.is_simulated ? <SimulatedBadge /> : null}
      <button
        type="button"
        onClick={onIngest}
        className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium hover:bg-slate-50 dark:border-slate-600 dark:hover:bg-slate-900"
      >
        Ingest source change
      </button>
    </section>
  )
}
