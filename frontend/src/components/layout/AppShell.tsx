import { Outlet, useLocation, Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { cn } from '../../lib/utils'
import { useAuth } from '../../lib/AuthContext'
import { useChat } from '../../features/chat/ChatProvider'
import { ChatSessionsDrawer, CHAT_SESSIONS_DRAWER_WIDTH } from '../../features/chat/ChatSessionsDrawer'
import { AppNavDrawer, APP_NAV_DRAWER_WIDTH } from './AppNavDrawer'
import { AppTopBar } from './AppTopBar'
import { UserDrawer, USER_DRAWER_WIDTH } from './UserDrawer'

export function AppShell() {
  const location = useLocation()
  const { user } = useAuth()
  const { pendingSessionKeys } = useChat()
  const isChatHome = location.pathname === '/app'
  const chatBusy = pendingSessionKeys.length > 0
  const [navOpen, setNavOpen] = useState(false)
  const [infoOpen, setInfoOpen] = useState(false)
  const [userOpen, setUserOpen] = useState(false)

  useEffect(() => {
    setNavOpen(false)
    setInfoOpen(false)
    setUserOpen(false)
  }, [location.pathname])

  const marginLeft = navOpen ? APP_NAV_DRAWER_WIDTH : 0
  const marginRight =
    isChatHome && infoOpen ? CHAT_SESSIONS_DRAWER_WIDTH : userOpen ? USER_DRAWER_WIDTH : 0

  return (
    <div
      className="flex h-[100dvh] flex-col overflow-hidden bg-background text-primary transition-[margin] duration-[var(--ds-duration-drawer)] ease-[var(--ds-ease-out)]"
      style={{ marginLeft, marginRight }}
    >
      <AppTopBar
        onOpenNav={() => setNavOpen(true)}
        onOpenInfo={() => {
          setUserOpen(false)
          setInfoOpen(true)
        }}
        onOpenUser={() => {
          setInfoOpen(false)
          setUserOpen(true)
        }}
        showInfoButton={isChatHome}
      />

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

      <AppNavDrawer open={navOpen} onClose={() => setNavOpen(false)} chatBusy={chatBusy} />
      {isChatHome ? (
        <ChatSessionsDrawer open={infoOpen} onClose={() => setInfoOpen(false)} />
      ) : null}
      <UserDrawer open={userOpen} onClose={() => setUserOpen(false)} />
    </div>
  )
}
