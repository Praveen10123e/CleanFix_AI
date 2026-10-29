import React, { useState, useRef, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/features/auth/AuthContext'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import {
  MonitorSpeaker,
  Menu,
  X,
  ChevronDown,
  LogOut,
} from 'lucide-react'

interface HeaderProps {
  mobileMenuOpen: boolean
  onToggleMobileMenu: () => void
}

export const Header: React.FC<HeaderProps> = ({ mobileMenuOpen, onToggleMobileMenu }) => {
  const { currentUser, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown on outside click
  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleOutsideClick)
    return () => document.removeEventListener('mousedown', handleOutsideClick)
  }, [])

  const getSectionTitle = () => {
    const path = location.pathname
    if (path.startsWith('/technician/complaints')) return 'Incident Queue'
    if (path.startsWith('/technician/equipment')) return 'Hardware Inventory'
    if (path.startsWith('/technician/manuals')) return 'Service Manuals'
    if (path.startsWith('/technician')) return 'Field Operations Console'

    if (path.startsWith('/faculty/troubleshooting')) return 'AI Troubleshooting'
    if (path.startsWith('/faculty/complaints')) return 'My Incident Reports'
    if (path.startsWith('/faculty/classrooms')) return 'Campus Classrooms'
    if (path.startsWith('/faculty')) return 'Faculty Portal'

    if (path.startsWith('/admin/users')) return 'User & Role Access'
    if (path.startsWith('/admin/classrooms')) return 'Classroom Directory'
    if (path.startsWith('/admin/devices')) return 'Device Telemetry'
    if (path.startsWith('/admin/reports')) return 'Operations Analytics'
    if (path.startsWith('/admin/complaints')) return 'All Campus Incidents'
    if (path.startsWith('/admin')) return 'Systems Administration'

    return 'Operations'
  }

  const roleBadgeVariants: Record<string, 'forest' | 'terracotta' | 'info'> = {
    faculty: 'forest',
    technician: 'terracotta',
    admin: 'info',
  }

  const roleVariant = currentUser ? roleBadgeVariants[currentUser.role] || 'forest' : 'neutral'

  const userInitials = currentUser?.name
    ? currentUser.name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .slice(0, 2)
        .toUpperCase()
    : 'U'

  const handleSignOut = async () => {
    setDropdownOpen(false)
    await logout()
    navigate('/login')
  }

  return (
    <header className="bg-white border-b border-warm-grey-200 sticky top-0 z-30 shadow-subtle">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
        {/* Left: Brand, Mobile Toggle, and Section Title */}
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleMobileMenu}
            className="md:hidden p-1.5 rounded text-charcoal-600 hover:text-charcoal-900 hover:bg-app-soft"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          <Link
            to={currentUser ? `/${currentUser.role}` : '/login'}
            className="flex items-center gap-2"
          >
            <div className="w-8 h-8 rounded-md bg-forest-600 text-white flex items-center justify-center shadow-subtle">
              <MonitorSpeaker className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-1 leading-none">
                <span className="font-bold text-sm text-charcoal-900 tracking-tight">ClassFix</span>
                <span className="font-bold text-sm text-forest-600">AI</span>
              </div>
            </div>
          </Link>

          <div className="hidden sm:flex items-center gap-2 pl-3 ml-3 border-l border-warm-grey-200">
            <span className="text-xs font-semibold text-charcoal-700">{getSectionTitle()}</span>
          </div>
        </div>

        {/* Right: Authenticated User Menu */}
        <div className="flex items-center gap-3" ref={dropdownRef}>
          {currentUser ? (
            <div className="relative">
              <button
                type="button"
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-2.5 p-1 rounded-lg hover:bg-app-soft transition-colors focus:outline-none"
              >
                <div className="w-8 h-8 rounded-full bg-forest-100 text-forest-800 border border-forest-300 font-semibold text-xs flex items-center justify-center">
                  {userInitials}
                </div>
                <div className="hidden md:flex flex-col text-left">
                  <span className="text-xs font-semibold text-charcoal-900 leading-tight">
                    {currentUser.name}
                  </span>
                  <span className="text-[10px] text-charcoal-500 capitalize leading-tight">
                    {currentUser.role}
                  </span>
                </div>
                <Badge variant={roleVariant} size="sm" className="hidden sm:inline-flex capitalize">
                  {currentUser.role}
                </Badge>
                <ChevronDown className="w-3.5 h-3.5 text-charcoal-400" />
              </button>

              {/* Dropdown Menu */}
              {dropdownOpen && (
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-elevated border border-warm-grey-200 py-2 z-50 animate-in fade-in zoom-in-95">
                  <div className="px-4 py-2 border-b border-warm-grey-200">
                    <p className="text-xs font-bold text-charcoal-900">{currentUser.name}</p>
                    <p className="text-[11px] text-charcoal-500 truncate">{currentUser.email}</p>
                    <div className="flex items-center gap-1.5 mt-1.5">
                      <Badge variant={roleVariant} size="sm" className="capitalize">
                        {currentUser.role}
                      </Badge>
                      {currentUser.department && (
                        <span className="text-[10px] text-charcoal-400 truncate">
                          {currentUser.department}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="pt-1">
                    <button
                      type="button"
                      onClick={handleSignOut}
                      className="w-full flex items-center gap-2 px-4 py-2 text-xs text-rose-700 hover:bg-rose-50 transition-colors"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <Link to="/login">
              <Button size="sm" variant="primary">
                Sign In
              </Button>
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}
