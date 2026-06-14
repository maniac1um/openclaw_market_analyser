import { cn } from '../../../lib/utils'

type SectionProps = {
  title?: string
  description?: string
  action?: React.ReactNode
  children: React.ReactNode
  className?: string
}

export function Section({ title, description, action, children, className }: SectionProps) {
  const hasHeader = title || description || action

  return (
    <section className={cn('flex flex-col gap-4', className)}>
      {hasHeader ? (
        <header className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            {title ? (
              <h2 className="text-sm font-semibold text-[var(--ds-text-primary)]">{title}</h2>
            ) : null}
            {description ? (
              <p className="mt-1 text-xs text-[var(--ds-text-secondary)]">{description}</p>
            ) : null}
          </div>
          {action ? <div className="shrink-0">{action}</div> : null}
        </header>
      ) : null}
      {children}
    </section>
  )
}
