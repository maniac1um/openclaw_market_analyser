const ALLOWED_PROTOCOLS = new Set(['http:', 'https:'])

export function safeExternalHref(url: string | undefined | null): string | undefined {
  if (!url) return undefined
  try {
    const parsed = new URL(url)
    if (!ALLOWED_PROTOCOLS.has(parsed.protocol)) return undefined
    return parsed.href
  } catch {
    return undefined
  }
}

export function markdownUrlTransform(url: string): string {
  return safeExternalHref(url) ?? ''
}
