// Shared className tokens — the single source of truth for component styling.
// Every value here traces back to frontend/DESIGN_SYSTEM.md; nothing styled
// outside this file should hardcode a token these already cover.

export const cardClass = 'rounded-xl border border-border bg-surface p-5 shadow-sm'
export const cellClass = 'h-12 px-4 py-2'
export const headingClass = 'sticky top-0 bg-surface-muted px-4 py-3 text-xs font-medium uppercase tracking-wide text-text-muted'
export const labelClass = 'mb-1 block text-xs font-medium uppercase tracking-wide text-text-muted'

export const inputClass = 'field-control unified-control w-full text-sm outline-none'
export const textareaClass = `${inputClass} unified-textarea`

const buttonBase =
  'press focus-ring inline-flex h-9 items-center justify-center gap-2 rounded-lg px-4 text-sm font-medium disabled:opacity-50 disabled:pointer-events-none'
export const primaryButton = `${buttonBase} bg-accent text-[var(--accent-contrast)] hover:bg-accent-hover`
export const secondaryButton = `${buttonBase} border border-border hover:bg-surface-muted`
export const destructiveButton = `${buttonBase} bg-status-overdue text-white hover:bg-[color-mix(in_srgb,var(--status-overdue)_85%,black)]`

// Existing document/CRM/catalogue/payment appearance, retained during migration.
export const documentPrimaryButton = 'inline-flex h-9 items-center justify-center rounded-lg bg-accent px-4 font-medium text-[var(--accent-contrast)] hover:bg-accent-hover focus-visible:outline-2 focus-visible:outline-accent disabled:opacity-50'
export const documentSecondaryButton = 'inline-flex h-9 items-center justify-center rounded-lg border border-border px-4 font-medium hover:bg-surface-muted focus-visible:outline-2 focus-visible:outline-accent disabled:opacity-50'
