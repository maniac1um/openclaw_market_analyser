import { DataRow } from '../../components/ui/ds'
import { ChartSkeleton } from '../../components/ui/ds/Skeleton'
import { MarkdownContent } from '../../components/markdown/MarkdownContent'
import { PriceTrendChart } from '../../components/charts/PriceTrendChart'
import type { ReportDetail } from '../../lib/api'
import { safeExternalHref } from '../../lib/urlSafety'
import { formatCnDateTime } from '../../lib/utils'
import { useReportTrendObservations } from './useReportTrendObservations'

const TREND_CHART_HEIGHT = 320

export function ReportDetailBody({ report }: { report: ReportDetail }) {
  const items = report.items || []
  const { observations, loading: trendLoading, show: showTrend } = useReportTrendObservations(report)

  return (
    <div className="flex flex-col">
      <section className="border-t border-[var(--ds-border)] py-8">
        <MarkdownContent>{report.report_markdown || report.analysis || '暂无分析内容'}</MarkdownContent>
      </section>

      {showTrend ? (
        <section className="border-t border-[var(--ds-border)] py-8">
          <h2 className="mb-4 text-sm font-semibold text-[var(--ds-text-primary)]">价格趋势</h2>
          <div className="border border-[var(--ds-border)]">
            {trendLoading ? (
              <ChartSkeleton height={TREND_CHART_HEIGHT} />
            ) : (
              <PriceTrendChart observations={observations} height={TREND_CHART_HEIGHT} />
            )}
          </div>
        </section>
      ) : null}

      {items.length > 0 ? (
        <section className="border-t border-[var(--ds-border)] py-8">
          <header className="mb-4 flex items-baseline justify-between gap-4">
            <h2 className="text-sm font-semibold text-[var(--ds-text-primary)]">相关新闻</h2>
            <span className="text-xs text-[var(--ds-text-secondary)]">共 {items.length} 条</span>
          </header>
          <div className="divide-y divide-[var(--ds-border)] border border-[var(--ds-border)]">
            {items.map((item, i) => {
              const href = safeExternalHref(item.url)
              return (
                <DataRow
                  key={`${item.url}-${i}`}
                  title={item.title || '无标题'}
                  subtitle={item.source || item.summary?.slice(0, 80)}
                  meta={formatCnDateTime(item.published_at)}
                  onClick={href ? () => window.open(href, '_blank', 'noopener,noreferrer') : undefined}
                />
              )
            })}
          </div>
        </section>
      ) : null}
    </div>
  )
}
