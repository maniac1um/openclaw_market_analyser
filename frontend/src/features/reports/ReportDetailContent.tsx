import { ReportDetailBody } from './ReportDetailBody'
import type { ReportDetail } from '../../lib/api'
import { formatCnDateTime } from '../../lib/utils'

function formatReportTime(report: { time_range?: { start?: string; end?: string }; generated_at?: string }) {
  if (report.time_range?.start || report.time_range?.end) {
    return `${formatCnDateTime(report.time_range?.start)} — ${formatCnDateTime(report.time_range?.end)}`
  }
  return formatCnDateTime(report.generated_at)
}

function formatSources(sources?: string[]) {
  if (!sources?.length) return '—'
  return sources.join('、')
}

export function ReportDetailContent({ report }: { report: ReportDetail }) {
  return (
    <div className="flex flex-col" data-onboarding="report-detail">
      <dl className="mb-8 flex flex-wrap gap-x-8 gap-y-2 text-sm">
        <div className="flex gap-2">
          <dt className="text-[var(--text-secondary)]">关键词</dt>
          <dd className="text-primary">{report.keyword || '—'}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="text-[var(--text-secondary)]">时间</dt>
          <dd className="text-primary">{formatReportTime(report)}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="text-[var(--text-secondary)]">数据源</dt>
          <dd className="text-primary">{formatSources(report.sources)}</dd>
        </div>
      </dl>
      <ReportDetailBody report={report} />
    </div>
  )
}

export function reportRowSubtitle(report: { keyword?: string }) {
  return report.keyword || undefined
}
