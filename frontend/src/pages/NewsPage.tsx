import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'
import { ExternalLink, Trash2 } from 'lucide-react'
import { api, ApiError } from '../lib/api'
import { safeExternalHref } from '../lib/urlSafety'
import { cn, formatCnDateTime } from '../lib/utils'
import { Badge } from '../components/ui/Badge'
import { MarkdownContent } from '../components/markdown/MarkdownContent'
import { ErrorBanner, EmptyState } from '../components/ui/States'
import {
  Panel,
  DataRow,
  Drawer,
  CommandBar,
  CommandBarInput,
  CommandBarButton,
  DrawerContentSkeleton,
  Skeleton,
  TableSkeleton,
} from '../components/ui/ds'

export function NewsPage() {
  const [searchParams] = useSearchParams()
  const [keyword, setKeyword] = useState(searchParams.get('q') || '')
  const [search, setSearch] = useState(searchParams.get('q') || '')
  const [activeId, setActiveId] = useState<number | null>(null)
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
      setActiveId(null)
      queryClient.invalidateQueries({ queryKey: ['news'] })
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const active = useMemo(() => newsQuery.data?.find((n) => n.id === activeId), [newsQuery.data, activeId])
  const items = newsQuery.data || []

  const toggleSelect = (id: number, checked: boolean) => {
    const next = new Set(selected)
    if (checked) next.add(id)
    else next.delete(id)
    setSelected(next)
  }

  if (newsQuery.isLoading) {
    return (
      <Panel className="w-full max-w-[400px] overflow-hidden p-0">
        <div className="border-b border-[var(--ds-border)] p-3">
          <Skeleton className="h-9 w-full rounded-lg" />
        </div>
        <TableSkeleton rows={8} />
      </Panel>
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
    <>
      <div className="flex min-h-0 flex-1 flex-col">
        <header className="mb-6">
          <h1 className="text-lg font-semibold text-[var(--ds-text-primary)]">新闻</h1>
          <p className="mt-1 text-sm text-[var(--ds-text-secondary)]">浏览 OpenClaw 入库的新闻条目</p>
        </header>

        <Panel className="flex w-full max-w-[400px] flex-col overflow-hidden p-0">
          <div className="border-b border-[var(--ds-border)] p-3">
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
            <p className="mt-2 text-xs text-[var(--ds-text-secondary)]">共 {items.length} 条</p>
          </div>

          <div className="max-h-[calc(100dvh-260px)] overflow-y-auto">
            {!items.length ? (
              <EmptyState title="暂无新闻" description="OpenClaw 入库后将在此展示" />
            ) : (
              <div className="divide-y divide-[var(--ds-border)]">
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
                      subtitle={n.keyword || undefined}
                      meta={formatCnDateTime(n.published_at || n.created_at)}
                      onClick={() => setActiveId(n.id)}
                      className="min-w-0 flex-1"
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        </Panel>
      </div>

      <Drawer
        open={activeId !== null}
        onClose={() => setActiveId(null)}
        title={active?.title || '新闻详情'}
      >
        {!active ? (
          <DrawerContentSkeleton />
        ) : (
          <div className="flex flex-col gap-4">
            <div className="flex flex-wrap gap-2">
              {active.keyword ? <Badge>{active.keyword}</Badge> : null}
              {active.source_name ? <Badge variant="muted">{active.source_name}</Badge> : null}
            </div>
            <p className="text-sm text-[var(--ds-text-secondary)]">
              {formatCnDateTime(active.published_at || active.created_at)}
            </p>
            {active.summary ? (
              <MarkdownContent className="text-sm">{active.summary}</MarkdownContent>
            ) : null}
            {safeExternalHref(active.source_url) ? (
              <a
                href={safeExternalHref(active.source_url)}
                target="_blank"
                rel="noreferrer"
                className={cn(
                  'inline-flex items-center gap-1 text-sm text-[var(--color-accent)] hover:underline',
                )}
              >
                查看原文 <ExternalLink className="h-3.5 w-3.5" />
              </a>
            ) : null}
          </div>
        )}
      </Drawer>
    </>
  )
}
