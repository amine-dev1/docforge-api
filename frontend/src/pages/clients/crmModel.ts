import axios from 'axios'
import { z } from 'zod'
import { api } from '../../lib/api'
import { errorMessage, getData } from '../invoices/documentModel'
import type { Envelope } from '../invoices/documentModel'

export type CrmKind = 'clients' | 'suppliers'
export const crmLabels = {
  clients: { title: 'Clients', singular: 'client', create: 'Nouveau client' },
  suppliers: { title: 'Fournisseurs', singular: 'fournisseur', create: 'Nouveau fournisseur' },
} as const
export const identityFields = [
  ['code', 'Code'], ['legal_name', 'Raison sociale *'], ['trade_name', 'Nom commercial'],
  ['ice', 'ICE'], ['rc', 'Registre de commerce'],
  ['if_number', 'Identifiant fiscal'], ['taxe_professionnelle', 'Taxe professionnelle'], ['cnss', 'CNSS'],
] as const
// Matches the `legal_form_type` Postgres ENUM (backend/docs/schema.sql) — the backend
// rejects any other value with a 422, so the form only ever offers these.
export const LEGAL_FORMS = ['SARL', 'SA', 'SAS', 'SNC', 'Auto-entrepreneur', 'Association', 'Autre'] as const
export const addressFields = [
  ['address_street', 'Adresse'], ['address_complement', 'Complément'], ['address_city', 'Ville'],
  ['address_zip', 'Code postal'], ['address_region', 'Région'], ['address_country', 'Pays (code)'],
  ['phone', 'Téléphone'], ['mobile', 'Mobile'], ['fax', 'Fax'], ['email', 'E-mail'], ['website', 'Site web'],
] as const
export const bankFields = [['bank_name', 'Banque'], ['bank_rib', 'RIB'], ['bank_iban', 'IBAN'], ['currency', 'Devise'], ['payment_terms_days', 'Délai de paiement (jours)']] as const
export const clientFields = [['tva_number', 'Numéro de TVA'], ['delivery_address_street', 'Adresse de livraison'], ['delivery_address_city', 'Ville de livraison'], ['delivery_address_zip', 'Code postal de livraison'], ['delivery_address_country', 'Pays de livraison (code)'], ['credit_limit', 'Plafond de crédit'], ['source', 'Source']] as const
export const contactFields = [['first_name', 'Prénom *'], ['last_name', 'Nom *'], ['title', 'Fonction'], ['department', 'Service'], ['email', 'E-mail'], ['phone', 'Téléphone'], ['mobile', 'Mobile'], ['notes', 'Notes']] as const
const text = z.string().trim()
const email = z.union([z.literal(''), z.email('Adresse e-mail invalide.')])
export const contactSchema = z.object({
  id: z.string().optional(), first_name: text.min(1, 'Le prénom est obligatoire.'), last_name: text.min(1, 'Le nom est obligatoire.'),
  title: text, department: text, email, phone: text, mobile: text, notes: text, is_primary: z.boolean(),
})
export const crmSchema = z.object({
  code: text, legal_name: text.min(1, 'La raison sociale est obligatoire.'), trade_name: text, legal_form: text,
  ice: text, rc: text, if_number: text, taxe_professionnelle: text, cnss: text, tva_number: text,
  phone: text, mobile: text, fax: text, email, website: text,
  address_street: text, address_complement: text, address_city: text, address_zip: text, address_region: text, address_country: text,
  delivery_address_street: text, delivery_address_city: text, delivery_address_zip: text, delivery_address_country: text,
  bank_name: text, bank_rib: text, bank_iban: text, bank_swift: text, currency: text,
  payment_terms_days: text.regex(/^-?\d+$/, 'Saisissez un nombre entier.').refine(v => Number.isSafeInteger(Number(v)), 'Nombre entier trop grand.'),
  credit_limit: text.refine(v => !v || /^-?\d+(\.\d+)?$/.test(v), 'Saisissez un montant valide.'),
  category: text, source: text, notes: text, is_active: z.boolean(), contacts: z.array(contactSchema),
})
export type CrmForm = z.infer<typeof crmSchema>
export type ContactForm = z.infer<typeof contactSchema>
export type CrmRecord = { id: string; contacts: (Record<string, unknown> & { id: string })[] } & Record<string, unknown>
export const emptyContact = (): ContactForm => ({ first_name: '', last_name: '', title: '', department: '', email: '', phone: '', mobile: '', notes: '', is_primary: false })
export function formValues(record?: CrmRecord): CrmForm {
  const values: Record<string, unknown> = {}
  for (const key of Object.keys(crmSchema.shape)) values[key] = record?.[key] == null ? '' : String(record[key])
  values.address_country = record?.address_country ?? 'MA'
  values.currency = record?.currency ?? 'MAD'
  values.payment_terms_days = String(record?.payment_terms_days ?? 30)
  values.is_active = record?.is_active ?? true
  values.contacts = (record?.contacts ?? []).map(contact => Object.fromEntries(Object.entries({ ...emptyContact(), id: contact.id }).map(([key, fallback]) => [key, contact[key] ?? fallback])))
  return values as CrmForm
}
export function crmError(error: unknown) {
  return axios.isAxiosError(error) && error.response?.status === 404 ? 'Cette fiche ou ce contact est introuvable.' : errorMessage(error)
}
export function recordPayload(values: CrmForm, kind: CrmKind, creating: boolean) {
  const { contacts: _contacts, ...rest } = values
  const payload: Record<string, unknown> = { ...rest, payment_terms_days: Number(values.payment_terms_days) }
  if (kind === 'suppliers') for (const [key] of clientFields) delete payload[key]
  else delete payload.bank_swift
  // PATCH ignores null. Keep empty strings for clearable text fields.
  for (const key of ['email', 'credit_limit']) if (payload[key] === '') {
    if (creating) payload[key] = null
    else delete payload[key]
  }
  return payload
}
export function contactPayload(contact: ContactForm, creating: boolean) {
  const { id: _id, ...rest } = contact
  const payload: Record<string, unknown> = { ...rest }
  if (!contact.email) {
    if (creating) payload.email = null
    else delete payload.email
  }
  return payload
}
export { api, getData }
export type { Envelope }
