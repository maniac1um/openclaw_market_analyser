import { useEffect, useRef, useState } from 'react'
import uPlot from 'uplot'
import 'uplot/dist/uPlot.min.css'
import { Button } from '../ui/Button'
import { baseUPlotOpts } from './chartTheme'
import { observationsToUPlotData } from './usePriceSeries'
import type { ChartObservation } from './types'
import { formatCnDateTime } from '../../lib/utils'

type TooltipState = {
  left: number
  top: number
  obs: ChartObservation
} | null

export function PriceTrendChart({
  observations,
  height = 400,
}: {
  observations: ChartObservation[]
  height?: number
}) {
  const containerRef = useRef<HTMLDivElement>(null)
  const plotRef = useRef<uPlot | null>(null)
  const metaRef = useRef<ChartObservation[]>([])
  const [tooltip, setTooltip] = useState<TooltipState>(null)
  const [containerWidth, setContainerWidth] = useState(400)

  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    const { data, meta } = observationsToUPlotData(observations)
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
            const obs = metaRef.current[idx]
            const left = u.cursor.left ?? 0
            const top = u.cursor.top ?? 0
            setTooltip({ left, top, obs })
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
  }, [observations, height])

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

  const resetZoom = () => {
    const u = plotRef.current
    const meta = metaRef.current
    if (!u || !meta.length) return
    const { data } = observationsToUPlotData(meta)
    u.setScale('x', { min: data[0][0], max: data[0][data[0].length - 1] })
  }

  if (!observations.length) {
    return (
      <div
        className="flex items-center justify-center text-sm text-[var(--ds-text-secondary)]"
        style={{ height }}
      >
        当前时间范围内暂无观测数据
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex justify-end px-4 pt-4">
        <Button variant="ghost" className="text-xs" onClick={resetZoom}>
          重置缩放
        </Button>
      </div>
      <div className="relative">
        <div ref={containerRef} className="w-full" style={{ height }} />
        {tooltip ? (
          <div
            className="pointer-events-none absolute z-10 rounded-lg border border-[var(--ds-border)] bg-[var(--ds-bg-base)]/95 px-3 py-2 text-xs backdrop-blur-md transition-opacity duration-150 ease-out"
            style={{
              left: Math.min(tooltip.left + 12, containerWidth - 180),
              top: Math.max(tooltip.top - 72, 8),
              opacity: 1,
            }}
          >
            <p className="font-medium text-[var(--ds-text-primary)]">{tooltip.obs.item_name}</p>
            <p className="mt-0.5 text-[var(--ds-text-secondary)]">{formatCnDateTime(tooltip.obs.captured_at)}</p>
            <p className="mt-1 font-semibold text-[var(--color-accent)]">¥{tooltip.obs.price.toFixed(2)}</p>
          </div>
        ) : null}
      </div>
      <p className="px-4 pb-3 text-xs text-[var(--ds-text-secondary)]">
        拖动选择区域缩放 · 双击图表重置 · 悬停查看详情
      </p>
    </div>
  )
}
