import { forwardRef, useId } from 'react'
import type { InputHTMLAttributes, TextareaHTMLAttributes } from 'react'
import { inputClass, textareaClass } from './classNames'

interface FieldChromeProps {
  label?: string
  /** Render only the control when its label and errors already exist in the layout. */
  bare?: boolean
  error?: string
  hint?: string
}

function describedBy(id: string, error?: string, hint?: string) {
  return error ? `${id}-error` : hint ? `${id}-hint` : undefined
}

export type TextFieldProps = FieldChromeProps & InputHTMLAttributes<HTMLInputElement>

// Works directly with react-hook-form's `register(name)` spread: pass its
// result alongside `label`/`error` and the ref wiring just works.
export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(function TextField(
  { label, error, hint, bare = false, id, className = '', placeholder, 'aria-describedby': description, ...rest },
  ref,
) {
  const autoId = useId()
  const fieldId = id ?? autoId
  const descriptions = [description, describedBy(fieldId, error, hint)].filter(Boolean).join(' ') || undefined
  const floating = !bare && Boolean(label)
  const pinned = Boolean(placeholder?.trim()) || ['date', 'time', 'datetime-local', 'month', 'week', 'color', 'file'].includes(rest.type ?? '')
  return (
    <div className="unified-field">
      <div className={floating ? 'floating-field' : undefined} data-pinned={pinned || undefined}>
      <input
        ref={ref}
        id={fieldId}
        className={`${inputClass} ${className}`}
        placeholder={placeholder ?? (floating ? ' ' : undefined)}
        {...rest}
        aria-invalid={error ? true : rest['aria-invalid']}
        aria-describedby={descriptions}
      />
      {floating && <label htmlFor={fieldId}>{label}</label>}
      </div>
      {hint && !error && <p id={`${fieldId}-hint`} className="mt-1 text-xs text-text-muted">{hint}</p>}
      {error && <p id={`${fieldId}-error`} className="mt-1 text-xs text-status-overdue">{error}</p>}
    </div>
  )
})

export type TextAreaFieldProps = FieldChromeProps & TextareaHTMLAttributes<HTMLTextAreaElement>

export const TextAreaField = forwardRef<HTMLTextAreaElement, TextAreaFieldProps>(function TextAreaField(
  { label, error, hint, bare = false, id, className = '', rows = 3, placeholder, 'aria-describedby': description, ...rest },
  ref,
) {
  const autoId = useId()
  const fieldId = id ?? autoId
  const descriptions = [description, describedBy(fieldId, error, hint)].filter(Boolean).join(' ') || undefined
  const floating = !bare && Boolean(label)
  return (
    <div className="unified-field">
      <div className={floating ? 'floating-field floating-textarea' : undefined} data-pinned={Boolean(placeholder?.trim()) || undefined}>
      <textarea
        ref={ref}
        id={fieldId}
        rows={rows}
        className={`${textareaClass} ${className}`}
        placeholder={placeholder ?? (floating ? ' ' : undefined)}
        {...rest}
        aria-invalid={error ? true : rest['aria-invalid']}
        aria-describedby={descriptions}
      />
      {floating && <label htmlFor={fieldId}>{label}</label>}
      </div>
      {hint && !error && <p id={`${fieldId}-hint`} className="mt-1 text-xs text-text-muted">{hint}</p>}
      {error && <p id={`${fieldId}-error`} className="mt-1 text-xs text-status-overdue">{error}</p>}
    </div>
  )
})

export interface CheckboxFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  /** Render only the control when its label and errors already exist in the layout. */
  bare?: boolean
}

export const CheckboxField = forwardRef<HTMLInputElement, CheckboxFieldProps>(function CheckboxField(
  { label, bare = false, className = '', ...rest },
  ref,
) {
  if (bare) return <input ref={ref} type="checkbox" className={className || 'accent-accent'} {...rest} />
  return (
    <label className={`flex h-9 items-center gap-2 self-end text-sm ${className}`}>
      <input ref={ref} type="checkbox" className="accent-accent" {...rest} />
      {label}
    </label>
  )
})
