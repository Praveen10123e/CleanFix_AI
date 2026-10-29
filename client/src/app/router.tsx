import React from 'react'
import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { LoginPage } from '@/features/auth/LoginPage'
import { AccessDeniedPage } from '@/features/auth/AccessDeniedPage'
import { ProtectedRoute } from '@/features/auth/ProtectedRoute'

// Faculty Pages
import { FacultyDashboard } from '@/features/faculty/FacultyDashboard'
import { FacultyComplaintsPage } from '@/features/faculty/FacultyComplaintsPage'
import { FacultyClassroomsPage } from '@/features/faculty/FacultyClassroomsPage'
import { FacultyClassroomEquipmentPage } from '@/features/faculty/FacultyClassroomEquipmentPage'
import { FacultyDeviceDetailsPage } from '@/features/faculty/FacultyDeviceDetailsPage'

// Technician Pages
import { TechnicianDashboard } from '@/features/technician/TechnicianDashboard'
import { TechnicianEquipmentPage } from '@/features/technician/TechnicianEquipmentPage'
import { TechnicianManualsPage } from '@/features/technician/TechnicianManualsPage'

// Admin Pages
import { AdminDashboard } from '@/features/admin/AdminDashboard'
import { AdminUsersPage } from '@/features/admin/AdminUsersPage'
import { AdminClassroomsPage } from '@/features/admin/AdminClassroomsPage'
import { AdminReportsPage } from '@/features/admin/AdminReportsPage'

import { useAuth } from '@/features/auth/AuthContext'
import { Button } from '@/components/ui/Button'
import { AlertCircle } from 'lucide-react'

// Root redirect based on authenticated user's actual database role
const RootRedirect: React.FC = () => {
  const { currentUser, isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return null
  }

  if (!isAuthenticated || !currentUser) {
    return <Navigate to="/login" replace />
  }

  return <Navigate to={`/${currentUser.role}`} replace />
}

// 404 Not Found Page
const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-app-bg flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-white p-8 rounded-lg border border-warm-grey-200 shadow-card text-center space-y-4">
        <div className="w-12 h-12 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
          <AlertCircle className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-charcoal-900 tracking-tight">Page Not Found</h2>
          <p className="text-xs text-charcoal-500 mt-1">
            The requested operations route or classroom does not exist.
          </p>
        </div>
        <Button variant="primary" size="sm" onClick={() => (window.location.href = '/')}>
          Back to Campus Overview
        </Button>
      </div>
    </div>
  )
}

export const router = createBrowserRouter([
  // Public Routes
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/unauthorized',
    element: <AccessDeniedPage />,
  },
  {
    path: '/access-denied',
    element: <AccessDeniedPage />,
  },

  // Authenticated Application Shell
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <AppShell />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <RootRedirect />,
      },

      // Faculty Routes (Protected: Faculty Only)
      {
        path: 'faculty',
        element: (
          <ProtectedRoute allowedRoles={['faculty']}>
            <FacultyDashboard />
          </ProtectedRoute>
        ),
      },
      {
        path: 'faculty/troubleshooting',
        element: (
          <ProtectedRoute allowedRoles={['faculty']}>
            <FacultyDashboard />
          </ProtectedRoute>
        ),
      },
      {
        path: 'faculty/assistant',
        element: (
          <ProtectedRoute allowedRoles={['faculty']}>
            <FacultyDashboard />
          </ProtectedRoute>
        ),
      },
      {
        path: 'faculty/complaints',
        element: (
          <ProtectedRoute allowedRoles={['faculty']}>
            <FacultyComplaintsPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'faculty/classrooms',
        element: (
          <ProtectedRoute allowedRoles={['faculty']}>
            <FacultyClassroomsPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'faculty/classrooms/:classroomId',
        element: (
          <ProtectedRoute allowedRoles={['faculty']}>
            <FacultyClassroomEquipmentPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'faculty/classrooms/:classroomId/devices/:deviceId',
        element: (
          <ProtectedRoute allowedRoles={['faculty']}>
            <FacultyDeviceDetailsPage />
          </ProtectedRoute>
        ),
      },

      // Technician Routes (Protected: Technician Only)
      {
        path: 'technician',
        element: (
          <ProtectedRoute allowedRoles={['technician']}>
            <TechnicianDashboard />
          </ProtectedRoute>
        ),
      },
      {
        path: 'technician/complaints',
        element: (
          <ProtectedRoute allowedRoles={['technician']}>
            <TechnicianDashboard />
          </ProtectedRoute>
        ),
      },
      {
        path: 'technician/complaints/:id',
        element: (
          <ProtectedRoute allowedRoles={['technician']}>
            <TechnicianDashboard />
          </ProtectedRoute>
        ),
      },
      {
        path: 'technician/equipment',
        element: (
          <ProtectedRoute allowedRoles={['technician']}>
            <TechnicianEquipmentPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'technician/manuals',
        element: (
          <ProtectedRoute allowedRoles={['technician']}>
            <TechnicianManualsPage />
          </ProtectedRoute>
        ),
      },

      // Admin Routes (Protected: Admin Only)
      {
        path: 'admin',
        element: (
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminDashboard />
          </ProtectedRoute>
        ),
      },
      {
        path: 'admin/users',
        element: (
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminUsersPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'admin/classrooms',
        element: (
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminClassroomsPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'admin/devices',
        element: (
          <ProtectedRoute allowedRoles={['admin']}>
            <TechnicianEquipmentPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'admin/complaints',
        element: (
          <ProtectedRoute allowedRoles={['admin']}>
            <TechnicianDashboard />
          </ProtectedRoute>
        ),
      },
      {
        path: 'admin/reports',
        element: (
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminReportsPage />
          </ProtectedRoute>
        ),
      },
    ],
  },

  // 404 Catch-All
  {
    path: '*',
    element: <NotFoundPage />,
  },
])
