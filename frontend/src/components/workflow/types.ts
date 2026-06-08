import type { Monitor } from '../../lib/api'

export type WorkflowModalMode = 'monitor' | 'config' | 'run'

export type SchedulerConfig = {
  job_name: string
  monitor_id: string
  cron_expr?: string
  timezone?: string
  enabled?: boolean
  retry_policy?: string
  notes?: string
  updated_at?: string
}

export type SchedulerRun = {
  job_name?: string
  status?: string
  monitor_id?: string | null
  message?: string
  last_seen_at?: string
  source?: string
}

export type WorkflowModalTarget =
  | { mode: 'monitor'; monitor: Monitor }
  | { mode: 'config'; config: SchedulerConfig }
  | { mode: 'run'; run: SchedulerRun }

export type WorkflowDetailsTab = 'detail' | 'runs' | 'status'
