import { cn } from '../../../lib/utils'

type PanelProps = React.HTMLAttributes<HTMLDivElement>

export function Panel({ className, children, ...props }: PanelProps) {
  return (
    <div
      className={cn(
        'rounded-xl border border-[var(--ds-border)] bg-[var(--ds-bg-panel)] p-6 backdrop-blur-md',
        'transition-[border-color] duration-150 ease-out hover:border-[var(--ds-border-hover)]',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  )
}
