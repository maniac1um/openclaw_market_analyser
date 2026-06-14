type UserMessageProps = {
  text: string
}

export function UserMessage({ text }: UserMessageProps) {
  return (
    <div className="flex justify-end py-2">
      <div className="max-w-[min(92%,36rem)] rounded-2xl bg-[var(--color-text)] px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap text-[var(--color-bg)]">
        {text}
      </div>
    </div>
  )
}
