import { useState } from 'react'

import { applyTheme, resolveTheme, type Theme } from '../../utils/theme'
import { IconMoon, IconSun } from '../ui/Icons'

/** Persisted light/dark switch that never hides the content it affects. */
export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof document !== 'undefined' && document.documentElement.classList.contains('dark')) {
      return 'dark'
    }
    return resolveTheme()
  })

  function toggle() {
    const next: Theme = theme === 'dark' ? 'light' : 'dark'
    applyTheme(next)
    setTheme(next)
  }

  const label = theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'

  return (
    <button
      type="button"
      className="ct-icon-btn"
      onClick={toggle}
      aria-label={label}
      title={label}
    >
      {theme === 'dark' ? <IconSun size={16} /> : <IconMoon size={16} />}
    </button>
  )
}
