import { Loader2, MessageSquarePlus, Square, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '../../lib/utils'
import { Drawer } from '../../components/ui/ds'
import { useChat } from './ChatProvider'
import type { UserMessage } from './types'

export const CHAT_SESSIONS_DRAWER_WIDTH = 300

type ChatSessionsDrawerProps = {
  open: boolean
  onClose: () => void
}

export function ChatSessionsDrawer({ open, onClose }: ChatSessionsDrawerProps) {
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
    cancelStreaming,
  } = useChat()

  const active = state.sessions[state.activeSessionKey]
  const activePending = isSessionPending(state.activeSessionKey)
  const hasPendingWork = pendingSessionKeys.length > 0

  const connectionLabel = !wsReady
    ? '连接中…'
    : activePending
      ? streamStatus === 'processing'
        ? '生成中…'
        : '生成中…'
      : hasPendingWork
        ? '后台生成'
        : '已连接'

  const handleSelectSession = (id: string) => {
    selectSession(id)
    onClose()
  }

  const handleDelete = (id: string) => {
    if (isSessionPending(id)) {
      toast.warning('该对话仍在后台生成，请等待完成或停止生成')
      return
    }
    if (!confirm('删除这条对话？')) return
    deleteSession(id)
  }

  return (
    <Drawer open={open} onClose={onClose} side="right" width={CHAT_SESSIONS_DRAWER_WIDTH} title="对话">
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between gap-2 rounded-lg border border-[var(--ds-border)] px-3 py-2 transition-[border-color] duration-[var(--ds-duration-fast)] hover:border-[var(--ds-border-hover)]">
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-[var(--ds-text-primary)]">
              {active?.title || 'OpenClaw'}
            </p>
            <p
              className={cn(
                'mt-0.5 inline-flex items-center gap-1 text-xs',
                wsReady && !activePending && !hasPendingWork && 'text-green-500',
                (activePending || hasPendingWork) && 'text-[var(--color-accent)]',
                !wsReady && 'text-[var(--ds-text-secondary)]',
              )}
            >
              {activePending || hasPendingWork ? (
                <Loader2 className="h-3 w-3 shrink-0 animate-spin" />
              ) : null}
              {connectionLabel}
            </p>
          </div>
          {activePending ? (
            <button
              type="button"
              onClick={cancelStreaming}
              className="inline-flex shrink-0 items-center gap-1 rounded-lg border border-[var(--border)] px-2 py-1 text-xs font-medium text-primary transition-colors hover:bg-[var(--row-hover)]"
            >
              <Square className="h-3 w-3 fill-current" />
              停止
            </button>
          ) : null}
        </div>

        <button
          type="button"
          onClick={() => {
            createSession()
            onClose()
          }}
          disabled={isStreaming}
          className="flex min-h-10 w-full items-center justify-center gap-2 rounded-lg border border-[var(--ds-border)] px-3 py-2 text-sm font-medium transition-[border-color,background-color] duration-[var(--ds-duration-fast)] hover:border-[var(--ds-border-hover)] hover:bg-[var(--ds-row-hover)] disabled:opacity-50"
        >
          <MessageSquarePlus className="h-4 w-4" />
          新对话
        </button>

        <div className="max-h-[calc(100dvh-280px)] overflow-y-auto">
          {state.sessionOrder.map((id) => {
            const s = state.sessions[id]
            if (!s) return null
            const userMsg = s.messages.find((m): m is UserMessage => m.role === 'user' && Boolean(m.text.trim()))
            const preview = userMsg?.text || '空白对话'
            return (
              <div
                key={id}
                className={cn(
                  'group relative mb-0.5 rounded-lg transition-colors',
                  id === state.activeSessionKey ? 'bg-[var(--ds-row-hover-active)]' : 'hover:bg-[var(--ds-row-hover)]',
                )}
              >
                <button
                  type="button"
                  onClick={() => handleSelectSession(id)}
                  className="w-full px-3 py-2.5 pr-10 text-left"
                >
                  <p className="truncate text-sm font-medium text-[var(--ds-text-primary)]">
                    {s.title}
                    {isSessionPending(id) ? (
                      <span className="ml-1.5 text-[10px] font-normal text-[var(--color-accent)]">生成中</span>
                    ) : null}
                  </p>
                  <p className="mt-0.5 truncate text-xs text-[var(--ds-text-secondary)]">{preview}</p>
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(id)}
                  className="absolute right-1 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-md text-[var(--text-secondary)] opacity-0 transition-opacity hover:bg-[var(--row-hover)] hover:text-red-500 group-hover:opacity-100"
                  aria-label="删除对话"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            )
          })}
        </div>

        <button
          type="button"
          onClick={() => {
            if (hasPendingWork) {
              toast.warning('仍有后台生成任务，请等待完成或停止生成')
              return
            }
            if (confirm('清空所有本地对话记录？')) clearAll()
          }}
          className="w-full rounded-lg px-3 py-2 text-left text-xs text-[var(--text-secondary)] transition-colors hover:bg-[var(--row-hover)] hover:text-primary"
        >
          清空所有对话
        </button>
      </div>
    </Drawer>
  )
}
