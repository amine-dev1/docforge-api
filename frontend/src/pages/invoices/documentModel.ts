import axios from 'axios'
import { z } from 'zod'
import { api } from '../../lib/api'

export type DocumentKind = 'invoices' | 'quotes'
export const documentLabels = {
  invoices: { title: 'Factures', create: 'Nouvelle facture', singular: 'Facture', type: 'invoice' },
  quotes: { title: 'Devis', create: 'Nouveau devis', singular: 'Devis', type: 'quote' },
} as const
export type Amount = string | number
export interface DocumentLine {
  id: string; position: number; description: string; quantity: Amount; unit: string | null
  unit_price_ht: Amount; discount_pct: Amount; discount_amount: Amount
  line_total_ht: Amount; tax_rate_value: Amount; tax_amount: Amount; line_total_ttc: Amount
}
export interface DocumentRecord {
  id: string; type: string; number: string; status: string; currency: string
  client_id: string | null; subtotal_ht: Amount; total_discount: Amount; total_tax: Amount
  total_ttc: Amount; amount_paid: Amount; amount_due: Amount; pdf_url: string | null
  issued_at: string | null; due_at: string | null; notes: string | null; terms: string | null
  created_at: string; lines: DocumentLine[]
}
export interface Client { id: string; legal_name: string; code: string | null; is_active: boolean }
export interface Envelope<T> { status: number; data: T }
export async function getData<T>(path: string, signal?: AbortSignal, params?: Record<string, unknown>) {
  return (await api.get<Envelope<T>>(path, { signal, params })).data.data
}
// The client endpoint is paginated, without a total count.
export async function getClients(signal?: AbortSignal) {
  const clients: Client[] = []
  for (let page = 1; ; page++) {
    const batch = await getData<Client[]>('/clients/', signal, { page, size: 100 })
    clients.push(...batch)
    if (batch.length < 100) return clients
  }
}
const decimal = z.string().regex(/^\d+(\.\d{1,6})?$/, 'Saisissez un nombre positif (6 décimales maximum).')
const percentage = decimal.refine(v => Number(v) <= 100, 'Le pourcentage doit être compris entre 0 et 100.')
const date = z.string().refine(v => !v || /^\d{4}-\d{2}-\d{2}$/.test(v) && Number.isFinite(Date.parse(v)), 'Date invalide.')
export const documentFormSchema = z.object({
  client_id: z.uuid('Sélectionnez un client.'),
  issued_at: date, due_at: date,
  notes: z.string(), terms: z.string(),
  lines: z.array(z.object({
    description: z.string().trim().min(1, 'La description est obligatoire.'),
    quantity: decimal.refine(v => Number(v) > 0, 'La quantité doit être supérieure à zéro.'),
    unit_price_ht: decimal, discount_pct: percentage, discount_amount: decimal, tax_rate_value: percentage,
  })).min(1, 'Ajoutez au moins une ligne.'),
})
export type DocumentForm = z.infer<typeof documentFormSchema>
export const emptyLine = (): DocumentForm['lines'][number] => ({
  description: '', quantity: '1', unit_price_ht: '0', discount_pct: '0', discount_amount: '0', tax_rate_value: '0',
})

// Decimal arithmetic: no binary floating-point rounding, nor intermediate rounding.
// Mirrors documents.py::_compute_line, including percentage precedence over fixed discount.
type Decimal = { value: bigint; scale: number }
const power = (n: number) => 10n ** BigInt(n)
function dec(raw: string): Decimal {
  if (!/^\d+(\.\d{1,6})?$/.test(raw)) return { value: 0n, scale: 0 }
  return { value: BigInt(raw.replace('.', '')), scale: raw.split('.')[1]?.length ?? 0 }
}
function add(a: Decimal, b: Decimal, sign = 1n): Decimal {
  const scale = Math.max(a.scale, b.scale)
  return { value: a.value * power(scale - a.scale) + sign * b.value * power(scale - b.scale), scale }
}
function mul(a: Decimal, b: Decimal): Decimal { return { value: a.value * b.value, scale: a.scale + b.scale } }
function percent(a: Decimal, b: Decimal): Decimal { const result = mul(a, b); return { ...result, scale: result.scale + 2 } }
function serialize(a: Decimal): string {
  const sign = a.value < 0n ? '-' : ''
  const digits = (a.value < 0n ? -a.value : a.value).toString().padStart(a.scale + 1, '0')
  return sign + (a.scale ? `${digits.slice(0, -a.scale)}.${digits.slice(-a.scale)}` : digits)
}
export function calculateTotals(lines: DocumentForm['lines']) {
  const computed = lines.map(line => {
    const base = mul(dec(line.quantity), dec(line.unit_price_ht))
    const pct = dec(line.discount_pct)
    const discount = pct.value ? percent(base, pct) : dec(line.discount_amount)
    const ht = add(base, discount, -1n)
    const tax = percent(ht, dec(line.tax_rate_value))
    return { discount, ht, tax, ttc: add(ht, tax) }
  })
  const sum = (key: keyof typeof computed[number]) => serialize(computed.reduce((total, line) => add(total, line[key]), dec('0')))
  return {
    subtotal_ht: sum('ht'), total_discount: sum('discount'), total_tax: sum('tax'), total_ttc: sum('ttc'),
    lines: computed.map(line => ({ line_total_ttc: serialize(line.ttc) })),
  }
}

// Generates the PDF on demand (doesn't depend on pdf_url / Google Drive, which
// isn't configured in most environments) and downloads it without opening a tab.
export async function openDocumentPdf(id: string, number: string, template = 'minimal') {
  const response = await api.get(`/documents/${id}/pdf`, { params: { template }, responseType: 'blob' })
  const url = URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
  const link = document.createElement('a')
  try {
    link.href = url
    link.download = `${number}.pdf`
    document.body.appendChild(link)
    link.click()
  } finally {
    link.remove()
    // Give the browser time to start reading the blob before releasing it.
    setTimeout(() => URL.revokeObjectURL(url), 1_000)
  }
}

export function pdfLink(url: string | null): string | null {
  if (!url) return null
  try {
    const parsed = new URL(url, window.location.origin)
    if (!['https:', 'http:'].includes(parsed.protocol)) return null
    const driveId = parsed.hostname === 'drive.google.com' && parsed.pathname.match(/^\/file\/d\/([\w-]+)/)?.[1]
    return driveId ? `https://drive.google.com/uc?export=download&id=${encodeURIComponent(driveId)}` : parsed.href
  } catch { return null }
}

export function money(value: Amount, currency: string) {
  try { return new Intl.NumberFormat('fr-MA', { style: 'currency', currency }).format(Number(value)) }
  catch { return `${Number(value).toFixed(2)} ${currency}` }
}
export function dateLabel(value: string | null) {
  if (!value) return '—'
  const date = new Date(value.slice(0, 10) + 'T12:00:00')
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleDateString('fr-FR')
}
export function errorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 404) return 'Ce document est introuvable.'
    if (error.response?.status === 401 || error.response?.status === 403) return 'Votre session ne permet pas cet accès. Veuillez vous reconnecter.'
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) return detail.map(e => `${e.loc?.slice(1).join(' / ') ?? 'Champ'} : ${e.msg}`).join(' ; ')
  }
  return 'Impossible de joindre le serveur. Vérifiez votre connexion et réessayez.'
}
