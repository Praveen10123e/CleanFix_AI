import React from 'react'
import { cn } from '@/utils/cn'

export type BadgeVariant =
  | 'default'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'neutral'
  | 'forest'
  | 'terracotta'

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant
  size?: 'sm' | 'md'
  dot?: boolean
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = 'default',
  size = 'md',
  dot = false,
  children,
  ...props
}) => {
  const variantStyles: Record<BadgeVariant, { bg: string; text: string; dot: string; border: string }> = {
    default: {
      bg: 'bg-ivory-200',
      text: 'text-charcoal-800',
      dot: 'bg-charcoal-500',
      border: 'border-warm-grey-300',
    },
    success: {
      bg: 'bg-emerald-50',
      text: 'text-emerald-800',
      dot: 'bg-emerald-600',
      border: 'border-emerald-200',
    },
    warning: {
      bg: 'bg-amber-50',
      text: 'text-amber-800',
      dot: 'bg-amber-500',
      border: 'border-amber-200',
    },
    danger: {
      bg: 'bg-rose-50',
      text: 'text-rose-800',
      dot: 'bg-rose-600',
      border: 'border-rose-200',
    },
    info: {
      bg: 'bg-sky-50',
      text: 'text-sky-800',
      dot: 'bg-sky-600',
      border: 'border-sky-200',
    },
    neutral: {
      bg: 'bg-warm-grey-100',
      text: 'text-charcoal-700',
      dot: 'bg-charcoal-400',
      border: 'border-warm-grey-200',
    },
    forest: {
      bg: 'bg-forest-50',
      text: 'text-forest-700',
      dot: 'bg-forest-600',
      border: 'border-forest-200',
    },
    terracotta: {
      bg: 'bg-terracotta-50',
      text: 'text-terracotta-700',
      dot: 'bg-terracotta-600',
      border: 'border-terracotta-200',
    },
  }

  const sizeStyles = {
    sm: 'text-xs px-2 py-0.5 font-medium',
    md: 'text-xs px-2.5 py-1 font-medium',
  }

  const v = variantStyles[variant]

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border',
        v.bg,
        v.text,
        v.border,
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {dot && <span className={cn('w-1.5 h-1.5 rounded-full shrink-0', v.dot)} />}
      <span>{children}</span>
    </span>
  )
}

