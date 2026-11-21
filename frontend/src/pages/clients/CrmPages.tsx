import { ActiveBadge, EmptyState, ErrorState, LoadingState, Pagination, cellClass, documentPrimaryButton as primaryButton, documentSecondaryButton as secondaryButton, headingClass } from '../../components/ui'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { crmError, crmLabels, getData } from './crmModel'
import type { CrmKind, CrmRecord } from './crmModel'
import { CrmFormPage } from './CrmFormPage'

export function CrmListPage({ kind }: { kind: CrmKind }) {
  const [page, setPage] = useState(1)
  const labels = crmLabels[kind]
  const records = useQuery({ queryKey: ['crm', kind, 'list', page], queryFn: ({ signal }) => getData<CrmRecord[]>(`/${kind}/`, signal, { page, size: 20 }) })
  return <div className="space-y-6">
    <header className="flex flex-wrap items-center justify-between gap-4"><h1 className="text-2xl font-semibold">{labels.title}</h1><Link className={primaryButton} to={`/${kind}/new`}>{labels.create}</Link></header>
    {records.isPending ? <LoadingState /> : records.isError ? <ErrorState buttonClassName={secondaryButton} message={crmError(records.error)} retry={() => { void records.refetch() }} /> : records.data.length === 0 ?
      <EmptyState title={page === 1 ? `Aucun ${labels.singular} pour le moment` : `Aucun autre ${labels.singular}`} message={page === 1 ? 'Créez une première fiche et renseignez ses contacts.' : 'Revenez à la page précédente.'} icon={<svg aria-hidden="true" className="h-12 w-12 text-text-faint" viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="2"><rect x="8" y="6" width="32" height="36" rx="3" /><circle cx="24" cy="18" r="5" /><path d="M15 35v-3a9 9 0 0 1 18 0v3" /></svg>} action={page === 1 && <Link className={primaryButton} to={`/${kind}/new`}>{labels.create}</Link>} /> : <div className="max-h-[65vh] overflow-auto rounded-xl border border-border bg-surface shadow-sm">
        <table className="w-full whitespace-nowrap text-left"><caption className="sr-only">{labels.title}, page {page}</caption><thead><tr>{['Raison sociale', 'Ville', 'Téléphone / e-mail', 'Statut'].map(label => <th scope="col" key={label} className={headingClass}>{label}</th>)}</tr></thead>
          <tbody>{records.data.map(record => <tr key={record.id} className="interactive-row border-t border-border even:bg-surface-muted">
            <td className={cellClass}><Link className="font-medium text-accent underline-offset-4 hover:underline" to={`/${kind}/${record.id}`}>{String(record.legal_name)}</Link></td>
            <td className={cellClass}>{String(record.address_city || '—')}</td>
            <td className={cellClass}><span className="block">{String(record.phone || record.mobile || '—')}</span><span className="block text-xs text-text-muted">{String(record.email || '—')}</span></td>
            <td className={cellClass}><ActiveBadge active={Boolean(record.is_active)} /></td>
          </tr>)}</tbody>
        </table>
      </div>}
    <Pagination buttonClassName={secondaryButton} page={page} onChange={setPage} disabled={records.isFetching} hasNext={!records.isError && (records.data?.length ?? 0) >= 20} />
  </div>
}
export function CrmDetailPage({ kind }: { kind: CrmKind }) {
  const { id } = useParams()
  const record = useQuery({ queryKey: ['crm', kind, 'detail', id], queryFn: ({ signal }) => getData<CrmRecord>(`/${kind}/${id}`, signal), enabled: Boolean(id) })
  return record.isPending ? <LoadingState /> : record.isError ? <div className="space-y-6"><Link className="text-accent hover:underline" to={`/${kind}`}>← {crmLabels[kind].title}</Link><ErrorState buttonClassName={secondaryButton} message={crmError(record.error)} retry={() => { void record.refetch() }} /></div> : <CrmFormPage key={`${kind}-${id}`} kind={kind} record={record.data} />
}
