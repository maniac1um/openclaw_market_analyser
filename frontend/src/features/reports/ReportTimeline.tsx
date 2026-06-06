import type { NewsItem } from '../../lib/api'
import { safeExternalHref } from '../../lib/urlSafety'
import { formatCnDateTime } from '../../lib/utils'

export function ReportTimeline({ items }: { items: NewsItem[] }) {
  const sorted = [...items].sort((a, b) => {
    const ta = a.published_at ? new Date(a.published_at).getTime() : 0
    const tb = b.published_at ? new Date(b.published_at).getTime() : 0
    return tb - ta
  })

  if (!sorted.length) {
    return <p className="text-sm text-[var(--color-muted)]">暂无时间线数据</p>
  }

  return (
    <ol className="relative space-y-0 border-l border-[var(--color-border)] pl-6">
      {sorted.map((item, i) => (
        <li key={`${item.url || item.title}-${i}`} className="relative pb-6 last:pb-0">
          <span className="absolute -left-[25px] top-1.5 h-2.5 w-2.5 rounded-full border-2 border-[var(--color-surface)] bg-[var(--color-accent)]" />
          <time className="text-xs text-[var(--color-muted)]">{formatCnDateTime(item.published_at)}</time>
          <p className="mt-1 text-sm font-medium">{item.title || '未命名'}</p>
          <p className="text-xs text-[var(--color-muted)]">{item.source}</p>
          {item.summary && <p className="mt-1 text-sm text-[var(--color-muted)] line-clamp-2">{item.summary}</p>}
          {safeExternalHref(item.url) && (
            <a href={safeExternalHref(item.url)} target="_blank" rel="noreferrer" className="mt-1 inline-block text-xs text-[var(--color-accent)] hover:underline">
              查看原文
            </a>
          )}
        </li>
      ))}
    </ol>
  )
}
