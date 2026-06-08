import { useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Skeleton, ErrorBanner, EmptyState } from '../components/ui/States'
import { formatCnDateTime } from '../lib/utils'
import { ChartTimeRangePicker } from '../components/charts/ChartTimeRangePicker'
import { PriceTrendChart } from '../components/charts/PriceTrendChart'
import { useFilteredObservations } from '../components/charts/usePriceSeries'
import type { ChartObservation, TimeRange } from '../components/charts/types'

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

  if (monitorsQuery.isLoading) return <Skeleton className="h-[500px]" />

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <label className="text-sm text-[var(--color-muted)]">监测任务</label>
        <select
          value={monitorId}
          onChange={(e) => setSelectedId(e.target.value)}
          className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
        >
          {(monitorsQuery.data || []).map((m) => (
            <option key={m.monitor_id} value={m.monitor_id}>
              {m.keyword} ({m.observation_count} 条)
            </option>
          ))}
        </select>
      </div>

      {!monitorsQuery.data?.length ? (
        <EmptyState
          title="暂无监测任务"
          description="监测任务由 OpenClaw Agent 或 API 创建。请配置 Agent 后刷新本页。"
        />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <Card>
              <CardContent className="p-4">
                <p className="text-xs text-[var(--color-muted)]">观测数</p>
                <p className="text-2xl font-semibold">{activeMonitor?.observation_count ?? 0}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-xs text-[var(--color-muted)]">URL 数</p>
                <p className="text-2xl font-semibold">{activeMonitor?.url_count ?? 0}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-xs text-[var(--color-muted)]">最近采集</p>
                <p className="text-sm font-medium">{formatCnDateTime(activeMonitor?.last_captured_at)}</p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <CardTitle>价格趋势</CardTitle>
              <ChartTimeRangePicker value={timeRange} onChange={setTimeRange} />
            </CardHeader>
            <CardContent>
              {truncated ? (
                <p className="mb-3 text-xs text-[var(--color-warning)]">
                  观测总数超过 1000 条，图表仅展示最近 1000 条记录
                </p>
              ) : null}
              {obsQuery.isLoading ? (
                <Skeleton className="h-64" />
              ) : obsQuery.isError ? (
                <ErrorBanner message={(obsQuery.error as Error).message} />
              ) : (
                <PriceTrendChart observations={filteredObservations} />
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>采集明细</CardTitle>
            </CardHeader>
            <CardContent className="overflow-x-auto p-0">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--color-border)] text-left text-xs text-[var(--color-muted)]">
                    <th className="px-4 py-2">#</th>
                    <th className="px-4 py-2">商品</th>
                    <th className="px-4 py-2">时间</th>
                    <th className="px-4 py-2">价格</th>
                    <th className="px-4 py-2">变化</th>
                  </tr>
                </thead>
                <tbody>
                  {[...(obsQuery.data?.rows || [])].reverse().map((row) => (
                    <tr key={row.index} className="border-b border-[var(--color-border)]">
                      <td className="px-4 py-2 text-[var(--color-muted)]">{row.index}</td>
                      <td className="px-4 py-2">{row.item_name}</td>
                      <td className="px-4 py-2 text-[var(--color-muted)]">{formatCnDateTime(row.captured_at)}</td>
                      <td className="px-4 py-2 font-medium">{row.price?.toFixed(2) ?? '-'}</td>
                      <td className={`px-4 py-2 ${(row.delta_from_prev ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {row.delta_from_prev != null
                          ? (row.delta_from_prev >= 0 ? '+' : '') + row.delta_from_prev.toFixed(2)
                          : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
