import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'
import { Search, Trash2, ExternalLink } from 'lucide-react'
import { api, ApiError } from '../lib/api'
import { safeExternalHref } from '../lib/urlSafety'
import { cn, formatCnDateTime } from '../lib/utils'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { MobileBackButton } from '../components/ui/MobileBackButton'
import { Skeleton, ErrorBanner, EmptyState } from '../components/ui/States'

export function NewsPage() {
  const [keyword, setKeyword] = useState('')
  const [search, setSearch] = useState('')
  const [activeId, setActiveId] = useState<number | null>(null)
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const queryClient = useQueryClient()

  const showList = activeId === null
  const showDetail = activeId !== null

  const newsQuery = useQuery({
    queryKey: ['news', search],
    queryFn: () => api.listNews(search || undefined),
  })

  const deleteMutation = useMutation({
    mutationFn: (ids: number[]) => api.deleteNews(ids),
    onSuccess: () => {
      toast.success('已删除')
      setSelected(new Set())
      setActiveId(null)
      queryClient.invalidateQueries({ queryKey: ['news'] })
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const active = useMemo(() => newsQuery.data?.find((n) => n.id === activeId), [newsQuery.data, activeId])

  if (newsQuery.isLoading) return <Skeleton className="h-[500px]" />

  if (newsQuery.isError) {
    const err = newsQuery.error as ApiError
    return (
      <ErrorBanner
        message={err.status === 503 ? '未配置新闻库。请设置 OPENCLAW_NEWS_DATABASE_URL。' : err.message}
        onRetry={() => newsQuery.refetch()}
      />
    )
  }

  const items = newsQuery.data || []

  return (
    <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
      <Card className={cn('overflow-hidden', !showList && 'hidden lg:block')}>
        <div className="border-b border-[var(--color-border)] p-3">
          <div className="flex gap-2">
            <div className="relative min-w-0 flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-[var(--color-muted)]" />
              <input
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && setSearch(keyword)}
                placeholder="按关键词筛选…"
                className="w-full rounded-md border border-[var(--color-border)] py-2 pl-9 pr-3 text-sm outline-none"
              />
            </div>
            <Button className="shrink-0" onClick={() => setSearch(keyword)}>
              搜索
            </Button>
          </div>
          {selected.size > 0 && (
            <Button
              variant="danger"
              className="mt-2 h-8 text-xs"
              onClick={() => {
                if (confirm(`删除 ${selected.size} 条？`)) deleteMutation.mutate([...selected])
              }}
            >
              <Trash2 className="h-3.5 w-3.5" /> 删除选中
            </Button>
          )}
        </div>
        <ul className="max-h-none overflow-y-auto lg:max-h-[calc(100vh-220px)]">
          {!items.length ? (
            <EmptyState title="暂无新闻" description="OpenClaw 入库后将在此展示" />
          ) : (
            items.map((n) => (
              <li key={n.id}>
                <button
                  onClick={() => setActiveId(n.id)}
                  className={`flex w-full items-start gap-2 border-b border-[var(--color-border)] px-3 py-3 text-left hover:bg-[var(--color-bg)] ${
                    activeId === n.id ? 'bg-[var(--color-bg)] border-l-2 border-l-[var(--color-accent)]' : ''
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selected.has(n.id)}
                    onChange={(e) => {
                      e.stopPropagation()
                      const next = new Set(selected)
                      if (e.target.checked) next.add(n.id)
                      else next.delete(n.id)
                      setSelected(next)
                    }}
                    onClick={(e) => e.stopPropagation()}
                    className="mt-1 h-4 w-4 shrink-0"
                  />
                  <div className="min-w-0">
                    <p className="text-sm font-medium line-clamp-2">{n.title}</p>
                    <div className="mt-1 flex gap-2">
                      {n.keyword && <Badge variant="muted">{n.keyword}</Badge>}
                    </div>
                    <p className="mt-1 text-xs text-[var(--color-muted)]">{formatCnDateTime(n.published_at || n.created_at)}</p>
                  </div>
                </button>
              </li>
            ))
          )}
        </ul>
      </Card>

      <Card className={cn('min-h-[400px]', !showDetail && 'hidden lg:block')}>
        {!active ? (
          <EmptyState title="选择一条新闻" description="从左侧列表选择查看详情" />
        ) : (
          <div className="p-4 sm:p-6">
            <MobileBackButton onClick={() => setActiveId(null)} />
            <div className="flex flex-wrap gap-2">
              {active.keyword && <Badge>{active.keyword}</Badge>}
              {active.source_name && <Badge variant="muted">{active.source_name}</Badge>}
            </div>
            <h2 className="mt-4 text-lg font-semibold sm:text-xl">{active.title}</h2>
            <p className="mt-2 text-sm text-[var(--color-muted)]">{formatCnDateTime(active.published_at || active.created_at)}</p>
            {active.summary && <p className="mt-4 text-sm leading-relaxed">{active.summary}</p>}
            {safeExternalHref(active.source_url) && (
              <a
                href={safeExternalHref(active.source_url)}
                target="_blank"
                rel="noreferrer"
                className="mt-4 inline-flex min-h-11 items-center gap-1 text-sm text-[var(--color-accent)] hover:underline"
              >
                查看原文 <ExternalLink className="h-3.5 w-3.5" />
              </a>
            )}
          </div>
        )}
      </Card>
    </div>
  )
}
