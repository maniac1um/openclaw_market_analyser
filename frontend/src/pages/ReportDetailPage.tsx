import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { api } from '../lib/api'
import { formatCnDateTime } from '../lib/utils'
import { ErrorBanner } from '../components/ui/States'
import { StatStripSkeleton, Skeleton as DsSkeleton } from '../components/ui/ds'
import { ReportDetailBody } from '../features/reports/ReportDetailBody'

function ReportDetailSkeleton() {
  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-10">
      <DsSkeleton className="h-8 w-2/3" />
      <DsSkeleton className="h-4 w-1/2" />
      <StatStripSkeleton items={4} />
      <div className="space-y-3">
        <DsSkeleton className="h-4 w-full" />
        <DsSkeleton className="h-4 w-[95%]" />
        <DsSkeleton className="h-4 w-[88%]" />
        <DsSkeleton className="h-64 w-full" />
      </div>
    </div>
  )
}

export function ReportDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const detailQuery = useQuery({
    queryKey: ['report', id],
    queryFn: () => api.getReport(id!),
    enabled: !!id,
  })

  if (!id) {
    return <ErrorBanner message="无效的报告 ID" onRetry={() => navigate('/app/reports')} />
  }

  if (detailQuery.isLoading) return <ReportDetailSkeleton />

  if (detailQuery.isError) {
    return (
      <ErrorBanner message={(detailQuery.error as Error).message} onRetry={() => detailQuery.refetch()} />
    )
  }

  const report = detailQuery.data
  if (!report) return null

  return (
    <article className="mx-auto w-full max-w-4xl" data-onboarding="report-detail">
      <Link
        to="/app/reports"
        className="mb-6 inline-flex items-center gap-1.5 text-sm text-[var(--ds-text-secondary)] transition-colors hover:text-[var(--ds-text-primary)]"
      >
        <ArrowLeft className="h-4 w-4" />
        返回列表
      </Link>

      <header className="mb-10 border-b border-[var(--ds-border)] pb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-[var(--ds-text-primary)]">
          {report.title || '未命名报告'}
        </h1>
        <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm text-[var(--ds-text-secondary)]">
          {report.keyword ? <span>关键词：{report.keyword}</span> : null}
          {report.time_range?.start || report.time_range?.end ? (
            <span>
              时间范围：{formatCnDateTime(report.time_range?.start)} — {formatCnDateTime(report.time_range?.end)}
            </span>
          ) : null}
          <span>生成于 {formatCnDateTime(report.generated_at)}</span>
          {report.items_count != null ? <span>新闻 {report.items_count} 条</span> : null}
        </div>
      </header>

      <ReportDetailBody report={report} />
    </article>
  )
}
