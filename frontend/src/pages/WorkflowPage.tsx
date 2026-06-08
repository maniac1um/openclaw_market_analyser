import { useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { api } from '../lib/api'
import { Skeleton, ErrorBanner } from '../components/ui/States'
import { WorkflowOverviewCards } from '../components/workflow/WorkflowOverviewCards'
import { MonitorTaskTable } from '../components/workflow/MonitorTaskTable'
import { SchedulerConfigTable } from '../components/workflow/SchedulerConfigTable'
import { SchedulerRunList } from '../components/workflow/SchedulerRunList'
import { WorkflowDiagnosticsPanel } from '../components/workflow/WorkflowDiagnosticsPanel'
import { WorkflowDetailsModal } from '../components/workflow/WorkflowDetailsModal'
import type { SchedulerConfig, SchedulerRun, WorkflowModalTarget } from '../components/workflow/types'

export function WorkflowPage() {
  const [modalTarget, setModalTarget] = useState<WorkflowModalTarget | null>(null)

  const stateQuery = useQuery({ queryKey: ['workflow'], queryFn: api.workflowState, refetchInterval: 30_000 })
  const monitorsQuery = useQuery({ queryKey: ['monitors'], queryFn: api.listMonitors })
  const diagQuery = useQuery({ queryKey: ['diagnostics'], queryFn: api.workflowDiagnostics })

  const configs = useMemo(
    () => (stateQuery.data?.external_scheduler_configs || []) as SchedulerConfig[],
    [stateQuery.data?.external_scheduler_configs],
  )
  const runs = useMemo(
    () => (stateQuery.data?.external_scheduler_runs || []) as SchedulerRun[],
    [stateQuery.data?.external_scheduler_runs],
  )
  const monitors = useMemo(() => {
    const fromApi = monitorsQuery.data || []
    if (fromApi.length) return fromApi
    return stateQuery.data?.overview?.price_monitoring?.recent || []
  }, [monitorsQuery.data, stateQuery.data?.overview?.price_monitoring?.recent])

  if (stateQuery.isLoading) return <Skeleton className="h-[500px]" />
  if (stateQuery.isError) {
    return <ErrorBanner message={(stateQuery.error as Error).message} onRetry={() => stateQuery.refetch()} />
  }

  const overview = stateQuery.data?.overview
  const gateway = stateQuery.data?.gateway
  const checks =
    ((diagQuery.data as { checks?: { label: string; ok: boolean; detail: string; severity: string }[] })?.checks ||
      [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">工作流控制台</h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">查看监测任务、调度配置与执行记录</p>
      </div>

      <WorkflowOverviewCards
        gatewayOk={gateway?.ok}
        overview={overview}
        configCount={configs.length}
      />

      <MonitorTaskTable monitors={monitors} onSelect={(monitor) => setModalTarget({ mode: 'monitor', monitor })} />

      <SchedulerConfigTable configs={configs} onSelect={(config) => setModalTarget({ mode: 'config', config })} />

      <SchedulerRunList runs={runs} onSelect={(run) => setModalTarget({ mode: 'run', run })} />

      <WorkflowDiagnosticsPanel checks={checks} loading={diagQuery.isLoading} />

      <WorkflowDetailsModal
        target={modalTarget}
        onClose={() => setModalTarget(null)}
        allRuns={runs}
        monitors={monitors}
        gatewayOk={gateway?.ok}
        internalScheduler={stateQuery.data?.internal_scheduler}
      />
    </div>
  )
}
