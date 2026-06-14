import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'
import { Trash2 } from 'lucide-react'
import { api, ApiError } from '../lib/api'
import { formatCnDateTime } from '../lib/utils'
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
import { newsRowSubtitle } from '../features/news/NewsArticleContent'

const LIST_MAX_WIDTH = '900px'

export function NewsPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [keyword, setKeyword] = useState(searchParams.get('q') || '')
  const [search, setSearch] = useState(searchParams.get('q') || '')
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const queryClient = useQueryClient()

  const newsQuery = useQuery({
    queryKey: ['news', search],
    queryFn: () => api.listNews(search || undefined),
  })

  const deleteMutation = useMutation({
    mutationFn: (ids: number[]) => api.deleteNews(ids),
    onSuccess: () => {
      toast.success('已删除')
      setSelected(new Set())
      queryClient.invalidateQueries({ queryKey: ['news'] })
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const items = newsQuery.data || []

  const toggleSelect = (id: number, checked: boolean) => {
    const next = new Set(selected)
    if (checked) next.add(id)
    else next.delete(id)
    setSelected(next)
  }

  if (newsQuery.isLoading) {
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

  if (newsQuery.isError) {
    const err = newsQuery.error as ApiError
    return (
      <ErrorBanner
        message={err.status === 503 ? '未配置新闻库。请设置 OPENCLAW_NEWS_DATABASE_URL。' : err.message}
        onRetry={() => newsQuery.refetch()}
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
              onKeyDown={(e) => e.key === 'Enter' && setSearch(keyword)}
              placeholder="按关键词筛选…"
              aria-label="搜索新闻"
            />
            <CommandBarButton className="text-xs" onClick={() => setSearch(keyword)}>
              搜索
            </CommandBarButton>
            {selected.size > 0 ? (
              <CommandBarButton
                variant="danger"
                className="text-xs"
                onClick={() => {
                  if (confirm(`删除 ${selected.size} 条？`)) deleteMutation.mutate([...selected])
                }}
              >
                <Trash2 className="h-3.5 w-3.5" />
                删除 ({selected.size})
              </CommandBarButton>
            ) : null}
          </CommandBar>
          <p className="mt-2 text-xs text-[var(--text-secondary)]">共 {items.length} 条</p>
        </div>

        <div className="max-h-[calc(100dvh-260px)] overflow-y-auto">
          {!items.length ? (
            <EmptyState title="暂无新闻" description="OpenClaw 入库后将在此展示" />
          ) : (
            <div className="divide-y divide-[var(--border)]">
              {items.map((n) => (
                <div key={n.id} className="flex items-stretch">
                  <label className="flex shrink-0 cursor-pointer items-center px-3">
                    <input
                      type="checkbox"
                      checked={selected.has(n.id)}
                      onChange={(e) => toggleSelect(n.id, e.target.checked)}
                      onClick={(e) => e.stopPropagation()}
                      className="h-4 w-4"
                      aria-label={`选择 ${n.title}`}
                    />
                  </label>
                  <DataRow
                    title={n.title}
                    subtitle={newsRowSubtitle(n)}
                    meta={formatCnDateTime(n.published_at || n.created_at)}
                    onClick={() => navigate(`/app/news/${n.id}`)}
                    className="min-w-0 flex-1"
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
      <h1 className="text-lg font-semibold text-primary">新闻</h1>
      <p className="mt-1 text-sm text-[var(--text-secondary)]">浏览 OpenClaw 入库的新闻条目</p>
    </header>
  )
}
