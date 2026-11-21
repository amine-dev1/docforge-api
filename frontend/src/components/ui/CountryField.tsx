import { forwardRef } from 'react'
import { SelectField } from './Select'
import type { SelectFieldProps, SelectOption } from './Select'
import { countries, countryByCode } from './countries'

export function CountryFlag({ code }: { code: string }) {
  if (!countryByCode.has(code)) return null
  return <img src={`https://flagcdn.com/${code.toLowerCase()}.svg`} alt="" aria-hidden="true"
    width="24" height="16" loading="lazy" referrerPolicy="no-referrer" className="h-4 w-6 shrink-0 rounded-sm object-cover"
    onLoad={event => { event.currentTarget.style.visibility = 'visible' }}
    onError={event => { event.currentTarget.style.visibility = 'hidden' }} />
}

const options = countries.map(country => ({ value: country.code, label: `${country.name} (${country.code})` }))
function renderCountry(option: SelectOption) {
  return <span className="flex min-w-0 items-center gap-2"><CountryFlag code={option.value} /><span className="truncate">{option.label}</span></span>
}

export type CountryFieldProps = Omit<SelectFieldProps, 'options' | 'renderOption' | 'renderValue'>
export const CountryField = forwardRef<HTMLButtonElement, CountryFieldProps>(function CountryField(
  { label = 'Pays', value, required, ...props }, ref,
) {
  // Preserve legacy values visibly until the user chooses a supported ISO code.
  const items = value && !countryByCode.has(value)
    ? [{ value, label: `${value} (valeur enregistrée)` }, ...options] : options
  return <SelectField {...props} ref={ref} label={label} value={value} required={required}
    placeholder={required ? 'Choisir un pays' : 'Non précisé'} options={items} renderOption={renderCountry} />
})
