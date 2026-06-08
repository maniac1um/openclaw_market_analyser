import type { ReportDetail } from '../../lib/api'

export type DemoPriceTrend = {
  keyword: string
  observation_count: number
  url_count: number
  last_captured_at: string
  points: { date: string; avg_price: number }[]
  rows: {
    item_name: string
    captured_at: string
    price: number
    delta_from_prev: number | null
  }[]
}

export const DEMO_REPORT_SLUGS = ['nebula-battery', 'stellar-panel'] as const

export async function loadDemoReport(slug: string): Promise<ReportDetail> {
  const res = await fetch(`/demo/reports/${slug}.json`)
  if (!res.ok) throw new Error('无法加载示例报告')
  return res.json() as Promise<ReportDetail>
}

export async function loadDemoPriceTrend(): Promise<DemoPriceTrend> {
  const res = await fetch('/demo/price-trend/sample-cell.json')
  if (!res.ok) throw new Error('无法加载价格示例')
  return res.json() as Promise<DemoPriceTrend>
}
