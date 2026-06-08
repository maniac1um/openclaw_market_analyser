import { formatCnDateTime } from '../../lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'
import { Badge } from '../ui/Badge'
import type { SchedulerRun } from './types'

function statusVariant(status?: string): 'success' | 'danger' | 'warning' | 'muted' {
  const s = (status || '').toLowerCase()
  if (s === 'ok' || s === 'success') return 'success'
  if (s === 'error' || s === 'failed') return 'danger'
  if (s === 'running' || s === 'pending') return 'warning'
  return 'muted'
}

export function SchedulerRunList({
  runs,
  onSelect,
}: {
  runs: SchedulerRun[]
  onSelect: (run: SchedulerRun) => void
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>最近调度运行</CardTitle>
      </CardHeader>
      <CardContent className="divide-y divide-[var(--color-border)] p-0">
        {!runs.length ? (
          <p className="p-4 text-sm text-[var(--color-muted)]">暂无运行记录</p>
        ) : (
          runs.slice(0, 20).map((r, i) => (
            <button
              key={`${r.job_name}-${r.last_seen_at}-${i}`}
              type="button"
              data-onboarding="scheduler-run"
              className="flex w-full flex-col gap-1 px-4 py-2 text-left text-sm transition-colors hover:bg-[var(--color-bg)] sm:flex-row sm:items-center sm:justify-between"
              onClick={() => onSelect(r)}
            >
              <span className="font-medium">{String(r.job_name || '-')}</span>
              <div className="flex items-center gap-2">
                <Badge variant={statusVariant(String(r.status))}>{String(r.status)}</Badge>
                <span className="text-xs text-[var(--color-muted)]">{formatCnDateTime(String(r.last_seen_at || ''))}</span>
              </div>
            </button>
          ))
        )}
      </CardContent>
    </Card>
  )
}
