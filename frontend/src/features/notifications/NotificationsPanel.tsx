import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCheck, Loader2 } from 'lucide-react'
import { api, type NotificationItem } from '../../lib/api'
import { cn, formatCnDateTime } from '../../lib/utils'

const NOTIFICATION_POLL_MS = 12_000

type NotificationsPanelProps = {
  active: boolean
}

const TYPE_LABELS: Record<string, string> = {
  report_ready: '报告',
  token_low: '余额',
  workflow_done: '工作流',
  monitor_error: '监测',
}

function typeBadgeLabel(type: string | null | undefined): string | null {
  if (!type) return null
  return TYPE_LABELS[type] ?? type
}

function NotificationRow({
  item,
  onMarkRead,
  marking,
}: {
  item: NotificationItem
  onMarkRead: (id: string) => void
  marking: boolean
}) {
  const typeLabel = typeBadgeLabel(item.notification_type)

  return (
    <article
      className={cn(
        'border-b border-[var(--ds-border)] px-1 py-3 transition-colors duration-[var(--ds-duration-fast)]',
        !item.read && 'border-l-2 border-l-[var(--color-accent)] bg-[var(--color-accent-soft)]/40 pl-3',
      )}
    >
      <button
        type="button"
        className="w-full text-left"
        onClick={() => {
          if (!item.read) onMarkRead(item.id)
        }}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="flex min-w-0 items-center gap-2">
            {typeLabel ? (
              <span
                className="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-[var(--color-accent)] ring-1 ring-[var(--color-accent)]/30"
              >
                {typeLabel}
              </span>
            ) : null}
            <h3
              className={cn(
                'truncate text-sm text-[var(--ds-text-primary)]',
                !item.read && 'font-semibold',
              )}
            >
              {item.title}
            </h3>
          </div>
          {!item.read ? (
            <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-[var(--color-accent)]" aria-hidden />
          ) : null}
        </div>
        <p className="mt-1 whitespace-pre-wrap text-xs leading-relaxed text-[var(--ds-text-secondary)]">
          {item.content}
        </p>
        <p className="mt-2 text-[10px] text-[var(--ds-text-secondary)]">{formatCnDateTime(item.created_at)}</p>
      </button>
      {!item.read ? (
        <button
          type="button"
          disabled={marking}
          onClick={() => onMarkRead(item.id)}
          className="mt-2 text-xs text-[var(--color-accent)] transition-opacity hover:underline disabled:opacity-50"
        >
          标记已读
        </button>
      ) : null}
    </article>
  )
}

export function NotificationsPanel({ active }: NotificationsPanelProps) {
  const queryClient = useQueryClient()

  const listQuery = useQuery({
    queryKey: ['notifications'],
    queryFn: () => api.listNotifications(),
    enabled: active,
    refetchInterval: active ? NOTIFICATION_POLL_MS : false,
    refetchIntervalInBackground: false,
  })

  const markReadMutation = useMutation({
    mutationFn: (id: string) => api.markNotificationRead(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  const markAllMutation = useMutation({
    mutationFn: () => api.markAllNotificationsRead(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  const notifications = listQuery.data?.notifications ?? []
  const unreadCount = listQuery.data?.unread_count ?? 0
  const marking = markReadMutation.isPending || markAllMutation.isPending

  if (listQuery.isLoading) {
    return (
      <div className="flex items-center justify-center py-12 text-sm text-[var(--ds-text-secondary)]">
        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        加载中…
      </div>
    )
  }

  if (listQuery.isError) {
    return (
      <p className="py-8 text-center text-sm text-red-500">{(listQuery.error as Error).message}</p>
    )
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="mb-3 flex items-center justify-between gap-2">
        <p className="text-xs text-[var(--ds-text-secondary)]">
          {unreadCount > 0 ? `${unreadCount} 条未读` : '全部已读'}
          {active ? <span className="ml-1 opacity-60">· 自动刷新</span> : null}
        </p>
        {unreadCount > 0 ? (
          <button
            type="button"
            disabled={marking}
            onClick={() => markAllMutation.mutate()}
            className="inline-flex items-center gap-1 text-xs text-[var(--color-accent)] hover:underline disabled:opacity-50"
          >
            <CheckCheck className="h-3.5 w-3.5" />
            全部已读
          </button>
        ) : null}
      </div>

      {notifications.length === 0 ? (
        <p className="py-12 text-center text-sm text-[var(--ds-text-secondary)]">暂无通知</p>
      ) : (
        <div className="-mx-1 min-h-0 flex-1 overflow-y-auto">
          {notifications.map((item) => (
            <NotificationRow
              key={item.id}
              item={item}
              marking={marking}
              onMarkRead={(id) => markReadMutation.mutate(id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export function useNotificationUnreadCount(enabled: boolean) {
  return useQuery({
    queryKey: ['notifications'],
    queryFn: () => api.listNotifications(),
    enabled,
    staleTime: 5_000,
    refetchInterval: enabled ? NOTIFICATION_POLL_MS : false,
    refetchIntervalInBackground: false,
  })
}
