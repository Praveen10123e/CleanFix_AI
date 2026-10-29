import React, { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { LoadingState } from '@/components/ui/LoadingState'
import { EmptyState } from '@/components/ui/EmptyState'
import { ErrorState } from '@/components/ui/ErrorState'
import { classroomService } from '@/services'
import type { Classroom, Device } from '@/types'
import {
  School,
  Tv,
  Mic,
  Monitor,
  Radio,
  ArrowRight,
  Bot,
  Info,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react'

export const FacultyClassroomEquipmentPage: React.FC = () => {
  const { classroomId } = useParams<{ classroomId: string }>()
  const navigate = useNavigate()

  const [classroom, setClassroom] = useState<Classroom | null>(null)
  const [devices, setDevices] = useState<Device[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = async () => {
    if (!classroomId) return
    try {
      setIsLoading(true)
      setError(null)

      const [cls, devs] = await Promise.all([
        classroomService.getClassroomById(classroomId),
        classroomService.getClassroomDevices(classroomId),
      ])

      setClassroom(cls)
      setDevices(devs)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to connect to the server. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [classroomId])

  if (isLoading) {
    return <LoadingState message="Loading classroom equipment inventory..." />
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadData} />
  }

  if (!classroom) {
    return (
      <div className="space-y-4">
        <Button variant="outline" size="sm" onClick={() => navigate('/faculty/classrooms')}>
          <ArrowLeft className="w-3.5 h-3.5 mr-1.5" />
          Back to Classrooms
        </Button>
        <EmptyState
          icon={<School className="w-8 h-8 text-charcoal-400" />}
          title="Classroom not found"
          description="The requested classroom ID was not found in the campus database."
        />
      </div>
    )
  }

  const getDeviceIcon = (type: string) => {
    switch (type) {
      case 'PROJECTOR':
        return <Tv className="w-4 h-4 text-forest-600" />
      case 'MICROPHONE':
        return <Mic className="w-4 h-4 text-emerald-600" />
      case 'AUDIO_AMPLIFIER':
        return <Radio className="w-4 h-4 text-blue-600" />
      default:
        return <Monitor className="w-4 h-4 text-charcoal-600" />
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={`${classroom.roomNumber} Equipment Inventory`}
        description={`Registered AV hardware in ${classroom.building}, Floor ${classroom.floor}. Capacity: ${classroom.capacity} seats.`}
        breadcrumbs={[
          { label: 'Home', href: '#' },
          { label: 'Faculty', href: '/faculty' },
          { label: 'Classrooms', href: '/faculty/classrooms' },
          { label: classroom.roomNumber },
        ]}
        actions={
          <Button variant="outline" size="sm" onClick={() => navigate('/faculty/classrooms')}>
            <ArrowLeft className="w-3.5 h-3.5 mr-1.5" />
            Classroom Directory
          </Button>
        }
      />

      {/* Classroom Status Summary Bar */}
      <div className="bg-white p-4 rounded-lg border border-warm-grey-200 flex flex-wrap items-center justify-between gap-4 shadow-subtle">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-md bg-forest-50 border border-forest-100 flex items-center justify-center text-forest-700">
            <School className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm text-charcoal-900">{classroom.roomNumber}</span>
              <span className="text-xs text-charcoal-500">&bull; {classroom.building}</span>
              <Badge
                variant={classroom.status === 'OPERATIONAL' ? 'success' : classroom.status === 'DEGRADED' ? 'warning' : 'danger'}
                size="sm"
                dot
              >
                {classroom.status}
              </Badge>
            </div>
            <div className="text-[11px] text-charcoal-500 mt-0.5">
              {devices.length} registered hardware component{devices.length === 1 ? '' : 's'} &bull; {classroom.activeTicketsCount} active ticket{classroom.activeTicketsCount === 1 ? '' : 's'}
            </div>
          </div>
        </div>

        <Link
          to={`/faculty/troubleshooting?classroomId=${classroom.id}`}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-forest-600 hover:bg-forest-700 text-white font-semibold text-xs transition-colors shadow-subtle"
        >
          <Bot className="w-3.5 h-3.5" />
          <span>Troubleshoot This Room</span>
        </Link>
      </div>

      {/* Equipment List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-charcoal-900">Installed Equipment</h3>
          <span className="text-xs text-charcoal-500">{devices.length} devices available</span>
        </div>

        {devices.length === 0 ? (
          <EmptyState
            icon={<Tv className="w-8 h-8 text-charcoal-400" />}
            title="No equipment is registered in this classroom yet."
            description="Contact campus IT AV operations to register hardware components for this classroom."
            actionLabel="Refresh Inventory"
            onAction={loadData}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {devices.map((device) => {
              const isOnline = device.status === 'ONLINE'
              const isWarning = device.status === 'WARNING'

              return (
                <Card key={device.id} className="border-warm-grey-200 shadow-subtle bg-white hover:border-forest-400 transition-all">
                  <CardHeader className="p-4 border-b border-warm-grey-200 bg-app-soft/30 flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 rounded-md bg-white border border-warm-grey-200 shadow-subtle">
                        {getDeviceIcon(device.type)}
                      </div>
                      <div>
                        <CardTitle className="text-sm font-bold leading-tight">{device.name}</CardTitle>
                        <p className="text-[11px] text-charcoal-500">{device.brand} &bull; {device.model}</p>
                      </div>
                    </div>
                    <Badge variant={isOnline ? 'success' : isWarning ? 'warning' : 'danger'} size="sm" dot>
                      {device.status}
                    </Badge>
                  </CardHeader>

                  <CardContent className="p-4 space-y-3 text-xs">
                    <div className="flex justify-between text-charcoal-600">
                      <span>Serial Number:</span>
                      <span className="font-mono text-charcoal-900">{device.serialNumber}</span>
                    </div>

                    {device.ipAddress && (
                      <div className="flex justify-between text-charcoal-600">
                        <span>IP Address:</span>
                        <span className="font-mono text-charcoal-900">{device.ipAddress}</span>
                      </div>
                    )}

                    <div className="flex justify-between text-charcoal-600">
                      <span>Type:</span>
                      <span className="text-charcoal-900 capitalize">{device.type.replace('_', ' ')}</span>
                    </div>

                    <div className="pt-3 border-t border-warm-grey-200 grid grid-cols-2 gap-2">
                      <Link
                        to={`/faculty/classrooms/${classroom.id}/devices/${device.id}`}
                        className="flex items-center justify-center gap-1.5 px-2.5 py-1.5 rounded border border-warm-grey-300 hover:bg-app-soft text-charcoal-800 font-medium text-xs transition-colors"
                      >
                        <Info className="w-3.5 h-3.5 text-charcoal-500" />
                        <span>View Details</span>
                      </Link>

                      <Link
                        to={`/faculty/troubleshooting?classroomId=${classroom.id}&deviceId=${device.id}`}
                        className="flex items-center justify-center gap-1.5 px-2.5 py-1.5 rounded bg-forest-50 hover:bg-forest-100 text-forest-700 font-semibold text-xs transition-colors"
                      >
                        <Bot className="w-3.5 h-3.5 text-forest-600" />
                        <span>Troubleshoot</span>
                      </Link>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

