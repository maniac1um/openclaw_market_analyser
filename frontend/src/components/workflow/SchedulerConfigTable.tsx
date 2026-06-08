import { formatCnDateTime } from '../../lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'
import { Badge } from '../ui/Badge'
import type { SchedulerConfig } from './types'

export function SchedulerConfigTable({
  configs,
  onSelect,
}: {
  configs: SchedulerConfig[]
  onSelect: (config: SchedulerConfig) => void
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>外部调度配置</CardTitle>
      </CardHeader>
      <CardContent className="overflow-x-auto p-0">
        {!configs.length ? (
          <p className="p-4 text-sm text-[var(--color-muted)]">暂无外部调度配置</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)] text-left text-xs text-[var(--color-muted)]">
                <th className="px-4 py-2">任务名</th>
                <th className="px-4 py-2">Cron</th>
                <th className="px-4 py-2">状态</th>
                <th className="px-4 py-2">更新于</th>
              </tr>
            </thead>
            <tbody>
              {configs.map((c) => (
                <tr
                  key={c.job_name}
                  className="cursor-pointer border-b border-[var(--color-border)] transition-colors hover:bg-[var(--color-bg)]"
                  onClick={() => onSelect(c)}
                >
                  <td className="px-4 py-2 font-medium">{c.job_name}</td>
                  <td className="px-4 py-2 font-mono text-xs">{c.cron_expr || '—'}</td>
                  <td className="px-4 py-2">
                    <Badge variant={c.enabled ? 'success' : 'muted'}>{c.enabled ? '启用' : '停用'}</Badge>
                  </td>
                  <td className="px-4 py-2 text-[var(--color-muted)]">{formatCnDateTime(c.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </CardContent>
    </Card>
  )
}
