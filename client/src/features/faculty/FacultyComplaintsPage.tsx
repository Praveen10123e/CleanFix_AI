import React, { useState, useEffect } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { LoadingState } from '@/components/ui/LoadingState'
import { EmptyState } from '@/components/ui/EmptyState'
import { ErrorState } from '@/components/ui/ErrorState'
import { complaintService } from '@/services'
import type { Complaint } from '@/types'
import { useAuth } from '@/features/auth/AuthContext'
import { AlertCircle, Clock, CheckCircle2, UserCheck, Bot } from 'lucide-react'

export const FacultyComplaintsPage: React.FC = () => {
  const { currentUser } = useAuth()
  const [complaints, setComplaints] = useState<Complaint[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const all = await complaintService.getComplaints()
      setComplaints(all)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve complaint history.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  if (isLoading) {
    return <LoadingState message="Loading your reported classroom incidents..." />
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadData} />
  }

  const myComplaints = complaints.filter(
    (c) =>
      c.reportedByUserId === currentUser?.id ||
      c.reportedByName?.toLowerCase().includes('vance') ||
      Boolean(c.troubleshootingSessionId)
  )

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Reported Classroom Incidents"
        description="Monitor status, technician assignments, and fix records for your reported AV issues."
        breadcrumbs={[
          { label: 'Home', href: '#' },
          { label: 'Faculty', href: '/faculty' },
          { label: 'My Complaints' },
        ]}
      />

      <Card className="border-warm-grey-200 shadow-subtle bg-white">
        <CardHeader className="bg-app-soft/40 border-b border-warm-grey-200 flex items-center justify-between">
          <CardTitle>Reported Incidents</CardTitle>
          <span className="text-xs text-charcoal-500 font-medium">
            {myComplaints.length} tickets recorded
          </span>
        </CardHeader>
        <CardContent className="p-0">
          {myComplaints.length === 0 ? (
            <EmptyState
              title="No reported incidents"
              description="You have no active or historical AV tickets on record."
            />
          ) : (
            <div className="divide-y divide-warm-grey-200">
              {myComplaints.map((ticket) => (
                <div key={ticket.id} className="p-5 hover:bg-app-soft/30 transition-colors space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-forest-700">
                        {ticket.ticketNumber}
                      </span>
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
                    </div>

                    <div className="text-xs text-charcoal-400 flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{new Date(ticket.createdAt).toLocaleString()}</span>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-semibold text-charcoal-900">{ticket.title}</h4>
                    <p className="text-xs text-charcoal-600 mt-1 leading-relaxed bg-app-bg p-2.5 rounded border border-warm-grey-200">
                      {ticket.description}
                    </p>
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-charcoal-500 pt-1">
                    <div>
                      Location: <strong className="text-charcoal-800">{ticket.classroomName}</strong>
                      {ticket.deviceName && ` &bull; ${ticket.deviceName}`}
                    </div>
                    <div>
                      Assigned Field Support: <strong className="text-forest-700">{ticket.assignedToName || 'Awaiting Dispatch'}</strong>
                    </div>
                  </div>

                  {ticket.resolutionNotes && (
                    <div className="p-3 bg-emerald-50 border border-emerald-200 rounded text-xs text-emerald-900 space-y-1">
                      <div className="flex items-center gap-1 font-bold text-emerald-800">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Technician Resolution Confirmed
                      </div>
                      <p>{ticket.resolutionNotes}</p>
                      {ticket.resolvedAt && (
                        <div className="text-[10px] text-emerald-700">
                          Resolved: {new Date(ticket.resolvedAt).toLocaleString()}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

