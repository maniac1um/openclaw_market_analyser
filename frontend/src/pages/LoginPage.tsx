import { type FormEvent, useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { useAuth } from '../lib/AuthContext'

export function LoginPage() {
  const { login, user, loading } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (!loading && user) return <Navigate to="/" replace />

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : '登录失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-bg)] px-4">
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
        <p className="mt-4 text-center text-sm text-[var(--color-muted)]">
          还没有账号？{' '}
          <Link to="/register" className="text-[var(--color-accent)] hover:underline">
            注册
          </Link>
        </p>
      </Card>
    </div>
  )
}
