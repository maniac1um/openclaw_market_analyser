import { useEffect, useState } from 'react'
import { ReportDetailView } from '../reports/ReportDetail'
import { Badge } from '../../components/ui/Badge'
import { Skeleton } from '../../components/ui/States'
import { DEMO_REPORT_SLUGS, loadDemoReport } from './demoData'
import type { ReportDetail } from '../../lib/api'
import { cn } from '../../lib/utils'

const SLUG_LABELS: Record<(typeof DEMO_REPORT_SLUGS)[number], string> = {
  'nebula-battery': '星云电池',
  'stellar-panel': '曜光组件',
}

export function DemoReportPreview() {
  const [active, setActive] = useState<(typeof DEMO_REPORT_SLUGS)[number]>('nebula-battery')
  const [report, setReport] = useState<ReportDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    void loadDemoReport(active).then((data) => {
      if (!cancelled) {
        setReport(data)
        setLoading(false)
      }
    })
    return () => {
      cancelled = true
    }
  }, [active])

  return (
    <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
      <div className="flex flex-col gap-2">
        {DEMO_REPORT_SLUGS.map((slug) => (
          <button
            key={slug}
            type="button"
            onClick={() => setActive(slug)}
            className={cn(
              'rounded-lg border px-3 py-3 text-left text-sm transition-colors',
              active === slug
                ? 'border-[var(--color-accent)] bg-[var(--color-accent-soft)] font-medium text-[var(--color-accent)]'
                : 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-muted)] hover:border-[var(--color-accent)]/40',
            )}
          >
            {SLUG_LABELS[slug]}
          </button>
        ))}
        <Badge variant="muted" className="mt-2 w-fit">
          虚构示例
        </Badge>
      </div>
      <div className="min-w-0 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 sm:p-6">
        {loading || !report ? <Skeleton className="h-[480px]" /> : <ReportDetailView report={report} />}
      </div>
    </div>
  )
}
