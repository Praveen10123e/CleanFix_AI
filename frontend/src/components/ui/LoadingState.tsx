import React from 'react'
import { Loader2 } from 'lucide-react'
import { cn } from '@/utils/cn'

export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
  label?: string
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  className,
  label,
}) => {
  const sizeMap = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  }

  return (
    <div className="inline-flex items-center gap-2 text-forest-700">
      <Loader2 className={cn('animate-spin', sizeMap[size], className)} />
      {label && <span className="text-xs font-medium text-charcoal-600">{label}</span>}
    </div>
  )
}

export interface LoadingStateProps {
  message?: string
  className?: string
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading classroom AV telemetry...',
  className,
}) => {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center p-12 text-center rounded-lg border border-dashed border-warm-grey-300 bg-ivory-50/70',
        className
      )}
    >
      <Loader2 className="w-8 h-8 text-forest-600 animate-spin mb-3" />
      <p className="text-sm font-medium text-charcoal-700">{message}</p>
      <p className="text-xs text-charcoal-400 mt-1">Connecting to ClassFix service interface</p>
    </div>
  )
}

