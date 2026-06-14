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
import type { SchedulerConfig } from './types'

export function SchedulerConfigTable({
  configs,
  onSelect,
}: {
  configs: SchedulerConfig[]
  onSelect: (config: SchedulerConfig) => void
}) {
  return (
    <Panel className="overflow-hidden p-0">
      <div className="border-b border-[var(--ds-border)] px-4 py-3">
        <h3 className="text-sm font-semibold text-[var(--ds-text-primary)]">外部调度配置</h3>
      </div>
      {!configs.length ? (
        <p className="p-4 text-sm text-[var(--ds-text-secondary)]">暂无外部调度配置</p>
      ) : (
        <div className="overflow-x-auto">
          <Table>
            <TableHead>
              <TableHeaderRow>
                <TableHeaderCell>任务名</TableHeaderCell>
                <TableHeaderCell>Cron</TableHeaderCell>
                <TableHeaderCell>状态</TableHeaderCell>
                <TableHeaderCell>更新于</TableHeaderCell>
              </TableHeaderRow>
            </TableHead>
            <TableBody>
              {configs.map((c) => (
                <TableRow key={c.job_name} interactive onClick={() => onSelect(c)}>
                  <TableCell className="font-medium">{c.job_name}</TableCell>
                  <TableCell className="font-mono text-xs">{c.cron_expr || '—'}</TableCell>
                  <TableCell>
                    <Badge variant={c.enabled ? 'success' : 'muted'}>{c.enabled ? '启用' : '停用'}</Badge>
                  </TableCell>
                  <TableCell className="text-[var(--ds-text-secondary)]">{formatCnDateTime(c.updated_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </Panel>
  )
}
