import { Navigate } from 'react-router-dom'
import { useAuth } from '../lib/AuthContext'
import { LandingPage } from './LandingPage'

export function LandingOrRedirect() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-[var(--color-muted)]">
        加载中…
      </div>
    )
  }

  if (user) return <Navigate to="/app" replace />

  return <LandingPage />
}
