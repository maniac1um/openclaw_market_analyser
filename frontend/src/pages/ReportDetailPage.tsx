import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { api } from '../lib/api'
import { formatCnDateTime } from '../lib/utils'
import { ErrorBanner } from '../components/ui/States'
import { Skeleton as DsSkeleton } from '../components/ui/ds'
import { ReportDetailBody } from '../features/reports/ReportDetailBody'

function formatReportTime(report: { time_range?: { start?: string; end?: string }; generated_at?: string }) {
  if (report.time_range?.start || report.time_range?.end) {
    return `${formatCnDateTime(report.time_range?.start)} — ${formatCnDateTime(report.time_range?.end)}`
  }
  return formatCnDateTime(report.generated_at)
}

function formatSources(sources?: string[]) {
  if (!sources?.length) return '—'
  return sources.join('、')
}

function ReportDetailSkeleton() {
  return (
    <div className="mx-auto flex w-full max-w-[900px] flex-col gap-8">
      <DsSkeleton className="h-10 w-2/3" />
      <div className="flex gap-6">
        <DsSkeleton className="h-4 w-24" />
        <DsSkeleton className="h-4 w-40" />
        <DsSkeleton className="h-4 w-32" />
      </div>
      <div className="space-y-3 border-t border-[var(--ds-border)] pt-8">
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
    <article className="mx-auto w-full max-w-[900px]" data-onboarding="report-detail">
      <Link
        to="/app/reports"
        className="mb-8 inline-flex items-center gap-1.5 text-sm text-[var(--ds-text-secondary)] transition-colors hover:text-[var(--ds-text-primary)]"
      >
        <ArrowLeft className="h-4 w-4" />
        返回列表
      </Link>

      <header className="mb-2">
        <h1 className="text-3xl font-semibold tracking-tight text-[var(--ds-text-primary)]">
          {report.title || '未命名报告'}
        </h1>
        <dl className="mt-5 flex flex-wrap gap-x-8 gap-y-2 text-sm">
          <div className="flex gap-2">
            <dt className="text-[var(--ds-text-secondary)]">关键词</dt>
            <dd className="text-[var(--ds-text-primary)]">{report.keyword || '—'}</dd>
          </div>
          <div className="flex gap-2">
            <dt className="text-[var(--ds-text-secondary)]">时间</dt>
            <dd className="text-[var(--ds-text-primary)]">{formatReportTime(report)}</dd>
          </div>
          <div className="flex gap-2">
            <dt className="text-[var(--ds-text-secondary)]">数据源</dt>
            <dd className="text-[var(--ds-text-primary)]">{formatSources(report.sources)}</dd>
          </div>
        </dl>
      </header>

      <ReportDetailBody report={report} />
    </article>
  )
}
