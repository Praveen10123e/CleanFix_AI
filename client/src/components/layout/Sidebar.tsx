import React from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '@/features/auth/AuthContext'
import {
  LayoutDashboard,
  ListTodo,
  Radio,
  BookOpen,
  School,
  Bot,
  AlertCircle,
  Users,
  BarChart3,
  Monitor,
} from 'lucide-react'
import { cn } from '@/utils/cn'

interface SidebarProps {
  mobileOpen: boolean
  onCloseMobile: () => void
}

interface NavItem {
  name: string
  to: string
  icon: React.ReactNode
  badge?: string
}

export const Sidebar: React.FC<SidebarProps> = ({ mobileOpen, onCloseMobile }) => {
  const { currentUser } = useAuth()
  const role = currentUser?.role || 'faculty'

  const navByRole: Record<string, NavItem[]> = {
    technician: [
      { name: 'Overview', to: '/technician', icon: <LayoutDashboard className="w-4 h-4" /> },
      { name: 'Complaints', to: '/technician/complaints', icon: <ListTodo className="w-4 h-4" /> },
      { name: 'Classroom Equipment', to: '/technician/equipment', icon: <Radio className="w-4 h-4" /> },
      { name: 'Service Manuals', to: '/technician/manuals', icon: <BookOpen className="w-4 h-4" /> },
    ],
    faculty: [
      { name: 'Dashboard', to: '/faculty', icon: <LayoutDashboard className="w-4 h-4" /> },
      { name: 'AI Troubleshooting', to: '/faculty/troubleshooting', icon: <Bot className="w-4 h-4" />, badge: 'AI' },
      { name: 'My Complaints', to: '/faculty/complaints', icon: <AlertCircle className="w-4 h-4" /> },
      { name: 'Classrooms', to: '/faculty/classrooms', icon: <School className="w-4 h-4" /> },
    ],
    admin: [
      { name: 'Overview', to: '/admin', icon: <LayoutDashboard className="w-4 h-4" /> },
      { name: 'User Management', to: '/admin/users', icon: <Users className="w-4 h-4" /> },
      { name: 'Classroom Directory', to: '/admin/classrooms', icon: <School className="w-4 h-4" /> },
      { name: 'Device Inventory', to: '/admin/devices', icon: <Monitor className="w-4 h-4" /> },
      { name: 'Complaints', to: '/admin/complaints', icon: <ListTodo className="w-4 h-4" /> },
      { name: 'Reports & Analytics', to: '/admin/reports', icon: <BarChart3 className="w-4 h-4" /> },
    ],
  }

  const items = navByRole[role] || navByRole.faculty

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-charcoal-900/40 backdrop-blur-xs md:hidden"
          onClick={onCloseMobile}
        />
      )}

      {/* Sidebar Content */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-40 w-60 bg-white border-r border-warm-grey-200 transform transition-transform duration-200 ease-in-out md:translate-x-0 md:static md:z-10 flex flex-col justify-between pt-14 md:pt-0 shrink-0',
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="p-3.5 space-y-4">
          <div className="px-2.5 text-[10px] font-bold uppercase tracking-wider text-charcoal-400">
            {role.toUpperCase()} NAVIGATION
          </div>

          <nav className="space-y-1">
            {items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === `/${role}`}
                onClick={onCloseMobile}
                className={({ isActive }) =>
                  cn(
                    'flex items-center justify-between px-3 py-2 text-xs font-medium rounded-md transition-colors',
                    isActive
                      ? 'bg-forest-50 text-forest-700 font-semibold border-l-2 border-forest-600'
                      : 'text-charcoal-600 hover:text-charcoal-900 hover:bg-app-soft'
                  )
                }
              >
                <div className="flex items-center gap-2.5">
                  {item.icon}
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span className="text-[9px] px-1.5 py-0.2 font-bold uppercase rounded bg-forest-100 text-forest-800">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            ))}
          </nav>
        </div>

        {/* Sidebar Footer */}
        <div className="p-3 border-t border-warm-grey-200 text-[10px] text-charcoal-400 space-y-0.5">
          <div className="font-semibold text-charcoal-600">ClassFix AI Platform</div>
          <div>Authorized University AV</div>
        </div>
      </aside>
    </>
  )
}
