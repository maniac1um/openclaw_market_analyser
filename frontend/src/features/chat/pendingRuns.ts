const PENDING_STORAGE_KEY = 'oc_portal_chat_pending_v1'

export function loadPendingSessionKeys(): string[] {
  try {
    const raw = localStorage.getItem(PENDING_STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed.filter((item): item is string => typeof item === 'string')
  } catch {
    return []
  }
}

export function savePendingSessionKeys(keys: string[]): void {
  try {
    localStorage.setItem(PENDING_STORAGE_KEY, JSON.stringify(Array.from(new Set(keys))))
  } catch {
    /* ignore */
  }
}

export function addPendingSessionKey(sessionKey: string): string[] {
  const next = Array.from(new Set([...loadPendingSessionKeys(), sessionKey]))
  savePendingSessionKeys(next)
  return next
}

export function removePendingSessionKey(sessionKey: string): string[] {
  const next = loadPendingSessionKeys().filter((key) => key !== sessionKey)
  savePendingSessionKeys(next)
  return next
}
