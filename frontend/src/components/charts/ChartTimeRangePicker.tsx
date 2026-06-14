import { cn } from '../../lib/utils'
import { TIME_RANGE_LABELS, type TimeRange } from './types'

const RANGES: TimeRange[] = ['1h', '6h', '24h', '7d', '30d', 'all']

export function ChartTimeRangePicker({
  value,
  onChange,
}: {
  value: TimeRange
  onChange: (r: TimeRange) => void
}) {
  return (
    <div className="flex flex-wrap gap-1">
      {RANGES.map((r) => (
        <button
          key={r}
          type="button"
          onClick={() => onChange(r)}
          className={cn(
            'rounded-md px-2.5 py-1 text-xs font-medium transition-colors duration-[var(--ds-duration-fast)]',
            value === r
              ? 'bg-[var(--color-accent)] text-[var(--accent-fg)]'
              : 'border border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--border-hover)] hover:text-primary',
          )}
        >
          {TIME_RANGE_LABELS[r]}
        </button>
      ))}
    </div>
  )
}
