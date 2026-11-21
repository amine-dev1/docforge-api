import { useEffect, useRef, useState } from 'react'
import { Controller, useForm, useWatch } from 'react-hook-form'
import { isAxiosError } from 'axios'
import { api } from '../../lib/api'
import { Button, CheckboxField, CountryField, PhoneField, ErrorState, FormSection, LoadingState, SelectField, TextAreaField, TextField, cardClass } from '../../components/ui'
import { companyPayload, companySections, formValues, validateField } from './companyModel'
import type { CompanyRecord, CompanyValues } from './companyModel'

function requestError(error: unknown) {
  if (isAxiosError(error)) {
    if (error.response?.status === 403) return 'Vous devez être administrateur pour modifier le profil de l’entreprise.'
    const detail: unknown = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (error.response?.status === 422) return 'Certaines informations sont invalides. Vérifiez les champs du formulaire.'
  }
  return 'Impossible de contacter le serveur. Vérifiez votre connexion puis réessayez.'
}

export function CompanyPage() {
  const [profile, setProfile] = useState<CompanyRecord | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    api.get<{ status: number; data: CompanyRecord }>('/tenant/me', { signal: controller.signal })
      .then(({ data }) => {
        if (!data.data?.tenant_id) throw new Error('Missing tenant ID')
        if (!controller.signal.aborted) setProfile(data.data)
      })
      .catch((reason: unknown) => { if (!controller.signal.aborted) setError(requestError(reason)) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [attempt])

  return <div className="space-y-6">
    <header>
      <h1 className="text-2xl font-semibold leading-tight">Profil entreprise</h1>
      <p className="mt-2 text-sm text-text-muted">Identité, coordonnées et paramètres utilisés pour vos documents.</p>
    </header>
    {loading ? <LoadingState /> : error ? <ErrorState message={error} retry={() => { setLoading(true); setError(''); setAttempt(value => value + 1) }} /> : profile && <CompanyForm profile={profile} />}
  </div>
}

function CompanyForm({ profile }: { profile: CompanyRecord }) {
  const [original, setOriginal] = useState(() => formValues(profile))
  const [saveError, setSaveError] = useState('')
  const [saved, setSaved] = useState(false)
  const formRef = useRef<HTMLFormElement>(null)
  const { control, register, handleSubmit, reset, setError, formState: { errors, isDirty, isSubmitting } } = useForm<CompanyValues>({
    defaultValues: original,
    shouldFocusError: false,
  })
  const addressCountry = useWatch({ control, name: 'address_country' })

  // Wait for FormSection to expand before focusing a field that was hidden.
  useEffect(() => {
    if (Object.keys(errors).length) formRef.current?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus()
  }, [errors])

  const save = handleSubmit(async values => {
    setSaveError('')
    setSaved(false)
    try {
      const payload = companyPayload(values, original)
      if (!Object.keys(payload).length) {
        reset(original)
        return
      }
      const { data } = await api.put<{ status: number; data: CompanyRecord }>(`/tenant/${encodeURIComponent(profile.tenant_id)}`, payload)
      const updated = formValues(data.data)
      setOriginal(updated)
      reset(updated)
      setSaved(true)
    } catch (reason) {
      setSaveError(requestError(reason))
      if (isAxiosError(reason) && Array.isArray(reason.response?.data?.detail)) {
        for (const issue of reason.response.data.detail as { loc?: unknown[]; msg?: string }[]) {
          const name = issue.loc?.[1]
          if (typeof name === 'string' && name in original) setError(name, { type: 'server', message: issue.msg ?? 'Valeur invalide.' })
        }
      }
    }
  })

  return <form ref={formRef} onSubmit={save} noValidate className="space-y-6" aria-busy={isSubmitting} onChange={() => setSaved(false)}>
    <p className="text-sm text-text-muted">Les champs marqués d’un astérisque (*) sont obligatoires.</p>
    <fieldset disabled={isSubmitting} className="min-w-0 space-y-6">
      <legend className="sr-only">Informations de l’entreprise</legend>
      {companySections.map((section, index) => <FormSection key={section.title} title={section.title} defaultOpen={index === 0} forceOpen={section.fields.some(field => Boolean(errors[field.name]))}>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {section.fields.map(field => {
            const label = `${field.label}${field.required ? ' *' : ''}`
            const error = errors[field.name]?.message
            if (field.name.endsWith('_country')) return <Controller key={field.name} control={control} name={field.name} rules={{ validate: value => validateField(field, value) }} render={({ field: binding }) => <CountryField {...binding} value={String(binding.value ?? '')} onChange={value => { binding.onChange(value); setSaved(false) }} label={label} disabled={isSubmitting} error={error} required={field.required} />} />
            if (['phone_main', 'phone_secondary', 'fax'].includes(field.name)) return <Controller key={field.name} control={control} name={field.name} rules={{ validate: value => validateField(field, value) }} render={({ field: binding }) => <PhoneField {...binding} value={String(binding.value ?? '')} onChange={value => { binding.onChange(value); setSaved(false) }} defaultCountry={String(addressCountry || 'MA')} label={label} disabled={isSubmitting} error={error} maxLength={field.maxLength} required={field.required} />} />
            if (field.options) return <Controller key={field.name} control={control} name={field.name} rules={{ validate: value => validateField(field, value) }} render={({ field: binding }) => <SelectField {...binding} value={String(binding.value ?? '')} onChange={value => { binding.onChange(value); setSaved(false) }} label={label} disabled={isSubmitting} options={field.options!.map(value => ({ value, label: value }))} placeholder={field.required ? undefined : 'Non précisé'} error={error} required={field.required} />} />
            const binding = register(field.name, { validate: value => validateField(field, value) })
            if (field.type === 'checkbox') return <CheckboxField key={field.name} label={label} {...binding} />
            if (field.type === 'textarea') return <div key={field.name} className="sm:col-span-2 lg:col-span-3"><TextAreaField label={label} {...binding} error={error} /></div>
            return <TextField key={field.name} label={label} {...binding} type={field.type ?? 'text'} maxLength={field.maxLength} required={field.required} hint={field.hint} error={error} min={field.type === 'number' ? 0 : undefined} max={field.type === 'number' && field.name !== 'capital_social' ? 32767 : undefined} step={field.name === 'capital_social' ? '0.01' : field.type === 'number' ? '1' : undefined} />
          })}
        </div>
      </FormSection>)}
    </fieldset>
    <div className={`${cardClass} space-y-4`}>
      {saveError && <p role="alert" className="text-sm text-status-overdue">{saveError}</p>}
      {Object.keys(errors).length > 0 && <p role="alert" className="text-sm text-status-overdue">Corrigez les champs signalés dans les sections ouvertes.</p>}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <p role="status" className="text-sm text-text-muted">{isSubmitting ? 'Enregistrement en cours…' : saved ? 'Profil entreprise enregistré.' : isDirty ? 'Modifications non enregistrées.' : 'Aucune modification en attente.'}</p>
        <div className="flex flex-wrap gap-3">
          <Button disabled={!isDirty || isSubmitting} onClick={() => { reset(original); setSaveError(''); setSaved(false) }}>Annuler les modifications</Button>
          <Button variant="primary" type="submit" disabled={!isDirty || isSubmitting}>{isSubmitting ? 'Enregistrement…' : 'Enregistrer'}</Button>
        </div>
      </div>
    </div>
  </form>
}
