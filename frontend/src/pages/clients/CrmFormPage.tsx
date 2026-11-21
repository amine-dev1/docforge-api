import { Button, cardClass, documentPrimaryButton as primaryButton, documentSecondaryButton as secondaryButton } from '../../components/ui'
import { useRef, useState } from 'react'
import type { FormEventHandler } from 'react'
import { FormProvider, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { api, contactPayload, crmError, crmLabels, crmSchema, formValues, getData, recordPayload } from './crmModel'
import type { ContactForm, CrmForm, CrmKind, CrmRecord, Envelope } from './crmModel'
import { AddressSection, BankSection, ContactsSection, IdentitySection, NotesSection } from './CrmFormSections'

export function CrmFormPage({ kind, record }: { kind: CrmKind; record?: CrmRecord }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const labels = crmLabels[kind]
  const [initialValues] = useState(() => formValues(record))
  const baseline = useRef(initialValues)
  const [saved, setSaved] = useState(false)
  const form = useForm<CrmForm>({ resolver: zodResolver(crmSchema), defaultValues: initialValues, shouldFocusError: false })
  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ['crm', kind] })
    if (kind === 'clients') void queryClient.invalidateQueries({ queryKey: ['document-clients'] })
  }
  const mutation = useMutation({
    retry: false,
    mutationFn: async (values: CrmForm) => {
      if (!record) return (await api.post<Envelope<CrmRecord>>(`/${kind}/`, {
        ...recordPayload(values, kind, true), contacts: values.contacts.map(c => contactPayload(c, true)),
      })).data.data
      const path = `/${kind}/${record.id}`
      await api.patch(path, recordPayload(values, kind, false))
      baseline.current = { ...values, contacts: baseline.current.contacts }
      // Each contact endpoint commits independently. Track acknowledged operations so
      // retrying a partially failed save does not recreate or re-delete contacts.
      for (const old of [...baseline.current.contacts]) if (old.id && !values.contacts.some(c => c.id === old.id)) {
        await api.delete(`${path}/contacts/${old.id}`)
        baseline.current.contacts = baseline.current.contacts.filter(c => c.id !== old.id)
      }
      for (const [index, contact] of values.contacts.entries()) {
        const previous = baseline.current.contacts.find(c => c.id === contact.id)
        if (contact.id) {
          if (JSON.stringify(previous) !== JSON.stringify(contact)) await api.patch(`${path}/contacts/${contact.id}`, contactPayload(contact, false))
          baseline.current.contacts = baseline.current.contacts.map(c => c.id === contact.id ? { ...contact } : c)
        } else {
          const created = (await api.post<Envelope<ContactForm & { id: string }>>(`${path}/contacts`, contactPayload(contact, true))).data.data
          contact.id = created.id
          form.setValue(`contacts.${index}.id`, created.id)
          baseline.current.contacts.push({ ...contact })
        }
      }
      return getData<CrmRecord>(path)
    },
    onSuccess: result => {
      baseline.current = formValues(result)
      form.reset(baseline.current)
      queryClient.setQueryData(['crm', kind, 'detail', result.id], result)
      setSaved(true)
      if (!record) navigate(`/${kind}/${result.id}`, { replace: true, state: { created: true } })
    },
    onSettled: invalidate,
  })
  const submit: FormEventHandler<HTMLFormElement> = event => { void form.handleSubmit(async values => {
    if (mutation.isPending) return
    setSaved(false)
    let invalid = false
    // The backend ignores null on PATCH and rejects empty EmailStr/Decimal.
    // Explain this limitation instead of silently restoring a cleared value.
    if (record) {
      for (const key of ['email', 'credit_limit'] as const) if (baseline.current[key] && !values[key] && (key !== 'credit_limit' || kind === 'clients')) {
        form.setError(key, { message: 'Le serveur ne permet pas de vider ce champ. Vous pouvez remplacer sa valeur.' })
        invalid = true
      }
      values.contacts.forEach((contact, index) => {
        if (contact.id && !contact.email && baseline.current.contacts.find(c => c.id === contact.id)?.email) {
          form.setError(`contacts.${index}.email`, { message: 'Le serveur ne permet pas de vider cet e-mail. Vous pouvez le remplacer.' })
          invalid = true
        }
      })
    }
    if (invalid) return
    try { await mutation.mutateAsync(values) } catch { /* Keep the edited values and acknowledged contact IDs. */ }
  })(event) }
  const busy = form.formState.isSubmitting || mutation.isPending
  return <div className="space-y-6">
    <Link className="text-accent hover:underline" to={`/${kind}`}>← {labels.title}</Link>
    <header><h1 className="text-2xl font-semibold">{record ? String(record.legal_name) : labels.create}</h1><p className="mt-2 text-text-muted">{record ? `Fiche ${labels.singular} · Modifiez les informations puis enregistrez.` : 'Renseignez la raison sociale et les coordonnées.'} Les champs marqués * sont obligatoires.</p></header>
    <FormProvider {...form}><form noValidate onSubmit={submit} onChange={() => setSaved(false)} className="space-y-6">
      {Object.keys(form.formState.errors).length > 0 && <p role="alert" className="text-status-overdue">Corrigez les champs signalés ci-dessous avant d’enregistrer.</p>}
      <fieldset disabled={busy} className="min-w-0 space-y-6"><legend className="sr-only">Informations de la fiche</legend>
        <IdentitySection kind={kind} /><AddressSection kind={kind} /><BankSection kind={kind} /><ContactsSection /><NotesSection kind={kind} />
      </fieldset>
      {mutation.isError && <div role="alert" className={cardClass}><p>{crmError(mutation.error)}</p><p className="mt-2 text-xs text-text-muted">Vos saisies sont conservées. {record ? 'Une partie des modifications peut avoir été enregistrée. Réessayez pour terminer.' : 'En cas d’interruption réseau, vérifiez la liste avant de réessayer pour éviter un doublon.'}</p></div>}
      {saved && !form.formState.isDirty && <p role="status" className="text-text-muted">Modifications enregistrées.</p>}
      <div className="flex flex-wrap justify-end gap-3"><Button classNameOverride={secondaryButton} variant="secondary" type="button" disabled={busy} onClick={() => navigate(`/${kind}`)}>Retour à la liste</Button><Button classNameOverride={primaryButton} variant="primary" type="submit"  disabled={busy}>{busy ? 'Enregistrement…' : record ? 'Enregistrer les modifications' : labels.create}</Button></div>
    </form></FormProvider>
  </div>
}
