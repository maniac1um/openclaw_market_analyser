import { Link } from 'react-router-dom'
import { riskLabel } from '../../../lib/insights'

type ReportSummaryMessageProps = {
  reportId: string
  trend?: string
  risk?: string
  title?: string
}

function formatRisk(value?: string): string | undefined {
  if (!value) return undefined
  return riskLabel[value] || value
}

export function ReportSummaryMessage({ reportId, trend, risk, title }: ReportSummaryMessageProps) {
  const riskText = formatRisk(risk) || risk

  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]/40 px-4 py-3">
      <p className="text-sm font-medium text-[var(--ds-text-primary)]">{title || '📊 分析完成'}</p>
      {trend ? (
        <p className="mt-1.5 text-sm text-[var(--ds-text-secondary)]">趋势：{trend}</p>
      ) : null}
      {riskText ? <p className="text-sm text-[var(--ds-text-secondary)]">风险：{riskText}</p> : null}
      <Link
        to={`/app/reports/${reportId}`}
        className="mt-2 inline-block text-sm font-medium text-[var(--color-accent)] transition-opacity hover:opacity-80"
      >
        查看完整报告 →
      </Link>
    </div>
  )
}
