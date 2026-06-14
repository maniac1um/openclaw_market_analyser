import type { ChatMessage, ChatSession, ChatStoragePayload, UserMessage } from './types'

export const CHAT_STORAGE_KEY = 'oc_portal_chat_v1'
const MAX_CHAT_SESSIONS = 20
const MAX_MESSAGES_PER_SESSION = 200

function toSafeText(v: unknown): string {
  if (typeof v !== 'string') return ''
  return v.slice(0, 4000)
}

function normalizeRole(raw: Record<string, unknown>): ChatMessage['role'] | null {
  if (raw.role === 'user' || raw.role === 'assistant' || raw.role === 'system' || raw.role === 'report') {
    return raw.role
  }
  if (raw.side === 'user') return 'user'
  if (raw.side === 'assistant') return 'assistant'
  return null
}

export function normalizeMessages(arr: unknown): ChatMessage[] {
  if (!Array.isArray(arr)) return []
  const out: ChatMessage[] = []
  for (const item of arr) {
    if (!item || typeof item !== 'object') continue
    const raw = item as Record<string, unknown>
    if (raw.role === 'report' || (raw.side === 'report' && typeof raw.reportId === 'string')) {
      const reportId = toSafeText(raw.reportId).trim()
      if (!reportId) continue
      out.push({
        role: 'report',
        reportId,
        trend: toSafeText(raw.trend).trim() || undefined,
        risk: toSafeText(raw.risk).trim() || undefined,
        title: toSafeText(raw.title).trim() || undefined,
      })
      continue
    }
    const role = normalizeRole(raw)
    if (!role || role === 'report') continue
    out.push({ role, text: toSafeText(raw.text) })
  }
  return out.slice(-MAX_MESSAGES_PER_SESSION)
}

function normalizeSession(raw: Partial<ChatSession> | undefined, orderId: string): ChatSession {
  const id = toSafeText(raw?.id || orderId).trim() || orderId
  const title = toSafeText(raw?.title || deriveTitleFromMessages(normalizeMessages(raw?.messages)) || '新对话').trim()
  const messages = normalizeMessages(raw?.messages)
  const idxRaw = Number(raw?.assistantIndex)
  const assistantIndex =
    Number.isInteger(idxRaw) && idxRaw >= 0 && idxRaw < messages.length ? idxRaw : null
  return { id, title, messages, assistantIndex }
}

export function genSessionKey(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID()
  return `session-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export function deriveTitleFromMessages(messages: ChatMessage[]): string {
  const firstUser = messages.find((m): m is UserMessage => m.role === 'user' && m.text.trim().length > 0)
  if (!firstUser) return '新对话'
  const t = firstUser.text.trim().replace(/\s+/g, ' ')
  return t.length > 28 ? `${t.slice(0, 28)}…` : t
}

export function trimSessions(
  sessions: Record<string, ChatSession>,
  sessionOrder: string[],
  activeSessionKey: string | null,
): { sessions: Record<string, ChatSession>; sessionOrder: string[]; activeSessionKey: string | null } {
  const uniqOrder: string[] = []
  const seen = new Set<string>()
  for (const id of sessionOrder) {
    if (!sessions[id] || seen.has(id)) continue
    seen.add(id)
    uniqOrder.push(id)
  }
  const order = uniqOrder.slice(0, MAX_CHAT_SESSIONS)
  const trimmed: Record<string, ChatSession> = {}
  for (const id of order) {
    const s = sessions[id]
    const messages = normalizeMessages(s.messages)
    trimmed[id] = {
      ...s,
      id,
      title: s.title || deriveTitleFromMessages(messages),
      messages,
      assistantIndex:
        s.assistantIndex != null && s.assistantIndex >= 0 && s.assistantIndex < messages.length
          ? s.assistantIndex
          : null,
    }
  }
  const active = activeSessionKey && trimmed[activeSessionKey] ? activeSessionKey : order[0] || null
  return { sessions: trimmed, sessionOrder: order, activeSessionKey: active }
}

export function saveChatState(
  sessions: Record<string, ChatSession>,
  sessionOrder: string[],
  activeSessionKey: string | null,
  nextSessionNum: number,
): void {
  try {
    const trimmed = trimSessions(sessions, sessionOrder, activeSessionKey)
    const payload: ChatStoragePayload = {
      version: 1,
      nextSessionNum,
      activeSessionKey: trimmed.activeSessionKey,
      sessionOrder: trimmed.sessionOrder,
      sessions: {},
    }
    for (const id of trimmed.sessionOrder) {
      const s = trimmed.sessions[id]
      payload.sessions[id] = {
        id: s.id,
        title: s.title,
        messages: s.messages,
        assistantIndex: s.assistantIndex,
      }
    }
    localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(payload))
  } catch {
    /* ignore */
  }
}

export function loadChatState(): {
  sessions: Record<string, ChatSession>
  sessionOrder: string[]
  activeSessionKey: string | null
  nextSessionNum: number
} | null {
  try {
    const raw = localStorage.getItem(CHAT_STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as ChatStoragePayload
    if (!parsed || typeof parsed !== 'object') return null

    const parsedSessions = parsed.sessions || {}
    const parsedOrder = Array.isArray(parsed.sessionOrder) ? parsed.sessionOrder : []

    // Merge sessions referenced in order plus any orphan keys in storage.
    const allIds = new Set<string>([
      ...parsedOrder.filter((id): id is string => typeof id === 'string'),
      ...Object.keys(parsedSessions),
    ])

    const rebuilt: Record<string, ChatSession> = {}
    const rebuiltOrder: string[] = []

    for (const id of parsedOrder) {
      if (typeof id !== 'string' || !allIds.has(id)) continue
      allIds.delete(id)
      const s = normalizeSession(parsedSessions[id], id)
      rebuilt[s.id] = s
      if (!rebuiltOrder.includes(s.id)) rebuiltOrder.push(s.id)
    }
    for (const id of allIds) {
      const s = normalizeSession(parsedSessions[id], id)
      rebuilt[s.id] = s
      if (!rebuiltOrder.includes(s.id)) rebuiltOrder.unshift(s.id)
    }

    if (!rebuiltOrder.length) return null

    const n = Number(parsed.nextSessionNum)
    const nextSessionNum = Number.isInteger(n) && n > 0 ? n : rebuiltOrder.length + 1
    const activeSessionKey =
      typeof parsed.activeSessionKey === 'string' && rebuilt[parsed.activeSessionKey]
        ? parsed.activeSessionKey
        : rebuiltOrder[0]

    return { ...trimSessions(rebuilt, rebuiltOrder, activeSessionKey), nextSessionNum }
  } catch {
    return null
  }
}

export function createEmptySession(nextNum: number): { session: ChatSession; nextSessionNum: number } {
  const id = genSessionKey()
  return {
    session: { id, title: '新对话', messages: [], assistantIndex: null },
    nextSessionNum: nextNum + 1,
  }
}

export function buildInitialChatState(): {
  sessions: Record<string, ChatSession>
  sessionOrder: string[]
  activeSessionKey: string
  nextSessionNum: number
} {
  const loaded = loadChatState()
  if (loaded && loaded.activeSessionKey) {
    return {
      sessions: loaded.sessions,
      sessionOrder: loaded.sessionOrder,
      activeSessionKey: loaded.activeSessionKey,
      nextSessionNum: loaded.nextSessionNum,
    }
  }
  const { session, nextSessionNum } = createEmptySession(1)
  return {
    sessions: { [session.id]: session },
    sessionOrder: [session.id],
    activeSessionKey: session.id,
    nextSessionNum,
  }
}
