import { Button, CheckboxField, DatePicker, ErrorState, LoadingState, SelectField, TextAreaField, TextField, cardClass, documentPrimaryButton as primaryButton, documentSecondaryButton as secondaryButton, inputClass } from '../../components/ui'
import { useState } from 'react'
import { Controller, useFieldArray, useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../../lib/api'
import { errorMessage, getClients, money } from '../invoices/documentModel'
import type { Envelope } from '../invoices/documentModel'
import { allocationIssues, cents, decimal, getInvoices, methods, paymentSchema } from './paymentModel'
import type { PaymentFormValues, PaymentRecord } from './paymentModel'
import { PaymentStatus } from './PaymentPages'

export function PaymentForm({ record }: { record?: PaymentRecord }) {
  const navigate = useNavigate()
  const cache = useQueryClient()
  const [saved, setSaved] = useState(false)
  const [validationError, setValidationError] = useState('')
  const [initialDate] = useState(() => new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 10))
  const clients = useQuery({ queryKey: ['document-clients'], queryFn: ({ signal }) => getClients(signal) })
  const invoices = useQuery({ queryKey: ['documents', 'invoices', 'payment-options'], queryFn: ({ signal }) => getInvoices(signal) })
  const form = useForm<PaymentFormValues>({
    resolver: zodResolver(paymentSchema),
    defaultValues: {
      client_id: record?.client_id ?? '', reference: record?.reference ?? '', method: record?.method ?? 'bank_transfer',
      amount: String(record?.amount ?? ''), currency: record?.currency ?? 'MAD',
      payment_date: record?.payment_date ?? initialDate,
      bank_reference: record?.bank_reference ?? '', notes: record?.notes ?? '', allocations: [],
    },
  })
  const allocations = useFieldArray({ control: form.control, name: 'allocations' })
  const values = useWatch({ control: form.control }) as PaymentFormValues
  const total = values.allocations.reduce((sum, row) => sum + cents(row.amount_allocated), 0n)
  const remaining = cents(values.amount) - total
  const openInvoices = (invoices.data ?? []).filter(invoice => invoice.client_id === values.client_id && cents(invoice.amount_due) > 0n && invoice.status !== 'cancelled')
  const issues = allocationIssues(values, invoices.data ?? [])
  const mutation = useMutation({
    retry: false,
    mutationFn: async (data: PaymentFormValues) => {
      if (record) {
        // PATCH does not recompute balances or support allocation changes.
        return (await api.patch<Envelope<PaymentRecord>>(`/payments/${record.id}`, {
          method: data.method, payment_date: data.payment_date, bank_reference: data.bank_reference, notes: data.notes,
        })).data.data
      }
      return (await api.post<Envelope<PaymentRecord>>('/payments/', { ...data, client_id: data.client_id || null })).data.data
    },
    onSuccess: payment => {
      setSaved(true)
      cache.setQueryData(['payments', 'detail', payment.id], payment)
      void cache.invalidateQueries({ queryKey: ['payments'] })
      void cache.invalidateQueries({ queryKey: ['documents', 'invoices'] })
      if (!record) navigate(`/payments/${payment.id}`, { replace: true })
    },
  })
  const busy = form.formState.isSubmitting || mutation.isPending
  const loading = clients.isPending || invoices.isPending
  const failed = clients.isError || invoices.isError
  const field = (name: 'reference' | 'amount' | 'currency' | 'payment_date' | 'bank_reference' | 'notes', label: string, locked = false) => {
    const error = form.formState.errors[name]
    const props = { ...form.register(name, name === 'currency' ? { onChange: () => allocations.replace([]) } : {}), id: `payment-${name}`, readOnly: locked, label, error: error?.message }
    return name === 'notes' ? <TextAreaField {...props} rows={3} /> : <TextField {...props} type={name === 'payment_date' ? 'date' : 'text'} inputMode={name === 'amount' ? 'decimal' : undefined} />
  }
  return <div className="space-y-6">
    <Link to="/payments" className="text-text-muted hover:text-text">← Paiements</Link>
    <header className="flex flex-wrap items-center justify-between gap-4"><h1 className="text-2xl font-semibold">{record ? record.reference : 'Nouveau paiement'}</h1>{record && <PaymentStatus status={record.status} />}</header>
    {loading && <LoadingState />}
    {failed && <ErrorState buttonClassName={secondaryButton} message={errorMessage(clients.error ?? invoices.error)} retry={() => { void clients.refetch(); void invoices.refetch() }} />}
    {saved && <p role="status" className="text-text-muted">Modifications enregistrées.</p>}
    <form noValidate className="space-y-6" onSubmit={form.handleSubmit(async data => {
      if (busy) return
      setSaved(false); setValidationError(''); mutation.reset()
      if (!record && data.allocations.length) {
        try {
          const fresh = await getInvoices()
          cache.setQueryData(['documents', 'invoices', 'payment-options'], fresh)
          const errors = allocationIssues(data, fresh)
          if (errors.length) {
            errors.forEach(({ index, message }) => form.setError(`allocations.${index}.amount_allocated`, { message }))
            setValidationError('Les soldes ont été vérifiés. Corrigez les allocations signalées.'); return
          }
        } catch (error) { setValidationError(errorMessage(error)); return }
      }
      await mutation.mutateAsync(data).catch(() => { /* Mutation error is shown below; keep all values. */ })
    })}>
      <section className={cardClass} aria-labelledby="payment-info"><h2 id="payment-info" className="mb-4 text-lg font-semibold">Informations du paiement</h2>
        <p className="mb-4 text-text-muted">{record ? 'Le client, la référence, le montant et la devise sont définitifs. Les informations de règlement restent modifiables.' : 'Les champs marqués * sont obligatoires. Vous pouvez enregistrer un paiement sans allocation.'}</p>
        <fieldset disabled={busy || loading || failed} className="grid min-w-0 gap-4 sm:grid-cols-2 lg:grid-cols-3"><legend className="sr-only">Informations</legend>
          <div>
            {record ? <TextField label="Client" id="payment-client" className={inputClass} readOnly value={clients.data?.find(client => client.id === record.client_id)?.legal_name ?? (record.client_id ? 'Client indisponible' : 'Sans client')} /> : <Controller control={form.control} name="client_id" render={({ field }) => <SelectField {...field} label="Client" id="payment-client" disabled={busy || loading || failed} aria-invalid={Boolean(form.formState.errors.client_id)} aria-describedby={form.formState.errors.client_id ? 'payment-client-error' : undefined} onChange={value => { field.onChange(value); allocations.replace([]) }} placeholder="Sans client" options={(clients.data ?? []).map(client => ({ value: client.id, label: client.legal_name + (client.is_active ? '' : ' — Inactif') }))} />} />}
            {form.formState.errors.client_id && <p id="payment-client-error" role="alert" className="text-xs text-status-overdue">{form.formState.errors.client_id.message}</p>}
          </div>
          {field('reference', 'Référence *', Boolean(record))}
          <div><Controller control={form.control} name="method" render={({ field }) => <SelectField {...field} label="Méthode *" id="payment-method" disabled={busy || loading || failed} options={[...(record && !methods[record.method] ? [{ value: record.method, label: record.method }] : []), ...Object.entries(methods).map(([value, label]) => ({ value, label }))]} />} /></div>
          {field('amount', 'Montant *', Boolean(record))}{field('currency', 'Devise *', Boolean(record))}
          <div><Controller control={form.control} name="payment_date" render={({ field }) => <DatePicker {...field} label="Date du paiement *" id="payment-date" disabled={busy} aria-invalid={Boolean(form.formState.errors.payment_date)} aria-describedby={form.formState.errors.payment_date ? 'payment-date-error' : undefined} />} />
            {form.formState.errors.payment_date && <p id="payment-date-error" role="alert" className="text-xs text-status-overdue">{form.formState.errors.payment_date.message}</p>}
          </div>
          {field('bank_reference', 'Référence bancaire')}
          <div className="sm:col-span-2">{field('notes', 'Notes')}</div>
        </fieldset>
      </section>
      <section className={cardClass} aria-labelledby="payment-allocations"><h2 id="payment-allocations" className="mb-4 text-lg font-semibold">Allocation sur factures</h2>
        {record ? <>
          <p className="mb-4 text-text-muted">Les allocations enregistrées sont définitives.</p>
          {record.allocations.length === 0 ? <p className="text-text-muted">Aucune allocation enregistrée.</p> : <ul className="divide-y divide-border">{record.allocations.map(row => <li key={row.id} className="flex flex-wrap justify-between gap-3 py-3"><Link className="text-accent underline underline-offset-4 tabular-nums" to={`/invoices/${row.document_id}`}>{invoices.data?.find(invoice => invoice.id === row.document_id)?.number ?? `Facture ${row.document_id}`}</Link><span className="font-medium tabular-nums">{money(row.amount_allocated, record.currency)}</span></li>)}</ul>}
        </> : <>
          <p className="mb-4 text-text-muted">Sélectionnez les factures et saisissez le montant à affecter à chacune. Les devises doivent correspondre.</p>
          {!values.client_id ? <p className="text-text-muted">Sélectionnez un client pour afficher ses factures ouvertes.</p> : !loading && !failed && openInvoices.length === 0 ? <div className="space-y-3 text-text-muted"><p>Ce client n’a aucune facture ouverte.</p><Link to="/invoices/new" className={`${secondaryButton} press`}>Créer une facture</Link></div> : null}
          <fieldset disabled={busy || loading || failed} className="min-w-0 space-y-3"><legend className="sr-only">Factures ouvertes</legend>{openInvoices.map(invoice => {
            const index = values.allocations.findIndex(row => row.document_id === invoice.id)
            const selected = index !== -1
            const error = selected ? form.formState.errors.allocations?.[index]?.amount_allocated?.message ?? issues.find(issue => issue.index === index)?.message : undefined
            return <div key={invoice.id} className="grid items-center gap-3 border-t border-border py-3 sm:grid-cols-2">
              <label className="flex items-center gap-3"><CheckboxField bare type="checkbox" className="accent-accent" checked={selected} disabled={invoice.currency !== values.currency} onChange={event => {
                form.clearErrors('allocations')
                if (!event.target.checked) allocations.remove(index)
                else allocations.append({ document_id: invoice.id, amount_allocated: decimal(remaining > 0n ? (remaining < cents(invoice.amount_due) ? remaining : cents(invoice.amount_due)) : 0n) })
              }} /><span><span className="font-medium tabular-nums">{invoice.number}</span><span className="block text-xs text-text-muted">Solde dû : {money(invoice.amount_due, invoice.currency)}{invoice.currency !== values.currency ? ' — Devise différente' : ''}</span></span></label>
              {selected && <div><TextField label={`Montant alloué (${values.currency})`} id={`allocation-${invoice.id}`} className={inputClass} inputMode="decimal" {...form.register(`allocations.${index}.amount_allocated`)} aria-invalid={Boolean(error)} aria-describedby={error ? `allocation-error-${invoice.id}` : undefined} />{error && <p id={`allocation-error-${invoice.id}`} className="mt-1 text-xs text-status-overdue">{error}</p>}</div>}
            </div>
          })}
          {values.allocations.map((row, index) => !openInvoices.some(invoice => invoice.id === row.document_id) && <div key={row.document_id} className="flex flex-wrap items-center justify-between gap-3 border-t border-border py-3"><p role="alert" className="text-status-overdue">Cette facture n’est plus disponible pour l’allocation.</p><Button classNameOverride={`${secondaryButton} press`} variant="secondary" type="button" onClick={() => { allocations.remove(index); form.clearErrors('allocations') }}>Retirer cette allocation</Button></div>)}
          </fieldset>
          {(form.formState.errors.allocations?.root?.message || form.formState.errors.allocations?.message || remaining < 0n) && <p role="alert" className="mt-3 text-status-overdue">{form.formState.errors.allocations?.root?.message ?? form.formState.errors.allocations?.message ?? 'Le total alloué dépasse le montant du paiement.'}</p>}
        </>}
        <dl className="mt-5 grid gap-4 border-t border-border pt-4 sm:grid-cols-3" aria-live="polite">{[
          ['Montant du paiement', record?.amount ?? values.amount], ['Montant alloué', record?.amount_allocated ?? decimal(total)], ['Montant restant', record?.amount_remaining ?? decimal(remaining)],
        ].map(([label, value]) => <div key={label}><dt className="text-xs font-medium uppercase tracking-wide text-text-muted">{label}</dt><dd className="mt-1 text-xl font-semibold tabular-nums">{money(value || '0', values.currency)}</dd></div>)}</dl>
      </section>
      {validationError && <p role="alert" className="text-status-overdue">{validationError}</p>}
      {mutation.isError && <div role="alert"><p className="text-status-overdue">{errorMessage(mutation.error)}</p><p className="mt-1 text-xs text-text-muted">Vos saisies sont conservées. En cas d’interruption réseau, vérifiez la liste avant de réessayer.</p></div>}
      <div className="flex justify-end gap-3"><Button classNameOverride={`${secondaryButton} press`} variant="secondary" type="button" disabled={busy} onClick={() => navigate('/payments')} >Retour à la liste</Button><Button classNameOverride={`${primaryButton} press`} variant="primary" type="submit" disabled={busy || loading || failed} >{busy ? 'Enregistrement…' : record ? 'Enregistrer les modifications' : 'Enregistrer le paiement'}</Button></div>
    </form>
  </div>
}
