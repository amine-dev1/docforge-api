import { forwardRef, useId, useState } from 'react'
import { TextField } from './Field'
import type { TextFieldProps } from './Field'
import { SelectField } from './Select'
import { CountryFlag } from './CountryField'
import { countries, countryByCode, countryForPhone, changePhoneCountry } from './countries'

const options = countries.map(country => ({ value: country.code, label: `${country.name} (${country.code}) +${country.dial}` }))
export interface PhoneFieldProps extends Omit<TextFieldProps, 'value' | 'defaultValue' | 'onChange' | 'type'> {
  value: string
  onChange: (value: string) => void
  defaultCountry?: string
}

export const PhoneField = forwardRef<HTMLInputElement, PhoneFieldProps>(function PhoneField(
  { value, onChange, defaultCountry = 'MA', label = 'Téléphone', id, disabled, readOnly, onBlur, hint, ...props }, ref,
) {
  const autoId = useId()
  const [chosenCountry, setChosenCountry] = useState<string | null>(null)
  const preferred = chosenCountry ?? defaultCountry
  const country = countryForPhone(value, preferred)
  const dial = countryByCode.get(country)?.dial
  return <div className="min-w-0">
    <div className="grid grid-cols-[minmax(112px,0.85fr)_minmax(0,1.15fr)] items-start gap-2">
      <SelectField label="Indicatif" id={`${id ?? autoId}-country`} value={country} options={options}
        aria-label={`Pays et indicatif — ${label}`} disabled={disabled || readOnly} placeholder="Indicatif"
        onChange={next => { setChosenCountry(next); onChange(changePhoneCountry(value, country, next)) }}
        renderValue={option => <span className="flex items-center gap-1.5"><CountryFlag code={option.value} /><span className="text-xs">{option.value} +{countryByCode.get(option.value)?.dial}</span></span>}
        renderOption={option => <span className="flex items-center gap-2"><CountryFlag code={option.value} /><span>{option.label}</span></span>} />
      <TextField {...props} ref={ref} id={id ?? autoId} label={label} type="tel" inputMode="tel" autoComplete="tel"
        value={value} onChange={event => onChange(event.target.value)} onBlur={onBlur} disabled={disabled} readOnly={readOnly}
        placeholder={dial ? `+${dial}…` : '+…'} />
    </div>
    {hint && <p className="mt-1 text-xs text-text-muted">{hint}</p>}
  </div>
})
