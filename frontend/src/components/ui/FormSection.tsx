import { useState } from 'react'
import type { ReactNode } from 'react'
import { cardClass } from './classNames'

export function FormSection({
  title,
  children,
  defaultOpen = true,
  forceOpen = false,
  toggleClassName = "focus-ring flex w-full items-center justify-between rounded text-left text-lg font-semibold",
}: {
  toggleClassName?: string
  title: string
  children: ReactNode
  defaultOpen?: boolean
  /** Keep expanded regardless of the toggle — e.g. while this section has a validation error. */
  forceOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)
  const expanded = open || forceOpen
  return (
    <section className={cardClass}>
      <h2>
        <button
          type="button"
          aria-expanded={expanded}
          onClick={() => setOpen(value => !value)}
          className={toggleClassName}
        >
          {title}
          <span aria-hidden="true" className="text-text-muted">{expanded ? '−' : '+'}</span>
        </button>
      </h2>
      <div hidden={!expanded} className="mt-5">{children}</div>
    </section>
  )
}
