import { Button, DatePicker, ErrorState, LoadingState, SelectField, TextAreaField, TextField, cardClass, cellClass, documentPrimaryButton as primaryButton, documentSecondaryButton as secondaryButton, headingClass, inputClass } from '../../components/ui'
import { Controller, useFieldArray, useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../../lib/api'
import { calculateTotals, documentFormSchema, documentLabels, emptyLine, getClients, errorMessage, money } from './documentModel'
import type { DocumentForm, DocumentKind, DocumentRecord, Envelope } from './documentModel'
import { TotalsPanel } from './DocumentUI'

const numericFields = [
  { key: 'quantity', label: 'Quantité' },
  { key: 'unit_price_ht', label: 'Prix HT' },
  { key: 'discount_pct', label: 'Remise %' },
  { key: 'discount_amount', label: 'Remise fixe' },
  { key: 'tax_rate_value', label: 'TVA %' },
] as const

export function DocumentCreatePage({ kind }: { kind: DocumentKind }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const labels = documentLabels[kind]
  const clients = useQuery({ queryKey: ['document-clients'], queryFn: ({ signal }) => getClients(signal) })
  const activeClients = clients.data?.filter(client => client.is_active) ?? []
  const form = useForm<DocumentForm>({
    resolver: zodResolver(documentFormSchema),
    defaultValues: { client_id: '', issued_at: '', due_at: '', notes: '', terms: '', lines: [emptyLine()] },
  })
  const { fields, append, remove } = useFieldArray({ control: form.control, name: 'lines' })
  const lines = useWatch({ control: form.control, name: 'lines' })
  const totals = calculateTotals(lines)
  const mutation = useMutation({
    mutationFn: async (values: DocumentForm) => {
      const { data } = await api.post<Envelope<DocumentRecord>>(`/${kind}/`, {
        ...values, type: labels.type, language: 'fr', currency: 'MAD', exchange_rate: '1',
        issued_at: values.issued_at ? `${values.issued_at}T00:00:00` : null,
        due_at: values.due_at ? `${values.due_at}T00:00:00` : null,
        lines: values.lines.map((line, position) => ({ ...line, position, type: 'product' })),
      })
      return data.data
    },
    retry: false,
    onSuccess: doc => {
      queryClient.setQueryData(['documents', kind, 'detail', doc.id], doc)
      void queryClient.invalidateQueries({ queryKey: ['documents', kind, 'list'] })
      navigate(`/${kind}/${doc.id}`, { replace: true })
    },
  })
  const submit = form.handleSubmit(async values => {
    if (mutation.isPending) return
    if (!activeClients.some(client => client.id === values.client_id)) {
      form.setError('client_id', { message: 'Sélectionnez un client actif.' })
      return
    }
    try { await mutation.mutateAsync(values) } catch { /* Displayed below; preserve all form values. */ }
  })
  const errors = form.formState.errors
  const busy = form.formState.isSubmitting || mutation.isPending
  return <div className="space-y-6">
    <Link to={`/${kind}`} className="text-accent hover:underline">← {labels.title}</Link>
    <header><h1 className="text-2xl font-semibold">{labels.create}</h1><p className="mt-2 text-text-muted">Enregistrement en brouillon · Devise : MAD · Numéro attribué automatiquement</p></header>
    {clients.isPending ? <LoadingState /> : clients.isError ? <ErrorState buttonClassName={secondaryButton} message={errorMessage(clients.error)} retry={() => { void clients.refetch() }} /> : activeClients.length === 0 ?
      <div className={cardClass}><h2 className="mb-2 text-lg font-semibold">Aucun client actif</h2><p className="mb-4 text-text-muted">Un client existant est nécessaire pour créer ce document.</p><Button classNameOverride={secondaryButton} variant="secondary" type="button" onClick={() => { void clients.refetch() }}>Actualiser les clients</Button></div> :
      <form onSubmit={submit} noValidate className="space-y-6">
        <fieldset disabled={busy} className="min-w-0 space-y-6">
          <legend className="sr-only">Informations du document</legend>
          <section className={`${cardClass} grid grid-cols-12 gap-4`}>
            <div className="col-span-12 md:col-span-6">
              <Controller control={form.control} name="client_id" render={({ field }) => <SelectField {...field} label="Client *" id="client" disabled={busy} aria-invalid={Boolean(errors.client_id)} aria-describedby={errors.client_id ? 'client-error' : undefined} placeholder="Sélectionner un client" options={activeClients.map(client => ({ value: client.id, label: client.legal_name + (client.code ? ' (' + client.code + ')' : '') }))} />} />{errors.client_id && <p id="client-error" className="mt-1 text-xs text-status-overdue">{errors.client_id.message}</p>}
            </div>
            {([{ key: 'issued_at', label: 'Date d’émission' }, { key: 'due_at', label: 'Échéance' }] as const).map(field => <div key={field.key} className="col-span-12 sm:col-span-6 md:col-span-3"><Controller control={form.control} name={field.key} render={({ field: f }) => <DatePicker {...f} label={field.label} id={field.key} disabled={busy} aria-invalid={Boolean(errors[field.key])} aria-describedby={errors[field.key] ? `${field.key}-error` : undefined} />} />{errors[field.key] && <p id={`${field.key}-error`} className="mt-1 text-xs text-status-overdue">{errors[field.key]?.message}</p>}</div>)}
          </section>
          <section className="space-y-3">
            <h2 className="text-lg font-semibold">Lignes du document</h2>
            <p id="discount-help" className="text-xs text-text-muted">Une remise en pourcentage remplace la remise fixe. La TVA s’applique au montant HT après remise.</p>
            <div className="max-h-[65vh] overflow-auto rounded-xl border border-border bg-surface shadow-sm"><table className="w-full text-left" aria-describedby="discount-help">
              <caption className="sr-only">Lignes éditables, montants en MAD</caption><thead><tr><th className={headingClass} scope="col">Description *</th>{numericFields.map(field => <th key={field.key} scope="col" className={`${headingClass} text-right whitespace-nowrap`}>{field.label}</th>)}<th scope="col" className={`${headingClass} whitespace-nowrap text-right`}>Total TTC</th><th scope="col" className={headingClass}><span className="sr-only">Actions</span></th></tr></thead>
              <tbody>{fields.map((field, index) => <tr key={field.id} className="border-t border-border align-top even:bg-surface-muted">
                <td className={`${cellClass} min-w-56`}><TextField bare {...form.register(`lines.${index}.description`)} aria-label={`Description ligne ${index + 1}`} aria-invalid={Boolean(errors.lines?.[index]?.description)} aria-describedby={errors.lines?.[index]?.description ? `description-${field.id}-error` : undefined} className={inputClass} />{errors.lines?.[index]?.description && <p id={`description-${field.id}-error`} className="mt-1 text-xs text-status-overdue">{errors.lines[index]?.description?.message}</p>}</td>
                {numericFields.map(numeric => {
                  const error = errors.lines?.[index]?.[numeric.key]
                  return <td className={`${cellClass} min-w-32`} key={numeric.key}><TextField bare type="text" inputMode="decimal" {...form.register(`lines.${index}.${numeric.key}`, { setValueAs: (value: string) => value.replace(',', '.') })} readOnly={numeric.key === 'discount_amount' && Number(lines[index]?.discount_pct) > 0} aria-label={`${numeric.label}, ligne ${index + 1}`} aria-invalid={Boolean(error)} aria-describedby={error ? `${field.id}-${numeric.key}-error` : undefined} className={`${inputClass} text-right tabular-nums read-only:bg-surface-muted read-only:text-text-muted`} />{error && <p id={`${field.id}-${numeric.key}-error`} className="mt-1 text-xs text-status-overdue">{error.message}</p>}</td>
                })}
                <td className={`${cellClass} whitespace-nowrap text-right font-semibold tabular-nums`}>{money(totals.lines[index]?.line_total_ttc ?? 0, 'MAD')}</td>
                <td className={cellClass}><Button variant="destructive" type="button" onClick={() => remove(index)} disabled={fields.length === 1} aria-label={`Supprimer la ligne ${index + 1}`} >Supprimer</Button></td>
              </tr>)}</tbody>
            </table></div>
            {errors.lines?.root?.message && <p role="alert">{errors.lines.root.message}</p>}
            <Button classNameOverride={secondaryButton} variant="secondary" type="button" onClick={() => append(emptyLine())} >+ Ajouter une ligne</Button>
          </section>
          <TotalsPanel totals={totals} currency="MAD" />
          <p className="text-right text-xs text-text-muted">Aperçu des totaux. Les montants enregistrés sont confirmés par le serveur.</p>
          <section className={`${cardClass} grid gap-4 md:grid-cols-2`}>{([{ key: 'notes', label: 'Notes' }, { key: 'terms', label: 'Conditions' }] as const).map(field => <div key={field.key}><TextAreaField label={field.label} id={field.key} {...form.register(field.key)} rows={3} /></div>)}</section>
        </fieldset>
        {mutation.isError && <div role="alert" className={cardClass}><p>{errorMessage(mutation.error)}</p><p className="mt-2 text-xs text-text-muted">Vos saisies sont conservées. En cas d’interruption réseau, vérifiez la liste avant de réessayer pour éviter un doublon.</p></div>}
        <div className="flex justify-end gap-3"><Button classNameOverride={secondaryButton} variant="secondary" type="button" disabled={busy} onClick={() => navigate(`/${kind}`)} >Annuler</Button><Button classNameOverride={primaryButton} variant="primary" type="submit" disabled={busy} >{busy ? 'Enregistrement…' : 'Créer le brouillon'}</Button></div>
      </form>}
  </div>
}
