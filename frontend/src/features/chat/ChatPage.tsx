import { useEffect, useRef, useState } from 'react'
import { Loader2, MessageSquarePlus, PanelLeftClose, PanelLeft, Send, Square, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '../../lib/utils'
import { useChat } from './ChatProvider'

function MessageBubble({
  side,
  text,
  isGenerating,
}: {
  side: 'user' | 'assistant'
  text: string
  isGenerating?: boolean
}) {
  if (side === 'user') {
    return (
      <div className="flex justify-end py-2">
        <div className="max-w-[min(85%,42rem)] rounded-2xl bg-[var(--color-text)] px-4 py-2.5 text-sm leading-relaxed text-[var(--color-bg)] whitespace-pre-wrap">
          {text}
        </div>
      </div>
    )
  }
  return (
    <div className="flex gap-3 py-3">
      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] text-xs font-semibold text-[var(--color-accent)]">
        OC
      </div>
      <div className="min-w-0 flex-1">
        <div className="text-sm leading-7 text-[var(--color-text)] whitespace-pre-wrap">
          {text || (
            <span className="inline-flex items-center gap-1 text-[var(--color-muted)]">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--color-muted)]" />
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--color-muted)] [animation-delay:150ms]" />
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--color-muted)] [animation-delay:300ms]" />
            </span>
          )}
        </div>
        {isGenerating ? (
          <p className="mt-2 inline-flex items-center gap-1.5 text-xs text-[var(--color-muted)]">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            生成中…
          </p>
        ) : null}
      </div>
    </div>
  )
}

export function ChatPage() {
  const {
    state,
    selectSession,
    createSession,
    deleteSession,
    clearAll,
    wsReady,
    isStreaming,
    streamStatus,
    pendingSessionKeys,
    isSessionPending,
    sendUserMessage,
    cancelStreaming,
  } = useChat()

  const [input, setInput] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const active = state.sessions[state.activeSessionKey]
  const activePending = isSessionPending(state.activeSessionKey)
  const hasPendingWork = pendingSessionKeys.length > 0

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [active?.messages, state.activeSessionKey, activePending])

  const sendMessage = () => {
    const text = input.trim()
    if (!text) return
    if (sendUserMessage(text)) {
      setInput('')
    }
  }

  const handleDelete = (id: string) => {
    if (isSessionPending(id)) {
      toast.warning('该对话仍在后台生成，请等待完成或停止生成')
      return
    }
    if (!confirm('删除这条对话？')) return
    deleteSession(id)
  }

  const connectionLabel = !wsReady
    ? '连接中…'
    : activePending
      ? streamStatus === 'processing'
        ? '生成中…（连接 Gateway）'
        : '生成中…'
      : hasPendingWork
        ? '后台生成中'
        : '已连接'

  return (
    <div className="flex h-full min-h-0 flex-1 overflow-hidden bg-[var(--color-bg)]">
      <aside
        className={cn(
          'flex shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] transition-all duration-200',
          sidebarOpen ? 'w-64' : 'w-0 overflow-hidden border-r-0',
        )}
      >
        <div className="flex items-center justify-between gap-2 p-3">
          <button
            type="button"
            onClick={createSession}
            disabled={isStreaming}
            className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-[var(--color-border)] px-3 py-2 text-sm font-medium transition-colors hover:bg-[var(--color-bg)] disabled:opacity-50"
          >
            <MessageSquarePlus className="h-4 w-4" />
            新对话
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-2 pb-2">
          {state.sessionOrder.map((id) => {
            const s = state.sessions[id]
            if (!s) return null
            const preview = s.messages.find((m) => m.side === 'user')?.text || '空白对话'
            return (
              <div
                key={id}
                className={cn(
                  'group relative mb-0.5 rounded-lg transition-colors',
                  id === state.activeSessionKey ? 'bg-[var(--color-bg)]' : 'hover:bg-[var(--color-bg)]/70',
                )}
              >
                <button
                  type="button"
                  onClick={() => selectSession(id)}
                  className="w-full px-3 py-2.5 text-left"
                >
                  <p className="truncate text-sm font-medium text-[var(--color-text)]">
                    {s.title}
                    {isSessionPending(id) ? (
                      <span className="ml-1.5 text-[10px] font-normal text-[var(--color-accent)]">生成中</span>
                    ) : null}
                  </p>
                  <p className="mt-0.5 truncate text-xs text-[var(--color-muted)]">{preview}</p>
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(id)}
                  className="absolute right-2 top-2 hidden rounded p-1 text-[var(--color-muted)] hover:bg-[var(--color-border)] hover:text-red-600 group-hover:block"
                  aria-label="删除对话"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            )
          })}
        </div>
        <div className="border-t border-[var(--color-border)] p-2">
          <button
            type="button"
            onClick={() => {
              if (hasPendingWork) {
                toast.warning('仍有后台生成任务，请等待完成或停止生成')
                return
              }
              if (confirm('清空所有本地对话记录？')) clearAll()
            }}
            className="w-full rounded-lg px-3 py-2 text-left text-xs text-[var(--color-muted)] hover:bg-[var(--color-bg)] hover:text-[var(--color-text)]"
          >
            清空所有对话
          </button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-12 shrink-0 items-center justify-between border-b border-[var(--color-border)] px-4">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setSidebarOpen((v) => !v)}
              className="rounded-md p-2 text-[var(--color-muted)] hover:bg-[var(--color-bg)] hover:text-[var(--color-text)]"
              aria-label="切换侧栏"
            >
              {sidebarOpen ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeft className="h-4 w-4" />}
            </button>
            <span className="text-sm font-medium">{active?.title || 'OpenClaw'}</span>
          </div>
          <div className="flex items-center gap-2">
            {activePending ? (
              <button
                type="button"
                onClick={cancelStreaming}
                className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--color-border)] px-2.5 py-1 text-xs font-medium text-[var(--color-text)] transition-colors hover:bg-[var(--color-bg)]"
              >
                <Square className="h-3 w-3 fill-current" />
                停止生成
              </button>
            ) : null}
            <span
              className={cn(
                'inline-flex items-center gap-1.5 text-xs',
                wsReady && !activePending && !hasPendingWork && 'text-green-600',
                (activePending || hasPendingWork) && 'text-[var(--color-accent)]',
                !wsReady && 'text-[var(--color-muted)]',
              )}
            >
              {activePending || hasPendingWork ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
              {connectionLabel}
            </span>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-3xl px-4 py-6">
            {!active?.messages.length ? (
              <div className="flex min-h-[50vh] flex-col items-center justify-center text-center">
                <h2 className="text-2xl font-semibold tracking-tight">有什么可以帮你？</h2>
                <p className="mt-2 max-w-md text-sm text-[var(--color-muted)]">
                  向 OpenClaw 提问市场分析、关键词追踪或任意研究任务。切换页面后回复会在后台继续，回到首页即可查看。
                </p>
              </div>
            ) : (
              active.messages.map((msg, i) => {
                const isLastAssistant =
                  activePending && msg.side === 'assistant' && active.assistantIndex === i
                return (
                  <MessageBubble
                    key={`${state.activeSessionKey}-${i}`}
                    side={msg.side}
                    text={msg.text}
                    isGenerating={isLastAssistant}
                  />
                )
              })
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="shrink-0 border-t border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-4">
          <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 shadow-sm focus-within:border-[var(--color-accent)]">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  sendMessage()
                }
              }}
              disabled={activePending || isStreaming}
              rows={1}
              placeholder={
                activePending ? 'OpenClaw 正在生成回复…' : '发送消息给 OpenClaw…'
              }
              className="max-h-40 min-h-[24px] flex-1 resize-none bg-transparent py-2 text-sm outline-none disabled:opacity-60"
            />
            <button
              type="button"
              onClick={sendMessage}
              disabled={activePending || isStreaming || !input.trim()}
              className="mb-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--color-text)] text-[var(--color-bg)] transition-opacity disabled:opacity-30"
              aria-label="发送"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
          <p className="mx-auto mt-2 max-w-3xl text-center text-xs text-[var(--color-muted)]">
            {activePending
              ? '生成中可切换其他页面；回到首页或等待轮询同步。可点击「停止生成」。'
              : hasPendingWork
                ? '其他对话仍在后台生成，回到对应对话或等待完成。'
                : 'OpenClaw 回复仅供参考。Enter 发送，Shift+Enter 换行。'}
          </p>
        </div>
      </div>
    </div>
  )
}
