import { forwardRef } from 'react'
import type { ButtonHTMLAttributes } from 'react'
import { destructiveButton, primaryButton, secondaryButton } from './classNames'

type Variant = 'primary' | 'secondary' | 'destructive'
const variantClass: Record<Variant, string> = { primary: primaryButton, secondary: secondaryButton, destructive: destructiveButton }

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  /** Exact styling for existing layouts that must retain their appearance. */
  classNameOverride?: string
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { classNameOverride, variant = 'secondary', className = '', type = 'button', ...rest },
  ref,
) {
  return <button ref={ref} type={type} className={classNameOverride ?? `${variantClass[variant]} ${className}`} {...rest} />
})
