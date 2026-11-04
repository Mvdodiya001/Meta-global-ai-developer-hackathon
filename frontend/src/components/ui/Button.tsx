import type { ButtonHTMLAttributes, ReactNode } from 'react'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  icon?: ReactNode
}

const VARIANTS: Record<NonNullable<ButtonProps['variant']>, string> = {
  primary: 'ct-btn--primary',
  secondary: 'ct-btn--secondary',
  ghost: 'ct-btn--ghost',
  danger: 'ct-btn--danger',
}

/** Shared action button for the whole product (P4 design system). */
export function Button({
  variant = 'secondary',
  size = 'md',
  loading = false,
  icon,
  className = '',
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      type="button"
      className={[
        'ct-btn',
        VARIANTS[variant],
        size === 'sm' ? 'ct-btn--sm' : size === 'lg' ? 'ct-btn--lg' : '',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading ? <span className="ct-spinner" aria-hidden="true" /> : icon}
      {children}
    </button>
  )
}
