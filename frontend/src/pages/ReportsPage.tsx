import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'
import { Trash2 } from 'lucide-react'
import { api, ApiError } from '../lib/api'
import { formatCnDateTime } from '../lib/utils'
import { Button } from '../components/ui/Button'
import { ErrorBanner, EmptyState } from '../components/ui/States'
import {
  Panel,
  DataRow,
  CommandBar,
  CommandBarInput,
  CommandBarButton,
  Skeleton,
  TableSkeleton,
} from '../components/ui/ds'
import { reportRowSubtitle } from '../features/reports/ReportDetailContent'
import { useOnboardingActive } from '../features/onboarding/OnboardingProvider'
import { ONBOARDING_EVENTS } from '../features/onboarding/types'

const LIST_MAX_WIDTH = '900px'

export function ReportsPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [keyword, setKeyword] = useState('')
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const queryClient = useQueryClient()
  const onboardingActive = useOnboardingActive()

  const reportsQuery = useQuery({
    queryKey: ['reports'],
    queryFn: api.listReports,
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

  if (reportsQuery.isLoading) {
    return (
      <div className="mx-auto w-full" style={{ maxWidth: LIST_MAX_WIDTH }}>
        <PageHeader />
        <Panel className="overflow-hidden p-0">
          <div className="border-b border-[var(--border)] p-3">
            <Skeleton className="h-9 w-full rounded-lg" />
          </div>
          <TableSkeleton rows={8} />
        </Panel>
      </div>
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
    <div className="mx-auto flex w-full flex-col" style={{ maxWidth: LIST_MAX_WIDTH }}>
      <PageHeader />

      <Panel className="flex flex-col overflow-hidden p-0">
        <div className="border-b border-[var(--border)] p-3">
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
          <p className="mt-2 text-xs text-[var(--text-secondary)]">共 {filtered.length} 条</p>
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
            <div className="divide-y divide-[var(--border)]">
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
                    subtitle={reportRowSubtitle(r)}
                    meta={formatCnDateTime(r.generated_at)}
                    onClick={() => openReport(r.ingest_id)}
                    className="min-w-0 flex-1 pr-3"
                  />
                </div>
              ))}
            </div>
          )}
        </div>
      </Panel>
    </div>
  )
}

function PageHeader() {
  return (
    <header className="mb-6">
      <h1 className="text-lg font-semibold text-primary">专题分析</h1>
      <p className="mt-1 text-sm text-[var(--text-secondary)]">浏览与管理 AI 生成的分析报告</p>
    </header>
  )
}
