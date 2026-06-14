import { cn } from '../../../lib/utils'

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn('animate-pulse rounded-md bg-white/[0.06]', className)}
      aria-hidden
    />
  )
}

export function SkeletonRow({ className }: { className?: string }) {
  return (
    <div className={cn('flex items-center justify-between gap-4 px-3 py-3', className)} aria-hidden>
      <div className="min-w-0 flex-1 space-y-2">
        <Skeleton className="h-4 w-[62%]" />
        <Skeleton className="h-3 w-[38%]" />
      </div>
      <Skeleton className="h-3 w-14 shrink-0" />
    </div>
  )
}

export function TableSkeleton({ rows = 6, className }: { rows?: number; className?: string }) {
  return (
    <div className={cn('divide-y divide-[var(--ds-border)]', className)} aria-busy aria-label="加载中">
      {Array.from({ length: rows }, (_, i) => (
        <SkeletonRow key={i} />
      ))}
    </div>
  )
}

export function StatStripSkeleton({ items = 3, className }: { items?: number; className?: string }) {
  return (
    <div className={cn('flex flex-wrap gap-x-10 gap-y-4', className)} aria-hidden>
      {Array.from({ length: items }, (_, i) => (
        <div key={i} className="flex flex-col gap-2">
          <Skeleton className="h-3 w-12" />
          <Skeleton className="h-7 w-16" />
        </div>
      ))}
    </div>
  )
}

export function ChartSkeleton({ height = 400, className }: { height?: number; className?: string }) {
  return (
    <div
      className={cn('flex w-full flex-col gap-3 px-4 py-4', className)}
      style={{ height }}
      aria-hidden
    >
      <Skeleton className="ml-auto h-7 w-16" />
      <Skeleton className="h-full min-h-[280px] w-full rounded-lg" />
    </div>
  )
}
