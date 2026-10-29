import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from './AuthContext'
import { Button } from '@/components/ui/Button'
import { ShieldAlert, ArrowLeft, LogOut } from 'lucide-react'

export const AccessDeniedPage: React.FC = () => {
  const { currentUser, logout } = useAuth()
  const navigate = useNavigate()

  const handleReturn = () => {
    if (currentUser?.role) {
      navigate(`/${currentUser.role}`)
    } else {
      navigate('/login')
    }
  }

  return (
    <div className="min-h-screen bg-app-bg flex items-center justify-center p-6 text-charcoal-900">
      <div className="max-w-md w-full bg-white p-8 rounded-lg border border-warm-grey-200 shadow-card text-center space-y-5">
        <div className="w-14 h-14 rounded-full bg-terracotta-50 text-terracotta-600 flex items-center justify-center mx-auto">
          <ShieldAlert className="w-7 h-7" />
        </div>

        <div>
          <h2 className="text-xl font-bold text-charcoal-900 tracking-tight">Access Restricted</h2>
          <p className="text-xs text-charcoal-500 mt-1.5 leading-relaxed">
            Your authenticated account does not possess the operational permissions required to view this area.
          </p>
        </div>

        {currentUser && (
          <div className="p-3 bg-app-soft rounded border border-warm-grey-200 text-xs text-left space-y-1">
            <div className="flex justify-between">
              <span className="text-charcoal-400">Authenticated User:</span>
              <span className="font-semibold text-charcoal-800">{currentUser.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-charcoal-400">Assigned Role:</span>
              <span className="font-mono uppercase font-bold text-forest-700">{currentUser.role}</span>
            </div>
          </div>
        )}

        <div className="flex flex-col sm:flex-row items-center justify-center gap-2 pt-2">
          <Button
            variant="primary"
            size="sm"
            onClick={handleReturn}
            leftIcon={<ArrowLeft className="w-3.5 h-3.5" />}
          >
            Return to Dashboard
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={logout}
            leftIcon={<LogOut className="w-3.5 h-3.5" />}
          >
            Sign Out
          </Button>
        </div>
      </div>
    </div>
  )
}

