export type BadgeTone = 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled'

const dotClass: Record<BadgeTone, string> = {
  draft: 'bg-status-draft',
  sent: 'bg-status-sent',
  paid: 'bg-status-paid',
  overdue: 'bg-status-overdue',
  cancelled: 'bg-status-cancelled',
}

// A status always shows as a pastille + label (charte §5) — never colour or
// text alone. Map a domain status to a BadgeTone at the call site.
export function Badge({ tone, label, wrap = false }: { tone: BadgeTone; label: string; wrap?: boolean }) {
  return (
    <span className={`inline-flex items-center gap-2 ${wrap ? '' : 'whitespace-nowrap '}rounded-full border border-border px-2 py-1 text-xs`}>
      <span aria-hidden="true" className={`h-1.5 w-1.5 rounded-full ${dotClass[tone]}`} />
      {label}
    </span>
  )
}

export function ActiveBadge({ active, wrap }: { active?: boolean; wrap?: boolean }) {
  return <Badge wrap={wrap} tone={active ? 'paid' : 'draft'} label={active ? 'Actif' : 'Inactif'} />
}
