import { useLayoutEffect, useRef, useState } from 'react'
import type { CSSProperties } from 'react'

// Shared positioning and presence only; each control owns its interaction model.
export function useFloatingPanel(open: boolean, close: () => void, matchWidth = false) {
  const triggerRef = useRef<HTMLButtonElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)
  const closeRef = useRef(close)
  const [present, setPresent] = useState(open)
  const [style, setStyle] = useState<CSSProperties>({ position: 'fixed', visibility: 'hidden' })
  useLayoutEffect(() => { closeRef.current = close })
  useLayoutEffect(() => {
    if (open) {
      setPresent(true)
      return
    }
    const timer = window.setTimeout(() => setPresent(false), 130)
    return () => window.clearTimeout(timer)
  }, [open])
  useLayoutEffect(() => {
    if (!open || !present) return
    const trigger = triggerRef.current
    const panel = panelRef.current
    if (!trigger || !panel) return
    const position = () => {
      const rect = trigger.getBoundingClientRect()
      const margin = 12, offset = 6
      const width = Math.min(matchWidth ? rect.width : panel.offsetWidth, window.innerWidth - margin * 2)
      const below = Math.max(0, window.innerHeight - rect.bottom - offset - margin)
      const above = Math.max(0, rect.top - offset - margin)
      const viewport = panel.querySelector<HTMLElement>('[data-panel-scroll]')
      const overflow = viewport ? viewport.scrollHeight - viewport.clientHeight : 0
      const naturalHeight = Math.min(panel.scrollHeight + overflow + 2, matchWidth ? 20 * parseFloat(getComputedStyle(document.documentElement).fontSize) : Infinity)
      const topSide = below < naturalHeight && above > below
      const available = topSide ? above : below
      const height = Math.min(naturalHeight, available)
      setStyle({ position: 'fixed', left: Math.max(margin, Math.min(rect.left, window.innerWidth - width - margin)),
        top: topSide ? Math.max(margin, rect.top - offset - height) : rect.bottom + offset,
        ...(matchWidth ? { width } : {}),
        '--trigger-width': matchWidth ? `${width}px` : undefined,
        '--panel-available-height': `${available}px`,
        '--panel-max-height': matchWidth ? '20rem' : `${available}px`,
        '--panel-transform-origin': topSide ? 'center bottom' : 'center top',
      } as CSSProperties)
    }
    position()
    const observer = new ResizeObserver(position)
    observer.observe(trigger)
    observer.observe(panel)
    window.addEventListener('resize', position)
    window.addEventListener('scroll', position, true)
    const outside = (event: PointerEvent) => {
      if (!panel.contains(event.target as Node) && !trigger.contains(event.target as Node)) closeRef.current()
    }
    const escape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { event.preventDefault(); closeRef.current(); trigger.focus() }
    }
    document.addEventListener('pointerdown', outside)
    document.addEventListener('keydown', escape)
    return () => {
      observer.disconnect()
      window.removeEventListener('resize', position)
      window.removeEventListener('scroll', position, true)
      document.removeEventListener('pointerdown', outside)
      document.removeEventListener('keydown', escape)
    }
  }, [open, present, matchWidth])
  return { triggerRef, panelRef, present: open || present, style }
}
