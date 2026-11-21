import { forwardRef, useId, useState, useRef, useLayoutEffect, useEffect } from 'react'
import type { ComponentPropsWithoutRef, ComponentType, KeyboardEvent, ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { inputClass } from './classNames'
import { useFloatingPanel } from './useFloatingPanel'

// Local type contract keeps the exported interface unchanged, including asChild.
declare const Select: { Trigger: ComponentType<ComponentPropsWithoutRef<'button'> & { asChild?: boolean }> }

export interface SelectOption {
  value: string
  label: string
  disabled?: boolean
}

export interface SelectFieldProps extends Omit<ComponentPropsWithoutRef<typeof Select.Trigger>, 'value' | 'defaultValue' | 'onChange' | 'children' | 'dir'> {
  label?: string
  bare?: boolean
  options?: SelectOption[]
  error?: string
  emptyHint?: string
  placeholder?: string
  value: string
  onChange: (value: string) => void
  name?: string
  renderOption?: (option: SelectOption) => ReactNode
  renderValue?: (option: SelectOption) => ReactNode
  required?: boolean
}

export const SelectField = forwardRef<HTMLButtonElement, SelectFieldProps>(function SelectField(
  { label, bare = false, options = [], error, emptyHint = 'Aucune valeur disponible.', placeholder,
    id, className = '', value, onChange, name, required, disabled, onBlur, asChild: _asChild,
    'aria-describedby': describedBy, renderOption, renderValue, ...rest }, ref,
) {
  const autoId = useId()
  const fieldId = id ?? autoId
  const listId = `${autoId}-listbox`
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(-1)
  const [inputMode, setInputMode] = useState<'pointer' | 'keyboard'>('keyboard')
  const search = useRef({ text: '', time: 0 })
  const viewportRef = useRef<HTMLDivElement>(null)
  const scrollTimer = useRef<ReturnType<typeof setInterval> | undefined>(undefined)
  const [scrollEdges, setScrollEdges] = useState({ up: false, down: false })
  const stopScroll = () => { clearInterval(scrollTimer.current); scrollTimer.current = undefined }
  const startScroll = (direction: number) => {
    stopScroll()
    scrollTimer.current = setInterval(() => viewportRef.current?.scrollBy({ top: direction * 10 }), 30)
  }
  const updateScrollEdges = () => {
    const viewport = viewportRef.current
    if (!viewport) return
    const up = viewport.scrollTop > 0
    const down = Math.ceil(viewport.scrollTop + viewport.clientHeight) < viewport.scrollHeight
    setScrollEdges(previous => previous.up === up && previous.down === down ? previous : { up, down })
  }
  useEffect(() => stopScroll, [])
  const expanded = open && !disabled
  const { triggerRef, panelRef, present, style } = useFloatingPanel(expanded, () => setOpen(false), true)
  const items = placeholder !== undefined && !options.some(option => option.value === '')
    ? [{ value: '', label: placeholder }, ...options] : options
  const hint = !bare && options.length === 0 && emptyHint
  const description = [describedBy, !bare && error ? `${fieldId}-error` : hint ? `${fieldId}-hint` : undefined].filter(Boolean).join(' ') || undefined
  const enabled = items.map((item, index) => item.disabled ? -1 : index).filter(index => index >= 0)
  const selected = items.find(option => option.value === value)
  const close = () => { stopScroll(); setOpen(false); triggerRef.current?.focus() }
  const choose = (index: number) => {
    if (!expanded || !items[index] || items[index].disabled) return
    onChange(items[index].value)
    close()
  }
  const show = (mode: 'pointer' | 'keyboard', last = false) => {
    if (disabled) return
    search.current = { text: '', time: 0 }
    setInputMode(mode)
    const selectedIndex = items.findIndex(option => option.value === value && !option.disabled)
    setActive(selectedIndex >= 0 ? selectedIndex : (last ? enabled.at(-1) : enabled[0]) ?? -1)
    setOpen(true)
  }
  useLayoutEffect(() => {
    if (!expanded) { stopScroll(); return }
    updateScrollEdges()
    const observer = new ResizeObserver(updateScrollEdges)
    if (viewportRef.current) observer.observe(viewportRef.current)
    return () => observer.disconnect()
  }, [expanded, present, items.length])
  useLayoutEffect(() => {
    if (!expanded) return
    panelRef.current?.focus({ preventScroll: true })
  }, [expanded, present, panelRef])
  useLayoutEffect(() => {
    if (expanded && inputMode === 'keyboard') {
      document.getElementById(`${listId}-${active}`)?.scrollIntoView({ block: 'nearest' })
    }
  }, [expanded, active, inputMode, present, listId])
  const handleKey = (event: KeyboardEvent<HTMLElement>) => {
    if (event.defaultPrevented || disabled) return
    setInputMode('keyboard')
    if (event.key === 'Tab') { setOpen(false); triggerRef.current?.focus(); return }
    if (event.key === 'Escape') { if (expanded) { event.preventDefault(); close() }; return }
    if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
      event.preventDefault()
      if (!expanded) { show('keyboard', event.key === 'ArrowUp' || event.key === 'End'); return }
      const pos = enabled.indexOf(active)
      const next = event.key === 'Home' ? enabled[0] : event.key === 'End' ? enabled.at(-1)
        : enabled[Math.max(0, Math.min(enabled.length - 1, pos + (event.key === 'ArrowDown' ? 1 : -1)))]
      setActive(next ?? -1)
      return
    }
    if (event.key === 'Enter' || (event.key === ' ' && (!search.current.text || Date.now() - search.current.time > 500))) {
      event.preventDefault()
      if (expanded) choose(active)
      else show('keyboard')
      return
    }
    if (event.key.length === 1 && !event.ctrlKey && !event.altKey && !event.metaKey) {
      event.preventDefault()
      const now = Date.now()
      const text = (now - search.current.time < 500 ? search.current.text : '') + event.key.toLocaleLowerCase('fr')
      search.current = { text, time: now }
      const query = [...text].every(char => char === text[0]) ? text[0] : text
      const start = expanded ? active : items.findIndex(option => option.value === value)
      const ordered = [...enabled.filter(index => index > start), ...enabled.filter(index => index <= start)]
      if (query.length > 1 && enabled.includes(start)) ordered.unshift(start)
      const match = ordered.find(index => items[index].label.toLocaleLowerCase('fr').startsWith(query))
      if (match !== undefined) {
        if (expanded) setActive(match)
        else onChange(items[match].value)
      }
    }
  }
  const triggerProps = {
    ...rest,
    ref: (node: HTMLButtonElement | null) => { triggerRef.current = node; if (typeof ref === 'function') ref(node); else if (ref) ref.current = node },
    id: fieldId, type: 'button' as const, disabled, onBlur,
    role: 'combobox', 'aria-haspopup': 'listbox' as const, 'aria-expanded': expanded, 'aria-controls': listId,
    'aria-required': required, 'aria-invalid': error ? true : rest['aria-invalid'], 'aria-describedby': description,
    'data-state': expanded ? 'open' : 'closed', 'data-placeholder': !selected ? '' : undefined,
    onClick: (event: React.MouseEvent<HTMLButtonElement>) => { rest.onClick?.(event); if (!event.defaultPrevented) { if (expanded) close(); else show('pointer') } },
    onKeyDown: (event: KeyboardEvent<HTMLButtonElement>) => { rest.onKeyDown?.(event); handleKey(event) },
    className: `${inputClass} select-trigger flex items-center justify-between gap-2 text-left disabled:cursor-not-allowed disabled:opacity-50 ${className}`,
  }
  const triggerChildren = <><span className="min-w-0 truncate">{selected ? (renderValue ?? renderOption)?.(selected) ?? selected.label : placeholder ?? 'Sélectionner…'}</span>
    <svg className="select-chevron shrink-0 text-text-muted" aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75"><path d="m6 9 6 6 6-6" /></svg></>
  const control = <>
    <button {...triggerProps}>{triggerChildren}</button>
    <select aria-hidden="true" tabIndex={-1} name={name} form={rest.form} required={required} disabled={disabled}
      className="sr-only" value={value} onChange={event => onChange(event.target.value)}
      onInvalid={() => triggerRef.current?.focus()}>
      {!items.some(item => item.value === '') && <option value="" />}
      {items.map(item => <option key={item.value} value={item.value} disabled={item.disabled}>{item.label}</option>)}
    </select>
    {present && createPortal(<div ref={panelRef} id={listId} role="listbox" tabIndex={-1}
      aria-labelledby={fieldId} aria-activedescendant={active >= 0 ? `${listId}-${active}` : undefined}
      data-state={expanded ? 'open' : 'closed'} data-input={inputMode} style={style} inert={!expanded}
      onKeyDown={handleKey}
      className="select-content z-50 flex flex-col overflow-hidden rounded-lg border border-border bg-surface p-1 text-sm text-text shadow-lg outline-none">
      {scrollEdges.up && <div aria-hidden="true" className="flex h-6 shrink-0 items-center justify-center text-text-muted"
        onPointerEnter={() => startScroll(-1)} onPointerLeave={stopScroll}>{"\u2303"}</div>}
      <div ref={viewportRef} data-panel-scroll="" onScroll={updateScrollEdges} className="min-h-0 overflow-y-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      {items.map((option, index) => <div key={option.value} id={`${listId}-${index}`} role="option"
        aria-selected={value === option.value} aria-disabled={option.disabled || undefined}
        data-state={value === option.value ? 'checked' : 'unchecked'} data-disabled={option.disabled ? '' : undefined}
        data-highlighted={active === index ? '' : undefined}
        onPointerMove={event => { if (event.pointerType !== 'touch' && !option.disabled) { setInputMode('pointer'); setActive(index) } }}
        onPointerLeave={() => { if (inputMode === 'pointer') setActive(-1) }}
        onClick={() => choose(index)}
        className="select-option relative flex min-h-9 cursor-default select-none items-center rounded-md py-2 pl-3 pr-9 outline-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50">
        {renderOption?.(option) ?? option.label}
        {value === option.value && <span className="absolute right-3 text-accent"><svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m5 12 4 4L19 6" /></svg></span>}
      </div>)}
      {items.length === 0 && <div className="px-3 py-2 text-text-muted">{emptyHint || 'Aucune valeur disponible.'}</div>}
      </div>
      {scrollEdges.down && <div aria-hidden="true" className="flex h-6 shrink-0 items-center justify-center text-text-muted"
        onPointerEnter={() => startScroll(1)} onPointerLeave={stopScroll}>{"\u2304"}</div>}
    </div>, document.body)}
  </>
  if (bare) return control
  return <div>
    <div className={label ? 'floating-field' : undefined} data-pinned={Boolean(label) || undefined}>
    {control}
    {label && <label htmlFor={fieldId}>{label}</label>}
    </div>
    {hint && !error && <p id={`${fieldId}-hint`} className="mt-1 text-xs text-text-muted">{emptyHint}</p>}
    {error && <p id={`${fieldId}-error`} className="mt-1 text-xs text-status-overdue">{error}</p>}
  </div>
})
