import { EmptyState, ErrorState, LoadingState, Pagination, cardClass, cellClass, documentPrimaryButton as primaryButton, documentSecondaryButton as secondaryButton, headingClass } from '../../components/ui'
import { errorMessage } from './documentModel'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { documentLabels, getClients, getData, dateLabel, money } from './documentModel'
import type { DocumentKind, DocumentRecord } from './documentModel'
import { InvoiceActions, PdfButton, StatusBadge, TotalsPanel } from './DocumentUI'

export function DocumentListPage({ kind }: { kind: DocumentKind }) {
  const [page, setPage] = useState(1)
  const labels = documentLabels[kind]
  const documents = useQuery({ queryKey: ['documents', kind, 'list', page], queryFn: ({ signal }) => getData<DocumentRecord[]>(`/${kind}/`, signal, { page, size: 20 }) })
  const clients = useQuery({ queryKey: ['document-clients'], queryFn: ({ signal }) => getClients(signal) })
  const names = new Map(clients.data?.map(client => [client.id, client.legal_name]))
  return <div className="space-y-6">
    <header className="flex flex-wrap items-center justify-between gap-4"><h1 className="text-2xl font-semibold">{labels.title}</h1><Link className={primaryButton} to={`/${kind}/new`}>{labels.create}</Link></header>
    {clients.isError && <ErrorState buttonClassName={secondaryButton} message={errorMessage(clients.error)} retry={() => { void clients.refetch() }} />}
    {documents.isPending ? <LoadingState /> : documents.isError ? <ErrorState buttonClassName={secondaryButton} message={errorMessage(documents.error)} retry={() => { void documents.refetch() }} /> : documents.data.length === 0 ?
      <EmptyState title={page === 1 ? `Aucun ${kind === 'invoices' ? 'document de facturation' : 'devis'} pour le moment` : 'Aucun autre document'} message={page === 1 ? 'Sélectionnez un client et ajoutez vos premières lignes.' : 'Revenez à la page précédente.'} icon={<svg aria-hidden="true" className="h-12 w-12 text-text-faint" viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="2"><rect x="12" y="5" width="26" height="38" rx="3" /><path d="M18 16h14M18 23h14M18 30h8" /></svg>} action={page === 1 && <Link className={primaryButton} to={`/${kind}/new`}>{labels.create}</Link>} /> : <div className="max-h-[65vh] overflow-auto rounded-xl border border-border bg-surface shadow-sm">
        <table className="w-full whitespace-nowrap text-left"><caption className="sr-only">{labels.title}, page {page}</caption>
          <thead><tr>{['Numéro', 'Client', 'Statut', 'Total TTC', 'Échéance', 'PDF'].map(label => <th key={label} scope="col" className={`${headingClass} ${label === 'Total TTC' || label === 'PDF' ? 'text-right' : ''}`}>{label}</th>)}</tr></thead>
          <tbody>{documents.data.map(doc => <tr key={doc.id} className="interactive-row border-t border-border even:bg-surface-muted">
            <td className={cellClass}><Link className="font-medium text-accent underline-offset-4 hover:underline" to={`/${kind}/${doc.id}`}>{doc.number}</Link></td>
            <td className={cellClass}>{doc.client_id ? names.get(doc.client_id) ?? (clients.isPending ? 'Chargement…' : 'Client indisponible') : 'Sans client'}</td>
            <td className={cellClass}><StatusBadge document={doc} /></td>
            <td className={`${cellClass} text-right font-semibold tabular-nums`}>{money(doc.total_ttc, doc.currency)}</td>
            <td className={cellClass}>{dateLabel(doc.due_at)}</td>
            <td className={`${cellClass} text-right`}><PdfButton documentId={doc.id} documentNumber={doc.number} compact /></td>
          </tr>)}</tbody>
        </table>
      </div>}
    <Pagination buttonClassName={secondaryButton} page={page} onChange={setPage} disabled={documents.isFetching} hasNext={!documents.isError && (documents.data?.length ?? 0) >= 20} />
  </div>
}

export function DocumentDetailPage({ kind }: { kind: DocumentKind }) {
  const { id } = useParams()
  const document = useQuery({ queryKey: ['documents', kind, 'detail', id], queryFn: ({ signal }) => getData<DocumentRecord>(`/${kind}/${id}`, signal), enabled: Boolean(id) })
  const clients = useQuery({ queryKey: ['document-clients'], queryFn: ({ signal }) => getClients(signal) })
  const doc = document.data
  return <div className="space-y-6">
    <Link className="text-accent hover:underline" to={`/${kind}`}>← {documentLabels[kind].title}</Link>
    {document.isPending ? <LoadingState /> : document.isError ? <ErrorState buttonClassName={secondaryButton} message={errorMessage(document.error)} retry={() => { void document.refetch() }} /> : doc && <>
      <header className="flex flex-wrap items-center justify-between gap-4"><div className="flex flex-wrap items-center gap-3"><h1 className="text-2xl font-semibold">{documentLabels[kind].singular} {doc.number}</h1><StatusBadge document={doc} /></div>{kind === 'invoices' ? <InvoiceActions key={doc.id} document={doc} /> : <PdfButton documentId={doc.id} documentNumber={doc.number} />}</header>
      {clients.isError && <ErrorState buttonClassName={secondaryButton} message={errorMessage(clients.error)} retry={() => { void clients.refetch() }} />}
      <dl className={`${cardClass} grid gap-6 sm:grid-cols-3`}>
        <div><dt className="mb-1 text-xs font-medium uppercase tracking-wide text-text-muted">Client</dt><dd>{doc.client_id ? clients.data?.find(c => c.id === doc.client_id)?.legal_name ?? (clients.isPending ? 'Chargement…' : 'Client indisponible') : 'Sans client'}</dd></div>
        <div><dt className="mb-1 text-xs font-medium uppercase tracking-wide text-text-muted">Date d’émission</dt><dd>{dateLabel(doc.issued_at)}</dd></div>
        <div><dt className="mb-1 text-xs font-medium uppercase tracking-wide text-text-muted">Échéance</dt><dd>{dateLabel(doc.due_at)}</dd></div>
      </dl>
      <div className="max-h-[65vh] overflow-auto rounded-xl border border-border bg-surface shadow-sm"><table className="w-full text-left"><caption className="sr-only">Lignes du document</caption>
        <thead><tr>{['Description', 'Quantité', 'Prix unitaire HT', 'Remise', 'TVA', 'Total TTC'].map((label, index) => <th scope="col" key={label} className={`${headingClass} whitespace-nowrap ${index ? 'text-right' : ''}`}>{label}</th>)}</tr></thead>
        <tbody>{[...doc.lines].sort((a, b) => a.position - b.position).map(line => <tr key={line.id} className="border-t border-border even:bg-surface-muted">
          <td className={`${cellClass} min-w-56 whitespace-pre-wrap`}>{line.description}</td>
          <td className={`${cellClass} text-right tabular-nums`}>{Number(line.quantity).toLocaleString('fr-FR')} {line.unit}</td>
          <td className={`${cellClass} whitespace-nowrap text-right tabular-nums`}>{money(line.unit_price_ht, doc.currency)}</td>
          <td className={`${cellClass} whitespace-nowrap text-right tabular-nums`}>{money(line.discount_amount, doc.currency)}{Number(line.discount_pct) !== 0 && <span className="block text-xs text-text-muted">{line.discount_pct} %</span>}</td>
          <td className={`${cellClass} text-right tabular-nums`}>{line.tax_rate_value} %</td>
          <td className={`${cellClass} whitespace-nowrap text-right font-semibold tabular-nums`}>{money(line.line_total_ttc, doc.currency)}</td>
        </tr>)}{doc.lines.length === 0 && <tr><td colSpan={6} className="p-6 text-center text-text-muted">Ce document ne contient aucune ligne.</td></tr>}</tbody>
      </table></div>
      <TotalsPanel totals={doc} currency={doc.currency} />
      {(doc.notes || doc.terms) && <div className={`${cardClass} grid gap-6 sm:grid-cols-2`}>{[['Notes', doc.notes], ['Conditions', doc.terms]].map(([label, value]) => value && <section key={label}><h2 className="mb-2 text-lg font-semibold">{label}</h2><p className="whitespace-pre-wrap text-text-muted">{value}</p></section>)}</div>}
    </>}
  </div>
}
