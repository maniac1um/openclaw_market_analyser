import { useMemo } from 'react'
import type { ChartObservation, TimeRange } from './types'
import { TIME_RANGE_MS } from './types'

export function filterObservationsByRange(observations: ChartObservation[], range: TimeRange): ChartObservation[] {
  const ms = TIME_RANGE_MS[range]
  if (ms === null) return observations
  const cutoff = Date.now() - ms
  return observations.filter((o) => new Date(o.captured_at).getTime() >= cutoff)
}

export function observationsToUPlotData(observations: ChartObservation[]): {
  data: [number[], number[]]
  meta: ChartObservation[]
} {
  const sorted = [...observations].sort(
    (a, b) => new Date(a.captured_at).getTime() - new Date(b.captured_at).getTime(),
  )
  const xs: number[] = []
  const ys: number[] = []
  for (const o of sorted) {
    xs.push(new Date(o.captured_at).getTime() / 1000)
    ys.push(o.price)
  }
  return { data: [xs, ys], meta: sorted }
}

export function useFilteredObservations(observations: ChartObservation[], range: TimeRange) {
  return useMemo(() => filterObservationsByRange(observations, range), [observations, range])
}

/** Coefficient of variation (std / mean) as a percentage. */
export function computePriceVolatility(observations: ChartObservation[]): string {
  if (observations.length < 2) return '—'
  const prices = observations.map((o) => o.price)
  const mean = prices.reduce((a, b) => a + b, 0) / prices.length
  if (mean === 0) return '—'
  const variance = prices.reduce((sum, p) => sum + (p - mean) ** 2, 0) / prices.length
  const cv = (Math.sqrt(variance) / mean) * 100
  return `${cv.toFixed(1)}%`
}
