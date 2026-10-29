import React, { useState, useEffect, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'
import { Button } from '@/components/ui/Button'
import {
  MonitorSpeaker,
  AlertCircle,
  School,
  CheckCircle2,
  Lock,
  KeyRound,
  ExternalLink,
} from 'lucide-react'
import { API_CONFIG } from '@/services/api/config'

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string
            callback: (response: { credential?: string }) => void
            auto_select?: boolean
            cancel_on_tap_outside?: boolean
          }) => void
          prompt: (notification?: (notification: unknown) => void) => void
          renderButton: (
            parent: HTMLElement,
            options: {
              type?: 'standard' | 'icon'
              theme?: 'outline' | 'filled_blue' | 'filled_black'
              size?: 'large' | 'medium' | 'small'
              text?: 'signin_with' | 'signup_with' | 'continue_with' | 'signin'
              shape?: 'rectangular' | 'pill' | 'circle' | 'square'
              width?: number
            }
          ) => void
        }
      }
    }
  }
}

export const LoginPage: React.FC = () => {
  const { loginWithGoogle, isAuthenticated, currentUser } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [manualToken, setManualToken] = useState('')
  const [showManualInput, setShowManualInput] = useState(false)
  const [gisInitialized, setGisInitialized] = useState(false)
  const googleBtnContainerRef = useRef<HTMLDivElement>(null)

  const googleClientId = API_CONFIG.googleClientId

  // Redirect if already authenticated based on backend role
  useEffect(() => {
    if (isAuthenticated && currentUser) {
      const from = (location.state as { from?: { pathname: string } })?.from?.pathname
      navigate(from || `/${currentUser.role}`, { replace: true })
    }
  }, [isAuthenticated, currentUser, navigate, location])

  // Process authenticated Google ID token
  const processGoogleToken = async (idToken: string) => {
    setIsLoading(true)
    setErrorMessage(null)
    try {
      const user = await loginWithGoogle(idToken)
      // Redirect strictly based on the actual role returned by the backend
      navigate(`/${user.role}`, { replace: true })
    } catch (err) {
      setErrorMessage(
        err instanceof Error
          ? err.message
          : 'Authentication failed. Please verify that your account is provisioned in the campus database.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  // Initialize Google Identity Services (GIS) if client ID is configured
  useEffect(() => {
    if (!googleClientId) return

    const initGIS = () => {
      if (window.google?.accounts?.id) {
        window.google.accounts.id.initialize({
          client_id: googleClientId,
          callback: (response: { credential?: string }) => {
            if (response.credential) {
              processGoogleToken(response.credential)
            } else {
              setErrorMessage('Google Sign-In completed without returning an ID token.')
            }
          },
        })
        setGisInitialized(true)

        if (googleBtnContainerRef.current) {
          window.google.accounts.id.renderButton(googleBtnContainerRef.current, {
            type: 'standard',
            theme: 'outline',
            size: 'large',
            text: 'continue_with',
            shape: 'rectangular',
            width: 320,
          })
        }
      }
    }

    if (window.google?.accounts?.id) {
      initGIS()
    } else {
      // If script tag not yet loaded, wait for it
      const interval = setInterval(() => {
        if (window.google?.accounts?.id) {
          clearInterval(interval)
          initGIS()
        }
      }, 200)
      return () => clearInterval(interval)
    }
  }, [googleClientId])

  const handleGoogleClick = () => {
    if (!googleClientId) {
      setErrorMessage(
        'Google OAuth Client ID is not configured. Please set VITE_GOOGLE_CLIENT_ID in your .env file or use an authorized ID token below.'
      )
      setShowManualInput(true)
      return
    }

    if (window.google?.accounts?.id && gisInitialized) {
      window.google.accounts.id.prompt()
    } else {
      setErrorMessage(
        'Google Sign-In is initializing. If this persists, verify your network connection to accounts.google.com.'
      )
    }
  }

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!manualToken.trim()) return
    await processGoogleToken(manualToken.trim())
  }

  return (
    <div className="min-h-screen bg-app-bg flex items-center justify-center p-4 sm:p-6 lg:p-10">
      <div className="max-w-4xl w-full bg-white rounded-xl border border-warm-grey-200 shadow-elevated overflow-hidden grid grid-cols-1 lg:grid-cols-12 min-h-[560px]">
        {/* Left Column: Institutional Branding (5 cols) */}
        <div className="lg:col-span-5 bg-forest-600 p-8 sm:p-10 text-white flex flex-col justify-between relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-forest-700/80 to-forest-900/90 pointer-events-none" />

          <div className="relative z-10 space-y-6">
            <div className="flex items-center gap-2.5">
              <div className="w-10 h-10 rounded-lg bg-white/10 backdrop-blur-xs border border-white/20 flex items-center justify-center">
                <MonitorSpeaker className="w-5 h-5 text-emerald-300" />
              </div>
              <div>
                <div className="font-bold text-lg leading-tight tracking-tight">ClassFix AI</div>
                <div className="text-[11px] text-emerald-200/80 font-medium">Smart Classroom AV Platform</div>
              </div>
            </div>

            <div className="space-y-2 pt-4">
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white leading-snug">
                Campus Audio-Visual Operations & Diagnostics
              </h1>
              <p className="text-xs text-emerald-100/80 leading-relaxed">
                Single sign-on access for faculty lectures, AV field technicians, and system administrators.
              </p>
            </div>

            <div className="space-y-3 pt-2 text-xs text-emerald-100/90">
              <div className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-300 shrink-0 mt-0.5" />
                <span>RAG-powered interactive diagnostics for classroom equipment</span>
              </div>
              <div className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-300 shrink-0 mt-0.5" />
                <span>Instant field technician ticket escalation during live lectures</span>
              </div>
              <div className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-300 shrink-0 mt-0.5" />
                <span>Centralized campus fleet telemetry and SLA resolution tracking</span>
              </div>
            </div>
          </div>

          <div className="relative z-10 pt-8 border-t border-white/10 text-[11px] text-emerald-200/60">
            Institutional IT &bull; Academic Technology Services &bull; Production Authentication
          </div>
        </div>

        {/* Right Column: Real Institutional Authentication (7 cols) */}
        <div className="lg:col-span-7 p-8 sm:p-12 flex flex-col justify-between bg-white">
          <div className="space-y-6 max-w-md w-full mx-auto">
            <div className="space-y-1 text-left">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-forest-50 border border-forest-100 text-forest-700 text-[11px] font-semibold mb-2">
                <Lock className="w-3 h-3" />
                University Single Sign-On
              </div>
              <h2 className="text-2xl font-bold text-charcoal-900 tracking-tight">Sign In</h2>
              <p className="text-xs text-charcoal-500">
                Authenticate with your university Google Workspace credentials. Your role is verified against the campus database.
              </p>
            </div>

            {errorMessage && (
              <div className="p-3 rounded-md bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-start gap-2 animate-in fade-in">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{errorMessage}</span>
              </div>
            )}

            {/* Google OAuth Action Button */}
            <div className="space-y-4 pt-2">
              <div ref={googleBtnContainerRef} className="flex justify-center" />

              {/* Native Button Fallback / Trigger */}
              <button
                type="button"
                onClick={handleGoogleClick}
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-3 px-4 py-2.5 rounded-md border border-warm-grey-300 bg-white hover:bg-app-bg text-charcoal-900 text-xs font-semibold shadow-subtle hover:border-warm-grey-400 transition-all focus:outline-none focus:ring-2 focus:ring-forest-600 disabled:opacity-60"
              >
                <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                  />
                </svg>
                <span>{isLoading ? 'Verifying with Database...' : 'Continue with Google'}</span>
              </button>

              <div className="text-[11px] text-charcoal-500 text-center space-y-1">
                <p>
                  Dispatches Google ID token to <code className="font-mono text-[10px] bg-app-soft px-1 py-0.5 rounded">POST /auth/google</code>.
                </p>
                <p className="text-[10px] text-charcoal-400">
                  Role permissions are authorized strictly from the backend database response.
                </p>
              </div>

              {/* Direct Token Verification Input for Backend Integration / Testing */}
              <div className="pt-4 border-t border-warm-grey-200">
                <button
                  type="button"
                  onClick={() => setShowManualInput(!showManualInput)}
                  className="w-full text-center text-[11px] text-forest-700 hover:text-forest-800 flex items-center justify-center gap-1 font-medium"
                >
                  <KeyRound className="w-3.5 h-3.5" />
                  <span>{showManualInput ? 'Hide Token Input' : 'Authenticate with Google ID Token'}</span>
                </button>

                {showManualInput && (
                  <form onSubmit={handleManualSubmit} className="mt-3 space-y-2">
                    <label className="block text-[11px] font-semibold text-charcoal-700">
                      Google ID Token (JWT)
                    </label>
                    <textarea
                      rows={3}
                      value={manualToken}
                      onChange={(e) => setManualToken(e.target.value)}
                      placeholder="Paste Google OAuth ID token..."
                      className="w-full text-xs font-mono p-2 rounded-md border border-warm-grey-300 text-charcoal-900 bg-white focus:outline-forest-600"
                    />
                    <Button
                      type="submit"
                      variant="primary"
                      size="sm"
                      className="w-full text-xs"
                      disabled={isLoading || !manualToken.trim()}
                    >
                      {isLoading ? 'Verifying...' : 'Submit Token to Backend'}
                    </Button>
                    <p className="text-[10px] text-charcoal-400 leading-tight">
                      Validates the token against <code className="font-mono">POST /auth/google</code> and verifies the user exists in the backend database.
                    </p>
                  </form>
                )}
              </div>
            </div>
          </div>

          <div className="pt-6 text-center text-[11px] text-charcoal-400 border-t border-warm-grey-100">
            For access or database provisioning, contact campus IT Operations at ext. 4357.
          </div>
        </div>
      </div>
    </div>
  )
}
