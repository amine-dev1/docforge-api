import { ActiveBadge, Button, EmptyState, ErrorState, LoadingState, Pagination, SelectField, cardClass, cellClass, documentPrimaryButton as primaryButton, documentSecondaryButton as secondaryButton, headingClass, inputClass } from '../../components/ui'
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { NavLink } from 'react-router-dom'
import { api } from '../../lib/api'
import { getData } from '../invoices/documentModel'
import { CatalogueForm } from './CatalogueForm'
import { catalogueError, labels, productTypes } from './catalogueModel'
import type { CatalogueKind, CatalogueRecord } from './catalogueModel'

const number = new Intl.NumberFormat('fr-MA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
function ActionIcon({ remove }: { remove?: boolean }) {
  return <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">{remove ? <><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 10v7m4-7v7" /></> : <><path d="m14 5 5 5M4 20l5-1L20 8a2 2 0 0 0-5-5L4 14z" /></>}</svg>
}

export function CataloguePage({ kind }: { kind: CatalogueKind }) {
  const [page, setPage] = useState(1)
  const [active, setActive] = useState('all')
  const [editor, setEditor] = useState<CatalogueRecord | 'new' | null>(null)
  const [removing, setRemoving] = useState<CatalogueRecord | null>(null)
  const [notice, setNotice] = useState('')
  const client = useQueryClient()
  const products = kind === 'products'
  const records = useQuery({
    queryKey: products ? ['catalogue', kind, page, active] : ['catalogue', kind],
    queryFn: ({ signal }) => getData<CatalogueRecord[]>(`/catalogue/${kind}/`, signal, products ? { page, size: 20, ...(active === 'all' ? {} : { is_active: active === 'active' }) } : undefined),
  })
  const invalidate = () => { void client.invalidateQueries({ queryKey: ['catalogue'] }) }
  const deletion = useMutation({
    retry: false,
    mutationFn: (record: CatalogueRecord) => api.delete(`/catalogue/${kind}/${record.id}`),
    onSuccess: () => {
      setRemoving(null)
      setNotice(products ? 'Produit désactivé.' : 'Élément supprimé.')
      if (page > 1 && records.data?.length === 1) setPage(page - 1)
      invalidate()
    },
  })
  const rows = records.data ?? []
  const visibleRows = products ? rows : [...rows].sort((a, b) => kind === 'categories' ? (a.sort_order ?? 0) - (b.sort_order ?? 0) || a.name.localeCompare(b.name, 'fr') : a.name.localeCompare(b.name, 'fr')).slice((page - 1) * 20, page * 20)
  const columns = kind === 'products' ? ['Code', 'Nom', 'Type', 'Achat HT', 'Vente HT', 'Statut'] : kind === 'categories' ? ['Code', 'Nom', 'Catégorie parente', 'Ordre'] : kind === 'units' ? ['Nom', 'Symbole', 'Par défaut'] : ['Nom', 'Libellé', 'Taux', 'Type', 'Par défaut', 'Statut']
  const create = () => { setNotice(''); setEditor('new'); setRemoving(null) }
  return <div className="space-y-6">
    <header className="flex flex-wrap items-center justify-between gap-4"><h1 className="text-2xl font-semibold">{labels[kind].title}</h1><Button classNameOverride={primaryButton} variant="primary" type="button" disabled={editor !== null || deletion.isPending} onClick={create} >{labels[kind].create}</Button></header>
    <nav aria-label="Catalogue" className="flex flex-wrap gap-2">{(Object.keys(labels) as CatalogueKind[]).map(tab => <NavLink key={tab} to={`/catalogue/${tab}`} className={({ isActive }) => `${secondaryButton} press ${isActive ? 'bg-surface-muted text-accent' : ''}`}>{labels[tab].title}</NavLink>)}</nav>
    {notice && <p role="status" className="text-text-muted">{notice}</p>}
    {editor && <CatalogueForm key={typeof editor === 'string' ? 'new' : editor.id} kind={kind} record={editor === 'new' ? undefined : editor} onCancel={() => setEditor(null)} onSaved={() => { setNotice(editor === 'new' ? 'Élément créé.' : 'Modifications enregistrées.'); setEditor(null); invalidate() }} />}
    {removing && <section className={cardClass} aria-labelledby="delete-title">
      <h2 id="delete-title" className="text-lg font-semibold">{products ? 'Désactiver' : 'Supprimer'} « {removing.name} » ?</h2>
      <p className="mt-2 text-text-muted">{products ? 'Le produit restera dans le catalogue et pourra être réactivé en modifiant sa fiche.' : 'Cette suppression est définitive et peut retirer les associations à cet élément.'}</p>
      {deletion.isError && <p role="alert" className="mt-3 text-status-overdue">{catalogueError(deletion.error)}</p>}
      <div className="mt-4 flex justify-end gap-3"><Button classNameOverride={secondaryButton} variant="secondary" type="button" disabled={deletion.isPending} onClick={() => setRemoving(null)}>Annuler</Button><Button variant="destructive" type="button" disabled={deletion.isPending} onClick={() => deletion.mutate(removing)}>{deletion.isPending ? 'Traitement…' : products ? 'Confirmer la désactivation' : 'Confirmer la suppression'}</Button></div>
    </section>}
    {products && <div className="max-w-xs"><SelectField label="Statut" id="catalogue-status" className={inputClass} value={active} onChange={value => { setActive(value); setPage(1) }} options={[{ value: 'all', label: 'Tous les produits' }, { value: 'active', label: 'Actifs' }, { value: 'inactive', label: 'Inactifs' }]} /></div>}
    {records.isPending ? <LoadingState /> : records.isError ? <ErrorState buttonClassName={secondaryButton} message={catalogueError(records.error)} retry={() => { void records.refetch() }} /> : visibleRows.length === 0 ?
      <EmptyState title="Aucun élément à afficher" message={page > 1 ? 'Revenez à la page précédente.' : products && active !== 'all' ? 'Aucun produit ne correspond à ce statut.' : 'Ajoutez votre premier élément au catalogue.'} icon={<svg aria-hidden="true" className="h-12 w-12 text-text-faint" viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="2"><path d="m6 14 18-8 18 8v22l-18 8-18-8zM6 14l18 8 18-8M24 22v22M15 10l18 8" /></svg>} action={page === 1 && <Button classNameOverride={primaryButton} variant="primary" type="button" disabled={editor !== null || deletion.isPending}  onClick={create}>{labels[kind].create}</Button>} /> : <div className="max-h-[65vh] overflow-auto rounded-xl border border-border bg-surface shadow-sm">
        <table className="w-full whitespace-nowrap text-left"><caption className="sr-only">{labels[kind].title}, page {page}</caption><thead><tr>{[...columns, 'Actions'].map(label => <th key={label} scope="col" className={`${headingClass} ${['Code', 'Achat HT', 'Vente HT', 'Taux', 'Ordre', 'Actions'].includes(label) ? 'text-right' : ''}`}>{label}</th>)}</tr></thead>
          <tbody>{visibleRows.map(row => <tr key={row.id} className="interactive-row border-t border-border even:bg-surface-muted">
            {(kind === 'products' || kind === 'categories') && <td className={`${cellClass} text-right font-medium tabular-nums`}>{row.code || '—'}</td>}
            <td className={`${cellClass} font-medium`}>{row.name}</td>
            {kind === 'products' && <><td className={cellClass}>{productTypes[row.type as keyof typeof productTypes] ?? row.type}</td><td className={`${cellClass} text-right font-medium tabular-nums`}>{number.format(Number(row.purchase_price_ht))}</td><td className={`${cellClass} text-right font-medium tabular-nums`}>{number.format(Number(row.sale_price_ht))}</td><td className={cellClass}><ActiveBadge wrap active={row.is_active} /></td></>}
            {kind === 'categories' && <><td className={cellClass}>{rows.find(parent => parent.id === row.parent_id)?.name ?? '—'}</td><td className={`${cellClass} text-right tabular-nums`}>{row.sort_order}</td></>}
            {kind === 'units' && <><td className={cellClass}>{row.symbol}</td><td className={cellClass}>{row.is_default ? 'Oui' : 'Non'}</td></>}
            {kind === 'tax-rates' && <><td className={cellClass}>{row.label}</td><td className={`${cellClass} text-right font-medium tabular-nums`}>{number.format(Number(row.rate))} %</td><td className={cellClass}>{row.type}</td><td className={cellClass}>{row.is_default ? 'Oui' : 'Non'}</td><td className={cellClass}><ActiveBadge wrap active={row.is_active} /></td></>}
            <td className={cellClass}><div className="flex justify-end gap-2"><Button classNameOverride={`${secondaryButton} press`} variant="secondary" type="button" disabled={editor !== null || deletion.isPending} aria-label={`Modifier ${row.name}`} title="Modifier" onClick={() => { setNotice(''); setRemoving(null); setEditor(row) }}><ActionIcon /></Button><Button variant="destructive" type="button" disabled={editor !== null || deletion.isPending || (products && !row.is_active)} aria-label={`${products ? 'Désactiver' : 'Supprimer'} ${row.name}`} title={products ? 'Désactiver' : 'Supprimer'} onClick={() => { deletion.reset(); setNotice(''); setRemoving(row) }}><ActionIcon remove /></Button></div></td>
          </tr>)}</tbody>
        </table>
      </div>}
    <Pagination buttonClassName={secondaryButton} page={page} onChange={setPage} disabled={records.isFetching || deletion.isPending} hasNext={!records.isError && (products ? rows.length >= 20 : page * 20 < rows.length)} />
  </div>
}
