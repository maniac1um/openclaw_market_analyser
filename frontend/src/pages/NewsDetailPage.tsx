import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { api } from '../lib/api'
import { ErrorBanner } from '../components/ui/States'
import { Skeleton } from '../components/ui/ds'
import { NewsArticleContent } from '../features/news/NewsArticleContent'

function NewsDetailSkeleton() {
  return (
    <div className="mx-auto flex w-full max-w-[800px] flex-col gap-6">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-10 w-full" />
      <div className="flex gap-4">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-4 w-24" />
      </div>
      <div className="space-y-3 border-t border-[var(--border)] pt-8">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-[92%]" />
      </div>
    </div>
  )
}

export function NewsDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const newsId = id ? Number(id) : NaN

  const detailQuery = useQuery({
    queryKey: ['news-item', newsId],
    queryFn: () => api.getNews(newsId),
    enabled: Number.isFinite(newsId),
  })

  if (!id || !Number.isFinite(newsId)) {
    return <ErrorBanner message="无效的新闻 ID" onRetry={() => navigate('/app/news')} />
  }

  if (detailQuery.isLoading) return <NewsDetailSkeleton />

  if (detailQuery.isError) {
    return (
      <ErrorBanner message={(detailQuery.error as Error).message} onRetry={() => detailQuery.refetch()} />
    )
  }

  const item = detailQuery.data
  if (!item) return null

  return (
    <article className="mx-auto w-full max-w-[800px]">
      <Link
        to="/app/news"
        className="mb-8 inline-flex items-center gap-1.5 text-sm text-[var(--text-secondary)] transition-colors hover:text-primary"
      >
        <ArrowLeft className="h-4 w-4" />
        返回列表
      </Link>

      <header className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight text-primary sm:text-3xl">
          {item.title || '未命名新闻'}
        </h1>
      </header>

      <NewsArticleContent item={item} />
    </article>
  )
}
