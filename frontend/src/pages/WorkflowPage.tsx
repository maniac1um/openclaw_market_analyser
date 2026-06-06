import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { toast } from 'sonner'
import { Play, Plus, Stethoscope } from 'lucide-react'
import { api } from '../lib/api'
import { formatCnDateTime } from '../lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Skeleton, ErrorBanner } from '../components/ui/States'

export function WorkflowPage() {
  const [keyword, setKeyword] = useState('')
  const [monitorId, setMonitorId] = useState('')
  const queryClient = useQueryClient()

  const stateQuery = useQuery({ queryKey: ['workflow'], queryFn: api.workflowState, refetchInterval: 30_000 })
  const diagQuery = useQuery({ queryKey: ['diagnostics'], queryFn: api.workflowDiagnostics })

  const bootstrapMutation = useMutation<{ monitor_id?: string }, Error, void>({
    mutationFn: () => api.workflowBootstrap({ keyword: keyword.trim(), candidate_count: 10 }) as Promise<{ monitor_id?: string }>,
    onSuccess: (data: { monitor_id?: string }) => {
      toast.success('监测任务已创建')
      if (data.monitor_id) setMonitorId(data.monitor_id)
      queryClient.invalidateQueries({ queryKey: ['workflow'] })
      queryClient.invalidateQueries({ queryKey: ['monitors'] })
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const analysisMutation = useMutation({
    mutationFn: () =>
      api.workflowAnalysis({
        monitor_id: monitorId,
        window_days: 7,
        news_hours: 72,
        horizon: '24h',
        publish: true,
      }),
    onSuccess: () => {
      toast.success('联合分析已触发并发布')
      queryClient.invalidateQueries({ queryKey: ['reports'] })
    },
    onError: (e: Error) => toast.error(e.message),
  })

  if (stateQuery.isLoading) return <Skeleton className="h-[500px]" />
  if (stateQuery.isError) return <ErrorBanner message={(stateQuery.error as Error).message} onRetry={() => stateQuery.refetch()} />

  const overview = stateQuery.data?.overview
  const gateway = stateQuery.data?.gateway
  const runs = stateQuery.data?.external_scheduler_runs || []
  const configs = stateQuery.data?.external_scheduler_configs || []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">工作流控制台</h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">管理监测任务、调度配置与联合分析</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-[var(--color-muted)]">Gateway</p>
            <Badge variant={gateway?.ok ? 'success' : 'danger'} className="mt-1">
              {gateway?.ok ? '在线' : '离线'}
            </Badge>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-[var(--color-muted)]">报告数</p>
            <p className="text-xl font-semibold">{overview?.reports?.published_count ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-[var(--color-muted)]">监测任务</p>
            <p className="text-xl font-semibold">{overview?.price_monitoring?.monitor_count ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-[var(--color-muted)]">外部调度</p>
            <p className="text-xl font-semibold">{configs.length}</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>创建监测任务</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="关键词，例如：羽毛球"
              className="w-full rounded-md border border-[var(--color-border)] px-3 py-2 text-sm outline-none"
            />
            <Button variant="primary" disabled={!keyword.trim() || bootstrapMutation.isPending} onClick={() => bootstrapMutation.mutate()}>
              <Plus className="h-4 w-4" /> 创建监测
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>触发联合分析</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <input
              value={monitorId}
              onChange={(e) => setMonitorId(e.target.value)}
              placeholder="monitor_id (UUID)"
              className="w-full rounded-md border border-[var(--color-border)] px-3 py-2 text-sm outline-none"
            />
            <Button
              variant="primary"
              disabled={!monitorId.trim() || analysisMutation.isPending}
              onClick={() => {
                if (confirm('确认触发联合分析并发布报告？')) analysisMutation.mutate()
              }}
            >
              <Play className="h-4 w-4" /> 立即分析
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center gap-2">
          <Stethoscope className="h-4 w-4" />
          <CardTitle>系统诊断</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {diagQuery.isLoading ? (
            <Skeleton className="h-20" />
          ) : (
            ((diagQuery.data as { checks?: { label: string; ok: boolean; detail: string; severity: string }[] })?.checks || []).map((c) => (
              <div key={c.label} className="flex items-start justify-between rounded-md border border-[var(--color-border)] px-3 py-2 text-sm">
                <span>{c.label}</span>
                <Badge variant={c.ok ? 'success' : c.severity === 'error' ? 'danger' : 'warning'}>
                  {c.detail}
                </Badge>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>最近调度运行</CardTitle>
        </CardHeader>
        <CardContent className="divide-y divide-[var(--color-border)] p-0">
          {!runs.length ? (
            <p className="p-4 text-sm text-[var(--color-muted)]">暂无运行记录</p>
          ) : (
            runs.slice(0, 8).map((r, i) => (
              <div key={i} className="flex items-center justify-between px-4 py-2 text-sm">
                <span>{String(r.job_name || '-')}</span>
                <div className="flex items-center gap-2">
                  <Badge variant={r.status === 'ok' ? 'success' : 'warning'}>{String(r.status)}</Badge>
                  <span className="text-xs text-[var(--color-muted)]">{formatCnDateTime(String(r.last_seen_at || ''))}</span>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  )
}
