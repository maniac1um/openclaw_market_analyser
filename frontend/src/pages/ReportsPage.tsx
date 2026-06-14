import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'
import { Eye, Trash2 } from 'lucide-react'
import { api, ApiError } from '../lib/api'
import { cn, formatCnDateTime } from '../lib/utils'
import { Button } from '../components/ui/Button'
import { ErrorBanner, EmptyState } from '../components/ui/States'
import {
  Panel,
  DataRow,
  Drawer,
  CommandBar,
  CommandBarInput,
  CommandBarButton,
  TableSkeleton,
} from '../components/ui/ds'
import { ReportPreviewBody } from '../features/reports/ReportDetailBody'
import { useOnboardingActive } from '../features/onboarding/OnboardingProvider'
import { ONBOARDING_EVENTS } from '../features/onboarding/types'

export function ReportsPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [keyword, setKeyword] = useState('')
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [previewId, setPreviewId] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const onboardingActive = useOnboardingActive()

  const reportsQuery = useQuery({
    queryKey: ['reports'],
    queryFn: api.listReports,
  })

  const previewQuery = useQuery({
    queryKey: ['report', previewId],
    queryFn: () => api.getReport(previewId!),
    enabled: !!previewId,
  })

  const filtered = useMemo(() => {
    const list = reportsQuery.data || []
    const q = keyword.trim().toLowerCase()
    if (!q) return list
    return list.filter(
      (r) =>
        (r.keyword || '').toLowerCase().includes(q) ||
        (r.title || '').toLowerCase().includes(q),
    )
  }, [reportsQuery.data, keyword])

  const deleteMutation = useMutation({
    mutationFn: (ids: string[]) => api.deleteReports(ids),
    onSuccess: () => {
      toast.success('报告已删除')
      setSelected(new Set())
      queryClient.invalidateQueries({ queryKey: ['reports'] })
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const openReport = (id: string) => {
    navigate(`/app/reports/${id}`)
    window.dispatchEvent(new CustomEvent(ONBOARDING_EVENTS.reportViewed))
  }

  useEffect(() => {
    const legacyId = searchParams.get('id')
    if (legacyId) {
      const qs = searchParams.get('onboarding')
      navigate(qs ? `/app/reports/${legacyId}?onboarding=${qs}` : `/app/reports/${legacyId}`, { replace: true })
      return
    }
    const onboarding = searchParams.get('onboarding')
    const list = reportsQuery.data
    if (onboarding !== 'step4' || !list?.length) return
    navigate(`/app/reports/${list[0].ingest_id}?onboarding=step4`, { replace: true })
    window.dispatchEvent(new CustomEvent(ONBOARDING_EVENTS.reportViewed))
  }, [searchParams, reportsQuery.data, navigate])

  const toggleSelect = (id: string, checked: boolean) => {
    const next = new Set(selected)
    if (checked) next.add(id)
    else next.delete(id)
    setSelected(next)
  }

  const previewReport = previewQuery.data

  if (reportsQuery.isLoading) {
    return (
      <Panel className="w-full max-w-[360px] overflow-hidden p-0">
        <div className="border-b border-[var(--ds-border)] p-3">
          <div className="h-9 animate-pulse rounded-lg bg-white/[0.06]" />
        </div>
        <TableSkeleton rows={8} />
      </Panel>
    )
  }

  if (reportsQuery.isError) {
    const err = reportsQuery.error as ApiError
    return (
      <ErrorBanner
        message={err.status === 503 ? '未配置报告数据库。请设置 OPENCLAW_DATABASE_URL。' : err.message}
        onRetry={() => reportsQuery.refetch()}
      />
    )
  }

  return (
    <>
      <div className="flex min-h-0 flex-1 flex-col">
        <Panel className="flex w-full max-w-[360px] flex-col overflow-hidden p-0">
          <div className="border-b border-[var(--ds-border)] p-3">
            <CommandBar className="border-0 bg-transparent p-0 backdrop-blur-none">
              <CommandBarInput
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="搜索关键词或标题…"
                aria-label="搜索报告"
              />
              {selected.size > 0 ? (
                <CommandBarButton
                  variant="danger"
                  className="text-xs"
                  onClick={() => {
                    if (confirm(`确认删除 ${selected.size} 条报告？`)) {
                      deleteMutation.mutate([...selected])
                    }
                  }}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  删除 ({selected.size})
                </CommandBarButton>
              ) : null}
            </CommandBar>
            <p className="mt-2 text-xs text-[var(--ds-text-secondary)]">共 {filtered.length} 条</p>
          </div>

          <div className="max-h-[calc(100dvh-220px)] overflow-y-auto">
            {!filtered.length ? (
              <EmptyState
                title="暂无报告"
                description="让 OpenClaw 提交分析报告后将在此展示"
                action={
                  onboardingActive ? (
                    <Link to="/app/workflow?onboarding=step3">
                      <Button variant="primary">查看工作流调度</Button>
                    </Link>
                  ) : (
                    <Link to="/#sample-report">
                      <Button variant="secondary">查看虚构示例报告</Button>
                    </Link>
                  )
                }
              />
            ) : (
              <div className="divide-y divide-[var(--ds-border)]">
                {filtered.map((r) => (
                  <div key={r.ingest_id} className="flex items-stretch">
                    <label className="flex shrink-0 cursor-pointer items-center px-3">
                      <input
                        type="checkbox"
                        checked={selected.has(r.ingest_id)}
                        onChange={(e) => toggleSelect(r.ingest_id, e.target.checked)}
                        onClick={(e) => e.stopPropagation()}
                        className="h-4 w-4"
                        aria-label={`选择 ${r.title || '报告'}`}
                      />
                    </label>
                    <DataRow
                      title={r.title || '未命名报告'}
                      subtitle={r.keyword}
                      meta={formatCnDateTime(r.generated_at)}
                      onClick={() => openReport(r.ingest_id)}
                      className="min-w-0 flex-1 pr-1"
                    />
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        setPreviewId(r.ingest_id)
                      }}
                      className={cn(
                        'mr-2 flex shrink-0 items-center self-center rounded-lg p-2',
                        'text-[var(--ds-text-secondary)] transition-colors hover:bg-white/5 hover:text-[var(--ds-text-primary)]',
                      )}
                      aria-label="快速预览"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Panel>
      </div>

      <Drawer
        open={!!previewId}
        onClose={() => setPreviewId(null)}
        title={previewReport?.title || '报告预览'}
      >
        {previewQuery.isLoading ? (
          <p className="text-sm text-[var(--ds-text-secondary)]">加载中…</p>
        ) : previewQuery.isError ? (
          <ErrorBanner message={(previewQuery.error as Error).message} onRetry={() => previewQuery.refetch()} />
        ) : previewReport ? (
          <div className="flex flex-col gap-6">
            <ReportPreviewBody report={previewReport} />
            <Button variant="primary" className="w-full" onClick={() => openReport(previewReport.ingest_id)}>
              查看完整报告
            </Button>
          </div>
        ) : null}
      </Drawer>
    </>
  )
}
