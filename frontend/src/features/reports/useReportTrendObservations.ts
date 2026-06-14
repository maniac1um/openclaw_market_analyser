import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api, type ReportDetail } from '../../lib/api'
import type { ChartObservation } from '../../components/charts/types'

function observationsFromItems(report: ReportDetail): ChartObservation[] {
  const keyword = report.keyword || '价格'
  return (report.items || [])
    .filter((item) => item.price != null && item.published_at)
    .map((item) => ({
      captured_at: item.published_at!,
      price: item.price!,
      item_name: keyword,
    }))
    .sort((a, b) => new Date(a.captured_at).getTime() - new Date(b.captured_at).getTime())
}

export function useReportTrendObservations(report: ReportDetail) {
  const fromItems = useMemo(() => observationsFromItems(report), [report])
  const useMonitor = fromItems.length === 0 && !!report.keyword?.trim()

  const monitorsQuery = useQuery({
    queryKey: ['monitors'],
    queryFn: api.listMonitors,
    enabled: useMonitor,
  })

  const monitorId = useMemo(() => {
    if (!useMonitor) return ''
    const keyword = report.keyword!.trim()
    return monitorsQuery.data?.find((m) => m.keyword === keyword)?.monitor_id || ''
  }, [useMonitor, report.keyword, monitorsQuery.data])

  const obsQuery = useQuery({
    queryKey: ['observations', monitorId],
    queryFn: () => api.observations(monitorId, 500),
    enabled: useMonitor && !!monitorId,
  })

  const fromMonitor = useMemo<ChartObservation[]>(() => {
    if (!useMonitor || !monitorId) return []
    return (obsQuery.data?.rows || [])
      .filter((row) => row.captured_at != null && row.price != null)
      .map((row) => ({
        captured_at: row.captured_at!,
        price: row.price!,
        item_name: row.item_name || report.keyword || '价格',
      }))
      .sort((a, b) => new Date(a.captured_at).getTime() - new Date(b.captured_at).getTime())
  }, [useMonitor, monitorId, obsQuery.data?.rows, report.keyword])

  const observations = fromItems.length > 0 ? fromItems : fromMonitor
  const loading = useMonitor && (monitorsQuery.isLoading || (!!monitorId && obsQuery.isLoading))

  return { observations, loading, show: observations.length > 0 || loading }
}
