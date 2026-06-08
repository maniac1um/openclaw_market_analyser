import { Stethoscope } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { Skeleton } from '../ui/States'

type Check = { label: string; ok: boolean; detail: string; severity: string }

export function WorkflowDiagnosticsPanel({
  checks,
  loading,
}: {
  checks: Check[]
  loading: boolean
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2">
        <Stethoscope className="h-4 w-4" />
        <CardTitle>系统诊断</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {loading ? (
          <Skeleton className="h-20" />
        ) : (
          checks.map((c) => (
            <div
              key={c.label}
              className="flex flex-col gap-2 rounded-md border border-[var(--color-border)] px-3 py-2 text-sm sm:flex-row sm:items-start sm:justify-between"
            >
              <span>{c.label}</span>
              <Badge variant={c.ok ? 'success' : c.severity === 'error' ? 'danger' : 'warning'}>
                {c.detail}
              </Badge>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  )
}
