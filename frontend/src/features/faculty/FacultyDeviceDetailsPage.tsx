import React, { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { LoadingState } from '@/components/ui/LoadingState'
import { EmptyState } from '@/components/ui/EmptyState'
import { ErrorState } from '@/components/ui/ErrorState'
import { deviceService, classroomService } from '@/services'
import type { Device, Classroom } from '@/types'
import {
  Tv,
  Mic,
  Monitor,
  Radio,
  Bot,
  ArrowLeft,
  Calendar,
  Wifi,
  Tag,
  CheckCircle2,
  AlertTriangle,
  Building,
} from 'lucide-react'

export const FacultyDeviceDetailsPage: React.FC = () => {
  const { classroomId, deviceId } = useParams<{ classroomId: string; deviceId: string }>()
  const navigate = useNavigate()

  const [device, setDevice] = useState<Device | null>(null)
  const [classroom, setClassroom] = useState<Classroom | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = async () => {
    if (!deviceId) return
    try {
      setIsLoading(true)
      setError(null)

      const [dev, cls] = await Promise.all([
        deviceService.getDeviceById(deviceId),
        classroomId ? classroomService.getClassroomById(classroomId) : Promise.resolve(null),
      ])

      setDevice(dev)
      setClassroom(cls)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to connect to the server. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [deviceId, classroomId])

  if (isLoading) {
    return <LoadingState message="Loading device technical specifications..." />
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadData} />
  }

  if (!device) {
    return (
      <div className="space-y-4">
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate(classroomId ? `/faculty/classrooms/${classroomId}` : '/faculty/classrooms')}
        >
          <ArrowLeft className="w-3.5 h-3.5 mr-1.5" />
          Back to Equipment
        </Button>
        <EmptyState
          icon={<Tv className="w-8 h-8 text-charcoal-400" />}
          title="Device Not Found"
          description="The requested hardware device was not found in the database."
        />
      </div>
    )
  }

  const isOnline = device.status === 'ONLINE'
  const isWarning = device.status === 'WARNING'

  return (
    <div className="space-y-6">
      <PageHeader
        title={device.name}
        description={`Hardware specifications and diagnostic telemetry for ${device.brand} ${device.model}.`}
        breadcrumbs={[
          { label: 'Home', href: '#' },
          { label: 'Faculty', href: '/faculty' },
          { label: 'Classrooms', href: '/faculty/classrooms' },
          ...(classroom
            ? [{ label: classroom.roomNumber, href: `/faculty/classrooms/${classroom.id}` }]
            : []),
          { label: device.name },
        ]}
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate(classroomId ? `/faculty/classrooms/${classroomId}` : '/faculty/classrooms')}
          >
            <ArrowLeft className="w-3.5 h-3.5 mr-1.5" />
            Classroom Equipment
          </Button>
        }
      />

      {/* Main Spec Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-warm-grey-200 shadow-subtle bg-white">
            <CardHeader className="p-5 border-b border-warm-grey-200 bg-app-soft/30 flex items-center justify-between">
              <div>
                <CardTitle className="text-base font-bold">{device.name}</CardTitle>
                <p className="text-xs text-charcoal-500">
                  {device.brand} &bull; Model {device.model}
                </p>
              </div>
              <Badge variant={isOnline ? 'success' : isWarning ? 'warning' : 'danger'} size="md" dot>
                {device.status}
              </Badge>
            </CardHeader>

            <CardContent className="p-6 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div className="p-3 rounded-lg border border-warm-grey-200 bg-app-soft/20">
                  <div className="text-[11px] text-charcoal-500 font-medium">Device Brand & Model</div>
                  <div className="font-semibold text-charcoal-900 mt-0.5">
                    {device.brand} {device.model}
                  </div>
                </div>

                <div className="p-3 rounded-lg border border-warm-grey-200 bg-app-soft/20">
                  <div className="text-[11px] text-charcoal-500 font-medium">Serial Number</div>
                  <div className="font-mono font-semibold text-charcoal-900 mt-0.5">
                    {device.serialNumber}
                  </div>
                </div>

                <div className="p-3 rounded-lg border border-warm-grey-200 bg-app-soft/20">
                  <div className="text-[11px] text-charcoal-500 font-medium">Equipment Type</div>
                  <div className="font-semibold text-charcoal-900 mt-0.5 capitalize">
                    {device.type.replace('_', ' ')}
                  </div>
                </div>

                <div className="p-3 rounded-lg border border-warm-grey-200 bg-app-soft/20">
                  <div className="text-[11px] text-charcoal-500 font-medium">Assigned Classroom</div>
                  <div className="font-semibold text-charcoal-900 mt-0.5">
                    {classroom ? `${classroom.roomNumber} (${classroom.building})` : device.classroomName || 'Assigned Room'}
                  </div>
                </div>

                <div className="p-3 rounded-lg border border-warm-grey-200 bg-app-soft/20">
                  <div className="text-[11px] text-charcoal-500 font-medium">Network IP Address</div>
                  <div className="font-mono font-semibold text-charcoal-900 mt-0.5">
                    {device.ipAddress || 'Not Assigned (Static/Direct)'}
                  </div>
                </div>

                <div className="p-3 rounded-lg border border-warm-grey-200 bg-app-soft/20">
                  <div className="text-[11px] text-charcoal-500 font-medium">Installation Date</div>
                  <div className="font-semibold text-charcoal-900 mt-0.5">
                    {new Date(device.installedAt).toLocaleDateString()}
                  </div>
                </div>
              </div>

              {/* Troubleshooting Call to Action */}
              <div className="pt-4 border-t border-warm-grey-200">
                <Link
                  to={`/faculty/troubleshooting?classroomId=${classroomId || device.classroomId}&deviceId=${device.id}`}
                  className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-lg bg-forest-600 hover:bg-forest-700 text-white font-semibold text-xs shadow-subtle transition-all"
                >
                  <Bot className="w-4 h-4" />
                  <span>Start AI Troubleshooting for this Device</span>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Info Column */}
        <div className="space-y-4">
          <Card className="border-warm-grey-200 shadow-subtle bg-white">
            <CardHeader className="p-4 border-b border-warm-grey-200">
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-charcoal-600">
                Classroom Context
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-3 text-xs">
              {classroom ? (
                <>
                  <div className="flex justify-between text-charcoal-600">
                    <span>Room Number:</span>
                    <span className="font-bold text-charcoal-900">{classroom.roomNumber}</span>
                  </div>
                  <div className="flex justify-between text-charcoal-600">
                    <span>Building:</span>
                    <span className="text-charcoal-900">{classroom.building}</span>
                  </div>
                  <div className="flex justify-between text-charcoal-600">
                    <span>Floor:</span>
                    <span className="text-charcoal-900">Floor {classroom.floor}</span>
                  </div>
                  <div className="flex justify-between text-charcoal-600">
                    <span>Seating Capacity:</span>
                    <span className="text-charcoal-900">{classroom.capacity} seats</span>
                  </div>
                  <div className="pt-2 border-t border-warm-grey-200">
                    <Link
                      to={`/faculty/classrooms/${classroom.id}`}
                      className="text-xs text-forest-700 hover:text-forest-800 font-semibold flex items-center gap-1"
                    >
                      <span>View All Equipment in {classroom.roomNumber}</span>
                      <span>&rarr;</span>
                    </Link>
                  </div>
                </>
              ) : (
                <p className="text-charcoal-500">Classroom details unavailable.</p>
              )}
            </CardContent>
          </Card>

          <Card className="border-warm-grey-200 shadow-subtle bg-white">
            <CardHeader className="p-4 border-b border-warm-grey-200">
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-charcoal-600">
                Support & Escalation
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 text-xs text-charcoal-600 space-y-2">
              <p>
                Encountering an audio or video failure in this lecture hall? Launch the interactive troubleshooter or escalate to the campus dispatch team.
              </p>
              <div className="pt-2">
                <span className="font-semibold text-charcoal-800">Dispatch Hotline:</span>
                <span className="font-mono text-charcoal-900 ml-1">ext. 4357</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

