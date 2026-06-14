import { useEffect, useRef, useState } from 'react'
import { Loader2, Send, Square } from 'lucide-react'
import { cn } from '../../lib/utils'
import { useChat } from '../chat/ChatProvider'
import { MessageItem } from './messages/MessageItem'

export function WorkspacePage() {
  const {
    state,
    isStreaming,
    pendingSessionKeys,
    isSessionPending,
    sendUserMessage,
    cancelStreaming,
  } = useChat()

  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const inputAreaRef = useRef<HTMLDivElement>(null)

  const active = state.sessions[state.activeSessionKey]
  const activePending = isSessionPending(state.activeSessionKey)
  const hasPendingWork = pendingSessionKeys.length > 0

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [active?.messages, state.activeSessionKey, activePending])

  useEffect(() => {
    const vv = window.visualViewport
    if (!vv) return

    const scrollInputIntoView = () => {
      window.requestAnimationFrame(() => {
        inputAreaRef.current?.scrollIntoView({ block: 'end', behavior: 'smooth' })
      })
    }

    vv.addEventListener('resize', scrollInputIntoView)
    return () => vv.removeEventListener('resize', scrollInputIntoView)
  }, [])

  const sendMessage = () => {
    const text = input.trim()
    if (!text) return
    if (sendUserMessage(text)) {
      setInput('')
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-1 flex-col">
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-[800px] px-4 py-6">
          {!active?.messages.length ? (
            <div className="flex min-h-[50vh] flex-col items-center justify-center px-2 text-center">
              <h2 className="text-xl font-semibold tracking-tight sm:text-2xl">有什么可以帮你？</h2>
              <p className="mt-2 max-w-md text-sm text-[var(--color-muted)]">
                向 OpenClaw 提问市场分析、关键词追踪或任意研究任务。切换页面后回复会在后台继续，回到工作区即可查看。
              </p>
            </div>
          ) : (
            active.messages.map((msg, i) => {
              const isLastAssistant =
                activePending && msg.role === 'assistant' && active.assistantIndex === i
              return (
                <MessageItem
                  key={`${state.activeSessionKey}-${i}`}
                  message={msg}
                  isGenerating={isLastAssistant}
                />
              )
            })
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div
        ref={inputAreaRef}
        className="shrink-0 border-t border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-3 pb-[calc(0.75rem+env(safe-area-inset-bottom))]"
      >
        {activePending ? (
          <div className="mx-auto mb-2 flex max-w-[800px] items-center justify-between gap-2">
            <span className="inline-flex items-center gap-1.5 text-xs text-[var(--color-accent)]">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              OpenClaw 正在生成回复…
            </span>
            <button
              type="button"
              onClick={cancelStreaming}
              className="inline-flex items-center gap-1 rounded-lg border border-[var(--color-border)] px-2 py-1 text-xs font-medium text-[var(--color-text)] transition-colors hover:bg-[var(--color-surface)]"
            >
              <Square className="h-3 w-3 fill-current" />
              停止生成
            </button>
          </div>
        ) : hasPendingWork ? (
          <p className="mx-auto mb-2 max-w-[800px] text-xs text-[var(--color-muted)]">
            其他对话仍在后台生成，点击右上角查看对话列表。
          </p>
        ) : null}

        <div className="mx-auto flex max-w-[800px] items-end gap-2 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 shadow-sm focus-within:border-[var(--color-accent)]">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onFocus={() => {
              window.setTimeout(() => {
                inputAreaRef.current?.scrollIntoView({ block: 'end', behavior: 'smooth' })
              }, 300)
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                sendMessage()
              }
            }}
            disabled={activePending || isStreaming}
            rows={1}
            placeholder={activePending ? '等待生成完成…' : '发送消息给 OpenClaw…'}
            className="max-h-40 min-h-[24px] flex-1 resize-none bg-transparent py-2 text-sm outline-none disabled:opacity-60"
          />
          <button
            type="button"
            onClick={sendMessage}
            disabled={activePending || isStreaming || !input.trim()}
            className={cn(
              'mb-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-lg',
              'bg-[var(--color-text)] text-[var(--color-bg)] transition-opacity disabled:opacity-30',
            )}
            aria-label="发送"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
        <p className="mx-auto mt-2 hidden max-w-[800px] text-center text-xs text-[var(--color-muted)] sm:block">
          OpenClaw 回复仅供参考。Enter 发送，Shift+Enter 换行。
        </p>
      </div>
    </div>
  )
}
