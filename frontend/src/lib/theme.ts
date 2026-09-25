// Light / dark theme. Follows the OS setting until the user picks one explicitly, then
// remembers the choice. index.html applies the stored theme before React loads, so the
// page never flashes the wrong colours.
import { useSyncExternalStore } from 'react'

export type Theme = 'light' | 'dark'
const KEY = 'theme'
const media = window.matchMedia('(prefers-color-scheme: dark)')

function stored(): Theme | null {
  try {
    const t = localStorage.getItem(KEY)
    return t === 'light' || t === 'dark' ? t : null
  } catch { return null }        // storage can be blocked; fall back to the OS setting
}

let current: Theme = stored() ?? (media.matches ? 'dark' : 'light')
const listeners = new Set<() => void>()

function apply(t: Theme) {
  current = t
  document.documentElement.classList.toggle('dark', t === 'dark')
  listeners.forEach((l) => l())
}

// Track the OS setting only while the user has not chosen a theme themselves
media.addEventListener('change', (e) => { if (!stored()) apply(e.matches ? 'dark' : 'light') })

export function setTheme(t: Theme) {
  try { localStorage.setItem(KEY, t) } catch { /* still applies for this session */ }
  apply(t)
}

/** The current theme, re-rendering when it changes (toggle or OS switch). */
export function useTheme(): Theme {
  return useSyncExternalStore(
    (cb) => { listeners.add(cb); return () => listeners.delete(cb) },
    () => current,
  )
}
