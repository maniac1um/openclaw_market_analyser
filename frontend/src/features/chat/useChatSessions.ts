import { useCallback, useRef, useState } from 'react'
import { toast } from 'sonner'
import {
  CHAT_STORAGE_KEY,
  createEmptySession,
  deriveTitleFromMessages,
  normalizeMessages,
  saveChatState,
  buildInitialChatState,
} from './storage'
import type { ChatSession } from './types'

export type ChatState = {
  sessions: Record<string, ChatSession>
  sessionOrder: string[]
  activeSessionKey: string
  nextSessionNum: number
}

export function useChatSessions() {
  const initial = useRef(buildInitialChatState()).current
  const [state, setState] = useState<ChatState>(initial)
  const stateRef = useRef(state)
  stateRef.current = state

  const commit = useCallback((next: ChatState) => {
    stateRef.current = next
    setState(next)
    saveChatState(next.sessions, next.sessionOrder, next.activeSessionKey, next.nextSessionNum)
  }, [])

  const selectSession = useCallback(
    (id: string) => {
      const cur = stateRef.current
      if (!cur.sessions[id]) return
      commit({ ...cur, activeSessionKey: id })
    },
    [commit],
  )

  const createSession = useCallback(() => {
    const cur = stateRef.current
    const { session, nextSessionNum } = createEmptySession(cur.nextSessionNum)
    commit({
      sessions: { ...cur.sessions, [session.id]: session },
      sessionOrder: [session.id, ...cur.sessionOrder].slice(0, 20),
      activeSessionKey: session.id,
      nextSessionNum,
    })
  }, [commit])

  const deleteSession = useCallback(
    (id: string) => {
      const cur = stateRef.current
      if (!cur.sessions[id]) return
      const sessions = { ...cur.sessions }
      delete sessions[id]
      const sessionOrder = cur.sessionOrder.filter((x) => x !== id)
      if (!sessionOrder.length) {
        const { session, nextSessionNum } = createEmptySession(1)
        commit({
          sessions: { [session.id]: session },
          sessionOrder: [session.id],
          activeSessionKey: session.id,
          nextSessionNum,
        })
        return
      }
      const activeSessionKey = id === cur.activeSessionKey ? sessionOrder[0] : cur.activeSessionKey
      commit({ ...cur, sessions, sessionOrder, activeSessionKey })
    },
    [commit],
  )

  const clearAll = useCallback(() => {
    try {
      localStorage.removeItem(CHAT_STORAGE_KEY)
    } catch {
      /* ignore */
    }
    const { session, nextSessionNum } = createEmptySession(1)
    commit({
      sessions: { [session.id]: session },
      sessionOrder: [session.id],
      activeSessionKey: session.id,
      nextSessionNum,
    })
    toast.success('已清空所有对话')
  }, [commit])

  const prepareOutgoingMessage = useCallback(
    (text: string): { sessionKey: string; nextState: ChatState } | null => {
      const cur = stateRef.current
      let sessionKey = cur.activeSessionKey
      let sessions = { ...cur.sessions }
      let sessionOrder = [...cur.sessionOrder]
      let nextSessionNum = cur.nextSessionNum

      if (!sessionKey || !sessions[sessionKey]) {
        const created = createEmptySession(nextSessionNum)
        sessionKey = created.session.id
        sessions[sessionKey] = created.session
        sessionOrder = [sessionKey, ...sessionOrder].slice(0, 20)
        nextSessionNum = created.nextSessionNum
      }

      const session = { ...sessions[sessionKey] }
      const messages = normalizeMessages([
        ...session.messages,
        { side: 'user' as const, text },
        { side: 'assistant' as const, text: '' },
      ])
      session.messages = messages
      session.assistantIndex = messages.length - 1
      session.title = deriveTitleFromMessages(messages)
      sessions[sessionKey] = session

      const nextState: ChatState = {
        sessions,
        sessionOrder,
        activeSessionKey: sessionKey,
        nextSessionNum,
      }
      commit(nextState)
      return { sessionKey, nextState }
    },
    [commit],
  )

  const applyAssistantDelta = useCallback(
    (sessionKey: string, text: string, done: boolean) => {
      const cur = stateRef.current
      const session = cur.sessions[sessionKey]
      if (!session || session.assistantIndex === null) return
      const messages = [...session.messages]
      messages[session.assistantIndex] = { side: 'assistant', text }
      const next: ChatState = {
        ...cur,
        sessions: {
          ...cur.sessions,
          [sessionKey]: { ...session, messages },
        },
      }
      commit(next)
      return done
    },
    [commit],
  )

  const applyAssistantError = useCallback(
    (sessionKey: string, error: string) => {
      const cur = stateRef.current
      const session = cur.sessions[sessionKey]
      if (!session) return
      const messages = [...session.messages]
      if (session.assistantIndex !== null) {
        messages[session.assistantIndex] = {
          side: 'assistant',
          text: `回复失败：${error || '未知错误'}`,
        }
      }
      commit({
        ...cur,
        sessions: {
          ...cur.sessions,
          [sessionKey]: { ...session, messages },
        },
      })
    },
    [commit],
  )

  return {
    state,
    stateRef,
    selectSession,
    createSession,
    deleteSession,
    clearAll,
    prepareOutgoingMessage,
    applyAssistantDelta,
    applyAssistantError,
  }
}
