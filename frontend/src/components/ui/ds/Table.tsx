import { cn } from '../../../lib/utils'

type TableProps = React.HTMLAttributes<HTMLTableElement>

export function Table({ className, children, ...props }: TableProps) {
  return (
    <table className={cn('w-full text-sm', className)} {...props}>
      {children}
    </table>
  )
}

type TableHeadProps = React.HTMLAttributes<HTMLTableSectionElement>

export function TableHead({ className, children, ...props }: TableHeadProps) {
  return (
    <thead className={className} {...props}>
      {children}
    </thead>
  )
}

type TableBodyProps = React.HTMLAttributes<HTMLTableSectionElement>

export function TableBody({ className, children, ...props }: TableBodyProps) {
  return (
    <tbody className={className} {...props}>
      {children}
    </tbody>
  )
}

type TableRowProps = React.HTMLAttributes<HTMLTableRowElement> & {
  interactive?: boolean
}

export function TableRow({ className, interactive, children, ...props }: TableRowProps) {
  return (
    <tr
      className={cn(
        'border-b border-[var(--ds-border)] transition-colors duration-[var(--ds-duration-fast)] ease-out',
        interactive && 'ds-table-row-interactive cursor-pointer',
        className,
      )}
      {...props}
    >
      {children}
    </tr>
  )
}

type TableHeaderRowProps = React.HTMLAttributes<HTMLTableRowElement>

export function TableHeaderRow({ className, children, ...props }: TableHeaderRowProps) {
  return (
    <tr
      className={cn(
        'border-b border-[var(--ds-border)] text-left text-xs text-[var(--ds-text-secondary)]',
        className,
      )}
      {...props}
    >
      {children}
    </tr>
  )
}

type TableCellProps = React.TdHTMLAttributes<HTMLTableCellElement>

export function TableCell({ className, children, ...props }: TableCellProps) {
  return (
    <td className={cn('px-4 py-2', className)} {...props}>
      {children}
    </td>
  )
}

type TableHeaderCellProps = React.ThHTMLAttributes<HTMLTableCellElement>

export function TableHeaderCell({ className, children, ...props }: TableHeaderCellProps) {
  return (
    <th className={cn('px-4 py-2 font-normal', className)} {...props}>
      {children}
    </th>
  )
}
