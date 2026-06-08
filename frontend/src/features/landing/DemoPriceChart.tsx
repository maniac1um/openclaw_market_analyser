import { useMemo, useState } from 'react'
import type { DemoPriceTrend } from './demoData'
import { ChartTimeRangePicker } from '../../components/charts/ChartTimeRangePicker'
import { PriceTrendChart } from '../../components/charts/PriceTrendChart'
import { useFilteredObservations } from '../../components/charts/usePriceSeries'
import type { ChartObservation, TimeRange } from '../../components/charts/types'

export function DemoPriceChart({ data }: { data: DemoPriceTrend }) {
  const [timeRange, setTimeRange] = useState<TimeRange>('30d')

  const observations = useMemo<ChartObservation[]>(() => {
    if (data.rows?.length) {
      return data.rows.map((r) => ({
        captured_at: r.captured_at,
        price: r.price,
        item_name: r.item_name,
      }))
    }
    return (data.points || []).map((p) => ({
      captured_at: `${p.date}T12:00:00+08:00`,
      price: p.avg_price,
      item_name: data.keyword,
    }))
  }, [data])

  const filtered = useFilteredObservations(observations, timeRange)

  return (
    <div className="space-y-3">
      <ChartTimeRangePicker value={timeRange} onChange={setTimeRange} />
      <PriceTrendChart observations={filtered} />
    </div>
  )
}
