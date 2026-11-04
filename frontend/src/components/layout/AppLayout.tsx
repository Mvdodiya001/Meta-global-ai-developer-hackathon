import { useState } from 'react'
import { Outlet } from 'react-router-dom'

import { DisclaimerBanner } from './DisclaimerBanner'
import { MatterSwitcher } from './MatterSwitcher'
import { SiteNav } from './SiteNav'
import { ThemeToggle } from './ThemeToggle'
import { IconChevronDown } from '../ui/Icons'

const SIDEBAR_STORAGE_KEY = 'clausetrace.sidebar'
const SIDEBAR_REGION_ID = 'clausetrace-sidebar'

function readInitialCollapsed(): boolean {
  try {
    return window.localStorage.getItem(SIDEBAR_STORAGE_KEY) === 'collapsed'
  } catch {
    return false
  }
}

export function AppLayout() {
  const [navCollapsed, setNavCollapsed] = useState<boolean>(readInitialCollapsed)

  function toggleNav() {
    setNavCollapsed((prev) => {
      const next = !prev
      try {
        window.localStorage.setItem(
          SIDEBAR_STORAGE_KEY,
          next ? 'collapsed' : 'expanded',
        )
      } catch {
        // storage unavailable; the in-memory state still applies
      }
      return next
    })
  }

  return (
    <div className={navCollapsed ? 'ct-shell ct-shell--nav-collapsed' : 'ct-shell'}>
      <a href="#main-content" className="ct-skip-link">
        Skip to content
      </a>
      <DisclaimerBanner />
      <div className="ct-shell-body">
        {!navCollapsed && (
          <aside
            id={SIDEBAR_REGION_ID}
            className="ct-sidebar"
            aria-label="ClauseTrace"
          >
            <div className="flex items-center justify-between gap-3">
              <div className="ct-brand">
                <span className="ct-brand-mark" aria-hidden="true">
                  CT
                </span>
                <span className="min-w-0">
                  <span className="ct-brand-name block">ClauseTrace</span>
                  <span className="ct-brand-sub block">Legal verification</span>
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  className="ct-icon-btn"
                  onClick={toggleNav}
                  aria-expanded={true}
                  aria-controls={SIDEBAR_REGION_ID}
                  aria-label="Hide navigation"
                  title="Hide navigation"
                >
                  <IconChevronDown size={16} className="rotate-90" />
                </button>
                <ThemeToggle />
              </div>
            </div>
            <MatterSwitcher />
            <SiteNav />
            <div className="ct-sidebar-foot">
              <p>
                Answers are conditional on accepted premises and recorded source
                versions. Earlier findings are never overwritten.
              </p>
            </div>
          </aside>
        )}

        <div className="ct-main-wrap">
          <div className="ct-topbar">
            <p className="ct-topbar-note">
              Matter workspace · draft findings need a lawyer&rsquo;s review
            </p>
          </div>
          <main id="main-content" className="ct-main">
            <Outlet />
          </main>
        </div>
      </div>
      {navCollapsed && (
        <button
          type="button"
          className="ct-nav-expand-tab"
          onClick={toggleNav}
          aria-expanded={false}
          aria-controls={SIDEBAR_REGION_ID}
          aria-label="Show navigation"
          title="Show navigation"
        >
          <IconChevronDown size={16} className="-rotate-90" />
        </button>
      )}
    </div>
  )
}
