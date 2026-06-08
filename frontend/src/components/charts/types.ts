export type TimeRange = '1h' | '6h' | '24h' | '7d' | '30d' | '90d' | 'all'

export type ChartObservation = {
  captured_at: string
  price: number
  item_name: string
}

export const TIME_RANGE_LABELS: Record<TimeRange, string> = {
  '1h': '1h',
  '6h': '6h',
  '24h': '24h',
  '7d': '7d',
  '30d': '30d',
  '90d': '90d',
  all: 'All',
}

export const TIME_RANGE_MS: Record<TimeRange, number | null> = {
  '1h': 3_600_000,
  '6h': 21_600_000,
  '24h': 86_400_000,
  '7d': 7 * 86_400_000,
  '30d': 30 * 86_400_000,
  '90d': 90 * 86_400_000,
  all: null,
}
