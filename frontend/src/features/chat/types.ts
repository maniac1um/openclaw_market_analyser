export type ChatMessage = {
  side: 'user' | 'assistant'
  text: string
}

export type ChatSession = {
  id: string
  title: string
  messages: ChatMessage[]
  assistantIndex: number | null
}

export type ChatStoragePayload = {
  version: 1
  nextSessionNum: number
  activeSessionKey: string | null
  sessionOrder: string[]
  sessions: Record<string, Omit<ChatSession, 'assistantIndex'> & { assistantIndex: number | null }>
}

export type AssistantStreamStatus =
  | 'processing'
  | 'streaming'
  | 'done'
  | 'cancelled'
  | 'timeout'

export type WsIncoming =
  | {
      type: 'assistant_delta'
      sessionKey: string
      text?: string
      done?: boolean
      status?: AssistantStreamStatus
    }
  | { type: 'assistant_error'; sessionKey: string; error?: string }

/** Client-side safety net if the server never sends done/error (ms). */
export const CHAT_CLIENT_WATCHDOG_MS = 630_000
