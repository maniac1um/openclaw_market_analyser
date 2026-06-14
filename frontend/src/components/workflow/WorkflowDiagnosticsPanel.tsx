import { Stethoscope } from 'lucide-react'
import { Badge } from '../ui/Badge'
import { Panel, Skeleton } from '../ui/ds'

type Check = { label: string; ok: boolean; detail: string; severity: string }

export function WorkflowDiagnosticsPanel({
  checks,
  loading,
}: {
  checks: Check[]
  loading: boolean
}) {
  return (
    <Panel className="overflow-hidden p-0">
      <div className="flex items-center gap-2 border-b border-[var(--ds-border)] px-4 py-3">
        <Stethoscope className="h-4 w-4 text-[var(--ds-text-secondary)]" />
        <h3 className="text-sm font-semibold text-[var(--ds-text-primary)]">系统诊断</h3>
      </div>
      <div className="space-y-2 p-4">
        {loading ? (
          <>
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </>
        ) : (
          checks.map((c) => (
            <div
              key={c.label}
              className="flex flex-col gap-2 rounded-lg border border-[var(--ds-border)] px-3 py-2.5 text-sm transition-[border-color] duration-[var(--ds-duration-fast)] hover:border-[var(--ds-border-hover)] sm:flex-row sm:items-start sm:justify-between"
            >
              <span>{c.label}</span>
              <Badge variant={c.ok ? 'success' : c.severity === 'error' ? 'danger' : 'warning'}>
                {c.detail}
              </Badge>
            </div>
          ))
        )}
      </div>
    </Panel>
  )
}
