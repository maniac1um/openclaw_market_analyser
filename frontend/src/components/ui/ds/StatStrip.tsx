import { cn } from '../../../lib/utils'

export type StatTrend = {
  value: string
  direction: 'up' | 'down'
}

export type StatStripItemProps = {
  label: string
  value: string | number
  trend?: StatTrend
  className?: string
}

export function StatStrip({
  className,
  children,
}: {
  className?: string
  children: React.ReactNode
}) {
  return (
    <div className={cn('flex flex-wrap items-start gap-x-10 gap-y-4', className)} role="group">
      {children}
    </div>
  )
}

export function StatStripItem({ label, value, trend, className }: StatStripItemProps) {
  return (
    <div className={cn('flex min-w-[5rem] flex-col gap-1', className)}>
      <span className="text-xs text-[var(--ds-text-secondary)]">{label}</span>
      <span className="text-2xl font-bold tracking-tight text-[var(--ds-text-primary)]">{value}</span>
      {trend ? (
        <span
          className={cn(
            'text-xs font-medium',
            trend.direction === 'up' ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]',
          )}
        >
          {trend.direction === 'up' ? '↑ ' : '↓ '}
          {trend.value}
        </span>
      ) : null}
    </div>
  )
}
