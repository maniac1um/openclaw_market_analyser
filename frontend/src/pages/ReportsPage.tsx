import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'
import { Trash2, Search } from 'lucide-react'
import { api, ApiError } from '../lib/api'
import { formatCnDateTime } from '../lib/utils'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Skeleton, ErrorBanner, EmptyState } from '../components/ui/States'
import { ReportDetailView } from '../features/reports/ReportDetail'

export function ReportsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [keyword, setKeyword] = useState('')
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const queryClient = useQueryClient()

  const activeId = searchParams.get('id') || undefined

  const reportsQuery = useQuery({
    queryKey: ['reports'],
    queryFn: api.listReports,
  })

  const detailQuery = useQuery({
    queryKey: ['report', activeId],
    queryFn: () => api.getReport(activeId!),
    enabled: !!activeId,
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
      if (activeId) setSearchParams({})
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const pickReport = (id: string) => {
    setSearchParams({ id })
  }

  if (reportsQuery.isLoading) {
    return (
      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <Skeleton className="h-[480px]" />
        <Skeleton className="h-[480px]" />
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
    <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
      <Card className="flex flex-col overflow-hidden">
        <div className="border-b border-[var(--color-border)] p-3">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-[var(--color-muted)]" />
            <input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="搜索关键词或标题…"
              className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] py-2 pl-9 pr-3 text-sm outline-none focus:border-[var(--color-accent)]"
            />
          </div>
          <div className="mt-2 flex items-center justify-between text-xs text-[var(--color-muted)]">
            <span>共 {filtered.length} 条</span>
            {selected.size > 0 && (
              <Button
                variant="danger"
                className="h-7 px-2 text-xs"
                onClick={() => {
                  if (confirm(`确认删除 ${selected.size} 条报告？`)) {
                    deleteMutation.mutate([...selected])
                  }
                }}
              >
                <Trash2 className="h-3.5 w-3.5" /> 删除
              </Button>
            )}
          </div>
        </div>
        <ul className="flex-1 overflow-y-auto">
          {!filtered.length ? (
            <EmptyState title="暂无报告" description="让 OpenClaw 提交分析报告后将在此展示" />
          ) : (
            filtered.map((r) => (
              <li key={r.ingest_id}>
                <button
                  onClick={() => pickReport(r.ingest_id)}
                  className={`flex w-full items-start gap-2 border-b border-[var(--color-border)] px-3 py-3 text-left transition-colors hover:bg-[var(--color-bg)] ${
                    activeId === r.ingest_id ? 'border-l-2 border-l-[var(--color-accent)] bg-[var(--color-bg)]' : ''
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selected.has(r.ingest_id)}
                    onChange={(e) => {
                      e.stopPropagation()
                      const next = new Set(selected)
                      if (e.target.checked) next.add(r.ingest_id)
                      else next.delete(r.ingest_id)
                      setSelected(next)
                    }}
                    onClick={(e) => e.stopPropagation()}
                    className="mt-1"
                  />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium leading-snug line-clamp-2">{r.title || '未命名报告'}</p>
                    <p className="mt-1 text-xs text-[var(--color-muted)]">{r.keyword}</p>
                    <p className="text-xs text-[var(--color-muted)]">{formatCnDateTime(r.generated_at)}</p>
                  </div>
                </button>
              </li>
            ))
          )}
        </ul>
      </Card>

      <div className="min-w-0">
        {!activeId ? (
          <EmptyState title="选择一份报告" description="从左侧列表选择报告查看详细分析" />
        ) : detailQuery.isLoading ? (
          <Skeleton className="h-[600px]" />
        ) : detailQuery.isError ? (
          <ErrorBanner message={(detailQuery.error as Error).message} onRetry={() => detailQuery.refetch()} />
        ) : detailQuery.data ? (
          <ReportDetailView report={detailQuery.data} />
        ) : null}
      </div>
    </div>
  )
}
