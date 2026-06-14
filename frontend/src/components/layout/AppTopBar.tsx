import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogOut, Menu, Search, Settings, Sparkles, User } from 'lucide-react'
import { useAuth } from '../../lib/AuthContext'
import { useOnboarding } from '../../features/onboarding/OnboardingProvider'
import { CommandBar, CommandBarInput } from '../ui/ds'

type AppTopBarProps = {
  onOpenNav?: () => void
}

export function AppTopBar({ onOpenNav }: AppTopBarProps) {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const { openGuide } = useOnboarding()
  const [query, setQuery] = useState('')
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!menuOpen) return
    const onPointerDown = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', onPointerDown)
    return () => document.removeEventListener('mousedown', onPointerDown)
  }, [menuOpen])

  const handleSearch = (e: FormEvent) => {
    e.preventDefault()
    const term = query.trim()
    if (!term) return
    navigate(`/app/news?q=${encodeURIComponent(term)}`)
  }

  const initials = user?.username?.slice(0, 1).toUpperCase() || '?'

  return (
    <header className="flex h-12 shrink-0 items-center gap-3 border-b border-[var(--ds-border)] px-4 md:px-8">
      <button
        type="button"
        onClick={onOpenNav}
        className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[var(--ds-text-secondary)] transition-colors hover:bg-white/5 hover:text-[var(--ds-text-primary)]"
        aria-label="打开导航菜单"
      >
        <Menu className="h-5 w-5" />
      </button>

      <form onSubmit={handleSearch} className="min-w-0 flex-1">
        <CommandBar className="border-0 bg-transparent p-0 backdrop-blur-none">
          <Search className="h-4 w-4 shrink-0 text-[var(--ds-text-secondary)]" aria-hidden />
          <CommandBarInput
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="搜索新闻、专题…"
            aria-label="全局搜索"
            className="min-w-0 border-0 px-0 focus:border-0"
          />
        </CommandBar>
      </form>

      {user ? (
        <div ref={menuRef} className="relative shrink-0">
          <button
            type="button"
            onClick={() => setMenuOpen((v) => !v)}
            className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--ds-border)] bg-[var(--ds-bg-panel)] text-xs font-medium text-[var(--ds-text-primary)] transition-colors hover:bg-white/5"
            aria-label="用户菜单"
            aria-expanded={menuOpen}
          >
            {initials}
          </button>

          {menuOpen ? (
            <div className="absolute top-full right-0 z-50 mt-2 min-w-[11rem] rounded-xl border border-[var(--ds-border)] bg-[var(--ds-bg-base)] py-1">
              <div className="border-b border-[var(--ds-border)] px-3 py-2">
                <p className="truncate text-sm font-medium text-[var(--ds-text-primary)]">{user.username}</p>
                <p className="truncate text-xs text-[var(--ds-text-secondary)]">{user.email}</p>
              </div>
              {!user.is_demo ? (
                <button
                  type="button"
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm text-[var(--ds-text-secondary)] transition-colors hover:bg-white/5 hover:text-[var(--ds-text-primary)]"
                  onClick={() => {
                    setMenuOpen(false)
                    openGuide()
                  }}
                >
                  <Sparkles className="h-4 w-4" />
                  新手引导
                </button>
              ) : null}
              <button
                type="button"
                className="flex w-full items-center gap-2 px-3 py-2 text-sm text-[var(--ds-text-secondary)] transition-colors hover:bg-white/5 hover:text-[var(--ds-text-primary)]"
                onClick={() => {
                  setMenuOpen(false)
                  navigate('/app/account')
                }}
              >
                <Settings className="h-4 w-4" />
                账户
              </button>
              <button
                type="button"
                className="flex w-full items-center gap-2 px-3 py-2 text-sm text-[var(--ds-text-secondary)] transition-colors hover:bg-white/5 hover:text-[var(--ds-text-primary)]"
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
          ) : null}
        </div>
      ) : (
        <span className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--ds-border)] text-[var(--ds-text-secondary)]">
          <User className="h-4 w-4" />
        </span>
      )}
    </header>
  )
}
