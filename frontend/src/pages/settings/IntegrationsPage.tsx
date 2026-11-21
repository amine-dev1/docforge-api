import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../lib/api'
import { Badge, Button, ErrorState, FormSection, LoadingState, TextField, cellClass, headingClass } from '../../components/ui'
import { errorMessage, getData, money } from '../invoices/documentModel'

export interface IntegrationStatus {
  stripe_connected: boolean
  stripe_publishable_key: string | null
  id: string
  resend_connected: boolean
  resend_from_email: string | null
}
interface StripeDashboard {
  available: { amount: number; currency: string }[]
  payments: { id: string; amount: number; currency: string; status: string; date: number; description: string | null }[]
}

export function IntegrationsPage() {
  const cache = useQueryClient()
  const profile = useQuery({ queryKey: ['integrations'], queryFn: ({ signal }) => getData<IntegrationStatus>('/tenant/me', signal) })
  const dashboard = useQuery({ queryKey: ['stripe-dashboard'], queryFn: ({ signal }) => getData<StripeDashboard>('/tenant/integrations/stripe/dashboard', signal), enabled: Boolean(profile.data?.stripe_connected), retry: false })
  const [secret, setSecret] = useState('')
  const [publishable, setPublishable] = useState('')
  const [webhookSecret, setWebhookSecret] = useState('')
  const [resendKey, setResendKey] = useState('')
  const [fromEmail, setFromEmail] = useState('')
  const [resendBusy, setResendBusy] = useState(false)
  const [resendError, setResendError] = useState('')
  const [resendMessage, setResendMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  async function save(disconnect = false) {
    setBusy(true); setError(''); setMessage('')
    try {
      const response = disconnect
        ? await api.delete('/tenant/integrations/stripe')
        : await api.post('/tenant/integrations/stripe', { secret_key: secret.trim(), publishable_key: publishable.trim(), webhook_secret: webhookSecret.trim() || null })
      cache.setQueryData(['integrations'], response.data.data)
      if (disconnect) cache.removeQueries({ queryKey: ['stripe-dashboard'] })
      else await cache.resetQueries({ queryKey: ['stripe-dashboard'] })
      setSecret(''); setPublishable(''); setWebhookSecret('')
      setMessage(disconnect ? 'Stripe déconnecté.' : 'Stripe connecté.')
    } catch (reason) { setError(errorMessage(reason)) }
    finally { setBusy(false) }
  }
  async function saveResend(disconnect = false) {
    setResendBusy(true); setResendError(''); setResendMessage('')
    try {
      const response = disconnect
        ? await api.delete('/tenant/integrations/resend')
        : await api.post('/tenant/integrations/resend', { api_key: resendKey.trim(), from_email: fromEmail.trim() })
      cache.setQueryData(['integrations'], response.data.data)
      setResendKey(''); setFromEmail('')
      setResendMessage(disconnect ? 'Resend déconnecté.' : 'Resend connecté.')
    } catch (reason) { setResendError(errorMessage(reason)) }
    finally { setResendBusy(false) }
  }
  if (profile.isPending) return <LoadingState />
  if (profile.isError) return <ErrorState message={errorMessage(profile.error)} retry={() => { void profile.refetch() }} />
  const connected = profile.data.stripe_connected
  const resendConnected = profile.data.resend_connected
  const webhookUrl = `${window.location.origin}/api/v1/webhooks/stripe/${profile.data.id}`
  return <div className="space-y-6">
    <header><h1 className="text-2xl font-semibold">Intégrations</h1><p className="mt-2 text-sm text-text-muted">Paiements de votre entreprise et envoi des documents par email.</p></header>
    <FormSection title="Stripe — votre entreprise" defaultOpen>
      <div className="space-y-4">
        <Badge tone={connected ? 'paid' : 'draft'} label={connected ? 'Connecté' : 'Non connecté'} />
        <p className="text-sm text-text-muted">Connectez le compte Stripe de cette entreprise pour créer des liens de paiement sur vos factures.</p>
        {connected && <p className="break-all text-sm text-text-muted">Clé publique : {profile.data.stripe_publishable_key}</p>}
        <form onSubmit={event => { event.preventDefault(); void save() }} className="space-y-4">
          <fieldset disabled={busy || resendBusy} className="grid gap-4 sm:grid-cols-2">
            <TextField label="Clé secrète Stripe" type="password" autoComplete="new-password" value={secret} onChange={event => setSecret(event.target.value)} required maxLength={255} placeholder="sk_test_… ou sk_live_…" hint="La clé enregistrée n’est jamais affichée." />
            <TextField label="Clé publique Stripe" value={publishable} onChange={event => setPublishable(event.target.value)} required maxLength={255} placeholder="pk_test_… ou pk_live_…" />
            <TextField label="Clé de signature du webhook (optionnelle)" type="password" autoComplete="new-password" value={webhookSecret} onChange={event => setWebhookSecret(event.target.value)} maxLength={255} placeholder="whsec_…" hint="Copiez cette clé depuis le tableau de bord Stripe." />
          </fieldset>
          <div className="flex flex-wrap gap-3">
            <Button type="submit" variant="primary" disabled={busy || resendBusy || !secret.trim() || !publishable.trim()}>{busy ? 'Traitement…' : connected ? 'Remplacer la connexion' : 'Connecter'}</Button>
            {connected && <Button variant="destructive" disabled={busy || resendBusy} onClick={() => { void save(true) }}>Déconnecter</Button>}
          </div>
        </form>
        <div className="space-y-2 text-sm">
          <p className="font-medium">URL du webhook à configurer dans Stripe</p>
          <code className="block select-all break-all rounded-lg bg-surface-raised p-3">{webhookUrl}</code>
          <p className="text-text-muted">Événements : checkout.session.completed et checkout.session.async_payment_succeeded. Stripe doit pouvoir accéder à cette URL publique en HTTPS.</p>
        </div>
        {error && <p role="alert" className="text-sm text-status-overdue">{error}</p>}
        {message && <p role="status" className="text-sm text-text-muted">{message}</p>}
        {connected && <section className="space-y-4 border-t border-border pt-4">
          <div className="flex items-center justify-between gap-3"><h2 className="font-semibold">Activité Stripe</h2><Button disabled={dashboard.isFetching} onClick={() => { void dashboard.refetch() }}>Actualiser</Button></div>
          {dashboard.isPending ? <LoadingState /> : dashboard.isError ? <ErrorState message={errorMessage(dashboard.error)} retry={() => { void dashboard.refetch() }} /> : <>
            <h3 className="text-sm font-medium">Solde disponible</h3>
            {dashboard.data.available.length ? <ul className="flex flex-wrap gap-4">{dashboard.data.available.map((balance, index) => <li key={`${balance.currency}-${index}`} className="font-semibold tabular-nums">{money(balance.amount, balance.currency)}</li>)}</ul> : <p className="text-sm text-text-muted">Aucun solde disponible.</p>}
            <div className="overflow-auto"><table className="w-full text-left"><caption className="sr-only">Dix paiements Stripe les plus récents</caption>
              <thead><tr>{['Date', 'Description', 'Montant', 'Statut'].map(label => <th key={label} className={headingClass}>{label}</th>)}</tr></thead>
              <tbody>{dashboard.data.payments.map(payment => <tr key={payment.id} className="interactive-row border-t border-border"><td className={cellClass}>{new Date(payment.date * 1000).toLocaleString('fr-FR')}</td><td className={cellClass}>{payment.description || 'Paiement Stripe'}</td><td className={`${cellClass} whitespace-nowrap tabular-nums`}>{money(payment.amount, payment.currency)}</td><td className={cellClass}>{payment.status}</td></tr>)}{!dashboard.data.payments.length && <tr><td colSpan={4} className="p-4 text-text-muted">Aucun paiement récent.</td></tr>}</tbody>
            </table></div>
          </>}
          <p className="text-sm text-text-muted">Avec le webhook configuré, les paiements des liens DocForge mettent automatiquement à jour le solde des factures.</p>
        </section>}
      </div>
    </FormSection>
    <FormSection title="Email — Resend" defaultOpen>
      <div className="space-y-4">
        <Badge tone={resendConnected ? 'paid' : 'draft'} label={resendConnected ? 'Connecté' : 'Non connecté'} />
        <p className="text-sm text-text-muted">Connectez le compte Resend de cette entreprise pour envoyer vos factures et devis par email.</p>
        {resendConnected && <p className="break-all text-sm text-text-muted">Email expéditeur : {profile.data.resend_from_email}</p>}
        <form onSubmit={event => { event.preventDefault(); void saveResend() }} className="space-y-4">
          <fieldset disabled={resendBusy || busy} className="grid gap-4 sm:grid-cols-2">
            <TextField label="Clé API Resend" type="password" autoComplete="new-password" value={resendKey} onChange={event => setResendKey(event.target.value)} required maxLength={255} placeholder="re_…" hint="La clé enregistrée n’est jamais affichée." />
            <TextField label="Email expéditeur" type="email" value={fromEmail} onChange={event => setFromEmail(event.target.value)} required maxLength={255} placeholder="facturation@votre-entreprise.com" hint="Utilisez un domaine autorisé dans votre compte Resend." />
          </fieldset>
          <div className="flex flex-wrap gap-3">
            <Button type="submit" variant="primary" disabled={resendBusy || busy || !resendKey.trim() || !fromEmail.trim()}>{resendBusy ? 'Traitement…' : resendConnected ? 'Remplacer la connexion' : 'Connecter'}</Button>
            {resendConnected && <Button variant="destructive" disabled={resendBusy || busy} onClick={() => { void saveResend(true) }}>Déconnecter</Button>}
          </div>
        </form>
        {resendError && <p role="alert" className="text-sm text-status-overdue">{resendError}</p>}
        {resendMessage && <p role="status" className="text-sm text-text-muted">{resendMessage}</p>}
      </div>
    </FormSection>
  </div>
}
