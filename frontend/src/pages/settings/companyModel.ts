export interface CompanyField {
  name: string
  label: string
  required?: boolean
  maxLength?: number
  type?: 'email' | 'number' | 'textarea' | 'checkbox'
  options?: string[]
  pattern?: RegExp
  hint?: string
}

const currency = { required: true, maxLength: 3, pattern: /^[A-Z]{3}$/, hint: 'Code ISO à 3 lettres majuscules (MAD, EUR…).' }
const country = { maxLength: 2, pattern: /^[A-Z]{2}$/, hint: 'Code ISO à 2 lettres majuscules (MA, FR…).' }
const color = { required: true, maxLength: 7, pattern: /^#[\da-fA-F]{6}$/, hint: 'Couleur hexadécimale : # suivi de 6 caractères.' }
const prefix = { required: true, maxLength: 10 }

export const companySections: { title: string; fields: CompanyField[] }[] = [
  { title: 'Identité légale', fields: [
    { name: 'legal_name', label: 'Raison sociale', required: true, maxLength: 300 },
    { name: 'slug', label: 'Identifiant URL', required: true, maxLength: 100 },
    { name: 'trade_name', label: 'Nom commercial', maxLength: 300 },
    { name: 'legal_form', label: 'Forme juridique', options: ['SARL', 'SA', 'SAS', 'SNC', 'Auto-entrepreneur', 'Association', 'Autre'] },
    { name: 'sector', label: 'Secteur d’activité', maxLength: 150 },
    { name: 'activity_description', label: 'Description de l’activité', type: 'textarea' },
    { name: 'ice', label: 'ICE', maxLength: 15, pattern: /^\d{15}$/, hint: '15 chiffres.' },
    { name: 'rc', label: 'Registre de commerce', maxLength: 30 },
    { name: 'if_number', label: 'Identifiant fiscal', maxLength: 20 },
    { name: 'taxe_professionnelle', label: 'Taxe professionnelle', maxLength: 20 },
    { name: 'cnss', label: 'CNSS', maxLength: 20 },
    { name: 'capital_social', label: 'Capital social', type: 'number', pattern: /^\d{1,13}(\.\d{1,2})?$/, hint: 'Montant positif ou nul, 2 décimales maximum.' },
    { name: 'capital_currency', label: 'Devise du capital', ...currency },
  ] },
  { title: 'Régime fiscal', fields: [
    { name: 'tva_regime', label: 'Régime de TVA', required: true, options: ['Encaissement', 'Débit', 'Exonéré', 'Non assujetti'] },
    { name: 'tva_assujetti', label: 'Entreprise assujettie à la TVA', type: 'checkbox' },
  ] },
  { title: 'Coordonnées', fields: [
    { name: 'phone_main', label: 'Téléphone principal', maxLength: 20 },
    { name: 'phone_secondary', label: 'Téléphone secondaire', maxLength: 20 },
    { name: 'fax', label: 'Fax', maxLength: 20 },
    { name: 'email_general', label: 'E-mail général', type: 'email', maxLength: 255 },
    { name: 'email_facturation', label: 'E-mail de facturation', type: 'email', maxLength: 255 },
    { name: 'website', label: 'Site web', maxLength: 300 },
  ] },
  { title: 'Adresse', fields: [
    { name: 'address_street', label: 'Rue', maxLength: 300 },
    { name: 'address_complement', label: 'Complément', maxLength: 200 },
    { name: 'address_city', label: 'Ville', maxLength: 100 },
    { name: 'address_zip', label: 'Code postal', maxLength: 10 },
    { name: 'address_region', label: 'Région', maxLength: 100 },
    { name: 'address_country', label: 'Pays', ...country, required: true },
  ] },
  { title: 'Adresse de facturation', fields: [
    { name: 'billing_address_street', label: 'Rue', maxLength: 300 },
    { name: 'billing_address_city', label: 'Ville', maxLength: 100 },
    { name: 'billing_address_zip', label: 'Code postal', maxLength: 10 },
    { name: 'billing_address_country', label: 'Pays', ...country },
  ] },
  { title: 'Banque', fields: [
    { name: 'bank_name', label: 'Banque', maxLength: 100 },
    { name: 'bank_branch', label: 'Agence', maxLength: 100 },
    { name: 'bank_rib', label: 'RIB', maxLength: 24, pattern: /^\d{24}$/, hint: '24 chiffres, sans espaces.' },
    { name: 'bank_iban', label: 'IBAN', maxLength: 34 },
    { name: 'bank_swift', label: 'SWIFT / BIC', maxLength: 11 },
  ] },
  { title: 'Image de marque PDF', fields: [
    { name: 'logo_url', label: 'URL du logo', maxLength: 500 },
    { name: 'primary_color', label: 'Couleur principale', ...color },
    { name: 'secondary_color', label: 'Couleur secondaire', ...color },
    { name: 'font_family', label: 'Police des documents', required: true, maxLength: 50 },
  ] },
  { title: 'Numérotation des documents', fields: [
    { name: 'invoice_prefix', label: 'Préfixe des factures', ...prefix },
    { name: 'quote_prefix', label: 'Préfixe des devis', ...prefix },
    { name: 'po_prefix', label: 'Préfixe des bons de commande', ...prefix },
    { name: 'dn_prefix', label: 'Préfixe des bons de livraison', ...prefix },
    { name: 'cn_prefix', label: 'Préfixe des avoirs', ...prefix },
  ] },
  { title: 'Préférences documents', fields: [
    { name: 'default_language', label: 'Langue par défaut', required: true, maxLength: 5, hint: 'Code de langue (fr, en, ar…).' },
    { name: 'default_currency', label: 'Devise par défaut', ...currency },
    { name: 'payment_terms_days', label: 'Délai de paiement (jours)', type: 'number', required: true },
    { name: 'quote_validity_days', label: 'Validité des devis (jours)', type: 'number', required: true },
    { name: 'payment_conditions', label: 'Conditions de paiement', type: 'textarea' },
    { name: 'invoice_footer', label: 'Pied de page des factures', type: 'textarea' },
  ] },
]

export type CompanyValues = Record<string, string | boolean>
export type CompanyRecord = { tenant_id: string } & Record<string, string | number | boolean | null>
export const companyFields = companySections.flatMap(section => section.fields)
export function formValues(record: CompanyRecord): CompanyValues {
  return Object.fromEntries(companyFields.map(field => [field.name,
    field.type === 'checkbox' ? record[field.name] === true : String(record[field.name] ?? ''),
  ]))
}

export function validateField(field: CompanyField, value: string | boolean) {
  if (field.type === 'checkbox') return true
  const text = String(value).trim()
  if (!text) return field.required ? 'Ce champ est obligatoire.' : true
  if (field.maxLength && text.length > field.maxLength) return `${field.maxLength} caractères maximum.`
  if (field.options && !field.options.includes(text)) return 'Sélectionnez une valeur proposée.'
  if (field.pattern && !field.pattern.test(text)) return field.hint ?? 'Format invalide.'
  if (field.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(text)) return 'Adresse e-mail invalide.'
  if (field.type === 'number' && field.name !== 'capital_social' && (!/^\d+$/.test(text) || Number(text) > 32767)) return 'Saisissez un nombre entier entre 0 et 32767.'
  return true
}

// Only editable, changed fields are sent. Blank optional fields explicitly clear
// their stored value; decimal capital stays a string to preserve its precision.
export function companyPayload(values: CompanyValues, original: CompanyValues) {
  return Object.fromEntries(companyFields.flatMap(field => {
    const value = typeof values[field.name] === 'string' ? String(values[field.name]).trim() : values[field.name]
    if (value === original[field.name]) return []
    return [[field.name, value === '' ? null : field.type === 'number' && field.name !== 'capital_social' ? Number(value) : value]]
  }))
}
