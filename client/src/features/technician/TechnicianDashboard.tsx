import React, { useState, useEffect } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { LoadingState } from '@/components/ui/LoadingState'
import { EmptyState } from '@/components/ui/EmptyState'
import { ErrorState } from '@/components/ui/ErrorState'
import { complaintService, deviceService } from '@/services'
import type { Complaint, Device, ComplaintStatus } from '@/types'
import { useAuth } from '@/features/auth/AuthContext'
import { ComplaintDetailDrawer } from './ComplaintDetailDrawer'
import {
  Wrench,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Radio,
  Search,
  ChevronRight,
  Filter,
  UserCheck,
} from 'lucide-react'

export const TechnicianDashboard: React.FC = () => {
  const { currentUser } = useAuth()
  const [complaints, setComplaints] = useState<Complaint[]>([])
  const [devices, setDevices] = useState<Device[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<'ALL' | ComplaintStatus>('ALL')
  const [onlyMyAssigned, setOnlyMyAssigned] = useState(false)

  // Selected ticket for slide-over drawer
  const [selectedComplaint, setSelectedComplaint] = useState<Complaint | null>(null)

  const loadData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const [allComplaints, allDevices] = await Promise.all([
        complaintService.getComplaints(),
        deviceService.getDevices(),
      ])
      setComplaints(allComplaints)
      setDevices(allDevices)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch technician incident data.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleComplaintUpdated = (updated: Complaint) => {
    setComplaints((prev) => prev.map((c) => (c.id === updated.id ? updated : c)))
    setSelectedComplaint(updated)
  }

  // Filter complaints
  const filteredComplaints = complaints.filter((c) => {
    if (statusFilter !== 'ALL' && c.status !== statusFilter) return false
    if (onlyMyAssigned && c.assignedToUserId !== currentUser?.id) return false
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      const matchTicket = c.ticketNumber.toLowerCase().includes(q)
      const matchRoom = c.classroomName.toLowerCase().includes(q)
      const matchTitle = c.title.toLowerCase().includes(q)
      const matchDevice = c.deviceName?.toLowerCase().includes(q)
      if (!matchTicket && !matchRoom && !matchTitle && !matchDevice) return false
    }
    return true
  })

  // Three compact summary metrics (max 3 per instructions)
  const openCount = complaints.filter(
    (c) => c.status === 'PENDING' || c.status === 'IN_PROGRESS' || c.status === 'ESCALATED'
  ).length
  const myAssignedCount = complaints.filter(
    (c) => c.assignedToUserId === currentUser?.id && c.status !== 'RESOLVED'
  ).length
  const hardwareAlertsCount = devices.filter(
    (d) => d.status === 'OFFLINE' || d.status === 'WARNING'
  ).length

  if (isLoading) {
    return <LoadingState message="Connecting to Campus AV Incident Queue & Telemetry..." />
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadData} />
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Technician Dashboard"
        description="Manage campus AV incidents and field repairs."
        breadcrumbs={[{ label: 'Home', href: '#' }, { label: 'Technician Console' }]}
      />

      {/* 1. Compact Row of 3 Useful Summary Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
        <Card className="border-warm-grey-200 shadow-subtle bg-white">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <div className="text-[11px] font-semibold text-charcoal-400 uppercase tracking-wider">
                Open Incidents
              </div>
              <div className="text-2xl font-bold text-charcoal-900 mt-0.5">{openCount}</div>
              <div className="text-[11px] text-terracotta-600 font-medium mt-0.5">
                {complaints.filter((c) => c.status === 'PENDING').length} unassigned tickets
              </div>
            </div>
            <div className="w-9 h-9 rounded-md bg-app-secondary text-forest-700 flex items-center justify-center">
              <Wrench className="w-4 h-4" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-warm-grey-200 shadow-subtle bg-white">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <div className="text-[11px] font-semibold text-charcoal-400 uppercase tracking-wider">
                Assigned to Me
              </div>
              <div className="text-2xl font-bold text-forest-700 mt-0.5">{myAssignedCount}</div>
              <div className="text-[11px] text-charcoal-500 mt-0.5">Active triage tasks</div>
            </div>
            <div className="w-9 h-9 rounded-md bg-forest-50 text-forest-600 flex items-center justify-center">
              <UserCheck className="w-4 h-4" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-warm-grey-200 shadow-subtle bg-white">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <div className="text-[11px] font-semibold text-charcoal-400 uppercase tracking-wider">
                Hardware Alerts
              </div>
              <div className="text-2xl font-bold text-amber-700 mt-0.5">{hardwareAlertsCount}</div>
              <div className="text-[11px] text-charcoal-500 mt-0.5">Units offline or degraded</div>
            </div>
            <div className="w-9 h-9 rounded-md bg-amber-50 text-amber-700 flex items-center justify-center">
              <Radio className="w-4 h-4" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 2. Primary Section: Large Complaint Queue */}
      <Card className="border-warm-grey-200 shadow-subtle bg-white">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-warm-grey-200 bg-app-soft/40">
          <div>
            <CardTitle>Field Incident Queue</CardTitle>
            <p className="text-xs text-charcoal-500 mt-0.5">
              Click any ticket to review hardware diagnostics, claim dispatch, or submit repair resolutions.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setOnlyMyAssigned(!onlyMyAssigned)}
              className={`px-2.5 py-1 text-xs rounded-md border font-medium transition-colors ${
                onlyMyAssigned
                  ? 'bg-forest-600 text-white border-forest-600'
                  : 'bg-white text-charcoal-700 border-warm-grey-300 hover:bg-app-soft'
              }`}
            >
              My Assigned Only
            </button>
          </div>
        </CardHeader>

        {/* Filter Controls Bar */}
        <div className="p-4 border-b border-warm-grey-200 bg-white flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          {/* Search Input */}
          <div className="relative flex-1 max-w-sm">
            <Search className="w-3.5 h-3.5 text-charcoal-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by ticket #, room, device, or title..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full text-xs pl-8 pr-3 py-1.5 rounded-md border border-warm-grey-300 text-charcoal-900 bg-white focus:outline-forest-600"
            />
          </div>

          {/* Status Tabs */}
          <div className="flex items-center bg-app-soft p-0.5 rounded-md text-xs border border-warm-grey-200 overflow-x-auto">
            {(['ALL', 'PENDING', 'IN_PROGRESS', 'RESOLVED', 'ESCALATED'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setStatusFilter(tab)}
                className={`px-3 py-1 rounded text-xs font-medium whitespace-nowrap transition-colors ${
                  statusFilter === tab
                    ? 'bg-white text-charcoal-900 shadow-subtle font-semibold'
                    : 'text-charcoal-600 hover:text-charcoal-900'
                }`}
              >
                {tab === 'ALL' ? 'All' : tab.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Complaint Rows */}
        <CardContent className="p-0">
          {filteredComplaints.length === 0 ? (
            <EmptyState
              title="No incidents found"
              description="No complaints match your current search query or filter criteria."
            />
          ) : (
            <div className="divide-y divide-warm-grey-200">
              {filteredComplaints.map((ticket) => {
                const isPending = ticket.status === 'PENDING'
                const isInProgress = ticket.status === 'IN_PROGRESS'
                const isResolved = ticket.status === 'RESOLVED'
                const isEscalated = ticket.status === 'ESCALATED'

                return (
                  <div
                    key={ticket.id}
                    onClick={() => setSelectedComplaint(ticket)}
                    className="p-4 sm:p-5 hover:bg-app-soft/50 transition-colors cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4 group"
                  >
                    {/* Left: Ticket ID, Severity, Title & Room/Device */}
                    <div className="space-y-1.5 flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs font-bold text-forest-700">
                          {ticket.ticketNumber}
                        </span>
                        <Badge
                          variant={
                            isResolved
                              ? 'success'
                              : isPending
                              ? 'warning'
                              : isInProgress
                              ? 'info'
                              : 'danger'
                          }
                          size="sm"
                          dot
                        >
                          {ticket.status}
                        </Badge>
                        <Badge
                          variant={
                            ticket.severity === 'CRITICAL'
                              ? 'danger'
                              : ticket.severity === 'HIGH'
                              ? 'warning'
                              : 'neutral'
                          }
                          size="sm"
                        >
                          {ticket.severity}
                        </Badge>
                        {ticket.troubleshootingSessionId && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-forest-50 text-forest-800 font-semibold border border-forest-200">
                            AI Diagnostic Attached
                          </span>
                        )}
                      </div>

                      <h4 className="text-xs sm:text-sm font-semibold text-charcoal-900 line-clamp-1 group-hover:text-forest-700 transition-colors">
                        {ticket.title}
                      </h4>

                      <div className="flex flex-wrap items-center gap-3 text-xs text-charcoal-500">
                        <span className="font-medium text-charcoal-800">{ticket.classroomName}</span>
                        {ticket.deviceName && (
                          <>
                            <span>&bull;</span>
                            <span className="truncate max-w-xs">{ticket.deviceName}</span>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Right: Time, Assignment, and Single Clear Primary Action */}
                    <div className="flex items-center justify-between md:justify-end gap-4 shrink-0 pt-2 md:pt-0 border-t md:border-t-0 border-warm-grey-100">
                      <div className="text-left md:text-right text-[11px] text-charcoal-500 space-y-0.5">
                        <div className="font-medium text-charcoal-800">
                          {ticket.assignedToName || (
                            <span className="text-terracotta-600 font-semibold">Unassigned</span>
                          )}
                        </div>
                        <div className="flex items-center gap-1 md:justify-end text-charcoal-400">
                          <Clock className="w-3 h-3" />
                          <span>{new Date(ticket.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                      </div>

                      {/* Single Primary Action Button */}
                      <Button
                        size="sm"
                        variant={isPending ? 'secondary' : isInProgress ? 'primary' : 'outline'}
                        onClick={(e) => {
                          e.stopPropagation()
                          setSelectedComplaint(ticket)
                        }}
                        rightIcon={<ChevronRight className="w-3.5 h-3.5" />}
                        className="shrink-0"
                      >
                        {isPending ? 'Triage' : isInProgress ? 'Inspect' : 'Details'}
                      </Button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 3. Secondary Section: Compact Hardware Alerts Panel */}
      <Card className="border-warm-grey-200 shadow-subtle bg-white">
        <CardHeader className="py-3 px-5 border-b border-warm-grey-200 bg-app-soft/40 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Radio className="w-4 h-4 text-amber-700" />
            <CardTitle className="text-sm font-bold text-charcoal-900">
              Classroom Equipment Status Alerts
            </CardTitle>
          </div>
          <span className="text-xs text-charcoal-500">
            {hardwareAlertsCount} units requiring attention
          </span>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y divide-warm-grey-200">
            {devices
              .filter((d) => d.status === 'OFFLINE' || d.status === 'WARNING')
              .map((dev) => (
                <div
                  key={dev.id}
                  className="px-5 py-3 flex items-center justify-between text-xs hover:bg-app-soft/40 transition-colors"
                >
                  <div className="space-y-0.5">
                    <div className="font-semibold text-charcoal-900 flex items-center gap-2">
                      <span>{dev.name}</span>
                      <span className="text-charcoal-400 font-normal">({dev.brand} {dev.model})</span>
                    </div>
                    <div className="text-[11px] text-charcoal-500">
                      Located in {dev.classroomName} &bull; S/N: {dev.serialNumber}
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <Badge variant={dev.status === 'WARNING' ? 'warning' : 'danger'} size="sm" dot>
                      {dev.status}
                    </Badge>
                  </div>
                </div>
              ))}
          </div>
        </CardContent>
      </Card>

      {/* Complaint Detail Drawer */}
      <ComplaintDetailDrawer
        complaint={selectedComplaint}
        onClose={() => setSelectedComplaint(null)}
        onComplaintUpdated={handleComplaintUpdated}
      />
    </div>
  )
}
