import { Button, CheckboxField, ErrorState, LoadingState, SelectField, TextAreaField, TextField, cardClass, documentPrimaryButton as primaryButton, documentSecondaryButton as secondaryButton } from '../../components/ui'
import { Controller, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueries } from '@tanstack/react-query'
import { api } from '../../lib/api'
import { getData } from '../invoices/documentModel'
import { catalogueError, eligibleParents, fields, formSchema, initialValues, labels, payload, productTypes, relationFields } from './catalogueModel'
import type { CatalogueFormValues, CatalogueKind, CatalogueRecord, FieldName } from './catalogueModel'

const fieldLabels: Record<FieldName, string> = {
  name: 'Nom *', code: 'Code', reference: 'Référence', description: 'Description', symbol: 'Symbole *', label: 'Libellé *',
  type: 'Type *', rate: 'Taux (%) *', purchase_price_ht: 'Prix d’achat HT *', sale_price_ht: 'Prix de vente HT *',
  sort_order: 'Ordre d’affichage *', parent_id: 'Catégorie parente', category_id: 'Catégorie', unit_id: 'Unité', tax_rate_id: 'Taux de TVA',
  is_active: 'Actif', is_default: 'Par défaut',
}

export function CatalogueForm({ kind, record, onCancel, onSaved }: {
  kind: CatalogueKind; record?: CatalogueRecord; onCancel: () => void; onSaved: () => void
}) {
  const form = useForm<CatalogueFormValues>({ resolver: zodResolver(formSchema(kind)), defaultValues: initialValues(kind, record) })
  const referenceKinds: CatalogueKind[] = kind === 'products' ? ['categories', 'units', 'tax-rates'] : kind === 'categories' ? ['categories'] : []
  const references = useQueries({ queries: referenceKinds.map(reference => ({
    queryKey: ['catalogue', reference], queryFn: ({ signal }: { signal: AbortSignal }) => getData<CatalogueRecord[]>(`/catalogue/${reference}/`, signal),
  })) })
  const mutation = useMutation({
    retry: false,
    mutationFn: (values: CatalogueFormValues) => record
      ? api.patch(`/catalogue/${kind}/${record.id}`, payload(kind, values))
      : api.post(`/catalogue/${kind}/`, payload(kind, values)),
    onSuccess: onSaved,
  })
  const busy = form.formState.isSubmitting || mutation.isPending
  const loading = references.some(query => query.isPending)
  const failed = references.find(query => query.isError)
  const optionsFor = (name: FieldName): { id: string; label: string }[] | undefined => {
    if (name === 'type' && kind === 'products') return Object.entries(productTypes).map(([id, label]) => ({ id, label }))
    if (!relationFields.some(field => field === name)) return undefined
    const reference = name === 'unit_id' ? 'units' : name === 'tax_rate_id' ? 'tax-rates' : 'categories'
    let rows = references[referenceKinds.indexOf(reference)]?.data ?? []
    if (name === 'parent_id') rows = eligibleParents(rows, record?.id)
    return rows.map(row => ({ id: row.id, label: `${row.name}${row.symbol ? ` (${row.symbol})` : ''}${row.rate != null ? ` (${row.rate} %)` : ''}${row.is_active === false ? ' — Inactif' : ''}` }))
  }
  return <section className={cardClass} aria-labelledby="catalogue-form-title">
    <h2 id="catalogue-form-title" className="text-lg font-semibold">{record ? `Modifier : ${record.name}` : labels[kind].create}</h2>
    <p className="mb-5 mt-2 text-text-muted">Les champs marqués * sont obligatoires.</p>
    {loading && <LoadingState />}
    {failed && <ErrorState buttonClassName={secondaryButton} message={catalogueError(failed.error)} retry={() => { references.forEach(query => { void query.refetch() }) }} />}
    <form noValidate onSubmit={form.handleSubmit(values => {
      if (busy) return
      let invalid = false
      // PATCH uses exclude_none=True: it cannot remove an existing foreign key or unique code.
      for (const field of [...relationFields, 'code'] as const) if (fields[kind].includes(field) && record?.[field] && !values[field]) {
        form.setError(field, { message: 'Le serveur ne permet pas de vider cette valeur. Vous pouvez la remplacer.' }, { shouldFocus: !invalid })
        invalid = true
      }
      if (!invalid) mutation.mutate(values)
    })} className="space-y-5">
      <fieldset disabled={busy || loading || Boolean(failed)} className="grid min-w-0 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <legend className="sr-only">Informations du catalogue</legend>
        {fields[kind].map(name => {
          const id = `catalogue-${name}`
          const error = form.formState.errors[name]
          const options = optionsFor(name)
          if (name === 'is_active' || name === 'is_default') return <label key={name} className="flex h-9 items-center gap-2 self-end"><CheckboxField bare type="checkbox" {...form.register(name)} className="accent-accent" />{fieldLabels[name]}</label>
          const attributes = { id, label: fieldLabels[name], error: error?.message }
          const current = record?.[name as keyof CatalogueRecord]
          const selectOptions = options && [
            ...(current && !options.some(option => option.id === current) ? [{ value: String(current), label: 'Valeur actuelle indisponible', disabled: true }] : []),
            ...options.map(option => ({ value: option.id, label: option.label })),
          ]
          return <div key={name} className={name === 'description' ? 'sm:col-span-2 lg:col-span-3' : ''}>
            {selectOptions ? <Controller control={form.control} name={name} render={({ field }) => <SelectField {...attributes} {...field} value={String(field.value ?? '')} disabled={busy || loading || Boolean(failed)} options={selectOptions} placeholder={name !== 'type' ? 'Non précisé' : undefined} emptyHint="" />} /> : name === 'description' ? <TextAreaField {...attributes} {...form.register(name)} rows={3} /> :
              <TextField {...attributes} {...form.register(name)} autoFocus={name === 'name'} inputMode={['rate', 'purchase_price_ht', 'sale_price_ht'].includes(name) ? 'decimal' : name === 'sort_order' ? 'numeric' : undefined} />}
            {options?.length === 0 && <p className="mt-1 text-xs text-text-muted">Aucune valeur disponible. Vous pouvez enregistrer sans relation.</p>}
          </div>
        })}
      </fieldset>
      {mutation.isError && <div role="alert"><p className="text-status-overdue">{catalogueError(mutation.error)}</p><p className="mt-1 text-xs text-text-muted">Vos saisies sont conservées. En cas d’interruption réseau, vérifiez la liste avant de réessayer.</p></div>}
      <div className="flex flex-wrap justify-end gap-3"><Button classNameOverride={`${secondaryButton} press`} variant="secondary" type="button" disabled={busy} onClick={onCancel} >Annuler</Button><Button classNameOverride={`${primaryButton} press`} variant="primary" type="submit" disabled={busy || loading || Boolean(failed)} >{busy ? 'Enregistrement…' : 'Enregistrer'}</Button></div>
    </form>
  </section>
}
