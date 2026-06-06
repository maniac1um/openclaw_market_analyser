import { useQuery } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Skeleton, ErrorBanner, EmptyState } from '../components/ui/States'
import { formatCnDateTime } from '../lib/utils'

export function PriceTrendPage() {
  const [monitorId, setMonitorId] = useState<string>('')
  const canvasRef = useRef<HTMLCanvasElement>(null)

  const monitorsQuery = useQuery({ queryKey: ['monitors'], queryFn: api.listMonitors })
  const timeseriesQuery = useQuery({
    queryKey: ['timeseries', monitorId],
    queryFn: () => api.timeseries(monitorId, 30),
    enabled: !!monitorId,
  })
  const obsQuery = useQuery({
    queryKey: ['observations', monitorId],
    queryFn: () => api.observations(monitorId, 100),
    enabled: !!monitorId,
  })

  useEffect(() => {
    if (!monitorsQuery.data?.length) return
    if (!monitorId) setMonitorId(monitorsQuery.data[0].monitor_id)
  }, [monitorsQuery.data, monitorId])

  useEffect(() => {
    const canvas = canvasRef.current
    const points = timeseriesQuery.data?.points || []
    if (!canvas || !points.length) return

    const dpr = window.devicePixelRatio || 1
    const rect = canvas.getBoundingClientRect()
    canvas.width = rect.width * dpr
    canvas.height = rect.height * dpr
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.scale(dpr, dpr)

    const w = rect.width
    const h = rect.height
    const pad = { t: 20, r: 16, b: 28, l: 48 }
    const prices = points.map((p) => p.avg_price).filter((p): p is number => p != null)
    if (!prices.length) return
    const min = Math.min(...prices)
    const max = Math.max(...prices)
    const range = max - min || 1

    const isDark = document.documentElement.classList.contains('dark')
    const grid = isDark ? '#262626' : '#e5e5e5'
    const line = isDark ? '#3b82f6' : '#2563eb'
    const text = isDark ? '#a3a3a3' : '#737373'

    ctx.clearRect(0, 0, w, h)
    ctx.strokeStyle = grid
    ctx.lineWidth = 1
    for (let i = 0; i <= 4; i++) {
      const y = pad.t + ((h - pad.t - pad.b) * i) / 4
      ctx.beginPath()
      ctx.moveTo(pad.l, y)
      ctx.lineTo(w - pad.r, y)
      ctx.stroke()
    }

    ctx.beginPath()
    ctx.strokeStyle = line
    ctx.lineWidth = 2
    points.forEach((p, i) => {
      const x = pad.l + ((w - pad.l - pad.r) * i) / Math.max(points.length - 1, 1)
      const y = pad.t + (h - pad.t - pad.b) * (1 - ((p.avg_price ?? min) - min) / range)
      if (i === 0) ctx.moveTo(x, y)
      else ctx.lineTo(x, y)
    })
    ctx.stroke()

    ctx.fillStyle = line + '22'
    ctx.lineTo(w - pad.r, h - pad.b)
    ctx.lineTo(pad.l, h - pad.b)
    ctx.closePath()
    ctx.fill()

    ctx.fillStyle = text
    ctx.font = '11px sans-serif'
    ctx.fillText(max.toFixed(0), 4, pad.t + 4)
    ctx.fillText(min.toFixed(0), 4, h - pad.b)
  }, [timeseriesQuery.data])

  const activeMonitor = monitorsQuery.data?.find((m) => m.monitor_id === monitorId)

  if (monitorsQuery.isLoading) return <Skeleton className="h-[500px]" />

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <label className="text-sm text-[var(--color-muted)]">监测任务</label>
        <select
          value={monitorId}
          onChange={(e) => setMonitorId(e.target.value)}
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
        <EmptyState title="暂无监测任务" description="前往工作流创建监测任务" />
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
            <CardHeader>
              <CardTitle>30 日均价趋势</CardTitle>
            </CardHeader>
            <CardContent>
              {timeseriesQuery.isLoading ? (
                <Skeleton className="h-64" />
              ) : timeseriesQuery.isError ? (
                <ErrorBanner message={(timeseriesQuery.error as Error).message} />
              ) : (
                <canvas ref={canvasRef} className="h-64 w-full" />
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
                  {(obsQuery.data?.rows || []).map((row) => (
                    <tr key={row.index} className="border-b border-[var(--color-border)]">
                      <td className="px-4 py-2 text-[var(--color-muted)]">{row.index}</td>
                      <td className="px-4 py-2">{row.item_name}</td>
                      <td className="px-4 py-2 text-[var(--color-muted)]">{formatCnDateTime(row.captured_at)}</td>
                      <td className="px-4 py-2 font-medium">{row.price?.toFixed(2) ?? '-'}</td>
                      <td className={`px-4 py-2 ${(row.delta_from_prev ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {row.delta_from_prev != null ? (row.delta_from_prev >= 0 ? '+' : '') + row.delta_from_prev.toFixed(2) : '-'}
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
