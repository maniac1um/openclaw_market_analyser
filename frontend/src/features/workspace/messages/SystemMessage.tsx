type SystemMessageProps = {
  text: string
}

export function SystemMessage({ text }: SystemMessageProps) {
  return (
    <div className="py-3 text-center">
      <p className="text-xs leading-relaxed text-[var(--color-muted)]">{text}</p>
    </div>
  )
}
