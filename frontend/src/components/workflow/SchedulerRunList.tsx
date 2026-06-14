import { formatCnDateTime } from '../../lib/utils'
import { Badge } from '../ui/Badge'
import { Panel } from '../ui/ds'
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
    <Panel className="overflow-hidden p-0">
      <div className="border-b border-[var(--ds-border)] px-4 py-3">
        <h3 className="text-sm font-semibold text-[var(--ds-text-primary)]">最近调度运行</h3>
      </div>
      {!runs.length ? (
        <p className="p-4 text-sm text-[var(--ds-text-secondary)]">暂无运行记录</p>
      ) : (
        <div className="divide-y divide-[var(--ds-border)]">
          {runs.slice(0, 20).map((r, i) => (
            <button
              key={`${r.job_name}-${r.last_seen_at}-${i}`}
              type="button"
              data-onboarding="scheduler-run"
              className="flex w-full flex-col gap-1 px-4 py-2.5 text-left text-sm transition-colors duration-[var(--ds-duration-fast)] hover:bg-[var(--ds-row-hover)] active:bg-[var(--ds-row-hover-active)] sm:flex-row sm:items-center sm:justify-between"
              onClick={() => onSelect(r)}
            >
              <span className="font-medium">{String(r.job_name || '-')}</span>
              <div className="flex items-center gap-2">
                <Badge variant={statusVariant(String(r.status))}>{String(r.status)}</Badge>
                <span className="text-xs text-[var(--ds-text-secondary)]">{formatCnDateTime(String(r.last_seen_at || ''))}</span>
              </div>
            </button>
          ))}
        </div>
      )}
    </Panel>
  )
}
