import { useEffect, useState } from 'react'

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window === 'undefined') return false
    return window.matchMedia(query).matches
  })

  useEffect(() => {
    const mql = window.matchMedia(query)
    const onChange = () => setMatches(mql.matches)
    onChange()
    mql.addEventListener('change', onChange)
    return () => mql.removeEventListener('change', onChange)
  }, [query])

  return matches
}

/** Tailwind `md` breakpoint (768px). */
export function useIsMdUp(): boolean {
  return useMediaQuery('(min-width: 768px)')
}

/** Tailwind `lg` breakpoint (1024px). */
export function useIsLgUp(): boolean {
  return useMediaQuery('(min-width: 1024px)')
}
