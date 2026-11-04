export type Theme = 'light' | 'dark'

const THEME_KEY = 'clausetrace.theme'

function prefersDark(): boolean {
  return (
    typeof window !== 'undefined' &&
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(prefers-color-scheme: dark)').matches
  )
}

export function storedTheme(): Theme | null {
  try {
    const value = window.localStorage.getItem(THEME_KEY)
    return value === 'dark' || value === 'light' ? value : null
  } catch {
    return null
  }
}

export function resolveTheme(): Theme {
  return storedTheme() ?? (prefersDark() ? 'dark' : 'light')
}

export function applyTheme(theme: Theme): void {
  document.documentElement.classList.toggle('dark', theme === 'dark')
  document.documentElement.dataset.theme = theme
  try {
    window.localStorage.setItem(THEME_KEY, theme)
  } catch {
    // storage unavailable; the in-memory class still applies
  }
}

/** Apply the saved or system theme before React paints (main.tsx). */
export function initTheme(): Theme {
  const theme = resolveTheme()
  document.documentElement.classList.toggle('dark', theme === 'dark')
  document.documentElement.dataset.theme = theme
  return theme
}
