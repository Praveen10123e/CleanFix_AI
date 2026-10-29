import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { LoadingState } from '@/components/ui/LoadingState'
import { ErrorState } from '@/components/ui/ErrorState'
import { adminService, classroomService, complaintService } from '@/services'
import type { AdminOverviewStats, Classroom, Complaint } from '@/types'
import {
  School,
  Monitor,
  AlertTriangle,
  Clock,
  Users,
  BarChart3,
  ListTodo,
  ArrowRight,
  RefreshCw,
  CheckCircle2,
} from 'lucide-react'

export const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<AdminOverviewStats | null>(null)
  const [classrooms, setClassrooms] = useState<Classroom[]>([])
  const [recentComplaints, setRecentComplaints] = useState<Complaint[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const [allStats, allClassrooms, allComplaints] = await Promise.all([
        adminService.getOverviewStats(),
        classroomService.getClassrooms(),
        complaintService.getComplaints(),
      ])
      setStats(allStats)
      setClassrooms(allClassrooms)
      setRecentComplaints(allComplaints.slice(0, 5))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch admin overview metrics.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  if (isLoading) {
    return <LoadingState message="Connecting to Campus AV Operations Telemetry..." />
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadData} />
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="AV Systems Administration"
        description="Campus classroom telemetry, equipment fleet matrix, and operations management."
        breadcrumbs={[{ label: 'Home', href: '#' }, { label: 'Admin Console' }]}
        actions={
          <Button
            size="sm"
            variant="outline"
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
            onClick={loadData}
          >
            Refresh Data
          </Button>
        }
      />

      {/* 4 Overview Telemetry Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        <Card className="border-warm-grey-200 shadow-subtle bg-white">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <div className="text-[11px] font-semibold text-charcoal-400 uppercase tracking-wider">
                Fleet Readiness
              </div>
              <div className="text-2xl font-bold text-forest-700 mt-1">
                {stats?.operationalClassrooms} / {stats?.totalClassrooms}
              </div>
              <div className="text-[11px] text-charcoal-500 mt-0.5">Rooms 100% Operational</div>
            </div>
            <div className="w-9 h-9 rounded-md bg-app-secondary text-forest-700 flex items-center justify-center">
              <School className="w-4 h-4" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-warm-grey-200 shadow-subtle bg-white">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <div className="text-[11px] font-semibold text-charcoal-400 uppercase tracking-wider">
                Active Incidents
              </div>
              <div className="text-2xl font-bold text-terracotta-700 mt-1">{stats?.activeTickets}</div>
              <div className="text-[11px] text-charcoal-500 mt-0.5">
                {stats?.criticalTickets} High / Critical
              </div>
            </div>
            <div className="w-9 h-9 rounded-md bg-terracotta-50 text-terracotta-600 flex items-center justify-center">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-warm-grey-200 shadow-subtle bg-white">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <div className="text-[11px] font-semibold text-charcoal-400 uppercase tracking-wider">
                Online Devices
              </div>
              <div className="text-2xl font-bold text-charcoal-900 mt-1">
                {stats?.onlineDevices} / {stats?.totalDevices}
              </div>
              <div className="text-[11px] text-emerald-700 mt-0.5 font-medium">
                Hardware Health: 99.4%
              </div>
            </div>
            <div className="w-9 h-9 rounded-md bg-app-soft text-forest-600 flex items-center justify-center">
              <Monitor className="w-4 h-4" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-warm-grey-200 shadow-subtle bg-white">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <div className="text-[11px] font-semibold text-charcoal-400 uppercase tracking-wider">
                Average Fix Time
              </div>
              <div className="text-2xl font-bold text-charcoal-900 mt-1">
                {stats?.avgResolutionTimeMinutes} min
              </div>
              <div className="text-[11px] text-charcoal-500 mt-0.5">Campus SLA Target: &lt;30m</div>
            </div>
            <div className="w-9 h-9 rounded-md bg-emerald-50 text-emerald-700 flex items-center justify-center">
              <Clock className="w-4 h-4" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Navigation Links */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <Link
          to="/admin/users"
          className="p-3.5 rounded-lg border border-warm-grey-200 bg-white hover:bg-app-soft/50 hover:border-forest-400 transition-all flex items-center justify-between group"
        >
          <div className="flex items-center gap-2.5">
            <Users className="w-4 h-4 text-forest-700" />
            <div>
              <div className="text-xs font-bold text-charcoal-900 group-hover:text-forest-700">User Management</div>
              <div className="text-[10px] text-charcoal-500">Manage roles & access</div>
            </div>
          </div>
          <ArrowRight className="w-3.5 h-3.5 text-charcoal-400 group-hover:text-forest-700" />
        </Link>

        <Link
          to="/admin/classrooms"
          className="p-3.5 rounded-lg border border-warm-grey-200 bg-white hover:bg-app-soft/50 hover:border-forest-400 transition-all flex items-center justify-between group"
        >
          <div className="flex items-center gap-2.5">
            <School className="w-4 h-4 text-forest-700" />
            <div>
              <div className="text-xs font-bold text-charcoal-900 group-hover:text-forest-700">Classrooms</div>
              <div className="text-[10px] text-charcoal-500">Directory & capacities</div>
            </div>
          </div>
          <ArrowRight className="w-3.5 h-3.5 text-charcoal-400 group-hover:text-forest-700" />
        </Link>

        <Link
          to="/admin/devices"
          className="p-3.5 rounded-lg border border-warm-grey-200 bg-white hover:bg-app-soft/50 hover:border-forest-400 transition-all flex items-center justify-between group"
        >
          <div className="flex items-center gap-2.5">
            <Monitor className="w-4 h-4 text-forest-700" />
            <div>
              <div className="text-xs font-bold text-charcoal-900 group-hover:text-forest-700">Device Inventory</div>
              <div className="text-[10px] text-charcoal-500">Hardware & telemetry</div>
            </div>
          </div>
          <ArrowRight className="w-3.5 h-3.5 text-charcoal-400 group-hover:text-forest-700" />
        </Link>

        <Link
          to="/admin/reports"
          className="p-3.5 rounded-lg border border-warm-grey-200 bg-white hover:bg-app-soft/50 hover:border-forest-400 transition-all flex items-center justify-between group"
        >
          <div className="flex items-center gap-2.5">
            <BarChart3 className="w-4 h-4 text-forest-700" />
            <div>
              <div className="text-xs font-bold text-charcoal-900 group-hover:text-forest-700">Reports & Analytics</div>
              <div className="text-[10px] text-charcoal-500">SLA & categories</div>
            </div>
          </div>
          <ArrowRight className="w-3.5 h-3.5 text-charcoal-400 group-hover:text-forest-700" />
        </Link>
      </div>

      {/* Main Grid: Recent Incidents and Classroom Fleet */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Recent Incidents */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="border-warm-grey-200 shadow-subtle bg-white">
            <CardHeader className="bg-app-soft/40 border-b border-warm-grey-200 flex items-center justify-between">
              <div>
                <CardTitle>Recent Incident Dispatches</CardTitle>
                <p className="text-xs text-charcoal-500 mt-0.5">Live campus ticket streams.</p>
              </div>
              <Link to="/admin/complaints">
                <Button size="sm" variant="ghost" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                  View All Complaints
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-warm-grey-200">
                {recentComplaints.map((ticket) => (
                  <div key={ticket.id} className="p-4 hover:bg-app-soft/30 transition-colors flex items-center justify-between gap-3 text-xs">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-forest-700">{ticket.ticketNumber}</span>
                        <span className="font-semibold text-charcoal-900">{ticket.classroomName}</span>
                        <Badge
                          variant={
                            ticket.status === 'RESOLVED'
                              ? 'success'
                              : ticket.status === 'PENDING'
                              ? 'warning'
                              : ticket.status === 'IN_PROGRESS'
                              ? 'info'
                              : 'danger'
                          }
                          size="sm"
                          dot
                        >
                          {ticket.status}
                        </Badge>
                      </div>
                      <p className="text-charcoal-600 line-clamp-1">{ticket.title}</p>
                    </div>

                    <div className="text-right text-[11px] text-charcoal-500 shrink-0">
                      <div>Assigned: {ticket.assignedToName || 'Unassigned'}</div>
                      <div className="text-charcoal-400">{new Date(ticket.createdAt).toLocaleTimeString()}</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right 1 Col: Classroom Status Fleet Matrix */}
        <div className="space-y-4">
          <Card className="border-warm-grey-200 shadow-subtle bg-white">
            <CardHeader className="bg-app-soft/40 border-b border-warm-grey-200 flex items-center justify-between">
              <CardTitle>Classroom Fleet Matrix</CardTitle>
              <Link to="/admin/classrooms" className="text-xs text-forest-700 hover:underline">
                Manage
              </Link>
            </CardHeader>
            <CardContent className="space-y-2.5 p-4">
              {classrooms.map((cls) => (
                <div key={cls.id} className="p-2.5 rounded border border-warm-grey-200 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-bold text-charcoal-900">{cls.roomNumber}</div>
                    <div className="text-[11px] text-charcoal-500">{cls.building} &bull; Cap: {cls.capacity}</div>
                  </div>
                  <Badge
                    variant={cls.status === 'OPERATIONAL' ? 'success' : cls.status === 'DEGRADED' ? 'warning' : 'danger'}
                    size="sm"
                    dot
                  >
                    {cls.status}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
