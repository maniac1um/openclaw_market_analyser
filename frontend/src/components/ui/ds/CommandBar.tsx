import { cn } from '../../../lib/utils'
import { Button } from '../Button'

type CommandBarProps = {
  children: React.ReactNode
  className?: string
}

export function CommandBar({ children, className }: CommandBarProps) {
  return (
    <div
      className={cn(
        'flex flex-wrap items-center gap-3 rounded-xl border border-[var(--ds-border)] bg-[var(--ds-bg-panel)] px-4 py-3 backdrop-blur-md',
        className,
      )}
      role="toolbar"
    >
      {children}
    </div>
  )
}

type CommandBarInputProps = React.InputHTMLAttributes<HTMLInputElement>

export function CommandBarInput({ className, ...props }: CommandBarInputProps) {
  return (
    <input
      className={cn(
        'min-w-[12rem] flex-1 rounded-lg border border-[var(--ds-border)] bg-transparent px-3 py-1.5 text-sm text-[var(--ds-text-primary)] placeholder:text-[var(--ds-text-secondary)] outline-none transition-colors focus:border-[var(--color-accent)]',
        className,
      )}
      {...props}
    />
  )
}

type CommandBarButtonProps = React.ComponentProps<typeof Button>

export function CommandBarButton({ className, variant = 'ghost', ...props }: CommandBarButtonProps) {
  return (
    <Button
      variant={variant}
      className={cn('shrink-0 text-[var(--ds-text-secondary)] hover:text-[var(--ds-text-primary)]', className)}
      {...props}
    />
  )
}
