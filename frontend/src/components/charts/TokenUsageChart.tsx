import { useEffect, useRef, useState } from 'react'
import uPlot from 'uplot'
import 'uplot/dist/uPlot.min.css'
import { baseUPlotOpts } from './chartTheme'
import { formatCnDateTime } from '../../lib/utils'
import { useTheme } from '../../lib/ThemeProvider'

export type UsageSeriesPoint = {
  bucket: string
  tokens: number
}

type TooltipState = {
  left: number
  point: UsageSeriesPoint
} | null

function seriesToUPlotData(points: UsageSeriesPoint[]) {
  const xs = points.map((p) => new Date(p.bucket).getTime() / 1000)
  const ys = points.map((p) => p.tokens)
  return { data: [xs, ys] as uPlot.AlignedData, meta: points }
}

export function TokenUsageChart({
  series,
  height = 320,
}: {
  series: UsageSeriesPoint[]
  height?: number
}) {
  const containerRef = useRef<HTMLDivElement>(null)
  const plotRef = useRef<uPlot | null>(null)
  const metaRef = useRef<UsageSeriesPoint[]>([])
  const [tooltip, setTooltip] = useState<TooltipState>(null)
  const [containerWidth, setContainerWidth] = useState(400)
  const { theme } = useTheme()

  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    const { data, meta } = seriesToUPlotData(series)
    metaRef.current = meta

    if (!data[0].length) {
      plotRef.current?.destroy()
      plotRef.current = null
      return
    }

    const width = el.clientWidth || 400
    const base = baseUPlotOpts(width, height)

    const opts: uPlot.Options = {
      width,
      height,
      scales: base.scales!,
      axes: base.axes!,
      series: base.series!,
      cursor: base.cursor,
      legend: base.legend,
      hooks: {
        setCursor: [
          (u) => {
            const idx = u.cursor.idx
            if (idx == null || idx < 0 || !metaRef.current[idx]) {
              setTooltip(null)
              return
            }
            const point = metaRef.current[idx]
            const left = u.cursor.left ?? 0
            setTooltip({ left, point })
          },
        ],
        ready: [
          (u) => {
            const over = u.over
            over.addEventListener('mouseleave', () => setTooltip(null))
            over.addEventListener('dblclick', () => {
              u.setScale('x', { min: data[0][0], max: data[0][data[0].length - 1] })
            })
          },
        ],
      },
    }

    plotRef.current?.destroy()
    plotRef.current = new uPlot(opts, data, el)

    return () => {
      plotRef.current?.destroy()
      plotRef.current = null
    }
  }, [series, height, theme])

  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    const ro = new ResizeObserver(() => {
      const u = plotRef.current
      const w = el.clientWidth
      if (w > 0) setContainerWidth(w)
      if (!u || w <= 0) return
      u.setSize({ width: w, height })
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [height])

  if (!series.length) {
    return (
      <div
        className="flex items-center justify-center text-sm text-[var(--ds-text-secondary)]"
        style={{ height }}
      >
        当前时间范围内暂无使用记录
      </div>
    )
  }

  const tooltipWidth = 152
  const tooltipLeft = tooltip
    ? Math.min(Math.max(tooltip.left - tooltipWidth / 2, 8), containerWidth - tooltipWidth - 8)
    : 0

  return (
    <div className="relative w-full">
      <div ref={containerRef} className="w-full" style={{ height }} />
      {tooltip ? (
        <div
          className="pointer-events-none absolute z-10 rounded-lg border border-[var(--border-hover)] bg-background/95 px-3 py-2.5 text-xs shadow-lg shadow-[var(--overlay)] backdrop-blur-md"
          style={{ left: tooltipLeft, top: 8, width: tooltipWidth }}
        >
          <p className="text-[var(--text-secondary)]">{formatCnDateTime(tooltip.point.bucket)}</p>
          <p className="mt-1.5 font-semibold tabular-nums text-[var(--color-accent)]">
            {tooltip.point.tokens.toLocaleString()} tokens
          </p>
        </div>
      ) : null}
    </div>
  )
}
