import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { LoadingState } from '@/components/ui/LoadingState'
import { EmptyState } from '@/components/ui/EmptyState'
import { ErrorState } from '@/components/ui/ErrorState'
import {
  classroomService,
  complaintService,
  troubleshootingService,
} from '@/services'
import type { Classroom, Device, Complaint, TroubleshootingSession } from '@/types'
import { useAuth } from '@/features/auth/AuthContext'
import { ClassroomDeviceSelector } from './ClassroomDeviceSelector'
import { InteractiveTroubleshooter } from './InteractiveTroubleshooter'
import {
  Sparkles,
  School,
  AlertCircle,
  Clock,
  CheckCircle2,
  Tv,
  Mic,
  Bot,
  RotateCcw,
  PlusCircle,
  HelpCircle,
} from 'lucide-react'

const ACTIVE_SESSION_STORAGE_KEY = 'classfix_active_faculty_session_id'

export const FacultyDashboard: React.FC = () => {
  const { currentUser } = useAuth()

  // Primary Data
  const [classrooms, setClassrooms] = useState<Classroom[]>([])
  const [complaints, setComplaints] = useState<Complaint[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Selection state
  const [selectedClassroomId, setSelectedClassroomId] = useState<string>('')
  const [devices, setDevices] = useState<Device[]>([])
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('')
  const [isLoadingDevices, setIsLoadingDevices] = useState(false)

  // Active Troubleshooting Session (Phase 2)
  const [activeSession, setActiveSession] = useState<TroubleshootingSession | null>(null)
  const [isRestoringSession, setIsRestoringSession] = useState(false)

  const [searchParams] = useSearchParams()
  const queryClassroomId = searchParams.get('classroomId')
  const queryDeviceId = searchParams.get('deviceId')

  // Load classrooms and complaints on mount
  const loadInitialData = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const [fetchedClassrooms, fetchedComplaints] = await Promise.all([
        classroomService.getClassrooms(),
        complaintService.getComplaints(),
      ])

      setClassrooms(fetchedClassrooms)
      setComplaints(fetchedComplaints)

      // Set classroom from URL query param or fallback to first room
      const targetRoomId = queryClassroomId || (fetchedClassrooms.length > 0 ? fetchedClassrooms[0].id : '')
      if (targetRoomId) {
        setSelectedClassroomId(targetRoomId)
        await loadDevicesForClassroom(targetRoomId)
        if (queryDeviceId) {
          setSelectedDeviceId(queryDeviceId)
        }
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to connect to campus classroom service.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  // Load devices when classroom changes
  const loadDevicesForClassroom = async (classroomId: string) => {
    setIsLoadingDevices(true)
    try {
      const clsDevices = await classroomService.getClassroomDevices(classroomId)
      setDevices(clsDevices)
      if (clsDevices.length > 0) {
        setSelectedDeviceId(clsDevices[0].id)
      } else {
        setSelectedDeviceId('')
      }
    } catch (err) {
      console.error('Error fetching classroom devices:', err)
      setDevices([])
      setSelectedDeviceId('')
    } finally {
      setIsLoadingDevices(false)
    }
  }

  // Check and restore active session if previously saved
  const checkStoredActiveSession = async () => {
    const storedSessionId = sessionStorage.getItem(ACTIVE_SESSION_STORAGE_KEY)
    if (!storedSessionId) return

    setIsRestoringSession(true)
    try {
      const session = await troubleshootingService.getSessionById(storedSessionId)
      if (session && session.status !== 'completed') {
        setActiveSession(session)
        setSelectedClassroomId(session.classroom_id)
        await loadDevicesForClassroom(session.classroom_id)
        setSelectedDeviceId(session.device_id)
      } else {
        sessionStorage.removeItem(ACTIVE_SESSION_STORAGE_KEY)
      }
    } catch {
      sessionStorage.removeItem(ACTIVE_SESSION_STORAGE_KEY)
    } finally {
      setIsRestoringSession(false)
    }
  }

  useEffect(() => {
    loadInitialData()
    checkStoredActiveSession()
  }, [queryClassroomId, queryDeviceId])

  // Handle classroom change
  const handleSelectClassroom = async (classroomId: string) => {
    setSelectedClassroomId(classroomId)
    await loadDevicesForClassroom(classroomId)
  }

  // Handle device change
  const handleSelectDevice = (deviceId: string) => {
    setSelectedDeviceId(deviceId)
  }

  // Session Started Callback
  const handleSessionStarted = (newSession: TroubleshootingSession) => {
    setActiveSession(newSession)
    sessionStorage.setItem(ACTIVE_SESSION_STORAGE_KEY, newSession.id)
  }

  // Reset Session
  const handleResetSession = () => {
    setActiveSession(null)
    sessionStorage.removeItem(ACTIVE_SESSION_STORAGE_KEY)
  }

  // Complaint created Callback
  const handleComplaintCreated = (newComplaint: Complaint) => {
    setComplaints((prev) => [newComplaint, ...prev.filter((c) => c.id !== newComplaint.id)])
    sessionStorage.removeItem(ACTIVE_SESSION_STORAGE_KEY)
  }

  const selectedDevice = devices.find((d) => d.id === selectedDeviceId)
  const myComplaints = complaints.filter(
    (c) =>
      c.reportedByUserId === currentUser?.id ||
      c.reportedByName?.toLowerCase().includes('vance') ||
      Boolean(c.troubleshootingSessionId)
  )

  if (isLoading || isRestoringSession) {
    return <LoadingState message="Connecting to Classroom AV Directory & Diagnostic Services..." />
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadInitialData} />
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Faculty AV Operations & AI Troubleshooting"
        description="Select classroom equipment, launch AI-guided diagnostics with technical manual citations, or dispatch field technicians."
        breadcrumbs={[{ label: 'Home', href: '#' }, { label: 'Faculty Assistant' }]}
        actions={
          activeSession ? (
            <Button
              size="sm"
              variant="outline"
              leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
              onClick={handleResetSession}
            >
              Start New Diagnostic
            </Button>
          ) : undefined
        }
      />

      {/* Top Telemetry Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-charcoal-400 uppercase tracking-wider">
                My Active Tickets
              </div>
              <div className="text-2xl font-bold text-charcoal-900 mt-1">
                {myComplaints.filter((c) => c.status !== 'RESOLVED').length}
              </div>
            </div>
            <div className="w-10 h-10 rounded-md bg-terracotta-50 text-terracotta-600 flex items-center justify-center">
              <AlertCircle className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-charcoal-400 uppercase tracking-wider">
                Active Classroom
              </div>
              <div className="text-xl font-bold text-charcoal-900 mt-1">
                {classrooms.find((c) => c.id === selectedClassroomId)?.roomNumber || 'None Selected'}
              </div>
              <div className="text-[11px] text-charcoal-500 mt-0.5">
                {devices.length} registered equipment units
              </div>
            </div>
            <div className="w-10 h-10 rounded-md bg-forest-50 text-forest-600 flex items-center justify-center">
              <School className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-charcoal-400 uppercase tracking-wider">
                Diagnostic Assistant
              </div>
              <div className="text-xs font-medium text-forest-700 mt-1 flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5" />
                {activeSession ? 'Session in progress' : 'Ready for device issue'}
              </div>
            </div>
            <div className="w-10 h-10 rounded-md bg-forest-50 text-forest-600 flex items-center justify-center">
              <Bot className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Interactive Workflow Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Classroom / Device Selector and Interactive Troubleshooter */}
        <div className="lg:col-span-2 space-y-6">
          {/* Equipment Selector (disabled when session is actively in progress) */}
          <Card className="border-warm-grey-300">
            <CardHeader>
              <CardTitle>Classroom & AV Hardware Selection</CardTitle>
              {activeSession && (
                <Badge variant="warning" size="sm">
                  Locked to Active Session
                </Badge>
              )}
            </CardHeader>
            <CardContent>
              <ClassroomDeviceSelector
                classrooms={classrooms}
                selectedClassroomId={selectedClassroomId}
                onSelectClassroom={handleSelectClassroom}
                devices={devices}
                selectedDeviceId={selectedDeviceId}
                onSelectDevice={handleSelectDevice}
                isLoadingDevices={isLoadingDevices}
                disabled={Boolean(activeSession)}
              />
            </CardContent>
          </Card>

          {/* Interactive Troubleshooter Panel (Phase 2 core) */}
          {selectedDevice ? (
            <InteractiveTroubleshooter
              key={selectedDevice.id + (activeSession?.id || 'new')}
              device={selectedDevice}
              initialSession={activeSession}
              onSessionStarted={handleSessionStarted}
              onComplaintCreated={handleComplaintCreated}
              onResetSession={handleResetSession}
            />
          ) : (
            <EmptyState
              title="Select an Equipment Unit"
              description="Choose a classroom and device above to launch diagnostic troubleshooting."
            />
          )}
        </div>

        {/* Right 1 Col: My Previous Incidents & Field Status */}
        <div className="space-y-4">
          <Card className="border-warm-grey-300">
            <CardHeader>
              <div>
                <CardTitle>My In-Lecture Incident Reports</CardTitle>
                <p className="text-xs text-charcoal-500 mt-0.5">
                  Live status of tickets escalated to field technicians.
                </p>
              </div>
              <Badge variant="forest" size="sm">
                Shared DB
              </Badge>
            </CardHeader>

            <CardContent className="p-0">
              {myComplaints.length === 0 ? (
                <EmptyState
                  title="No active incident tickets"
                  description="All equipment reported by you is currently functioning or resolved."
                />
              ) : (
                <div className="divide-y divide-warm-grey-200 max-h-[600px] overflow-y-auto">
                  {myComplaints.map((ticket) => {
                    const isPending = ticket.status === 'PENDING'
                    const isInProgress = ticket.status === 'IN_PROGRESS'
                    const isResolved = ticket.status === 'RESOLVED'

                    return (
                      <div key={ticket.id} className="p-4 hover:bg-ivory-50 transition-colors">
                        <div className="space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-xs font-bold text-forest-700">
                              {ticket.ticketNumber}
                            </span>
                            <Badge
                              variant={
                                isPending
                                  ? 'warning'
                                  : isInProgress
                                  ? 'info'
                                  : isResolved
                                  ? 'success'
                                  : 'danger'
                              }
                              size="sm"
                              dot
                            >
                              {ticket.status}
                            </Badge>
                          </div>

                          <div className="text-xs font-semibold text-charcoal-900">
                            {ticket.classroomName} &bull; {ticket.deviceName || 'Classroom AV'}
                          </div>

                          <p className="text-xs text-charcoal-600 line-clamp-2">
                            {ticket.title}
                          </p>

                          {ticket.aiSuggestedAction && (
                            <div className="mt-1.5 p-1.5 rounded bg-forest-50 border border-forest-100 text-[11px] text-forest-900">
                              <span className="font-semibold text-forest-800">Diagnostic context: </span>
                              {ticket.aiSuggestedAction}
                            </div>
                          )}

                          {ticket.resolutionNotes && (
                            <div className="mt-1.5 p-1.5 rounded bg-emerald-50 border border-emerald-100 text-[11px] text-emerald-900">
                              <span className="font-semibold text-emerald-800">Field Resolution: </span>
                              {ticket.resolutionNotes}
                            </div>
                          )}

                          <div className="flex items-center justify-between pt-1 text-[10px] text-charcoal-400">
                            <span>
                              Assigned: {ticket.assignedToName || 'Awaiting Dispatch'}
                            </span>
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {new Date(ticket.createdAt).toLocaleTimeString([], {
                                hour: '2-digit',
                                minute: '2-digit',
                              })}
                            </span>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
