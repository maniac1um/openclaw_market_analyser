import { AlertCircle, Inbox, RefreshCw } from 'lucide-react'
import { Button } from './Button'

export { Skeleton, SkeletonRow, TableSkeleton, StatStripSkeleton, ChartSkeleton, PageSkeleton, DrawerContentSkeleton } from './ds/Skeleton'

export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
      <div className="flex-1">
        <p>{message}</p>
        {onRetry && (
          <Button variant="ghost" className="mt-2 h-8 px-2 text-red-700" onClick={onRetry}>
            <RefreshCw className="h-3.5 w-3.5" /> 重试
          </Button>
        )}
      </div>
    </div>
  )
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string
  description?: string
  action?: React.ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-border)]/50">
        <Inbox className="h-6 w-6 text-[var(--color-muted)]" />
      </div>
      <h3 className="text-base font-medium text-[var(--color-text)]">{title}</h3>
      {description && <p className="mt-1 max-w-sm text-sm text-[var(--color-muted)]">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
