import { useMemo, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Modal } from '../ui/Modal'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import type { Monitor } from '../../lib/api'
import { formatCnDateTime } from '../../lib/utils'
import type { SchedulerConfig, SchedulerRun, WorkflowDetailsTab, WorkflowModalTarget } from './types'

function statusVariant(status?: string): 'success' | 'danger' | 'warning' | 'muted' {
  const s = (status || '').toLowerCase()
  if (s === 'ok' || s === 'success') return 'success'
  if (s === 'error' || s === 'failed') return 'danger'
  if (s === 'running' || s === 'pending') return 'warning'
  return 'muted'
}

function modalTitle(target: WorkflowModalTarget): string {
  if (target.mode === 'monitor') return `监测任务 · ${target.monitor.keyword || '未命名'}`
  if (target.mode === 'config') return `调度配置 · ${target.config.job_name}`
  return `执行记录 · ${target.run.job_name || '-'}`
}

function relatedRuns(
  runs: SchedulerRun[],
  target: WorkflowModalTarget,
): SchedulerRun[] {
  if (target.mode === 'monitor') {
    const id = target.monitor.monitor_id
    return runs.filter((r) => r.monitor_id === id)
  }
  if (target.mode === 'config') {
    const name = target.config.job_name
    return runs.filter((r) => r.job_name === name)
  }
  const name = target.run.job_name
  return runs.filter((r) => r.job_name === name)
}

function DetailRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5 border-b border-[var(--color-border)] py-2 sm:flex-row sm:justify-between">
      <span className="text-xs text-[var(--color-muted)]">{label}</span>
      <span className="text-sm">{value}</span>
    </div>
  )
}

function MonitorDetailTab({ monitor, monitors }: { monitor: Monitor; monitors: Monitor[] }) {
  const linked = monitors.find((m) => m.monitor_id === monitor.monitor_id) || monitor
  return (
    <div className="space-y-3">
      <DetailRow label="Monitor ID" value={<code className="text-xs">{linked.monitor_id}</code>} />
      <DetailRow label="关键词" value={linked.keyword || '—'} />
      <DetailRow label="创建时间" value={formatCnDateTime(linked.created_at)} />
      <DetailRow label="观测数" value={linked.observation_count ?? 0} />
      <DetailRow label="URL 数" value={linked.url_count ?? 0} />
      <DetailRow label="最近采集" value={formatCnDateTime(linked.last_captured_at)} />
      <DetailRow
        label="采集状态"
        value={
          <Badge variant={(linked.observation_count ?? 0) > 0 ? 'success' : 'warning'}>
            {(linked.observation_count ?? 0) > 0 ? '正常' : '待采集'}
          </Badge>
        }
      />
      <Link to={`/app/price-trend?monitor=${linked.monitor_id}`}>
        <Button variant="secondary" className="mt-2 w-full sm:w-auto">
          查看价格趋势
        </Button>
      </Link>
    </div>
  )
}

function ConfigDetailTab({ config, monitors }: { config: SchedulerConfig; monitors: Monitor[] }) {
  const kw = monitors.find((m) => m.monitor_id === config.monitor_id)?.keyword
  return (
    <div className="space-y-3">
      <DetailRow label="任务名" value={config.job_name} />
      <DetailRow label="Monitor ID" value={<code className="text-xs">{config.monitor_id}</code>} />
      <DetailRow label="关键词" value={kw || '—'} />
      <DetailRow label="Cron" value={<code className="text-xs">{config.cron_expr || '—'}</code>} />
      <DetailRow label="时区" value={config.timezone || '—'} />
      <DetailRow
        label="启用"
        value={<Badge variant={config.enabled ? 'success' : 'muted'}>{config.enabled ? '是' : '否'}</Badge>}
      />
      <DetailRow label="重试策略" value={config.retry_policy || '—'} />
      <DetailRow label="备注" value={config.notes || '—'} />
      <DetailRow label="更新于" value={formatCnDateTime(config.updated_at)} />
    </div>
  )
}

function RunDetailTab({ run }: { run: SchedulerRun }) {
  return (
    <div className="space-y-3">
      <DetailRow label="任务名" value={run.job_name || '—'} />
      <DetailRow
        label="状态"
        value={<Badge variant={statusVariant(run.status)}>{run.status || '—'}</Badge>}
      />
      <DetailRow label="Monitor ID" value={run.monitor_id ? <code className="text-xs">{run.monitor_id}</code> : '—'} />
      <DetailRow label="消息" value={run.message || '—'} />
      <DetailRow label="来源" value={run.source || '—'} />
      <DetailRow label="最后上报" value={formatCnDateTime(run.last_seen_at)} />
    </div>
  )
}

function RunsTab({ runs }: { runs: SchedulerRun[] }) {
  if (!runs.length) {
    return <p className="text-sm text-[var(--color-muted)]">暂无关联执行记录</p>
  }
  return (
    <div className="divide-y divide-[var(--color-border)]">
      {runs.slice(0, 30).map((r, i) => (
        <div key={`${r.job_name}-${r.last_seen_at}-${i}`} className="flex flex-col gap-1 py-2 text-sm sm:flex-row sm:items-center sm:justify-between">
          <span className="font-medium">{r.job_name}</span>
          <div className="flex items-center gap-2">
            <Badge variant={statusVariant(r.status)}>{r.status}</Badge>
            <span className="text-xs text-[var(--color-muted)]">{formatCnDateTime(r.last_seen_at)}</span>
          </div>
          {r.message ? <p className="w-full text-xs text-[var(--color-muted)]">{r.message}</p> : null}
        </div>
      ))}
    </div>
  )
}

function StatusTab({
  gatewayOk,
  internalScheduler,
  latestRun,
}: {
  gatewayOk?: boolean
  internalScheduler?: Record<string, unknown>
  latestRun?: SchedulerRun
}) {
  const enabled = Boolean(internalScheduler?.enabled)
  const started = Boolean(internalScheduler?.started)
  return (
    <div className="space-y-3">
      <DetailRow
        label="Gateway"
        value={<Badge variant={gatewayOk ? 'success' : 'danger'}>{gatewayOk ? '在线' : '离线'}</Badge>}
      />
      <DetailRow
        label="内置调度"
        value={
          <Badge variant={enabled && started ? 'success' : 'warning'}>
            {enabled ? (started ? '运行中' : '已启用未启动') : '未启用'}
          </Badge>
        }
      />
      {internalScheduler?.interval_minutes != null ? (
        <DetailRow label="采集间隔" value={`${String(internalScheduler.interval_minutes)} 分钟`} />
      ) : null}
      {latestRun ? (
        <>
          <DetailRow label="最近执行" value={latestRun.job_name || '—'} />
          <DetailRow
            label="执行状态"
            value={<Badge variant={statusVariant(latestRun.status)}>{latestRun.status}</Badge>}
          />
          <DetailRow label="执行消息" value={latestRun.message || '—'} />
          <DetailRow label="执行时间" value={formatCnDateTime(latestRun.last_seen_at)} />
        </>
      ) : (
        <p className="text-sm text-[var(--color-muted)]">暂无最近执行记录</p>
      )}
    </div>
  )
}

const TABS: { id: WorkflowDetailsTab; label: string }[] = [
  { id: 'detail', label: '任务详情' },
  { id: 'runs', label: '最近执行' },
  { id: 'status', label: '执行状态' },
]

export function WorkflowDetailsModal({
  target,
  onClose,
  allRuns,
  monitors,
  gatewayOk,
  internalScheduler,
}: {
  target: WorkflowModalTarget | null
  onClose: () => void
  allRuns: SchedulerRun[]
  monitors: Monitor[]
  gatewayOk?: boolean
  internalScheduler?: Record<string, unknown>
}) {
  const [tab, setTab] = useState<WorkflowDetailsTab>('detail')

  const runs = useMemo(() => (target ? relatedRuns(allRuns, target) : []), [allRuns, target])
  const latestRun = runs[0] || allRuns[0]

  if (!target) return null

  return (
    <Modal open={!!target} onClose={onClose} title={modalTitle(target)} className="sm:max-w-xl">
      <div className="mb-4 flex gap-1 border-b border-[var(--color-border)]">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
              tab === t.id
                ? 'border-[var(--color-accent)] text-[var(--color-accent)]'
                : 'border-transparent text-[var(--color-muted)] hover:text-[var(--color-text)]'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'detail' && target.mode === 'monitor' && (
        <MonitorDetailTab monitor={target.monitor} monitors={monitors} />
      )}
      {tab === 'detail' && target.mode === 'config' && (
        <ConfigDetailTab config={target.config} monitors={monitors} />
      )}
      {tab === 'detail' && target.mode === 'run' && <RunDetailTab run={target.run} />}
      {tab === 'runs' && <RunsTab runs={runs} />}
      {tab === 'status' && (
        <StatusTab gatewayOk={gatewayOk} internalScheduler={internalScheduler} latestRun={latestRun} />
      )}
    </Modal>
  )
}
