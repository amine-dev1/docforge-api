import { z } from 'zod'
import axios from 'axios'
import { errorMessage } from '../invoices/documentModel'

export type CatalogueKind = 'products' | 'categories' | 'units' | 'tax-rates'
export const labels = {
  products: { title: 'Produits', create: 'Nouveau produit' },
  categories: { title: 'Catégories', create: 'Nouvelle catégorie' },
  units: { title: 'Unités', create: 'Nouvelle unité' },
  'tax-rates': { title: 'Taux de TVA', create: 'Nouveau taux' },
}
// product_type ENUM in backend/docs/schema.sql. Tax type is VARCHAR(30).
export const productTypes = { product: 'Produit', service: 'Service', consumable: 'Consommable', package: 'Lot' }
export interface CatalogueRecord {
  id: string
  name: string
  code?: string | null
  reference?: string | null
  description?: string | null
  parent_id?: string | null
  category_id?: string | null
  unit_id?: string | null
  tax_rate_id?: string | null
  symbol?: string
  label?: string
  type?: string
  rate?: string | number
  purchase_price_ht?: string | number
  sale_price_ht?: string | number
  sort_order?: number
  is_active?: boolean
  is_default?: boolean
}
const text = z.string().trim()
const baseSchema = z.object({
  name: text.min(1, 'Le nom est obligatoire.'), code: text, reference: text, description: text,
  symbol: text, label: text, type: text, rate: text, purchase_price_ht: text, sale_price_ht: text,
  sort_order: text, parent_id: text, category_id: text, unit_id: text, tax_rate_id: text,
  is_active: z.boolean(), is_default: z.boolean(),
})
export type CatalogueFormValues = z.infer<typeof baseSchema>
export type FieldName = keyof CatalogueFormValues
export const fields: Record<CatalogueKind, FieldName[]> = {
  units: ['name', 'symbol', 'is_default'],
  'tax-rates': ['name', 'label', 'rate', 'type', 'is_default', 'is_active'],
  categories: ['name', 'code', 'description', 'parent_id', 'sort_order'],
  products: ['name', 'code', 'reference', 'description', 'type', 'category_id', 'unit_id', 'tax_rate_id', 'purchase_price_ht', 'sale_price_ht', 'is_active'],
}
export const relationFields = ['parent_id', 'category_id', 'unit_id', 'tax_rate_id'] as const
export function formSchema(kind: CatalogueKind) {
  return baseSchema.superRefine((values, ctx) => {
    const issue = (field: FieldName, message: string) => ctx.addIssue({ code: 'custom', path: [field], message })
    const limits: Partial<Record<FieldName, number>> = {
      name: { products: 300, categories: 150, units: 50, 'tax-rates': 100 }[kind],
      code: kind === 'categories' ? 30 : 50, reference: 100, symbol: 10, label: 20, type: 30,
    }
    for (const field of fields[kind]) {
      const value = values[field]
      if (typeof value !== 'string') continue
      if (limits[field] && value.length > limits[field]!) issue(field, `${limits[field]} caractères maximum.`)
      if (['symbol', 'label', 'type'].includes(field) && !value) issue(field, 'Ce champ est obligatoire.')
      if (relationFields.some(key => key === field) && value && !z.uuid().safeParse(value).success) issue(field, 'Sélectionnez une valeur valide.')
      if (['rate', 'purchase_price_ht', 'sale_price_ht'].includes(field)) {
        if (!/^-?\d+(\.\d{1,2})?$/.test(value) || Math.abs(Number(value)) >= (field === 'rate' ? 1000 : 10000000000)) issue(field, 'Nombre valide requis (2 décimales maximum, dans les limites du serveur).')
      }
    }
    if (kind === 'products' && !Object.hasOwn(productTypes, values.type)) issue('type', 'Sélectionnez un type de produit.')
    if (kind === 'categories' && (!/^-?\d+$/.test(values.sort_order) || Number(values.sort_order) < -32768 || Number(values.sort_order) > 32767)) issue('sort_order', 'Entier entre −32768 et 32767 requis.')
  })
}
export function initialValues(kind: CatalogueKind, record?: CatalogueRecord): CatalogueFormValues {
  return {
    name: record?.name ?? '', code: record?.code ?? '', reference: record?.reference ?? '', description: record?.description ?? '',
    symbol: record?.symbol ?? '', label: record?.label ?? '', type: record?.type ?? (kind === 'products' ? 'product' : 'TVA'),
    rate: String(record?.rate ?? 0), purchase_price_ht: String(record?.purchase_price_ht ?? 0), sale_price_ht: String(record?.sale_price_ht ?? 0),
    sort_order: String(record?.sort_order ?? 0), parent_id: record?.parent_id ?? '', category_id: record?.category_id ?? '',
    unit_id: record?.unit_id ?? '', tax_rate_id: record?.tax_rate_id ?? '', is_active: record?.is_active ?? true, is_default: record?.is_default ?? false,
  }
}
export function payload(kind: CatalogueKind, values: CatalogueFormValues) {
  return Object.fromEntries(fields[kind].map(key => {
    const value = values[key]
    if (key === 'sort_order') return [key, Number(value)]
    // Empty unique codes must stay NULL, including when editing an uncoded record.
    // Existing values cannot be cleared via PATCH; the form explains that limitation.
    if (value === '' && (relationFields.some(field => field === key) || key === 'code')) return [key, null]
    return [key, value]
  }))
}
export function catalogueError(error: unknown) {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 404) return 'Cet élément du catalogue est introuvable. Actualisez la liste.'
    if (error.response?.status === 409 || (error.response?.status ?? 0) >= 500) return 'Le serveur a refusé cette opération. Vérifiez les valeurs uniques (code, symbole ou taux/type) et les éventuelles utilisations de cet élément.'
  }
  return errorMessage(error)
}
export function eligibleParents(categories: CatalogueRecord[], id?: string) {
  const excluded = new Set(id ? [id] : [])
  let changed = true
  while (changed) {
    changed = false
    for (const category of categories) if (category.parent_id && excluded.has(category.parent_id) && !excluded.has(category.id)) {
      excluded.add(category.id)
      changed = true
    }
  }
  return categories.filter(category => !excluded.has(category.id))
}
