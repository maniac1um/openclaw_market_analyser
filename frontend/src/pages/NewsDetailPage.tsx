import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, ExternalLink } from 'lucide-react'
import { api } from '../lib/api'
import { safeExternalHref } from '../lib/urlSafety'
import { cn, formatCnDateTime } from '../lib/utils'
import { Badge } from '../components/ui/Badge'
import { MarkdownContent } from '../components/markdown/MarkdownContent'
import { ErrorBanner } from '../components/ui/States'
import { Skeleton } from '../components/ui/ds'

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
        <Skeleton className="h-4 w-[95%]" />
        <Skeleton className="h-4 w-[88%]" />
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
    queryKey: ['news', newsId],
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

  const sourceHref = safeExternalHref(item.source_url)
  const published = formatCnDateTime(item.published_at || item.created_at)

  return (
    <article className="mx-auto w-full max-w-[800px]">
      <Link
        to="/app/news"
        className="mb-8 inline-flex items-center gap-1.5 text-sm text-[var(--text-secondary)] transition-colors hover:text-primary"
      >
        <ArrowLeft className="h-4 w-4" />
        返回列表
      </Link>

      <header className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-primary sm:text-3xl">
          {item.title || '未命名新闻'}
        </h1>
        <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-[var(--text-secondary)]">
          {published ? <time dateTime={item.published_at || item.created_at}>{published}</time> : null}
          {item.source_name ? (
            <>
              {published ? <span aria-hidden>·</span> : null}
              <span>{item.source_name}</span>
            </>
          ) : null}
          {item.keyword ? <Badge>{item.keyword}</Badge> : null}
        </div>
        {sourceHref ? (
          <a
            href={sourceHref}
            target="_blank"
            rel="noreferrer"
            className={cn(
              'mt-4 inline-flex items-center gap-1 text-sm text-[var(--color-accent)] hover:underline',
            )}
          >
            查看原文 <ExternalLink className="h-3.5 w-3.5" />
          </a>
        ) : null}
      </header>

      {item.summary ? (
        <div className="border-t border-[var(--border)] pt-8">
          <MarkdownContent>{item.summary}</MarkdownContent>
        </div>
      ) : (
        <p className="border-t border-[var(--border)] pt-8 text-sm text-[var(--text-secondary)]">暂无正文内容</p>
      )}
    </article>
  )
}
