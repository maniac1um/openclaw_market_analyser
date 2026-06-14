import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { api } from '../lib/api'
import { ErrorBanner } from '../components/ui/States'
import { Skeleton } from '../components/ui/ds'
import { ReportDetailContent } from '../features/reports/ReportDetailContent'

function ReportDetailSkeleton() {
  return (
    <div className="mx-auto flex w-full max-w-[900px] flex-col gap-8">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-10 w-2/3" />
      <div className="flex gap-6">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-4 w-32" />
      </div>
      <div className="space-y-3 border-t border-[var(--border)] pt-8">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-[95%]" />
        <Skeleton className="h-64 w-full" />
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
    <article className="mx-auto w-full max-w-[900px]">
      <Link
        to="/app/reports"
        className="mb-8 inline-flex items-center gap-1.5 text-sm text-[var(--text-secondary)] transition-colors hover:text-primary"
      >
        <ArrowLeft className="h-4 w-4" />
        返回列表
      </Link>

      <header className="mb-2">
        <h1 className="text-3xl font-semibold tracking-tight text-primary">
          {report.title || '未命名报告'}
        </h1>
      </header>

      <ReportDetailContent report={report} />
    </article>
  )
}
