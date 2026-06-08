import type { Monitor } from '../../lib/api'
import { formatCnDateTime } from '../../lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'
import { Badge } from '../ui/Badge'

export function MonitorTaskTable({
  monitors,
  onSelect,
}: {
  monitors: Monitor[]
  onSelect: (monitor: Monitor) => void
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>监测任务</CardTitle>
      </CardHeader>
      <CardContent className="overflow-x-auto p-0">
        {!monitors.length ? (
          <p className="p-4 text-sm text-[var(--color-muted)]">暂无监测任务。请通过 OpenClaw Agent 或 API 创建。</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)] text-left text-xs text-[var(--color-muted)]">
                <th className="px-4 py-2">关键词</th>
                <th className="px-4 py-2">观测数</th>
                <th className="px-4 py-2">最近采集</th>
                <th className="px-4 py-2">状态</th>
              </tr>
            </thead>
            <tbody>
              {monitors.map((m) => (
                <tr
                  key={m.monitor_id}
                  data-onboarding="monitor-row"
                  className="cursor-pointer border-b border-[var(--color-border)] transition-colors hover:bg-[var(--color-bg)]"
                  onClick={() => onSelect(m)}
                >
                  <td className="px-4 py-2 font-medium">{m.keyword || m.monitor_id.slice(0, 8)}</td>
                  <td className="px-4 py-2">{m.observation_count ?? 0}</td>
                  <td className="px-4 py-2 text-[var(--color-muted)]">{formatCnDateTime(m.last_captured_at)}</td>
                  <td className="px-4 py-2">
                    <Badge variant={(m.observation_count ?? 0) > 0 ? 'success' : 'warning'}>
                      {(m.observation_count ?? 0) > 0 ? '正常' : '待采集'}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </CardContent>
    </Card>
  )
}
