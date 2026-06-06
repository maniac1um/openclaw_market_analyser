import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { toast } from 'sonner'
import { api, ApiError, type ChatRunPayload } from '../../lib/api'
import { checkOutgoingPrompt } from '../../lib/promptSafety'
import {
  addPendingSessionKey,
  loadPendingSessionKeys,
  removePendingSessionKey,
  savePendingSessionKeys,
} from './pendingRuns'
import { useChatSessions } from './useChatSessions'
import { CHAT_CLIENT_WATCHDOG_MS, type WsIncoming } from './types'

const POLL_INTERVAL_MS = 1500

function chatWsUrl(): string {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}/api/v1/chat/ws`
}

type StreamStatus = 'idle' | 'processing' | 'streaming'

type ChatContextValue = ReturnType<typeof useChatSessions> & {
  wsReady: boolean
  isStreaming: boolean
  streamStatus: StreamStatus
  pendingSessionKeys: string[]
  isSessionPending: (sessionKey: string) => boolean
  sendUserMessage: (text: string) => boolean
  cancelStreaming: () => void
}

const ChatContext = createContext<ChatContextValue | null>(null)

export function useChat(): ChatContextValue {
  const ctx = useContext(ChatContext)
  if (!ctx) {
    throw new Error('useChat must be used within ChatProvider')
  }
  return ctx
}

function applyRunPayload(
  run: ChatRunPayload,
  handlers: {
    applyAssistantDelta: (sessionKey: string, text: string, done: boolean) => void
    applyAssistantError: (sessionKey: string, error: string) => void
  },
): boolean {
  const key = run.sessionKey
  if (!key) return false
  if (run.error && run.done) {
    handlers.applyAssistantError(key, run.error)
    return true
  }
  handlers.applyAssistantDelta(key, run.text ?? '', Boolean(run.done))
  return Boolean(run.done)
}

export function ChatProvider({ children }: { children: ReactNode }) {
  const sessionsApi = useChatSessions()
  const { applyAssistantDelta, applyAssistantError } = sessionsApi

  const [wsReady, setWsReady] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamStatus, setStreamStatus] = useState<StreamStatus>('idle')
  const [pendingSessionKeys, setPendingSessionKeys] = useState<string[]>(() => loadPendingSessionKeys())

  const wsRef = useRef<WebSocket | null>(null)
  const busySessionKey = useRef<string | null>(null)
  const watchdogTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pendingRef = useRef(pendingSessionKeys)
  pendingRef.current = pendingSessionKeys

  const syncPending = useCallback((keys: string[]) => {
    pendingRef.current = keys
    setPendingSessionKeys(keys)
    savePendingSessionKeys(keys)
  }, [])

  const markPending = useCallback(
    (sessionKey: string) => {
      syncPending(addPendingSessionKey(sessionKey))
    },
    [syncPending],
  )

  const clearPending = useCallback(
    (sessionKey: string) => {
      syncPending(removePendingSessionKey(sessionKey))
    },
    [syncPending],
  )

  const clearWatchdog = useCallback(() => {
    if (watchdogTimerRef.current) {
      clearTimeout(watchdogTimerRef.current)
      watchdogTimerRef.current = null
    }
  }, [])

  const finishStreaming = useCallback(() => {
    clearWatchdog()
    setIsStreaming(false)
    setStreamStatus('idle')
    busySessionKey.current = null
  }, [clearWatchdog])

  const applyRun = useCallback(
    (run: ChatRunPayload) => {
      const done = applyRunPayload(run, { applyAssistantDelta, applyAssistantError })
      if (done) {
        clearPending(run.sessionKey)
        if (run.sessionKey === busySessionKey.current) {
          if (run.status === 'cancelled') {
            toast.message('已停止生成')
          } else if (run.status === 'timeout') {
            toast.error('响应超时')
          }
          finishStreaming()
        }
      } else if (run.status === 'processing') {
        setStreamStatus('processing')
      } else {
        setStreamStatus('streaming')
      }
      return done
    },
    [applyAssistantDelta, applyAssistantError, clearPending, finishStreaming],
  )

  const handleIncoming = useCallback(
    (data: WsIncoming) => {
      if (!data?.sessionKey) return
      if (data.type === 'assistant_delta') {
        applyRun({
          sessionKey: data.sessionKey,
          text: data.text,
          done: data.done,
          status: data.status,
        })
      } else if (data.type === 'assistant_error') {
        applyAssistantError(data.sessionKey, data.error || '未知错误')
        clearPending(data.sessionKey)
        if (data.sessionKey === busySessionKey.current) {
          finishStreaming()
        }
      }
    },
    [applyAssistantError, applyRun, clearPending, finishStreaming],
  )

  const pollPendingRuns = useCallback(async () => {
    const keys = pendingRef.current
    if (!keys.length) return
    await Promise.all(
      keys.map(async (sessionKey) => {
        try {
          const run = await api.chatRun(sessionKey)
          applyRun(run)
        } catch (err) {
          if (err instanceof ApiError && err.status === 404) {
            clearPending(sessionKey)
            if (sessionKey === busySessionKey.current) {
              finishStreaming()
            }
          }
        }
      }),
    )
  }, [applyRun, clearPending, finishStreaming])

  const syncActiveRunsFromServer = useCallback(async () => {
    try {
      const { runs } = await api.chatActiveRuns()
      if (!runs.length) return
      const merged = new Set([...pendingRef.current, ...runs.map((run) => run.sessionKey)])
      syncPending(Array.from(merged))
      for (const run of runs) {
        applyRun(run)
      }
    } catch {
      /* ignore */
    }
  }, [applyRun, syncPending])

  useEffect(() => {
    void syncActiveRunsFromServer()
  }, [syncActiveRunsFromServer])

  useEffect(() => {
    let cancelled = false
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined

    const connect = () => {
      if (cancelled) return
      const ws = new WebSocket(chatWsUrl())
      wsRef.current = ws
      ws.onopen = () => {
        setWsReady(true)
        void syncActiveRunsFromServer()
      }
      ws.onclose = () => {
        setWsReady(false)
        if (!cancelled) reconnectTimer = setTimeout(connect, 2000)
      }
      ws.onerror = () => setWsReady(false)
      ws.onmessage = (event) => {
        let data: WsIncoming | null = null
        try {
          data = JSON.parse(event.data)
        } catch {
          return
        }
        if (data) handleIncoming(data)
      }
    }
    connect()
    return () => {
      cancelled = true
      if (reconnectTimer) clearTimeout(reconnectTimer)
      wsRef.current?.close()
      wsRef.current = null
      clearWatchdog()
    }
  }, [clearWatchdog, handleIncoming, syncActiveRunsFromServer])

  useEffect(() => {
    if (!pendingSessionKeys.length) return
    const timer = setInterval(() => {
      void pollPendingRuns()
    }, POLL_INTERVAL_MS)
    return () => clearInterval(timer)
  }, [pendingSessionKeys.length, pollPendingRuns])

  useEffect(() => {
    if (!isStreaming) {
      clearWatchdog()
      return
    }
    watchdogTimerRef.current = setTimeout(() => {
      const key = busySessionKey.current
      if (!key) return
      wsRef.current?.send(JSON.stringify({ type: 'cancel_message', sessionKey: key }))
      toast.error('等待超时，已请求停止')
      finishStreaming()
    }, CHAT_CLIENT_WATCHDOG_MS)
    return clearWatchdog
  }, [clearWatchdog, finishStreaming, isStreaming])

  const sendUserMessage = useCallback(
    (text: string) => {
      const trimmed = text.trim()
      if (!trimmed || isStreaming) return false

      const safety = checkOutgoingPrompt(trimmed)
      if (!safety.ok) {
        toast.error(safety.message)
        return false
      }

      const ws = wsRef.current
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        toast.error('连接未就绪，请稍后重试')
        return false
      }

      const prepared = sessionsApi.prepareOutgoingMessage(trimmed)
      if (!prepared) return false

      markPending(prepared.sessionKey)
      setIsStreaming(true)
      setStreamStatus('processing')
      busySessionKey.current = prepared.sessionKey
      ws.send(
        JSON.stringify({
          type: 'user_message',
          text: trimmed,
          sessionKey: prepared.sessionKey,
        }),
      )
      return true
    },
    [isStreaming, markPending, sessionsApi],
  )

  const cancelStreaming = useCallback(() => {
    const key = busySessionKey.current || pendingSessionKeys[pendingSessionKeys.length - 1]
    if (!key) return
    wsRef.current?.send(JSON.stringify({ type: 'cancel_message', sessionKey: key }))
  }, [pendingSessionKeys])

  const isSessionPending = useCallback(
    (sessionKey: string) => pendingSessionKeys.includes(sessionKey),
    [pendingSessionKeys],
  )

  const value = useMemo<ChatContextValue>(
    () => ({
      ...sessionsApi,
      wsReady,
      isStreaming,
      streamStatus,
      pendingSessionKeys,
      isSessionPending,
      sendUserMessage,
      cancelStreaming,
    }),
    [
      sessionsApi,
      wsReady,
      isStreaming,
      streamStatus,
      pendingSessionKeys,
      isSessionPending,
      sendUserMessage,
      cancelStreaming,
    ],
  )

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
}
