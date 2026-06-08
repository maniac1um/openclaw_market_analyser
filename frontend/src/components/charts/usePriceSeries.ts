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
