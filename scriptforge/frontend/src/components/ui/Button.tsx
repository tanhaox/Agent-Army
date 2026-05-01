import { ButtonHTMLAttributes, ReactNode } from 'react';
import Spinner from './Spinner';

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';
type Size = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  children: ReactNode;
}

const VARIANT_CLASSES: Record<Variant, string> = {
  primary:
    'bg-brand text-white hover:bg-brand-hover active:bg-brand-active',
  secondary:
    'bg-transparent border border-border-default text-text-primary hover:bg-bg-hover active:bg-bg-card',
  ghost:
    'bg-transparent text-text-secondary hover:text-text-primary hover:bg-bg-hover',
  danger:
    'bg-error text-white hover:bg-red-600 active:bg-red-700',
};

const SIZE_CLASSES: Record<Size, string> = {
  sm: 'px-3 py-1.5 text-xs rounded-md',
  md: 'px-4 py-2 text-sm rounded-md',
  lg: 'px-6 py-2.5 text-base rounded-lg',
};

export default function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  children,
  className = '',
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 font-medium transition-all duration-150 ease-[cubic-bezier(0.4,0,0.2,1)] cursor-pointer
        ${VARIANT_CLASSES[variant]}
        ${SIZE_CLASSES[size]}
        ${disabled || loading ? 'opacity-40 pointer-events-none' : ''}
        ${className}`}
      {...props}
    >
      {loading && <Spinner size={size === 'sm' ? 14 : 16} />}
      {children}
    </button>
  );
}
