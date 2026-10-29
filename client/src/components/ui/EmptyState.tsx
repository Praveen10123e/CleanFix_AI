import React from 'react'
import { Inbox } from 'lucide-react'
import { cn } from '@/utils/cn'
import { Button } from './Button'

export interface EmptyStateProps {
  icon?: React.ReactNode
  title: string
  description?: string
  actionLabel?: string
  onAction?: () => void
  className?: string
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actionLabel,
  onAction,
  className,
}) => {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center p-12 text-center rounded-lg border border-dashed border-warm-grey-300 bg-white/70',
        className
      )}
    >
      <div className="w-12 h-12 rounded-full bg-ivory-200 text-charcoal-500 flex items-center justify-center mb-4">
        {icon || <Inbox className="w-6 h-6" />}
      </div>
      <h4 className="text-sm font-semibold text-charcoal-900 mb-1">{title}</h4>
      {description && <p className="text-xs text-charcoal-500 max-w-sm mb-5">{description}</p>}
      {actionLabel && onAction && (
        <Button size="sm" variant="outline" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  )
}

