import { Button } from './Button'

export function Pagination({
  page,
  onChange,
  disabled,
  hasNext,
  className = "flex flex-wrap items-center justify-end gap-3",
  buttonClassName,
}: {
  className?: string
  buttonClassName?: string
  page: number
  onChange: (page: number) => void
  disabled?: boolean
  /** Whether a "Suivant" click would actually find more rows. */
  hasNext: boolean
}) {
  return (
    <nav aria-label="Pagination" className={className}>
      <Button classNameOverride={buttonClassName} disabled={page === 1 || disabled} onClick={() => onChange(page - 1)}>Précédent</Button>
      <span aria-live="polite" className="text-text-muted">Page {page}</span>
      <Button classNameOverride={buttonClassName} disabled={disabled || !hasNext} onClick={() => onChange(page + 1)}>Suivant</Button>
    </nav>
  )
}
