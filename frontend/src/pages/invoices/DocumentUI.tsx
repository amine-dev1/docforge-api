import { Badge, Button, TextField, cardClass, documentSecondaryButton as secondaryButton } from '../../components/ui'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../lib/api'
import { getData, errorMessage } from './documentModel'
import type { IntegrationStatus } from '../settings/IntegrationsPage'
import { useState } from 'react'
import type { Amount, DocumentRecord } from './documentModel'
import { openDocumentPdf, money } from './documentModel'

import type { BadgeTone } from '../../components/ui'

export function InvoiceActions({ document: doc }: { document: DocumentRecord }) {
  const cache = useQueryClient()
  const profile = useQuery({ queryKey: ['integrations'], queryFn: ({ signal }) => getData<IntegrationStatus>('/tenant/me', signal) })
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [url, setUrl] = useState('')
  async function act(action: 'send' | 'stripe-checkout') {
    setBusy(action); setError(''); setMessage('')
    try {
      const response = await api.post(`/invoices/${doc.id}/${action}`)
      if (action === 'stripe-checkout') setUrl(response.data.data.url)
      else {
        cache.setQueryData(['documents', 'invoices', 'detail', doc.id], response.data.data)
        void cache.invalidateQueries({ queryKey: ['documents', 'invoices', 'list'] })
        setMessage('Email envoyé au client.')
        if (doc.client_id) {
          try {
            const client = await getData<{ email: string }>(`/clients/${doc.client_id}`)
            setMessage(`Email envoyé à ${client.email}.`)
          } catch { /* Delivery succeeded even if refreshing recipient details failed. */ }
        }
      }
    } catch (reason) { setError(errorMessage(reason)) }
    finally { setBusy('') }
  }
  return <div className="w-full space-y-3">
    <div className="flex flex-wrap justify-end gap-3">
      <PdfButton documentId={doc.id} documentNumber={doc.number} />
      <Button disabled={Boolean(busy)} onClick={() => { void act('send') }}>{busy === 'send' ? 'Envoi…' : 'Envoyer par email'}</Button>
      {profile.data?.stripe_connected && Number(doc.amount_due) > 0 && <Button disabled={Boolean(busy)} onClick={() => { void act('stripe-checkout') }}>{busy === 'stripe-checkout' ? 'Création…' : 'Lien de paiement Stripe'}</Button>}
    </div>
    {profile.isError && <p role="alert" className="text-sm text-status-overdue">{errorMessage(profile.error)} <button type="button" className="underline" onClick={() => { void profile.refetch() }}>Réessayer</button></p>}
    {error && <p role="alert" className="text-sm text-status-overdue">{error}</p>}
    {message && <p role="status" className="text-sm text-text-muted">{message}</p>}
    {url && <div className={`${cardClass} space-y-3`}><TextField label="Lien de paiement Stripe" value={url} readOnly onFocus={event => event.target.select()} /><Button onClick={async () => { try { await navigator.clipboard.writeText(url); setMessage('Lien copié.'); setError('') } catch { setError('Copie indisponible. Sélectionnez et copiez le lien manuellement.') } }}>Copier le lien</Button><p className="text-sm text-text-muted">Après paiement, enregistrez le règlement manuellement dans DocForge.</p></div>}
  </div>
}

const statuses: Record<string, { label: string; tone: BadgeTone }> = {
  draft: { label: 'Brouillon', tone: 'draft' },
  sent: { label: 'Envoyé', tone: 'sent' },
  paid: { label: 'Payé', tone: 'paid' },
  overdue: { label: 'En retard', tone: 'overdue' },
  cancelled: { label: 'Annulé', tone: 'cancelled' },
}
export function StatusBadge({ document }: { document: DocumentRecord }) {
  const [now] = useState(() => Date.now())
  const due = document.due_at ? new Date(document.due_at.slice(0, 10) + 'T23:59:59').getTime() : Infinity
  const overdue = due < now && Number(document.amount_due) > 0
  const status = statuses[document.status] ?? { label: document.status, tone: 'draft' }
  // Keep a server status visible, but only use the alert color for an elapsed due date.
  const tone = document.status === 'overdue' && !overdue ? 'draft' : status.tone
  return <Badge tone={tone} label={status.label} />
}
export function PdfButton({ documentId, documentNumber, compact = false }: { documentId: string; documentNumber: string; compact?: boolean }) {
  const [state, setState] = useState<'idle' | 'loading' | 'error'>('idle')
  const onClick = async () => {
    setState('loading')
    try {
      await openDocumentPdf(documentId, documentNumber)
      setState('idle')
    } catch {
      setState('error')
    }
  }
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={state === 'loading'}
      className={`press ${compact ? 'text-accent underline underline-offset-4 disabled:opacity-50' : secondaryButton}`}
    >
      {state === 'loading' ? 'Génération…' : compact ? 'PDF' : 'Télécharger le PDF'}
      {state === 'error' && <span className="ml-2 text-xs text-status-overdue">Échec, réessayez</span>}
    </button>
  )
}
type Totals = Pick<DocumentRecord, 'subtotal_ht' | 'total_discount' | 'total_tax' | 'total_ttc'> & Partial<Pick<DocumentRecord, 'amount_paid' | 'amount_due'>>
export function TotalsPanel({ totals, currency }: { totals: Totals; currency: string }) {
  const rows: [string, Amount][] = [['Remise incluse', totals.total_discount], ['Total HT après remise', totals.subtotal_ht], ['TVA', totals.total_tax], ['Total TTC', totals.total_ttc]]
  if (totals.amount_paid != null) rows.push(['Montant payé', totals.amount_paid])
  if (totals.amount_due != null) rows.push(['Reste à payer', totals.amount_due])
  return <dl className={`${cardClass} ml-auto w-full max-w-sm space-y-3`}>{rows.map(([label, amount]) => <div key={label} className={`flex justify-between gap-4 ${label === 'Total TTC' ? 'border-t border-border pt-3 text-lg font-semibold' : ''}`}><dt className="text-text-muted">{label}</dt><dd className="text-right font-semibold tabular-nums">{money(amount, currency)}</dd></div>)}</dl>
}
