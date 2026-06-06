import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { LogOut, Moon, Sun, FileText, User, Settings } from 'lucide-react'
import { useEffect, useState } from 'react'
import { cn } from '../../lib/utils'
import { useAuth } from '../../lib/AuthContext'

const nav = [
  { to: '/', label: '首页' },
  { to: '/reports', label: '专题分析' },
  { to: '/news', label: '新闻动态' },
  { to: '/price-trend', label: '价格趋势' },
  { to: '/keyword-tracking', label: '关键词追踪' },
  { to: '/workflow', label: '工作流' },
]

export function AppShell() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const isChatHome = location.pathname === '/'
  const [dark, setDark] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem('oc_dark') === '1'
    setDark(saved)
    document.documentElement.classList.toggle('dark', saved)
  }, [])

  const toggleDark = () => {
    const next = !dark
    setDark(next)
    document.documentElement.classList.toggle('dark', next)
    localStorage.setItem('oc_dark', next ? '1' : '0')
  }

  const shellPadding = 'w-full px-4 sm:px-6'

  return (
    <div className={cn('flex min-h-screen flex-col bg-[var(--color-bg)]', isChatHome && 'h-screen overflow-hidden')}>
      <header className="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-md">
        <div className={cn('flex h-14 items-center justify-between', shellPadding)}>
          <Link to="/" className="flex items-center gap-2 text-sm font-semibold tracking-tight">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-[var(--color-accent)] text-white">
              <FileText className="h-4 w-4" />
            </span>
            OpenClaw 分析平台
          </Link>
          <div className="flex items-center gap-2">
            {user && (
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setMenuOpen((v) => !v)}
                  className="flex items-center gap-1.5 rounded-md border border-[var(--color-border)] px-2.5 py-1.5 text-sm text-[var(--color-muted)] hover:text-[var(--color-text)]"
                >
                  <User className="h-4 w-4" />
                  <span className="max-w-[8rem] truncate">{user.username}</span>
                </button>
                {menuOpen && (
                  <div className="absolute right-0 top-full z-50 mt-1 min-w-[10rem] rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] py-1 shadow-lg">
                    <div className="border-b border-[var(--color-border)] px-3 py-2 text-xs text-[var(--color-muted)]">
                      {user.email}
                    </div>
                    <button
                      type="button"
                      className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-[var(--color-bg)]"
                      onClick={() => {
                        setMenuOpen(false)
                        navigate('/account')
                      }}
                    >
                      <Settings className="h-4 w-4" />
                      个人中心
                    </button>
                    <button
                      type="button"
                      className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-[var(--color-bg)]"
                      onClick={async () => {
                        setMenuOpen(false)
                        await logout()
                        navigate('/login')
                      }}
                    >
                      <LogOut className="h-4 w-4" />
                      退出登录
                    </button>
                  </div>
                )}
              </div>
            )}
            <button
              onClick={toggleDark}
              className="rounded-md border border-[var(--color-border)] p-2 text-[var(--color-muted)] hover:text-[var(--color-text)]"
              aria-label="切换主题"
            >
              {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
            <a
              href="/docs"
              target="_blank"
              rel="noreferrer"
              className="hidden rounded-md border border-[var(--color-border)] px-3 py-1.5 text-sm text-[var(--color-muted)] hover:text-[var(--color-text)] sm:inline-block"
            >
              API 文档
            </a>
          </div>
        </div>
        <nav className={cn('overflow-x-auto', shellPadding)}>
          <ul className="flex gap-6 text-sm">
            {nav.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    cn(
                      'inline-block border-b-2 py-3 transition-colors',
                      isActive
                        ? 'border-[var(--color-accent)] font-medium text-[var(--color-accent)]'
                        : 'border-transparent text-[var(--color-muted)] hover:text-[var(--color-text)]',
                    )
                  }
                >
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </header>
      <main
        className={cn(
          'flex min-h-0 flex-1 flex-col',
          isChatHome ? 'overflow-hidden' : cn(shellPadding, 'py-6'),
        )}
      >
        <Outlet />
      </main>
    </div>
  )
}
