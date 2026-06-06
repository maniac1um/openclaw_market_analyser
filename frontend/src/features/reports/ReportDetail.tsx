import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import type { ReportDetail as ReportDetailType } from '../../lib/api'
import { deriveInsights } from '../../lib/insights'
import { safeExternalHref, markdownUrlTransform } from '../../lib/urlSafety'
import { formatCnDateTime } from '../../lib/utils'
import { InsightGrid } from './InsightGrid'
import { ReportTimeline } from './ReportTimeline'

export function ReportDetailView({ report }: { report: ReportDetailType }) {
  const insights = deriveInsights(report)
  const items = report.items || []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{report.title || '未命名报告'}</h1>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {report.keyword && <Badge>{report.keyword}</Badge>}
          <span className="text-sm text-[var(--color-muted)]">
            {formatCnDateTime(report.time_range?.start)} — {formatCnDateTime(report.time_range?.end)}
          </span>
          <span className="text-sm text-[var(--color-muted)]">生成于 {formatCnDateTime(report.generated_at)}</span>
        </div>
      </div>

      <InsightGrid insights={insights} />

      {items.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>新闻摘要</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            {items.slice(0, 6).map((item, i) => (
              <div key={`${item.url}-${i}`} className="rounded-lg border border-[var(--color-border)] p-3">
                <p className="text-sm font-medium leading-snug">{item.title}</p>
                <p className="mt-1 text-xs text-[var(--color-muted)]">{item.source}</p>
                {item.summary && <p className="mt-2 text-sm text-[var(--color-muted)] line-clamp-3">{item.summary}</p>}
                {safeExternalHref(item.url) && (
                  <a href={safeExternalHref(item.url)} target="_blank" rel="noreferrer" className="mt-2 inline-block text-xs text-[var(--color-accent)]">
                    阅读原文 →
                  </a>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>AI 结论</CardTitle>
        </CardHeader>
        <CardContent className="prose-report text-sm">
          <ReactMarkdown remarkPlugins={[remarkGfm]} urlTransform={markdownUrlTransform}>
            {report.analysis || '暂无分析内容'}
          </ReactMarkdown>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>事件时间线</CardTitle>
        </CardHeader>
        <CardContent>
          <ReportTimeline items={items} />
        </CardContent>
      </Card>

      {(report.sources || []).length > 0 && (
        <div className="flex flex-wrap gap-2">
          {(report.sources || []).map((s) => (
            <Badge key={s} variant="muted">
              {s}
            </Badge>
          ))}
        </div>
      )}
    </div>
  )
}
