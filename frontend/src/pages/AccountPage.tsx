import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Key, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { ErrorBanner } from '../components/ui/States'
import { useAuth } from '../lib/AuthContext'
import { api, type ApiKeyItem } from '../lib/api'
import { ONBOARDING_EVENTS } from '../features/onboarding/types'
import { useOnboardingActive } from '../features/onboarding/OnboardingProvider'

export function AccountPage() {
  const { user } = useAuth()
  const onboardingActive = useOnboardingActive()
  const queryClient = useQueryClient()
  const [newKey, setNewKey] = useState<string | null>(null)
  const [label, setLabel] = useState('default')

  const keysQuery = useQuery({
    queryKey: ['api-keys'],
    queryFn: () => api.listApiKeys(),
  })

  const createMutation = useMutation({
    mutationFn: () => api.createApiKey(label.trim() || 'default'),
    onSuccess: (data) => {
      setNewKey(data.api_key)
      window.dispatchEvent(new CustomEvent(ONBOARDING_EVENTS.apiKeyCreated))
      void queryClient.invalidateQueries({ queryKey: ['api-keys'] })
      toast.success('API Key 已生成，请立即复制保存')
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const revokeMutation = useMutation({
    mutationFn: (id: string) => api.revokeApiKey(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['api-keys'] })
      toast.success('已撤销')
    },
    onError: (err: Error) => toast.error(err.message),
  })

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold">个人中心</h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">管理账号与 OpenClaw API Key</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>账号信息</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between gap-4">
            <span className="text-[var(--color-muted)]">用户名</span>
            <span>{user?.username}</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-[var(--color-muted)]">邮箱</span>
            <span>{user?.email}</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-[var(--color-muted)]">角色</span>
            <span>{user?.role}</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-4 w-4" />
            OpenClaw API Key
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-[var(--color-muted)]">
            在 OpenClaw Agent / Cursor Skill 中将 <code className="rounded bg-[var(--color-bg)] px-1">X-Api-Key</code>{' '}
            配置为下方生成的 Key。Key 仅展示一次，请妥善保管。
          </p>

          <div className="flex flex-wrap items-end gap-2" data-onboarding="api-key-create">
            <label className="flex-1 text-sm">
              <span className="mb-1 block text-[var(--color-muted)]">标签</span>
              <input
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2"
                placeholder="default"
              />
            </label>
            <Button variant="primary" onClick={() => createMutation.mutate()} disabled={createMutation.isPending}>
              生成新 Key
            </Button>
          </div>

          {newKey && (
            <div className="rounded-md border border-amber-500/40 bg-amber-500/10 p-3 text-sm">
              <p className="mb-2 font-medium text-amber-700 dark:text-amber-300">请立即复制（不会再次显示）</p>
              <code className="block break-all rounded bg-[var(--color-bg)] p-2 font-mono text-xs">{newKey}</code>
              <Button
                variant="secondary"
                className="mt-2"
                onClick={() => {
                  void navigator.clipboard.writeText(newKey)
                  toast.success('已复制到剪贴板')
                }}
              >
                复制
              </Button>
            </div>
          )}

          {keysQuery.isError && <ErrorBanner message={(keysQuery.error as Error).message} />}
          {keysQuery.isLoading && <p className="text-sm text-[var(--color-muted)]">加载中…</p>}

          <ul className="divide-y divide-[var(--color-border)] rounded-md border border-[var(--color-border)]">
            {(keysQuery.data ?? []).map((k: ApiKeyItem) => (
              <li key={k.id} className="flex items-center justify-between gap-3 px-3 py-2 text-sm">
                <div>
                  <div className="font-medium">{k.label}</div>
                  <div className="font-mono text-xs text-[var(--color-muted)]">{k.key_prefix}…</div>
                  <div className="text-xs text-[var(--color-muted)]">
                    创建于 {new Date(k.created_at).toLocaleString()}
                    {k.last_used_at ? ` · 最近使用 ${new Date(k.last_used_at).toLocaleString()}` : ''}
                  </div>
                </div>
                <Button
                  variant="ghost"
                  aria-label="撤销"
                  onClick={() => revokeMutation.mutate(k.id)}
                  disabled={revokeMutation.isPending}
                >
                  <Trash2 className="h-4 w-4 text-red-500" />
                </Button>
              </li>
            ))}
            {keysQuery.isSuccess && keysQuery.data.length === 0 && (
              <li className="px-3 py-4 text-center text-sm text-[var(--color-muted)]">
                暂无 API Key
                {onboardingActive ? (
                  <div className="mt-3">
                    <p className="mb-2 text-xs">Step 2（可选）：Agent 集成时使用</p>
                    <Link to="/app/account?onboarding=step2">
                      <Button variant="secondary" className="h-8 text-xs">
                        了解 API Key
                      </Button>
                    </Link>
                  </div>
                ) : null}
              </li>
            )}
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}
