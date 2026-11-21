import { z } from 'zod'
import { getData } from '../invoices/documentModel'
import type { Amount, DocumentRecord } from '../invoices/documentModel'

export interface PaymentAllocation { id: string; document_id: string; amount_allocated: Amount }
export interface PaymentRecord {
  id: string; client_id: string | null; reference: string; method: string; amount: Amount; currency: string
  amount_allocated: Amount; amount_remaining: Amount; status: string; payment_date: string
  notes: string | null; bank_reference: string | null; allocations: PaymentAllocation[]
}
export const methods: Record<string, string> = { bank_transfer: 'Virement bancaire', cheque: 'Chèque', cash: 'Espèces', card: 'Carte bancaire', mobile_payment: 'Paiement mobile', other: 'Autre' }
// Numeric(15, 2): integer cents keep sums and comparisons exact.
export function cents(value: Amount): bigint {
  const raw = String(value)
  if (!/^\d+(\.\d{1,2})?$/.test(raw)) return 0n
  const [whole, fraction = ''] = raw.split('.')
  return BigInt(whole) * 100n + BigInt(fraction.padEnd(2, '0'))
}
export function decimal(value: bigint): string {
  const absolute = value < 0n ? -value : value
  return `${value < 0n ? '-' : ''}${absolute / 100n}.${String(absolute % 100n).padStart(2, '0')}`
}
const amount = z.string().regex(/^\d{1,13}(\.\d{1,2})?$/, 'Montant positif, avec 2 décimales maximum.').refine(v => cents(v) > 0n, 'Le montant doit être supérieur à zéro.')
export const paymentSchema = z.object({
  client_id: z.union([z.literal(''), z.uuid('Sélectionnez un client.')]),
  reference: z.string().trim().min(1, 'La référence est obligatoire.').max(50),
  method: z.string().min(1, 'Sélectionnez une méthode.'), amount,
  currency: z.string().trim().regex(/^[A-Z]{3}$/, 'Utilisez un code devise de 3 lettres majuscules.'),
  payment_date: z.iso.date('Date invalide.'), bank_reference: z.string().max(100), notes: z.string(),
  allocations: z.array(z.object({ document_id: z.uuid(), amount_allocated: amount })),
}).superRefine((values, ctx) => {
  const total = values.allocations.reduce((sum, row) => sum + cents(row.amount_allocated), 0n)
  if (total > cents(values.amount)) ctx.addIssue({ code: 'custom', path: ['allocations'], message: 'Le total alloué dépasse le montant du paiement.' })
  const seen = new Set<string>()
  values.allocations.forEach((row, index) => {
    if (seen.has(row.document_id)) ctx.addIssue({ code: 'custom', path: ['allocations', index, 'document_id'], message: 'Cette facture est déjà sélectionnée.' })
    seen.add(row.document_id)
  })
})
export type PaymentFormValues = z.infer<typeof paymentSchema>
export function allocationIssues(values: PaymentFormValues, invoices: DocumentRecord[]) {
  return values.allocations.flatMap((row, index) => {
    const invoice = invoices.find(item => item.id === row.document_id)
    const message = !invoice || invoice.client_id !== values.client_id || invoice.status === 'cancelled' || cents(invoice.amount_due) <= 0n
      ? 'Cette facture n’est plus ouverte pour ce client.'
      : invoice.currency !== values.currency ? 'La devise de la facture doit correspondre à celle du paiement.'
      : cents(row.amount_allocated) > cents(invoice.amount_due) ? 'Le montant dépasse le solde dû de cette facture.' : null
    return message ? [{ index, message }] : []
  })
}
export async function getInvoices(signal?: AbortSignal) {
  const rows: DocumentRecord[] = []
  for (let page = 1; ; page++) {
    const batch = await getData<DocumentRecord[]>('/invoices/', signal, { page, size: 100 })
    rows.push(...batch)
    if (batch.length < 100) return rows
  }
}
