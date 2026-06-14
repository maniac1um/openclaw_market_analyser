import { Panel, Section, StatStrip, StatStripItem, DataRow, StatStripSkeleton, TableSkeleton, Skeleton } from '../../components/ui/ds'
import { MarkdownContent } from '../../components/markdown/MarkdownContent'
import type { ReportDetail } from '../../lib/api'
import { deriveInsights, riskLabel, sentimentLabel } from '../../lib/insights'
import { safeExternalHref } from '../../lib/urlSafety'
import { formatCnDateTime } from '../../lib/utils'

export function ReportDrawerContent({ report }: { report: ReportDetail }) {
  const insights = deriveInsights(report)
  const items = (report.items || []).slice(0, 6)

  const sentiment = insights.sentiment ? sentimentLabel[insights.sentiment] || insights.sentiment : '—'
  const risk = insights.risk_level ? riskLabel[insights.risk_level] || insights.risk_level : '—'
  const confidence = insights.confidence || '—'
  const forecast = insights.forecast || '—'

  return (
    <div className="flex flex-col gap-8">
      <StatStrip>
        <StatStripItem label="情绪分析" value={sentiment} />
        <StatStripItem label="风险等级" value={risk} />
        <StatStripItem label="市场影响" value={forecast} />
        <StatStripItem label="置信度" value={confidence} />
      </StatStrip>

      <Section title="AI 分析">
        <MarkdownContent className="text-sm">{report.report_markdown || report.analysis || '暂无分析内容'}</MarkdownContent>
      </Section>

      {items.length > 0 ? (
        <Section title="相关新闻" description={`共 ${items.length} 条`}>
          <Panel className="divide-y divide-[var(--ds-border)] p-0">
            {items.map((item, i) => {
              const href = safeExternalHref(item.url)
              return (
                <DataRow
                  key={`${item.url}-${i}`}
                  title={item.title || '无标题'}
                  subtitle={item.source || item.summary?.slice(0, 60)}
                  meta={formatCnDateTime(item.published_at)}
                  onClick={href ? () => window.open(href, '_blank', 'noopener,noreferrer') : undefined}
                />
              )
            })}
          </Panel>
        </Section>
      ) : null}
    </div>
  )
}

export function ReportDrawerSkeleton() {
  return (
    <div className="flex flex-col gap-8">
      <StatStripSkeleton items={4} />
      <div className="space-y-3">
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-[92%]" />
        <Skeleton className="h-4 w-[85%]" />
        <Skeleton className="h-4 w-[78%]" />
      </div>
      <Section title="相关新闻">
        <Panel className="p-0">
          <TableSkeleton rows={4} />
        </Panel>
      </Section>
    </div>
  )
}
