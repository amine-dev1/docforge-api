import type { ReactNode } from 'react'
import { cardClass } from './classNames'
import { Button } from './Button'

export function LoadingState() {
  return (
    <div role="status" className={cardClass}>
      <span className="sr-only">Chargement…</span>
      <div className="space-y-4 motion-safe:animate-pulse">
        {[1, 2, 3, 4].map(n => <div key={n} className="h-8 rounded bg-surface-muted" />)}
      </div>
    </div>
  )
}

// `message` is a plain string: format the error (axios status, zod issue...)
// at the call site, this component stays domain-agnostic.
export function ErrorState({ message, retry, buttonClassName }: { message: string; retry: () => void; buttonClassName?: string }) {
  return (
    <div role="alert" className={cardClass}>
      <p className="mb-3">{message}</p>
      <Button classNameOverride={buttonClassName} onClick={retry}>Réessayer</Button>
    </div>
  )
}

// Default icon: an open box, used across lists with nothing to show yet.
const defaultIcon = (
  <svg aria-hidden="true" className="h-12 w-12 text-text-faint" viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="m6 14 18-8 18 8v22l-18 8-18-8zM6 14l18 8 18-8M24 22v22M15 10l18 8" />
  </svg>
)

export function EmptyState({
  title,
  message,
  action,
  icon = defaultIcon,
}: {
  title: string
  message?: string
  action?: ReactNode
  icon?: ReactNode
}) {
  return (
    <div className={`${cardClass} flex flex-col items-center gap-4 py-12 text-center`}>
      {icon}
      <h2 className="text-lg font-semibold">{title}</h2>
      {message && <p className="text-text-muted">{message}</p>}
      {action}
    </div>
  )
}
