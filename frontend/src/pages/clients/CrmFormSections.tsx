import { Button, CheckboxField, CountryField, PhoneField, FormSection, SelectField, TextAreaField, TextField, documentSecondaryButton as secondaryButton } from '../../components/ui'
import type { ReactNode } from 'react'
import { Controller, useFieldArray, useFormContext, useWatch } from 'react-hook-form'
import type { FieldPath } from 'react-hook-form'
import { LEGAL_FORMS, addressFields, bankFields, clientFields, contactFields, emptyContact, identityFields } from './crmModel'
import type { CrmForm, CrmKind } from './crmModel'

// CRM opens every section when any validation error exists, as before.
function CrmSection({ title, children }: { title: string; children: ReactNode }) {
  const { formState: { errors } } = useFormContext<CrmForm>()
  return <FormSection toggleClassName="flex w-full items-center justify-between rounded text-left text-lg font-semibold focus-visible:outline-2 focus-visible:outline-accent" title={title} forceOpen={Object.keys(errors).length > 0}>{children}</FormSection>
}
export function CrmField({ name, label }: { name: FieldPath<CrmForm>; label: string }) {
  const { control, register, getFieldState, formState } = useFormContext<CrmForm>()
  const addressCountry = useWatch({ control, name: 'address_country' })
  const error = getFieldState(name, formState).error
  const id = `crm-${name}`
  if (name.endsWith('_country')) return <Controller control={control} name={name} render={({ field }) =>
    <CountryField {...field} value={String(field.value ?? '')} label={label.replace(' (code)', '')} id={id} error={error?.message} disabled={formState.isSubmitting} />} />
  if (/(^|\.)(phone|mobile|fax)$/.test(name)) return <Controller control={control} name={name} render={({ field }) =>
    <PhoneField {...field} value={String(field.value ?? '')} defaultCountry={addressCountry || 'MA'} label={label} id={id} error={error?.message} disabled={formState.isSubmitting} />} />
  return <TextField label={label} id={id} {...register(name)} type={name.endsWith('email') ? 'email' : 'text'} error={error?.message} />
}
function Fields({ fields }: { fields: readonly (readonly [FieldPath<CrmForm>, string])[] }) {
  return <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{fields.map(([name, label]) => <CrmField key={name} name={name} label={label} />)}</div>
}
export function LegalFormField() {
  const { control, formState: { isSubmitting } } = useFormContext<CrmForm>()
  const id = 'crm-legal_form'
  return <Controller control={control} name="legal_form" render={({ field, fieldState }) => <SelectField {...field} label="Forme juridique" id={id} disabled={isSubmitting} error={fieldState.error?.message} placeholder="Non précisé" options={LEGAL_FORMS.map(form => ({ value: form, label: form }))} />} />
}
export function IdentitySection({ kind }: { kind: CrmKind }) {
  const { register } = useFormContext<CrmForm>()
  return <CrmSection title="Identité légale"><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <CrmField name="code" label="Code" /><CrmField name="legal_name" label="Raison sociale *" /><CrmField name="trade_name" label="Nom commercial" />
      <LegalFormField />
      {identityFields.slice(3).map(([name, label]) => <CrmField key={name} name={name} label={label} />)}
    </div>
    {kind === 'clients' && <div className="mt-4"><CrmField name="tva_number" label="Numéro de TVA" /></div>}
    <label className="mt-5 flex items-center gap-2"><CheckboxField bare type="checkbox" {...register('is_active')} className="accent-accent" />Fiche active</label>
  </CrmSection>
}
export function AddressSection({ kind }: { kind: CrmKind }) {
  return <CrmSection title="Adresse et coordonnées"><Fields fields={addressFields} />{kind === 'clients' && <div className="mt-6"><h3 className="mb-3 font-medium">Livraison</h3><Fields fields={clientFields.slice(1, 5)} /></div>}</CrmSection>
}
export function BankSection({ kind }: { kind: CrmKind }) {
  return <CrmSection title="Banque et règlement"><Fields fields={bankFields} /><div className="mt-4"><CrmField name={kind === 'clients' ? 'credit_limit' : 'bank_swift'} label={kind === 'clients' ? 'Plafond de crédit' : 'SWIFT'} /></div></CrmSection>
}
export function ContactsSection() {
  const { control, register } = useFormContext<CrmForm>()
  const { fields, append, remove } = useFieldArray({ control, name: 'contacts', keyName: 'formKey' })
  return <CrmSection title="Contacts"><div className="space-y-4">
    {fields.length === 0 && <p className="text-text-muted">Aucun contact. Ajoutez un interlocuteur pour cette fiche.</p>}
    {fields.map((field, index) => <fieldset key={field.formKey} className="min-w-0 rounded-lg border border-border p-4">
      <legend className="px-2 font-medium">Contact {index + 1}</legend>
      <div className="grid gap-4 sm:grid-cols-2">{contactFields.map(([name, label]) => <CrmField key={name} name={`contacts.${index}.${name}`} label={label} />)}</div>
      <div className="mt-4 flex flex-wrap items-center justify-between gap-3"><label className="flex items-center gap-2"><CheckboxField bare type="checkbox" {...register(`contacts.${index}.is_primary`)} className="accent-accent" />Contact principal</label>
        <Button classNameOverride={secondaryButton} variant="secondary" type="button" onClick={() => remove(index)} aria-label={`Retirer le contact ${index + 1}`}>Retirer</Button>
      </div>
    </fieldset>)}
    <Button classNameOverride={secondaryButton} variant="secondary" type="button" onClick={() => append(emptyContact())}>+ Ajouter un contact</Button>
    <p className="text-xs text-text-muted">Les ajouts, modifications et retraits sont appliqués à l’enregistrement.</p>
  </div></CrmSection>
}
export function NotesSection({ kind }: { kind: CrmKind }) {
  const { register } = useFormContext<CrmForm>()
  return <CrmSection title="Informations complémentaires"><div className="grid gap-4 sm:grid-cols-2"><CrmField name="category" label="Catégorie" />{kind === 'clients' && <CrmField name="source" label="Source" />}</div><div className="mt-4"><TextAreaField label="Notes" id="crm-notes" rows={3} {...register('notes')} /></div></CrmSection>
}
