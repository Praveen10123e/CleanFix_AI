import React, { useState, useEffect } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { LoadingState } from '@/components/ui/LoadingState'
import { EmptyState } from '@/components/ui/EmptyState'
import { ErrorState } from '@/components/ui/ErrorState'
import { adminService } from '@/services'
import type { User, UserRole, CreateUserDTO } from '@/types'
import { Users, Plus, UserCheck } from 'lucide-react'

export const AdminUsersPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Add User Modal State
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<UserRole>('faculty')
  const [department, setDepartment] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const loadData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const all = await adminService.getUsers()
      setUsers(all)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve staff directory.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || !email.trim()) return

    setIsSubmitting(true)
    try {
      const dto: CreateUserDTO = {
        name: name.trim(),
        email: email.trim(),
        role,
        department: department.trim() || undefined,
      }
      await adminService.createUser(dto)
      setIsModalOpen(false)
      setName('')
      setEmail('')
      setDepartment('')
    } catch (err) {
      alert('Failed to create user: ' + (err instanceof Error ? err.message : 'Unknown'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleRoleChange = async (userId: string, newRole: UserRole) => {
    try {
      await adminService.updateUserRole(userId, newRole)
    } catch (err) {
      alert('Failed to update role: ' + (err instanceof Error ? err.message : 'Unknown'))
    }
  }

  if (isLoading) {
    return <LoadingState message="Connecting to Campus User Directory..." />
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadData} />
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="User & Role Management"
        description="Review campus personnel, assign operational permissions, and register new AV staff."
        breadcrumbs={[
          { label: 'Home', href: '#' },
          { label: 'Admin', href: '/admin' },
          { label: 'Users' },
        ]}
        actions={
          <Button
            size="sm"
            variant="primary"
            leftIcon={<Plus className="w-3.5 h-3.5" />}
            onClick={() => setIsModalOpen(true)}
          >
            Add Campus User
          </Button>
        }
      />

      <Card className="border-warm-grey-200 shadow-subtle bg-white">
        <CardHeader className="bg-app-soft/40 border-b border-warm-grey-200 flex items-center justify-between">
          <CardTitle>Registered Personnel</CardTitle>
          <span className="text-xs text-charcoal-500 font-medium">{users.length} accounts</span>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-app-soft text-charcoal-600 border-b border-warm-grey-200">
                <tr>
                  <th className="py-2.5 px-4 font-semibold">User Name & Email</th>
                  <th className="py-2.5 px-3 font-semibold">Department</th>
                  <th className="py-2.5 px-3 font-semibold">Current Role</th>
                  <th className="py-2.5 px-4 text-right font-semibold">Assign Role</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-warm-grey-200">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-app-soft/30 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-bold text-charcoal-900">{u.name}</div>
                      <div className="text-[11px] text-charcoal-500">{u.email}</div>
                    </td>
                    <td className="py-3 px-3 text-charcoal-700">{u.department || 'General Academic'}</td>
                    <td className="py-3 px-3">
                      <Badge
                        variant={
                          u.role === 'admin'
                            ? 'info'
                            : u.role === 'technician'
                            ? 'terracotta'
                            : 'forest'
                        }
                        size="sm"
                        className="capitalize"
                      >
                        {u.role}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <select
                        value={u.role}
                        onChange={(e) => handleRoleChange(u.id, e.target.value as UserRole)}
                        className="text-xs p-1 rounded border border-warm-grey-300 text-charcoal-900 bg-white"
                      >
                        <option value="faculty">Faculty</option>
                        <option value="technician">Technician</option>
                        <option value="admin">Admin</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Add User Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-charcoal-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-lg shadow-elevated border border-warm-grey-300 max-w-md w-full p-6 animate-in zoom-in-95">
            <h3 className="font-bold text-base text-charcoal-900 mb-3">Add Campus Personnel</h3>
            <form onSubmit={handleCreateUser} className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">
                  Full Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Dr. Arthur Pendelton"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full text-xs p-2 rounded border border-warm-grey-300 text-charcoal-900"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">
                  Email Address *
                </label>
                <input
                  type="email"
                  required
                  placeholder="e.g. arthur.p@university.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full text-xs p-2 rounded border border-warm-grey-300 text-charcoal-900"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">
                    Role *
                  </label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value as UserRole)}
                    className="w-full text-xs p-2 rounded border border-warm-grey-300 text-charcoal-900 bg-white"
                  >
                    <option value="faculty">Faculty</option>
                    <option value="technician">Technician</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">
                    Department
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Electrical Eng"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="w-full text-xs p-2 rounded border border-warm-grey-300 text-charcoal-900"
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-warm-grey-200 flex justify-end gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  isLoading={isSubmitting}
                >
                  Create Account
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

