import { useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../lib/api'
import { ErrorBanner, EmptyState } from '../components/ui/States'
import {
  StatStrip,
  StatStripItem,
  DataRow,
  StatStripSkeleton,
  ChartSkeleton,
  TableSkeleton,
  Skeleton,
} from '../components/ui/ds'
import { formatCnDateTime, cn } from '../lib/utils'
import { ChartTimeRangePicker } from '../components/charts/ChartTimeRangePicker'
import { PriceTrendChart } from '../components/charts/PriceTrendChart'
import {
  useFilteredObservations,
  computePriceVolatility,
} from '../components/charts/usePriceSeries'
import type { ChartObservation, TimeRange } from '../components/charts/types'
import { TIME_RANGE_MS } from '../components/charts/types'

const CHART_HEIGHT = 400

function PriceTrendSkeleton() {
  return (
    <div className="flex flex-col gap-8">
      <StatStripSkeleton items={3} />
      <ChartSkeleton height={CHART_HEIGHT} />
      <Skeleton className="h-8 w-64" />
      <TableSkeleton rows={6} />
    </div>
  )
}

function formatDelta(delta: number | null | undefined): string {
  if (delta == null) return '—'
  return (delta >= 0 ? '+' : '') + delta.toFixed(2)
}

function latestCapturedAt(observations: ChartObservation[]): string | undefined {
  if (!observations.length) return undefined
  return observations.reduce((latest, o) =>
    new Date(o.captured_at).getTime() > new Date(latest).getTime() ? o.captured_at : latest,
  observations[0].captured_at)
}

export function PriceTrendPage() {
  const [searchParams] = useSearchParams()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [timeRange, setTimeRange] = useState<TimeRange>('30d')

  const monitorsQuery = useQuery({ queryKey: ['monitors'], queryFn: api.listMonitors })

  const monitorId = useMemo(() => {
    const list = monitorsQuery.data || []
    if (!list.length) return ''
    if (selectedId && list.some((m) => m.monitor_id === selectedId)) return selectedId
    const fromUrl = searchParams.get('monitor')
    if (fromUrl && list.some((m) => m.monitor_id === fromUrl)) return fromUrl
    return list[0].monitor_id
  }, [monitorsQuery.data, selectedId, searchParams])

  const obsQuery = useQuery({
    queryKey: ['observations', monitorId],
    queryFn: () => api.observations(monitorId, 1000),
    enabled: !!monitorId,
  })

  const allObservations = useMemo<ChartObservation[]>(() => {
    return (obsQuery.data?.rows || [])
      .filter((r) => r.captured_at != null && r.price != null)
      .map((r) => ({
        captured_at: r.captured_at!,
        price: r.price!,
        item_name: r.item_name,
      }))
  }, [obsQuery.data?.rows])

  const filteredObservations = useFilteredObservations(allObservations, timeRange)
  const activeMonitor = monitorsQuery.data?.find((m) => m.monitor_id === monitorId)
  const truncated = (activeMonitor?.observation_count ?? 0) > 1000
  const volatility = useMemo(() => computePriceVolatility(filteredObservations), [filteredObservations])
  const updatedAt = latestCapturedAt(filteredObservations) ?? activeMonitor?.last_captured_at

  const tableRows = useMemo(() => {
    const rows = obsQuery.data?.rows || []
    const ms = TIME_RANGE_MS[timeRange]
    return [...rows]
      .filter((r) => {
        if (r.captured_at == null || r.price == null) return false
        if (ms === null) return true
        return new Date(r.captured_at).getTime() >= Date.now() - ms
      })
      .reverse()
  }, [obsQuery.data?.rows, timeRange])

  if (monitorsQuery.isLoading) return <PriceTrendSkeleton />

  if (!monitorsQuery.data?.length) {
    return (
      <EmptyState
        title="暂无监测任务"
        description="监测任务由 OpenClaw Agent 或 API 创建。请配置 Agent 后刷新本页。"
      />
    )
  }

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-wrap items-center gap-4">
        <h1 className="text-lg font-semibold text-[var(--ds-text-primary)]">价格趋势</h1>
        <select
          value={monitorId}
          onChange={(e) => setSelectedId(e.target.value)}
          className="rounded-lg border border-[var(--ds-border)] bg-[var(--ds-bg-panel)] px-3 py-1.5 text-sm text-[var(--ds-text-primary)] outline-none transition-colors focus:border-[var(--color-accent)]"
        >
          {(monitorsQuery.data || []).map((m) => (
            <option key={m.monitor_id} value={m.monitor_id}>
              {m.keyword} ({m.observation_count} 条)
            </option>
          ))}
        </select>
      </header>

      <StatStrip>
        <StatStripItem label="观测数" value={filteredObservations.length} />
        <StatStripItem label="更新时间" value={formatCnDateTime(updatedAt)} />
        <StatStripItem label="波动" value={volatility} />
      </StatStrip>

      {truncated ? (
        <p className="text-xs text-[var(--color-warning)]">
          观测总数超过 1000 条，图表仅展示最近 1000 条记录
        </p>
      ) : null}

      {obsQuery.isLoading ? (
        <ChartSkeleton height={CHART_HEIGHT} />
      ) : obsQuery.isError ? (
        <ErrorBanner message={(obsQuery.error as Error).message} onRetry={() => obsQuery.refetch()} />
      ) : (
        <PriceTrendChart observations={filteredObservations} height={CHART_HEIGHT} />
      )}

      <ChartTimeRangePicker value={timeRange} onChange={setTimeRange} />

      {obsQuery.isLoading ? (
        <TableSkeleton rows={6} />
      ) : !tableRows.length ? (
        <p className="text-sm text-[var(--ds-text-secondary)]">暂无观测记录</p>
      ) : (
        <div className="divide-y divide-[var(--ds-border)]">
          {tableRows.map((row) => {
            const delta = row.delta_from_prev
            const deltaText = formatDelta(delta)
            const deltaColor =
              delta == null
                ? 'text-[var(--ds-text-secondary)]'
                : delta >= 0
                  ? 'text-[var(--color-success)]'
                  : 'text-[var(--color-danger)]'

            return (
              <DataRow
                key={row.index}
                title={row.item_name}
                subtitle={formatCnDateTime(row.captured_at)}
                meta={
                  <span className="flex items-center gap-3 tabular-nums">
                    <span className="font-medium text-[var(--ds-text-primary)]">
                      ¥{row.price?.toFixed(2) ?? '—'}
                    </span>
                    <span className={cn('text-xs', deltaColor)}>{deltaText}</span>
                  </span>
                }
              />
            )
          })}
        </div>
      )}
    </div>
  )
}
