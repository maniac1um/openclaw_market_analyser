import { type FormEvent, useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { useAuth } from '../lib/AuthContext'

export function RegisterPage() {
  const { register, user, loading } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (!loading && user) return <Navigate to="/" replace />

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await register(email, username, password)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : '注册失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-bg)] px-4">
      <Card className="w-full max-w-md p-6">
        <h1 className="mb-1 text-lg font-semibold">注册</h1>
        <p className="mb-6 text-sm text-[var(--color-muted)]">创建您的 OpenClaw 账号</p>
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
            <span className="mb-1 block text-[var(--color-muted)]">用户名</span>
            <input
              type="text"
              required
              minLength={3}
              maxLength={32}
              pattern="[a-zA-Z0-9_-]+"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-[var(--color-muted)]">密码（至少 8 位，含字母和数字）</span>
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
            {submitting ? '注册中…' : '注册'}
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-[var(--color-muted)]">
          已有账号？{' '}
          <Link to="/login" className="text-[var(--color-accent)] hover:underline">
            登录
          </Link>
        </p>
      </Card>
    </div>
  )
}
