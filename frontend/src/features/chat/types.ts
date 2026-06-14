export type UserMessage = { role: 'user'; text: string }
export type AssistantMessage = { role: 'assistant'; text: string }
export type SystemMessage = { role: 'system'; text: string }
export type ReportMessage = {
  role: 'report'
  reportId: string
  trend?: string
  risk?: string
  title?: string
}

export type ChatMessage = UserMessage | AssistantMessage | SystemMessage | ReportMessage

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

export function isTextMessage(msg: ChatMessage): msg is UserMessage | AssistantMessage | SystemMessage {
  return msg.role === 'user' || msg.role === 'assistant' || msg.role === 'system'
}
