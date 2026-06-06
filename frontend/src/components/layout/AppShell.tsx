import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Loader2, LogOut, Menu, Moon, Sun, FileText, User, Settings, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { cn } from '../../lib/utils'
import { useAuth } from '../../lib/AuthContext'
import { useChat } from '../../features/chat/ChatProvider'

const nav = [
  { to: '/', label: '首页' },
  { to: '/reports', label: '专题分析' },
  { to: '/news', label: '新闻动态' },
  { to: '/price-trend', label: '价格趋势' },
  { to: '/keyword-tracking', label: '关键词追踪' },
  { to: '/workflow', label: '工作流' },
]

function NavLinkItem({
  item,
  chatBusy,
  onNavigate,
  vertical,
}: {
  item: (typeof nav)[number]
  chatBusy: boolean
  onNavigate?: () => void
  vertical?: boolean
}) {
  return (
    <NavLink
      to={item.to}
      end={item.to === '/'}
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(
          vertical
            ? 'flex items-center gap-2 rounded-lg px-3 py-3 text-sm transition-colors'
            : 'inline-flex items-center gap-1.5 border-b-2 py-3 transition-colors',
          vertical
            ? isActive
              ? 'bg-[var(--color-accent-soft)] font-medium text-[var(--color-accent)]'
              : 'text-[var(--color-muted)] hover:bg-[var(--color-bg)] hover:text-[var(--color-text)]'
            : isActive
              ? 'border-[var(--color-accent)] font-medium text-[var(--color-accent)]'
              : 'border-transparent text-[var(--color-muted)] hover:text-[var(--color-text)]',
        )
      }
    >
      {item.label}
      {item.to === '/' && chatBusy ? (
        <span className="inline-flex items-center gap-1 rounded-full bg-[var(--color-accent)]/10 px-1.5 py-0.5 text-[10px] font-medium text-[var(--color-accent)]">
          <Loader2 className="h-3 w-3 animate-spin" />
          生成中
        </span>
      ) : null}
    </NavLink>
  )
}

export function AppShell() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const { pendingSessionKeys } = useChat()
  const isChatHome = location.pathname === '/'
  const chatBusy = pendingSessionKeys.length > 0
  const [dark, setDark] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [navDrawerOpen, setNavDrawerOpen] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem('oc_dark') === '1'
    setDark(saved)
    document.documentElement.classList.toggle('dark', saved)
  }, [])

  useEffect(() => {
    setNavDrawerOpen(false)
    setUserMenuOpen(false)
  }, [location.pathname])

  useEffect(() => {
    if (!navDrawerOpen) return
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = prev
    }
  }, [navDrawerOpen])

  const toggleDark = () => {
    const next = !dark
    setDark(next)
    document.documentElement.classList.toggle('dark', next)
    localStorage.setItem('oc_dark', next ? '1' : '0')
  }

  const shellPadding = 'w-full px-4 sm:px-6'

  return (
    <div className={cn('flex min-h-screen flex-col bg-[var(--color-bg)]', isChatHome && 'h-[100dvh] overflow-hidden')}>
      <header className="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-md pt-[env(safe-area-inset-top)]">
        <div className={cn('flex h-14 items-center justify-between gap-2', shellPadding)}>
          <div className="flex min-w-0 items-center gap-2">
            <button
              type="button"
              onClick={() => setNavDrawerOpen(true)}
              className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-md text-[var(--color-muted)] hover:bg-[var(--color-bg)] hover:text-[var(--color-text)] md:hidden"
              aria-label="打开导航菜单"
            >
              <Menu className="h-5 w-5" />
            </button>
            <Link to="/" className="flex min-w-0 items-center gap-2 text-sm font-semibold tracking-tight">
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-[var(--color-accent)] text-white">
                <FileText className="h-4 w-4" />
              </span>
              <span className="truncate md:hidden">OpenClaw</span>
              <span className="hidden truncate md:inline">OpenClaw 分析平台</span>
            </Link>
          </div>
          <div className="flex shrink-0 items-center gap-1.5 sm:gap-2">
            {user && (
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setUserMenuOpen((v) => !v)}
                  className="flex items-center gap-1.5 rounded-md border border-[var(--color-border)] px-2 py-1.5 text-sm text-[var(--color-muted)] hover:text-[var(--color-text)] sm:px-2.5"
                >
                  <User className="h-4 w-4 shrink-0" />
                  <span className="hidden max-w-[8rem] truncate sm:inline">{user.username}</span>
                </button>
                {userMenuOpen ? (
                  <>
                    <button
                      type="button"
                      className="fixed inset-0 z-40"
                      aria-label="关闭用户菜单"
                      onClick={() => setUserMenuOpen(false)}
                    />
                    <div className="absolute right-0 top-full z-50 mt-1 min-w-[10rem] rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] py-1 shadow-lg">
                      <div className="border-b border-[var(--color-border)] px-3 py-2 text-xs text-[var(--color-muted)]">
                        {user.email}
                      </div>
                      <button
                        type="button"
                        className="flex w-full items-center gap-2 px-3 py-2.5 text-sm hover:bg-[var(--color-bg)]"
                        onClick={() => {
                          setUserMenuOpen(false)
                          navigate('/account')
                        }}
                      >
                        <Settings className="h-4 w-4" />
                        个人中心
                      </button>
                      <button
                        type="button"
                        className="flex w-full items-center gap-2 px-3 py-2.5 text-sm hover:bg-[var(--color-bg)]"
                        onClick={async () => {
                          setUserMenuOpen(false)
                          await logout()
                          navigate('/login')
                        }}
                      >
                        <LogOut className="h-4 w-4" />
                        退出登录
                      </button>
                    </div>
                  </>
                ) : null}
              </div>
            )}
            <button
              onClick={toggleDark}
              className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-[var(--color-border)] text-[var(--color-muted)] hover:text-[var(--color-text)]"
              aria-label="切换主题"
            >
              {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
            <a
              href="/docs"
              target="_blank"
              rel="noreferrer"
              className="hidden rounded-md border border-[var(--color-border)] px-3 py-1.5 text-sm text-[var(--color-muted)] hover:text-[var(--color-text)] lg:inline-block"
            >
              API 文档
            </a>
          </div>
        </div>
        <nav className={cn('hidden border-t border-[var(--color-border)] md:block', shellPadding)}>
          <ul className="flex gap-6 text-sm">
            {nav.map((item) => (
              <li key={item.to}>
                <NavLinkItem item={item} chatBusy={chatBusy} />
              </li>
            ))}
          </ul>
        </nav>
      </header>

      {navDrawerOpen ? (
        <div className="fixed inset-0 z-50 md:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            aria-label="关闭导航菜单"
            onClick={() => setNavDrawerOpen(false)}
          />
          <div className="absolute inset-y-0 left-0 flex w-[min(18rem,85vw)] flex-col bg-[var(--color-surface)] shadow-xl pt-[env(safe-area-inset-top)]">
            <div className="flex h-14 items-center justify-between border-b border-[var(--color-border)] px-4">
              <span className="text-sm font-semibold">导航</span>
              <button
                type="button"
                onClick={() => setNavDrawerOpen(false)}
                className="inline-flex h-10 w-10 items-center justify-center rounded-md text-[var(--color-muted)] hover:bg-[var(--color-bg)]"
                aria-label="关闭导航菜单"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <nav className="flex-1 overflow-y-auto p-3">
              <div className="flex flex-col gap-1">
                {nav.map((item) => (
                  <NavLinkItem
                    key={item.to}
                    item={item}
                    chatBusy={chatBusy}
                    vertical
                    onNavigate={() => setNavDrawerOpen(false)}
                  />
                ))}
              </div>
            </nav>
            <div className="border-t border-[var(--color-border)] p-3 pb-[calc(0.75rem+env(safe-area-inset-bottom))]">
              <a
                href="/docs"
                target="_blank"
                rel="noreferrer"
                className="block rounded-lg px-3 py-3 text-sm text-[var(--color-muted)] hover:bg-[var(--color-bg)]"
              >
                API 文档
              </a>
            </div>
          </div>
        </div>
      ) : null}

      <main
        className={cn(
          'flex min-h-0 flex-1 flex-col',
          isChatHome ? 'overflow-hidden' : cn(shellPadding, 'py-4 md:py-6'),
        )}
      >
        <Outlet />
      </main>
    </div>
  )
}
