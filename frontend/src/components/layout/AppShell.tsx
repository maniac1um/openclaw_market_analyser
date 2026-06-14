import { NavLink, Outlet, useLocation, Link } from 'react-router-dom'
import { Loader2, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { cn } from '../../lib/utils'
import { useAuth } from '../../lib/AuthContext'
import { useChat } from '../../features/chat/ChatProvider'
import { AppSidebar, sidebarNav } from './AppSidebar'
import { AppTopBar } from './AppTopBar'

function MobileNavDrawer({
  open,
  onClose,
  chatBusy,
}: {
  open: boolean
  onClose: () => void
  chatBusy: boolean
}) {
  useEffect(() => {
    if (!open) return
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = prev
    }
  }, [open])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 md:hidden">
      <button
        type="button"
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        aria-label="关闭导航菜单"
        onClick={onClose}
      />
      <div className="absolute inset-y-0 left-0 flex w-[220px] flex-col bg-[var(--ds-bg-base)] pt-[env(safe-area-inset-top)]">
        <div className="flex h-12 items-center justify-end border-b border-[var(--ds-border)] px-3">
          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-[var(--ds-text-secondary)] hover:bg-white/5"
            aria-label="关闭导航菜单"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <nav className="flex flex-1 flex-col gap-0.5 overflow-y-auto p-3" aria-label="主导航">
          {sidebarNav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={'end' in item ? item.end : false}
              onClick={onClose}
              className={({ isActive }) =>
                cn(
                  'relative flex items-center rounded-lg px-3 py-2.5 text-sm transition-colors',
                  isActive
                    ? 'font-medium text-[var(--ds-text-primary)]'
                    : 'text-[var(--ds-text-secondary)] hover:bg-white/5 hover:text-[var(--ds-text-primary)]',
                )
              }
            >
              {({ isActive }) => (
                <>
                  {isActive ? (
                    <span
                      className="absolute top-1/2 left-0 h-5 w-0.5 -translate-y-1/2 rounded-full bg-[var(--color-accent)]"
                      aria-hidden
                    />
                  ) : null}
                  <span className="pl-1">{item.label}</span>
                  {item.to === '/app' && chatBusy ? (
                    <Loader2 className="ml-auto h-3 w-3 animate-spin text-[var(--color-accent)]" />
                  ) : null}
                </>
              )}
            </NavLink>
          ))}
        </nav>
      </div>
    </div>
  )
}

export function AppShell() {
  const location = useLocation()
  const { user } = useAuth()
  const { pendingSessionKeys } = useChat()
  const isChatHome = location.pathname === '/app'
  const chatBusy = pendingSessionKeys.length > 0
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  useEffect(() => {
    document.documentElement.classList.add('dark')
    const saved = localStorage.getItem('oc_dark')
    if (saved === null) localStorage.setItem('oc_dark', '1')
  }, [])

  useEffect(() => {
    setMobileNavOpen(false)
  }, [location.pathname])

  return (
    <div className="flex h-[100dvh] overflow-hidden bg-[var(--ds-bg-base)] text-[var(--ds-text-primary)]">
      <AppSidebar chatBusy={chatBusy} className="hidden md:flex" />

      <div className="flex min-w-0 flex-1 flex-col">
        <AppTopBar onOpenMobileNav={() => setMobileNavOpen(true)} />

        {user?.is_demo ? (
          <div className="shrink-0 border-b border-amber-900/50 bg-amber-950/40 px-4 py-2 text-center text-xs text-amber-200 md:px-8">
            演示账号 · 只读环境 ·{' '}
            <Link to="/register" className="font-medium underline">
              注册正式账号
            </Link>
          </div>
        ) : null}

        <main
          className={cn(
            'flex min-h-0 flex-1 flex-col overflow-auto',
            isChatHome ? 'overflow-hidden' : 'p-8',
          )}
        >
          <Outlet />
        </main>
      </div>

      <MobileNavDrawer open={mobileNavOpen} onClose={() => setMobileNavOpen(false)} chatBusy={chatBusy} />
    </div>
  )
}
