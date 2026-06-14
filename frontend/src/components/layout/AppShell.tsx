import { Outlet, useLocation, Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { cn } from '../../lib/utils'
import { useAuth } from '../../lib/AuthContext'
import { useChat } from '../../features/chat/ChatProvider'
import { ChatSessionsDrawer } from '../../features/chat/ChatSessionsDrawer'
import { AppNavDrawer } from './AppNavDrawer'
import { AppTopBar } from './AppTopBar'

export function AppShell() {
  const location = useLocation()
  const { user } = useAuth()
  const { pendingSessionKeys } = useChat()
  const isChatHome = location.pathname === '/app'
  const chatBusy = pendingSessionKeys.length > 0
  const [navOpen, setNavOpen] = useState(false)
  const [infoOpen, setInfoOpen] = useState(false)

  useEffect(() => {
    setNavOpen(false)
    setInfoOpen(false)
  }, [location.pathname])

  return (
    <div className="flex h-[100dvh] flex-col overflow-hidden bg-background text-primary">
      <AppTopBar
        onOpenNav={() => setNavOpen(true)}
        onOpenInfo={() => setInfoOpen(true)}
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
    </div>
  )
}
