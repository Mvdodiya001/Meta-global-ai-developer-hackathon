import { useEffect, useState } from 'react'

import { api } from '../../api/client'
import { currentMatterId, rememberMatterId } from '../../api/demoSession'
import type { MatterSummary } from '../../api/types'

/**
 * Sidebar matter picker (Phase 0). Switching reloads the app so every
 * screen refetches inside the newly selected matter.
 */
export function MatterSwitcher() {
  const [matters, setMatters] = useState<MatterSummary[]>([])
  const [creating, setCreating] = useState(false)
  const [title, setTitle] = useState('')
  const [clientName, setClientName] = useState('')
  const [busy, setBusy] = useState(false)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    void (async () => {
      try {
        const list = await api.matters()
        setMatters(list.matters)
      } catch {
        setFailed(true)
      }
    })()
  }, [])

  function switchTo(matterId: string) {
    rememberMatterId(matterId)
    window.location.reload()
  }

  async function create() {
    if (!title.trim() || !clientName.trim() || busy) {
      return
    }
    setBusy(true)
    try {
      const created = await api.createMatter({
        title: title.trim(),
        client_name: clientName.trim(),
      })
      switchTo(created.id)
    } catch {
      setFailed(true)
      setBusy(false)
    }
  }

  if (failed) {
    // Auth-enforced API + no token yet: point at sign-in, don't vanish.
    return (
      <div className="px-1">
        <p className="ct-nav-group !px-1">Matter</p>
        <a href="/signin" className="ct-nav-link">
          Sign in to see matters
        </a>
      </div>
    )
  }

  if (matters.length === 0) {
    return null
  }

  const selected = matters.some((m) => m.id === currentMatterId())
    ? currentMatterId()
    : matters[0].id

  return (
    <div className="px-1">
      <label htmlFor="matter-switcher" className="ct-nav-group !px-1">
        Matter
      </label>
      <select
        id="matter-switcher"
        className="ct-select !py-1.5 text-[0.82rem]"
        value={selected}
        onChange={(event) => switchTo(event.target.value)}
      >
        {matters.map((matter) => (
          <option key={matter.id} value={matter.id}>
            {matter.title}
          </option>
        ))}
      </select>
      {creating ? (
        <div className="mt-2 space-y-2">
          <input
            aria-label="New matter title"
            className="ct-input !py-1.5 text-[0.82rem]"
            placeholder="Matter title"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
          <input
            aria-label="New matter client"
            className="ct-input !py-1.5 text-[0.82rem]"
            placeholder="Client name"
            value={clientName}
            onChange={(event) => setClientName(event.target.value)}
          />
          <div className="flex gap-2">
            <button
              type="button"
              className="ct-btn ct-btn--primary ct-btn--sm"
              disabled={busy || !title.trim() || !clientName.trim()}
              onClick={() => void create()}
            >
              Create matter
            </button>
            <button
              type="button"
              className="ct-btn ct-btn--ghost ct-btn--sm"
              onClick={() => setCreating(false)}
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <button
          type="button"
          className="ct-btn ct-btn--ghost ct-btn--sm mt-1 !px-1"
          onClick={() => setCreating(true)}
        >
          + New matter
        </button>
      )}
    </div>
  )
}
