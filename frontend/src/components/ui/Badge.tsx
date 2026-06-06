import { cn } from '../../lib/utils'

const variants = {
  default: 'bg-[var(--color-accent-soft)] text-[var(--color-accent)]',
  success: 'bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-400',
  danger: 'bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-400',
  warning: 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-400',
  muted: 'bg-[var(--color-border)] text-[var(--color-muted)]',
}

export function Badge({
  children,
  variant = 'default',
  className,
}: {
  children: React.ReactNode
  variant?: keyof typeof variants
  className?: string
}) {
  return (
    <span className={cn('inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium', variants[variant], className)}>
      {children}
    </span>
  )
}
