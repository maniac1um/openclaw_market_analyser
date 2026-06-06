import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { setAuthHeaderProvider } from './api'

export type AuthUser = {
  id: string
  email: string
  username: string
  role: string
}

type AuthContextValue = {
  user: AuthUser | null
  accessToken: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshSession: () => Promise<boolean>
  getAuthHeaders: () => Record<string, string>
}

const AuthContext = createContext<AuthContextValue | null>(null)

async function parseAuthResponse(res: Response): Promise<{ user: AuthUser; access_token: string }> {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch {
      /* ignore */
    }
    throw new Error(String(detail))
  }
  return res.json()
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const applyAuth = useCallback((payload: { user: AuthUser; access_token: string }) => {
    setUser(payload.user)
    setAccessToken(payload.access_token)
  }, [])

  const refreshSession = useCallback(async (): Promise<boolean> => {
    const res = await fetch('/api/v1/public/auth/refresh', {
      method: 'POST',
      credentials: 'include',
    })
    if (!res.ok) {
      setUser(null)
      setAccessToken(null)
      return false
    }
    const body = await parseAuthResponse(res)
    applyAuth(body)
    return true
  }, [applyAuth])

  const getAuthHeaders = useCallback((): Record<string, string> => {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (accessToken) headers.Authorization = `Bearer ${accessToken}`
    return headers
  }, [accessToken])

  useEffect(() => {
    setAuthHeaderProvider(getAuthHeaders)
  }, [getAuthHeaders])

  useEffect(() => {
    void (async () => {
      try {
        const meRes = await fetch('/api/v1/public/auth/me', {
          credentials: 'include',
        })
        if (meRes.ok) {
          const me = (await meRes.json()) as AuthUser
          setUser(me)
          setLoading(false)
          return
        }
        await refreshSession()
      } catch {
        setUser(null)
        setAccessToken(null)
      } finally {
        setLoading(false)
      }
    })()
  }, [refreshSession])

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await fetch('/api/v1/public/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email, password }),
      })
      applyAuth(await parseAuthResponse(res))
    },
    [applyAuth],
  )

  const register = useCallback(
    async (email: string, username: string, password: string) => {
      const res = await fetch('/api/v1/public/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email, username, password }),
      })
      applyAuth(await parseAuthResponse(res))
    },
    [applyAuth],
  )

  const logout = useCallback(async () => {
    await fetch('/api/v1/public/auth/logout', { method: 'DELETE', credentials: 'include' })
    setUser(null)
    setAccessToken(null)
  }, [])

  const value = useMemo(
    () => ({ user, accessToken, loading, login, register, logout, refreshSession, getAuthHeaders }),
    [user, accessToken, loading, login, register, logout, refreshSession, getAuthHeaders],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
