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

export type WsIncoming =
  | { type: 'assistant_delta'; sessionKey: string; text?: string; done?: boolean }
  | { type: 'assistant_error'; sessionKey: string; error?: string }
