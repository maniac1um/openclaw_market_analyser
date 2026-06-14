import { cn } from '../../lib/utils'
import { useTheme } from '../../lib/ThemeProvider'

type ThemeToggleProps = {
  className?: string
}

export function ThemeToggle({ className }: ThemeToggleProps) {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={cn(
        'inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[var(--text-secondary)] transition-colors duration-[var(--ds-duration-fast)] hover:bg-[var(--row-hover)] hover:text-[var(--text)]',
        className,
      )}
      aria-label={isDark ? '切换到浅色模式' : '切换到深色模式'}
      title={isDark ? '浅色模式' : '深色模式'}
    >
      <span className="text-base leading-none" aria-hidden>
        {isDark ? '☀️' : '🌙'}
      </span>
    </button>
  )
}
