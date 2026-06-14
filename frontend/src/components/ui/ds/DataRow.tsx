import { cn } from '../../../lib/utils'

type DataRowProps = {
  title: React.ReactNode
  subtitle?: React.ReactNode
  meta?: React.ReactNode
  onClick?: () => void
  className?: string
}

export function DataRow({ title, subtitle, meta, onClick, className }: DataRowProps) {
  const interactive = Boolean(onClick)

  return (
    <div
      role={interactive ? 'button' : undefined}
      tabIndex={interactive ? 0 : undefined}
      onClick={onClick}
      onKeyDown={
        interactive
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                onClick?.()
              }
            }
          : undefined
      }
      className={cn(
        'flex items-center justify-between gap-4 px-3 py-3',
        'transition-colors duration-150 ease-out',
        interactive
          ? 'cursor-pointer hover:bg-white/[0.06] active:bg-white/[0.08]'
          : 'hover:bg-white/[0.04]',
        className,
      )}
    >
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-[var(--ds-text-primary)]">{title}</p>
        {subtitle ? (
          <p className="mt-0.5 truncate text-xs text-[var(--ds-text-secondary)]">{subtitle}</p>
        ) : null}
      </div>
      {meta ? <div className="shrink-0 text-xs text-[var(--ds-text-secondary)]">{meta}</div> : null}
    </div>
  )
}
