import type { Monitor } from '../../lib/api'
import { formatCnDateTime } from '../../lib/utils'
import { Badge } from '../ui/Badge'
import {
  Panel,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeaderRow,
  TableCell,
  TableHeaderCell,
} from '../ui/ds'

export function MonitorTaskTable({
  monitors,
  onSelect,
}: {
  monitors: Monitor[]
  onSelect: (monitor: Monitor) => void
}) {
  return (
    <Panel className="overflow-hidden p-0">
      <div className="border-b border-[var(--ds-border)] px-4 py-3">
        <h3 className="text-sm font-semibold text-[var(--ds-text-primary)]">监测任务</h3>
      </div>
      {!monitors.length ? (
        <p className="p-4 text-sm text-[var(--ds-text-secondary)]">暂无监测任务。请通过 OpenClaw Agent 或 API 创建。</p>
      ) : (
        <div className="overflow-x-auto">
          <Table>
            <TableHead>
              <TableHeaderRow>
                <TableHeaderCell>关键词</TableHeaderCell>
                <TableHeaderCell>观测数</TableHeaderCell>
                <TableHeaderCell>最近采集</TableHeaderCell>
                <TableHeaderCell>状态</TableHeaderCell>
              </TableHeaderRow>
            </TableHead>
            <TableBody>
              {monitors.map((m) => (
                <TableRow
                  key={m.monitor_id}
                  data-onboarding="monitor-row"
                  interactive
                  onClick={() => onSelect(m)}
                >
                  <TableCell className="font-medium">{m.keyword || m.monitor_id.slice(0, 8)}</TableCell>
                  <TableCell>{m.observation_count ?? 0}</TableCell>
                  <TableCell className="text-[var(--ds-text-secondary)]">{formatCnDateTime(m.last_captured_at)}</TableCell>
                  <TableCell>
                    <Badge variant={(m.observation_count ?? 0) > 0 ? 'success' : 'warning'}>
                      {(m.observation_count ?? 0) > 0 ? '正常' : '待采集'}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </Panel>
  )
}
