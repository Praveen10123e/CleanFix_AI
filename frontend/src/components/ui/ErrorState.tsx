import React from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { cn } from '@/utils/cn'
import { Button } from './Button'

export interface ErrorStateProps {
  title?: string
  message: string
  onRetry?: () => void
  className?: string
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Service Unavailable',
  message,
  onRetry,
  className,
}) => {
  return (
    <div
      className={cn(
        'p-6 rounded-lg border border-rose-200 bg-rose-50/70 text-charcoal-900',
        className
      )}
    >
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
        <div className="flex-1">
          <h4 className="text-sm font-semibold text-rose-900">{title}</h4>
          <p className="text-xs text-rose-800 mt-1">{message}</p>
          {onRetry && (
            <div className="mt-4">
              <Button
                size="sm"
                variant="outline"
                onClick={onRetry}
                leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
                className="border-rose-300 text-rose-900 hover:bg-rose-100"
              >
                Retry Request
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

