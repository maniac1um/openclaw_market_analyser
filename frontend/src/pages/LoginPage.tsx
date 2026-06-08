import { type FormEvent, useEffect, useRef, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { useAuth } from '../lib/AuthContext'
import { DEMO_EMAIL, DEMO_PASSWORD } from '../lib/demoConstants'
import { AuthMarketingPanel } from '../components/auth/AuthMarketingPanel'

function appHomeFrom(from: unknown): string {
  if (typeof from === 'string' && from.startsWith('/app')) return from
  return '/app'
}

export function LoginPage() {
  const { login, user, loading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const demoAuto = searchParams.get('demo') === '1'
  const demoAttempted = useRef(false)

  const [email, setEmail] = useState(demoAuto ? DEMO_EMAIL : '')
  const [password, setPassword] = useState(demoAuto ? DEMO_PASSWORD : '')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const from = (location.state as { from?: string } | null)?.from

  if (!loading && user) {
    return <Navigate to={appHomeFrom(from)} replace />
  }

  async function doLogin(loginEmail: string, loginPassword: string) {
    setError(null)
    setSubmitting(true)
    try {
      await login(loginEmail, loginPassword)
      navigate(appHomeFrom(from), { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : '登录失败')
    } finally {
      setSubmitting(false)
    }
  }

  useEffect(() => {
    if (!demoAuto || demoAttempted.current || loading || user) return
    demoAttempted.current = true
    void doLogin(DEMO_EMAIL, DEMO_PASSWORD)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [demoAuto, loading, user])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    await doLogin(email, password)
  }

  return (
    <div className="flex min-h-screen flex-col bg-[var(--color-bg)] lg:flex-row">
      <AuthMarketingPanel />
      <div className="flex flex-1 flex-col px-4">
        <div className="mx-auto w-full max-w-md pt-8 lg:pt-10">
          <Link
            to="/"
            className="inline-flex items-center gap-1 text-sm text-[var(--color-muted)] hover:text-[var(--color-text)]"
          >
            <ArrowLeft className="h-4 w-4" />
            返回首页
          </Link>
        </div>
        <div className="flex flex-1 items-center justify-center pb-12">
          <Card className="w-full max-w-md p-6">
          <h1 className="mb-1 text-lg font-semibold">登录</h1>
          <p className="mb-6 text-sm text-[var(--color-muted)]">OpenClaw 分析平台</p>
          <form onSubmit={onSubmit} className="space-y-4">
            <label className="block text-sm">
              <span className="mb-1 block text-[var(--color-muted)]">邮箱</span>
              <input
                type="text"
                inputMode="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2"
              />
            </label>
            <label className="block text-sm">
              <span className="mb-1 block text-[var(--color-muted)]">密码</span>
              <input
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2"
              />
            </label>
            {error && <p className="text-sm text-red-500">{error}</p>}
            <Button type="submit" variant="primary" className="w-full" disabled={submitting}>
              {submitting ? '登录中…' : '登录'}
            </Button>
          </form>
          <div className="mt-4 space-y-3 text-center text-sm text-[var(--color-muted)]">
            <p>
              还没有账号？{' '}
              <Link to="/register" className="text-[var(--color-accent)] hover:underline">
                注册
              </Link>
            </p>
            <p>
              想先看看效果？{' '}
              <Link to="/login?demo=1" className="text-[var(--color-accent)] hover:underline">
                试用登录
              </Link>
              <span className="mt-1 block text-xs">演示环境，请勿输入真实商业机密</span>
            </p>
          </div>
        </Card>
        </div>
      </div>
    </div>
  )
}
