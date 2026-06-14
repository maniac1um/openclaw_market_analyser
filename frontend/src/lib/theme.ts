export const THEME_STORAGE_KEY = 'theme'

export type Theme = 'dark' | 'light'

export function resolveTheme(stored: string | null): Theme | null {
  if (stored === 'dark' || stored === 'light') return stored
  return null
}

export function getStoredTheme(): Theme {
  const saved = resolveTheme(localStorage.getItem(THEME_STORAGE_KEY))
  if (saved) return saved

  const legacy = localStorage.getItem('oc_dark')
  if (legacy === '1') return 'dark'
  if (legacy === '0') return 'light'

  if (typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark'
  }
  return 'light'
}

export function applyTheme(theme: Theme) {
  document.documentElement.classList.toggle('dark', theme === 'dark')
}

export function persistTheme(theme: Theme) {
  localStorage.setItem(THEME_STORAGE_KEY, theme)
}

export function initTheme() {
  applyTheme(getStoredTheme())
}

export function toggleTheme(current: Theme): Theme {
  return current === 'dark' ? 'light' : 'dark'
}
