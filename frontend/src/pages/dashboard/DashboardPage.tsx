import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Badge, EmptyState, ErrorState, LoadingState, cardClass, cellClass, headingClass, primaryButton as primaryBtn } from '../../components/ui'
import type { BadgeTone } from '../../components/ui'
import { dateLabel, errorMessage, getClients, getData, money } from '../invoices/documentModel'
import type { DocumentRecord } from '../invoices/documentModel'
import type { PaymentRecord } from '../payments/paymentModel'

const statusMeta: Record<string, { label: string; tone: BadgeTone }> = {
  draft: { label: 'Brouillon', tone: 'draft' },
  sent: { label: 'Envoyée', tone: 'sent' },
  paid: { label: 'Payée', tone: 'paid' },
  partially_paid: { label: 'Partiellement payée', tone: 'sent' },
  overdue: { label: 'En retard', tone: 'overdue' },
  cancelled: { label: 'Annulée', tone: 'cancelled' },
}

function isOverdue(doc: DocumentRecord, now: number) {
  const due = doc.due_at ? new Date(doc.due_at.slice(0, 10) + 'T23:59:59').getTime() : Infinity
  return due < now && Number(doc.amount_due) > 0
}

function Kpi({ label, value, hint, tone }: { label: string; value: string; hint?: string; tone?: 'positive' | 'negative' }) {
  return (
    <div className={cardClass}>
      <div className="text-xs font-medium uppercase tracking-wide text-text-muted">{label}</div>
      <div className="mt-2 text-xl font-semibold tabular-nums">{value}</div>
      {hint && <div className={`mt-1 text-xs ${tone === 'negative' ? 'text-status-overdue' : tone === 'positive' ? 'text-money-positive' : 'text-text-muted'}`}>{hint}</div>}
    </div>
  )
}

// Bar chart, one hue (accent): magnitude over time. Native <title> ships the
// hover layer (exact value) without a custom tooltip component.
function RevenueChart({ buckets, currency }: { buckets: { label: string; value: number }[]; currency: string }) {
  const max = Math.max(1, ...buckets.map(b => b.value))
  return (
    <div className={cardClass}>
      <h2 className="mb-5 text-sm font-semibold">Facturation des 6 derniers mois</h2>
      <div className="flex h-40 items-end gap-3">
        {buckets.map(b => (
          <div key={b.label} className="flex flex-1 flex-col items-center gap-2">
            <div className="flex h-32 w-full items-end">
              <div
                className="w-full rounded-t bg-accent transition-[height] duration-300 ease-out"
                style={{ height: `${Math.max(2, (b.value / max) * 100)}%` }}
              >
                <title>{`${b.label} : ${money(b.value, currency)}`}</title>
              </div>
            </div>
            <span className="text-xs text-text-muted">{b.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// Three categories, each with a distinct meaning (paid/pending/overdue): status
// colors carry identity, direct labels since there are only three bars.
function StatusChart({ rows, currency }: { rows: { label: string; value: number; tone: BadgeTone }[]; currency: string }) {
  const max = Math.max(1, ...rows.map(r => r.value))
  const toneBar: Record<BadgeTone, string> = { paid: 'bg-status-paid', sent: 'bg-status-sent', overdue: 'bg-status-overdue', draft: 'bg-status-draft', cancelled: 'bg-status-cancelled' }
  return (
    <div className={cardClass}>
      <h2 className="mb-5 text-sm font-semibold">Répartition des factures</h2>
      <div className="space-y-4">
        {rows.map(r => (
          <div key={r.label}>
            <div className="mb-1 flex items-center justify-between text-xs">
              <span className="font-medium text-text-muted">{r.label}</span>
              <span className="font-semibold tabular-nums">{money(r.value, currency)}</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-surface-muted">
              <div className={`h-full rounded-full ${toneBar[r.tone]} transition-[width] duration-300 ease-out`} style={{ width: `${Math.max(2, (r.value / max) * 100)}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export function DashboardPage() {
  const [now] = useMemo(() => [Date.now()], [])
  // shortcut: aggregates only the 100 most recent invoices/payments (no server-side stats
  // endpoint yet). Upgrade: add a backend aggregation endpoint if volume grows past this.
  const invoices = useQuery({
    queryKey: ['dashboard', 'invoices'],
    queryFn: ({ signal }) => getData<DocumentRecord[]>('/invoices/', signal, { page: 1, size: 100 }),
  })
  const payments = useQuery({
    queryKey: ['dashboard', 'payments'],
    queryFn: ({ signal }) => getData<PaymentRecord[]>('/payments/', signal, { page: 1, size: 100 }),
  })
  const clients = useQuery({ queryKey: ['document-clients'], queryFn: ({ signal }) => getClients(signal) })
  const names = new Map(clients.data?.map(client => [client.id, client.legal_name]))

  const loading = invoices.isPending || payments.isPending
  const failed = invoices.isError ? invoices : payments.isError ? payments : null

  const rows = invoices.data ?? []
  const currency = rows[0]?.currency ?? 'MAD'
  const totalInvoiced = rows.reduce((sum, doc) => sum + Number(doc.total_ttc), 0)
  const totalCollected = (payments.data ?? []).reduce((sum, p) => sum + Number(p.amount_allocated), 0)
  const overdueDocs = rows.filter(doc => isOverdue(doc, now))
  const totalOverdue = overdueDocs.reduce((sum, doc) => sum + Number(doc.amount_due), 0)
  const pendingDocs = rows.filter(doc => Number(doc.amount_due) > 0 && !isOverdue(doc, now))
  const totalPending = pendingDocs.reduce((sum, doc) => sum + Number(doc.amount_due), 0)
  const recent = [...rows].sort((a, b) => b.number.localeCompare(a.number)).slice(0, 8)

  // shortcut: buckets only issued (non-draft) documents by calendar month, last 6
  // months including the current one. Upgrade: a backend monthly-totals endpoint.
  const monthFmt = new Intl.DateTimeFormat('fr-FR', { month: 'short' })
  const monthBuckets = Array.from({ length: 6 }, (_, i) => {
    const d = new Date()
    d.setMonth(d.getMonth() - (5 - i), 1)
    return { year: d.getFullYear(), month: d.getMonth(), label: monthFmt.format(d).replace('.', '') }
  }).map(bucket => ({
    label: bucket.label,
    value: rows
      .filter(doc => {
        const issued = new Date(doc.issued_at ?? doc.created_at)
        return issued.getFullYear() === bucket.year && issued.getMonth() === bucket.month
      })
      .reduce((sum, doc) => sum + Number(doc.total_ttc), 0),
  }))
  const totalPaidAmount = rows.filter(doc => doc.status === 'paid').reduce((sum, doc) => sum + Number(doc.total_ttc), 0)
  const statusRows: { label: string; value: number; tone: BadgeTone }[] = [
    { label: 'Payées', value: totalPaidAmount, tone: 'paid' },
    { label: 'En attente', value: totalPending, tone: 'sent' },
    { label: 'En retard', value: totalOverdue, tone: 'overdue' },
  ]

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Tableau de bord</h1>
          <p className="text-sm text-text-muted">Vue d’ensemble de votre activité de facturation.</p>
        </div>
        <Link className={primaryBtn} to="/invoices/new">+ Nouvelle facture</Link>
      </header>

      {failed ? (
        <ErrorState message={errorMessage(failed.error)} retry={() => { void invoices.refetch(); void payments.refetch() }} />
      ) : loading ? (
        <LoadingState />
      ) : rows.length === 0 ? (
        <EmptyState
          title="Aucune facture pour le moment"
          message="Créez votre première facture pour voir apparaître vos indicateurs ici."
          action={<Link className={primaryBtn} to="/invoices/new">+ Nouvelle facture</Link>}
        />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Kpi label="Montant facturé" value={money(totalInvoiced, currency)} hint={`${rows.length} document${rows.length > 1 ? 's' : ''}`} />
            <Kpi label="Encaissé" value={money(totalCollected, currency)} tone="positive" hint={`${(payments.data ?? []).length} paiement${(payments.data ?? []).length > 1 ? 's' : ''}`} />
            <Kpi label="En attente" value={money(totalPending, currency)} hint={`${pendingDocs.length} facture${pendingDocs.length > 1 ? 's' : ''} à suivre`} />
            <Kpi label="En retard" value={money(totalOverdue, currency)} tone={overdueDocs.length > 0 ? 'negative' : undefined} hint={overdueDocs.length > 0 ? `${overdueDocs.length} à relancer` : 'Aucune relance à faire'} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <RevenueChart buckets={monthBuckets} currency={currency} />
            <StatusChart rows={statusRows} currency={currency} />
          </div>

          <div className="overflow-hidden rounded-xl border border-border bg-surface shadow-sm">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <h2 className="text-sm font-semibold">Factures récentes</h2>
              <Link to="/invoices" className="text-xs font-medium text-accent hover:underline">Voir toutes les factures</Link>
            </div>
            <table className="w-full whitespace-nowrap text-left">
              <thead><tr>{['Numéro', 'Client', 'Statut', 'Total TTC', 'Échéance'].map(label => <th key={label} scope="col" className={`${headingClass} ${label === 'Total TTC' ? 'text-right' : ''}`}>{label}</th>)}</tr></thead>
              <tbody>
                {recent.map(doc => {
                  const meta = statusMeta[isOverdue(doc, now) ? 'overdue' : doc.status] ?? statusMeta.draft
                  return (
                    <tr key={doc.id} className="interactive-row border-t border-border even:bg-surface-muted">
                      <td className={cellClass}><Link className="font-medium text-accent underline-offset-4 hover:underline" to={`/invoices/${doc.id}`}>{doc.number}</Link></td>
                      <td className={cellClass}>{doc.client_id ? names.get(doc.client_id) ?? '—' : 'Sans client'}</td>
                      <td className={cellClass}><Badge tone={meta.tone} label={meta.label} /></td>
                      <td className={`${cellClass} text-right font-semibold tabular-nums`}>{money(doc.total_ttc, doc.currency)}</td>
                      <td className={cellClass}>{dateLabel(doc.due_at)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
