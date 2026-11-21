import { useId, useState, useLayoutEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { useFloatingPanel } from './useFloatingPanel'
import { inputClass } from './classNames'

export interface DatePickerProps {
  value: string // yyyy-mm-dd, '' for empty
  onChange: (value: string) => void
  label?: string
  bare?: boolean
  id?: string
  error?: string
  placeholder?: string
  disabled?: boolean
  required?: boolean
  name?: string
  onBlur?: () => void
  'aria-describedby'?: string
}

const weekdays = ['L', 'M', 'M', 'J', 'V', 'S', 'D']
const monthFormatter = new Intl.DateTimeFormat('fr-FR', { month: 'long', year: 'numeric' })
const dayLabelFormatter = new Intl.DateTimeFormat('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })

function toIso(d: Date) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
function parseIso(value: string): Date | null {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return null
  const d = new Date(`${value}T12:00:00`)
  return Number.isNaN(d.getTime()) ? null : d
}
function sameDay(a: Date, b: Date) {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()
}
// Monday-first 6-week grid, including the leading/trailing days from adjacent months.
function buildGrid(monthCursor: Date): Date[] {
  const first = new Date(monthCursor.getFullYear(), monthCursor.getMonth(), 1)
  const startOffset = (first.getDay() + 6) % 7 // 0 = Monday
  const start = new Date(first)
  start.setDate(first.getDate() - startOffset)
  return Array.from({ length: 42 }, (_, i) => {
    const d = new Date(start)
    d.setDate(start.getDate() + i)
    return d
  })
}

export function DatePicker({
  value, onChange, label, bare = false, id, error, placeholder = 'jj/mm/aaaa', disabled, required, name, onBlur,
  'aria-describedby': describedBy,
}: DatePickerProps) {
  const autoId = useId()
  const fieldId = id ?? autoId
  const [open, setOpen] = useState(false)
  const selected = parseIso(value)
  const [cursor, setCursor] = useState(() => selected ?? new Date())
  const today = new Date()
  const expanded = open && !disabled
  const { triggerRef, panelRef, present, style } = useFloatingPanel(expanded, () => setOpen(false))
  const wasOpen = useRef(false)
  useLayoutEffect(() => {
    if (expanded) panelRef.current?.querySelector<HTMLButtonElement>('button')?.focus({ preventScroll: true })
    else if (wasOpen.current) triggerRef.current?.focus({ preventScroll: true })
    wasOpen.current = expanded
  }, [expanded, present, panelRef, triggerRef])

  const control = (
    <>
        <button
          type="button"
          id={fieldId}
          ref={triggerRef}
          aria-expanded={expanded}
          aria-controls={`${autoId}-calendar`}
          onClick={() => { setOpen(!expanded); if (!expanded) setCursor(selected ?? new Date()) }}
          name={name}
          disabled={disabled}
          onBlur={onBlur}
          aria-invalid={Boolean(error)}
          aria-describedby={[describedBy, !bare && error ? `${fieldId}-error` : undefined].filter(Boolean).join(' ') || undefined}
          aria-haspopup="dialog"
          className={`${inputClass} field-control flex items-center justify-between gap-2 text-left disabled:cursor-not-allowed disabled:opacity-50`}
        >
          <span className={selected ? '' : 'text-text-faint'}>{selected ? selected.toLocaleDateString('fr-FR') : placeholder}</span>
          <svg aria-hidden="true" className="shrink-0 text-text-muted" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
            <rect x="3" y="5" width="18" height="16" rx="3" /><path d="M3 10h18M8 3v4M16 3v4" />
          </svg>
        </button>
      {present && createPortal(<div
          ref={panelRef}
          id={`${autoId}-calendar`}
          style={style}
          data-state={expanded ? 'open' : 'closed'}
          inert={!expanded}
          role="dialog"
          aria-label="Choisir une date"
          className="select-content z-50 w-72 overflow-y-auto rounded-lg border border-border bg-surface p-3 text-sm text-text shadow-lg"
        >
          <div className="mb-3 flex items-center justify-between">
            <button type="button" aria-label="Mois précédent" className="press focus-ring flex h-7 w-7 items-center justify-center rounded-md text-text-muted hover:bg-surface-muted" onClick={() => setCursor(c => new Date(c.getFullYear(), c.getMonth() - 1, 1))}>
              <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m15 18-6-6 6-6" /></svg>
            </button>
            <span className="text-sm font-semibold capitalize">{monthFormatter.format(cursor)}</span>
            <button type="button" aria-label="Mois suivant" className="press focus-ring flex h-7 w-7 items-center justify-center rounded-md text-text-muted hover:bg-surface-muted" onClick={() => setCursor(c => new Date(c.getFullYear(), c.getMonth() + 1, 1))}>
              <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m9 18 6-6-6-6" /></svg>
            </button>
          </div>
          <div className="mb-1 grid grid-cols-7 text-center text-xs font-medium text-text-faint">
            {weekdays.map((w, i) => <span key={i}>{w}</span>)}
          </div>
          <div className="grid grid-cols-7 gap-y-1">
            {buildGrid(cursor).map(day => {
              const inMonth = day.getMonth() === cursor.getMonth()
              const isSelected = Boolean(selected && sameDay(day, selected))
              const isToday = sameDay(day, today)
              return (
                <button
                  key={day.toISOString()}
                  type="button"
                  aria-label={dayLabelFormatter.format(day)}
                  aria-current={isToday ? 'date' : undefined}
                  aria-selected={isSelected}
                  className={[
                    'press focus-ring mx-auto flex h-8 w-8 items-center justify-center rounded-full text-sm tabular-nums transition-colors duration-100 ease-out',
                    isSelected ? 'bg-accent font-semibold text-[var(--accent-contrast)]'
                      : isToday ? 'font-semibold text-highlight ring-1 ring-inset ring-highlight hover:bg-surface-muted'
                      : inMonth ? 'text-text hover:bg-surface-muted' : 'text-text-faint hover:bg-surface-muted',
                  ].join(' ')}
                  onClick={() => { onChange(toIso(day)); setOpen(false) }}
                >
                  {day.getDate()}
                </button>
              )
            })}
          </div>
          <div className="mt-3 flex justify-between border-t border-border pt-2">
            <button type="button" className="press focus-ring rounded-md px-2 py-1 text-xs font-medium text-accent hover:bg-surface-muted" onClick={() => { onChange(toIso(today)); setOpen(false) }}>Aujourd’hui</button>
            {value && <button type="button" className="press focus-ring rounded-md px-2 py-1 text-xs font-medium text-text-muted hover:bg-surface-muted" onClick={() => { onChange(''); setOpen(false) }}>Effacer</button>}
          </div>
        </div>, document.body)}
    </>
  )

  if (bare) return control
  return (
    <div>
      <div className={label ? 'floating-field' : undefined} data-pinned={Boolean(label) || undefined}>
      {control}
      {label && <label htmlFor={fieldId}>{label}{required ? ' *' : ''}</label>}
      </div>
      {error && <p id={`${fieldId}-error`} className="mt-1 text-xs text-status-overdue">{error}</p>}
    </div>
  )
}
