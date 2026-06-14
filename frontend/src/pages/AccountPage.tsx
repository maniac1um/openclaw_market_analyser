import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Key, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '../components/ui/Button'
import { ErrorBanner } from '../components/ui/States'
import { Panel, Section, DataRow } from '../components/ui/ds'
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
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-10">
      <header>
        <h1 className="text-lg font-semibold text-[var(--ds-text-primary)]">账户</h1>
        <p className="mt-1 text-sm text-[var(--ds-text-secondary)]">管理账号与 OpenClaw API Key</p>
      </header>

      <Section title="账号信息">
        <Panel className="divide-y divide-[var(--ds-border)] p-0">
          <DataRow title="用户名" meta={user?.username} />
          <DataRow title="邮箱" meta={user?.email} />
          <DataRow title="角色" meta={user?.role} />
        </Panel>
      </Section>

      <Section
        title="OpenClaw API Key"
        description="在 OpenClaw Agent / Cursor Skill 中将 X-Api-Key 配置为下方生成的 Key。Key 仅展示一次，请妥善保管。"
      >
        <div className="flex flex-wrap items-end gap-2" data-onboarding="api-key-create">
          <label className="flex-1 text-sm">
            <span className="mb-1 block text-[var(--ds-text-secondary)]">标签</span>
            <input
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              className="w-full rounded-lg border border-[var(--ds-border)] bg-[var(--ds-bg-panel)] px-3 py-2 text-[var(--ds-text-primary)] outline-none focus:border-[var(--color-accent)]"
              placeholder="default"
            />
          </label>
          <Button variant="primary" onClick={() => createMutation.mutate()} disabled={createMutation.isPending}>
            <Key className="h-4 w-4" />
            生成新 Key
          </Button>
        </div>

        {newKey ? (
          <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-3 text-sm">
            <p className="mb-2 font-medium text-amber-300">请立即复制（不会再次显示）</p>
            <code className="block break-all rounded bg-[var(--code-bg)] p-2 font-mono text-xs">{newKey}</code>
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
        ) : null}

        {keysQuery.isError ? <ErrorBanner message={(keysQuery.error as Error).message} /> : null}
        {keysQuery.isLoading ? <p className="text-sm text-[var(--ds-text-secondary)]">加载中…</p> : null}

        <Panel className="divide-y divide-[var(--ds-border)] p-0">
          {(keysQuery.data ?? []).map((k: ApiKeyItem) => (
            <div key={k.id} className="flex items-center justify-between gap-3 px-4 py-3">
              <div className="min-w-0">
                <p className="text-sm font-medium text-[var(--ds-text-primary)]">{k.label}</p>
                <p className="font-mono text-xs text-[var(--ds-text-secondary)]">{k.key_prefix}…</p>
                <p className="text-xs text-[var(--ds-text-secondary)]">
                  创建于 {new Date(k.created_at).toLocaleString()}
                  {k.last_used_at ? ` · 最近使用 ${new Date(k.last_used_at).toLocaleString()}` : ''}
                </p>
              </div>
              <Button
                variant="ghost"
                aria-label="撤销"
                onClick={() => revokeMutation.mutate(k.id)}
                disabled={revokeMutation.isPending}
              >
                <Trash2 className="h-4 w-4 text-red-500" />
              </Button>
            </div>
          ))}
          {keysQuery.isSuccess && keysQuery.data.length === 0 ? (
            <div className="px-4 py-6 text-center text-sm text-[var(--ds-text-secondary)]">
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
            </div>
          ) : null}
        </Panel>
      </Section>
    </div>
  )
}
