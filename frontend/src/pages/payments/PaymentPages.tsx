import { Badge, EmptyState, ErrorState, LoadingState, Pagination, cellClass, documentPrimaryButton as primaryButton, documentSecondaryButton as secondaryButton, headingClass } from '../../components/ui'
import type { BadgeTone } from '../../components/ui'
import { errorMessage } from '../invoices/documentModel'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { dateLabel, getClients, getData, money } from '../invoices/documentModel'
import { methods } from './paymentModel'
import type { PaymentRecord } from './paymentModel'
import { PaymentForm } from './PaymentForm'

export function PaymentStatus({ status }: { status: string }) {
  const states: Record<string, [string, BadgeTone]> = {
    pending: ['À allouer', 'draft'], partial: ['Partiellement alloué', 'sent'],
    allocated: ['Alloué', 'paid'], confirmed: ['Confirmé', 'paid'],
    rejected: ['Rejeté', 'overdue'], cancelled: ['Annulé', 'cancelled'],
  }
  const [label, tone] = states[status] ?? [status, 'draft']
  return <Badge tone={tone} label={label} />
}

export function PaymentListPage() {
  const [page, setPage] = useState(1)
  const payments = useQuery({ queryKey: ['payments', 'list', page], queryFn: ({ signal }) => getData<PaymentRecord[]>('/payments/', signal, { page, size: 20 }) })
  const clients = useQuery({ queryKey: ['document-clients'], queryFn: ({ signal }) => getClients(signal) })
  const rows = payments.data ?? []
  return <div className="space-y-6">
    <header className="flex flex-wrap items-center justify-between gap-4"><h1 className="text-2xl font-semibold">Paiements</h1><Link to="/payments/new" className={`${primaryButton} press`}>Nouveau paiement</Link></header>
    {payments.isPending || clients.isPending ? <LoadingState /> : payments.isError || clients.isError ? <ErrorState buttonClassName={secondaryButton} message={errorMessage(payments.error ?? clients.error)} retry={() => { void payments.refetch(); void clients.refetch() }} /> : rows.length === 0 ?
      <EmptyState title="Aucun paiement à afficher" message={page > 1 ? 'Revenez à la page précédente.' : 'Enregistrez un paiement et répartissez-le sur les factures de votre client.'} icon={<svg aria-hidden="true" className="h-12 w-12 text-text-faint" viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="2"><rect x="5" y="10" width="38" height="28" rx="4" /><path d="M5 19h38M12 30h10" /></svg>} action={page === 1 && <Link to="/payments/new" className={`${primaryButton} press`}>Nouveau paiement</Link>} /> : <div className="max-h-[65vh] overflow-auto rounded-xl border border-border bg-surface shadow-sm">
        <table className="w-full whitespace-nowrap text-left"><caption className="sr-only">Paiements, page {page}</caption><thead><tr>{['Référence', 'Client', 'Méthode', 'Montant', 'Alloué', 'Restant', 'Statut', 'Date'].map((label, index) => <th key={label} scope="col" className={`${headingClass} ${[0, 3, 4, 5].includes(index) ? 'text-right' : ''}`}>{label}</th>)}</tr></thead>
          <tbody>{rows.map(row => <tr key={row.id} className="interactive-row border-t border-border even:bg-surface-muted">
            <td className={`${cellClass} text-right font-medium tabular-nums`}><Link to={`/payments/${row.id}`} className="text-accent underline underline-offset-4">{row.reference}</Link></td>
            <td className={cellClass}>{clients.data?.find(client => client.id === row.client_id)?.legal_name ?? (row.client_id ? 'Client indisponible' : 'Sans client')}</td>
            <td className={cellClass}>{methods[row.method] ?? row.method}</td>
            {[row.amount, row.amount_allocated, row.amount_remaining].map((value, index) => <td key={index} className={`${cellClass} text-right font-medium tabular-nums`}>{money(value, row.currency)}</td>)}
            <td className={cellClass}><PaymentStatus status={row.status} /></td><td className={cellClass}>{dateLabel(row.payment_date)}</td>
          </tr>)}</tbody>
        </table>
      </div>}
    <Pagination buttonClassName={`${secondaryButton} press`} page={page} onChange={setPage} disabled={payments.isFetching} hasNext={!payments.isError && (payments.data?.length ?? 0) >= 20} className="flex items-center justify-end gap-3" />
  </div>
}

export function PaymentDetailPage() {
  const { id } = useParams()
  const payment = useQuery({ queryKey: ['payments', 'detail', id], queryFn: ({ signal }) => getData<PaymentRecord>(`/payments/${id}`, signal), enabled: Boolean(id) })
  if (payment.isPending) return <LoadingState />
  if (payment.isError) return <ErrorState buttonClassName={secondaryButton} message={errorMessage(payment.error)} retry={() => { void payment.refetch() }} />
  return <PaymentForm key={payment.data.id} record={payment.data} />
}
export function PaymentCreatePage() { return <PaymentForm /> }
