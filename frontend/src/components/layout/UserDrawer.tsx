import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Coins, CreditCard, LogOut, Moon, Sun } from 'lucide-react'
import { Drawer } from '../ui/ds'
import { useAuth } from '../../lib/AuthContext'
import { useTheme } from '../../lib/ThemeProvider'
import { cn } from '../../lib/utils'
import {
  NotificationsPanel,
  useNotificationUnreadCount,
} from '../../features/notifications/NotificationsPanel'

export const USER_DRAWER_WIDTH = 300

type DrawerTab = 'account' | 'notifications'

type UserDrawerProps = {
  open: boolean
  onClose: () => void
}

function DrawerActionRow({
  icon: Icon,
  label,
  onClick,
  destructive,
}: {
  icon: typeof LogOut
  label: string
  onClick?: () => void
  destructive?: boolean
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'flex w-full items-center gap-2.5 px-4 py-3 text-left text-sm transition-colors duration-[var(--ds-duration-fast)]',
        'text-[var(--ds-text-primary)] hover:bg-[var(--ds-row-hover)]',
        destructive && 'text-red-500 hover:text-red-400',
      )}
    >
      <Icon className="h-4 w-4 shrink-0" />
      <span>{label}</span>
    </button>
  )
}

function ThemeSettingRow() {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left text-sm text-[var(--ds-text-primary)] transition-colors duration-[var(--ds-duration-fast)] hover:bg-[var(--ds-row-hover)]"
    >
      <span className="flex items-center gap-2.5">
        {isDark ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        主题
      </span>
      <span className="text-xs text-[var(--ds-text-secondary)]">{isDark ? '深色' : '浅色'}</span>
    </button>
  )
}

function DrawerTabs({
  tab,
  onChange,
  unreadCount,
}: {
  tab: DrawerTab
  onChange: (tab: DrawerTab) => void
  unreadCount: number
}) {
  return (
    <div className="flex gap-1 border-b border-[var(--ds-border)]">
      {(
        [
          ['account', '账户'],
          ['notifications', '通知'],
        ] as const
      ).map(([id, label]) => (
        <button
          key={id}
          type="button"
          onClick={() => onChange(id)}
          className={cn(
            'relative flex-1 px-3 py-2.5 text-sm font-medium transition-colors duration-[var(--ds-duration-fast)]',
            tab === id
              ? 'text-[var(--ds-text-primary)] after:absolute after:inset-x-3 after:bottom-0 after:h-0.5 after:rounded-full after:bg-[var(--color-accent)]'
              : 'text-[var(--ds-text-secondary)] hover:text-[var(--ds-text-primary)]',
          )}
        >
          <span className="inline-flex items-center justify-center gap-1.5">
            {label}
            {id === 'notifications' && unreadCount > 0 ? (
              <span className="inline-flex min-w-[1.125rem] items-center justify-center rounded-full bg-[var(--color-accent)] px-1 text-[10px] font-semibold text-[var(--accent-fg)]">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            ) : null}
          </span>
        </button>
      ))}
    </div>
  )
}

export function UserDrawer({ open, onClose }: UserDrawerProps) {
  const navigate = useNavigate()
  const { user, logout, refreshUser } = useAuth()
  const [tab, setTab] = useState<DrawerTab>('account')
  const notificationsQuery = useNotificationUnreadCount(open)

  useEffect(() => {
    if (open) void refreshUser()
  }, [open, refreshUser])

  useEffect(() => {
    if (!open) setTab('account')
  }, [open])

  if (!user) return null

  const initials = user.username.slice(0, 1).toUpperCase()
  const balanceLabel =
    typeof user.token_balance === 'number' ? user.token_balance.toLocaleString() : '—'
  const unreadCount = notificationsQuery.data?.unread_count ?? 0

  const handleLogout = async () => {
    onClose()
    await logout()
    navigate('/login')
  }

  return (
    <Drawer
      open={open}
      onClose={onClose}
      side="right"
      width={USER_DRAWER_WIDTH}
      title={tab === 'account' ? '账户' : '通知'}
      className={tab === 'notifications' ? '[&>div:last-child]:flex [&>div:last-child]:min-h-0 [&>div:last-child]:flex-col' : undefined}
    >
      <div className={cn('flex flex-col', tab === 'notifications' ? 'min-h-0 flex-1 gap-4' : 'gap-6')}>
        <DrawerTabs tab={tab} onChange={setTab} unreadCount={unreadCount} />

        {tab === 'account' ? (
          <>
            <div className="flex items-center gap-3">
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-[var(--border)] bg-[var(--bg-panel)] text-sm font-medium text-primary">
                {initials}
              </span>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-[var(--ds-text-primary)]">{user.username}</p>
                <p className="truncate text-xs text-[var(--ds-text-secondary)]">{user.email}</p>
                {user.is_demo ? (
                  <p className="mt-0.5 text-[10px] font-medium text-amber-500">演示账号</p>
                ) : null}
              </div>
            </div>

            <section className="flex flex-col gap-2">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-xs font-medium uppercase tracking-wide text-[var(--ds-text-secondary)]">Token</h3>
                <button
                  type="button"
                  onClick={() => {
                    onClose()
                    navigate('/app/usage')
                  }}
                  className="text-xs text-[var(--color-accent)] transition-colors hover:underline"
                >
                  使用详情
                </button>
              </div>
              <div className="rounded-lg border border-[var(--ds-border)] bg-[var(--ds-bg-panel)] px-4 py-3">
                <div className="flex items-center gap-2 text-[var(--ds-text-secondary)]">
                  <Coins className="h-4 w-4 shrink-0" />
                  <span className="text-xs">当前余额</span>
                </div>
                <p className="mt-1 text-2xl font-semibold tabular-nums text-[var(--ds-text-primary)]">
                  {balanceLabel}
                </p>
                <button
                  type="button"
                  onClick={() => {
                    onClose()
                    navigate('/app/billing')
                  }}
                  className="mt-3 w-full rounded-lg border border-[var(--ds-border)] bg-background px-3 py-2 text-sm font-medium text-[var(--ds-text-primary)] transition-colors duration-[var(--ds-duration-fast)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)]"
                >
                  充值
                </button>
              </div>
            </section>

            <section className="flex flex-col gap-2">
              <h3 className="text-xs font-medium uppercase tracking-wide text-[var(--ds-text-secondary)]">设置</h3>
              <div className="overflow-hidden rounded-lg border border-[var(--ds-border)] bg-[var(--ds-bg-panel)] divide-y divide-[var(--ds-border)]">
                <ThemeSettingRow />
                <DrawerActionRow icon={LogOut} label="退出登录" onClick={handleLogout} destructive />
              </div>
            </section>

            <section className="flex flex-col gap-2">
              <h3 className="text-xs font-medium uppercase tracking-wide text-[var(--ds-text-secondary)]">更多</h3>
              <div className="overflow-hidden rounded-lg border border-[var(--ds-border)] bg-[var(--ds-bg-panel)] divide-y divide-[var(--ds-border)]">
                <DrawerActionRow
                  icon={CreditCard}
                  label="账单"
                  onClick={() => {
                    onClose()
                    navigate('/app/billing')
                  }}
                />
              </div>
            </section>
          </>
        ) : (
          <NotificationsPanel active={open && tab === 'notifications'} />
        )}
      </div>
    </Drawer>
  )
}
