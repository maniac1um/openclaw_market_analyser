import { ExternalLink } from 'lucide-react'
import { Badge } from '../../components/ui/Badge'
import { MarkdownContent } from '../../components/markdown/MarkdownContent'
import { safeExternalHref } from '../../lib/urlSafety'
import { cn, formatCnDateTime } from '../../lib/utils'
import type { NewsLibraryItem } from '../../lib/api'

export function NewsArticleContent({ item }: { item: NewsLibraryItem }) {
  const sourceHref = safeExternalHref(item.source_url)
  const published = formatCnDateTime(item.published_at || item.created_at)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2 text-sm text-[var(--text-secondary)]">
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
            'inline-flex items-center gap-1 text-sm text-[var(--color-accent)] hover:underline',
          )}
        >
          查看原文 <ExternalLink className="h-3.5 w-3.5" />
        </a>
      ) : null}
      {item.summary ? (
        <div className="border-t border-[var(--border)] pt-8">
          <MarkdownContent>{item.summary}</MarkdownContent>
        </div>
      ) : (
        <p className="border-t border-[var(--border)] pt-8 text-sm text-[var(--text-secondary)]">暂无正文内容</p>
      )}
    </div>
  )
}

function truncate(text: string | undefined, max = 80) {
  if (!text) return undefined
  const t = text.trim()
  if (t.length <= max) return t
  return `${t.slice(0, max)}…`
}

export function newsRowSubtitle(item: NewsLibraryItem) {
  return truncate(item.summary) || item.keyword || undefined
}
