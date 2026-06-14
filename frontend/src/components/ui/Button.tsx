import { cn } from '../../lib/utils'

const variants = {
  primary: 'bg-[var(--color-accent)] text-[var(--accent-fg)] hover:opacity-90',
  secondary: 'border border-[var(--border-solid)] bg-[var(--surface)] text-primary hover:bg-background',
  danger: 'border border-red-200 text-red-600 hover:bg-red-50 dark:border-red-900 dark:hover:bg-red-950',
  ghost: 'text-[var(--text-secondary)] hover:bg-background hover:text-primary',
}

export function Button({
  children,
  variant = 'secondary',
  className,
  disabled,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: keyof typeof variants }) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors disabled:opacity-50',
        variants[variant],
        className,
      )}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  )
}
