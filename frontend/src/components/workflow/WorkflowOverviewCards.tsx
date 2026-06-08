import { Card, CardContent } from '../ui/Card'
import { Badge } from '../ui/Badge'
import type { WorkOverview } from '../../lib/api'
import type { SchedulerConfig } from './types'

export function WorkflowOverviewCards({
  gatewayOk,
  overview,
  configCount,
}: {
  gatewayOk?: boolean
  overview?: WorkOverview
  configCount: number
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardContent className="p-4">
          <p className="text-xs text-[var(--color-muted)]">Gateway</p>
          <Badge variant={gatewayOk ? 'success' : 'danger'} className="mt-1">
            {gatewayOk ? '在线' : '离线'}
          </Badge>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <p className="text-xs text-[var(--color-muted)]">报告数</p>
          <p className="text-xl font-semibold">{overview?.reports?.published_count ?? 0}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <p className="text-xs text-[var(--color-muted)]">监测任务</p>
          <p className="text-xl font-semibold">{overview?.price_monitoring?.monitor_count ?? 0}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <p className="text-xs text-[var(--color-muted)]">外部调度</p>
          <p className="text-xl font-semibold">{configCount}</p>
        </CardContent>
      </Card>
    </div>
  )
}

export type { SchedulerConfig }
