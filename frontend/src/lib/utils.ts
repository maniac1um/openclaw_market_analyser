import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCnDateTime(value: string | null | undefined): string {
  if (!value) return '-'
  try {
    const dt = new Date(value)
    if (Number.isNaN(dt.getTime())) return value
    return dt.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    })
  } catch {
    return value
  }
}

export function formatDateShort(value: string | null | undefined): string {
  if (!value) return '-'
  try {
    const dt = new Date(value)
    if (Number.isNaN(dt.getTime())) return value
    return dt.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return value
  }
}
