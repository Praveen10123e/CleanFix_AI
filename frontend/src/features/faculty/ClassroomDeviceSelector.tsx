import React from 'react'
import type { Classroom, Device } from '@/types'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { School, Tv, Mic, Monitor, Layers, Radio, CheckCircle2, AlertTriangle } from 'lucide-react'

interface ClassroomDeviceSelectorProps {
  classrooms: Classroom[]
  selectedClassroomId: string
  onSelectClassroom: (classroomId: string) => void
  devices: Device[]
  selectedDeviceId: string
  onSelectDevice: (deviceId: string) => void
  isLoadingDevices?: boolean
  disabled?: boolean
}

export const ClassroomDeviceSelector: React.FC<ClassroomDeviceSelectorProps> = ({
  classrooms,
  selectedClassroomId,
  onSelectClassroom,
  devices,
  selectedDeviceId,
  onSelectDevice,
  isLoadingDevices = false,
  disabled = false,
}) => {
  const selectedClassroom = classrooms.find((c) => c.id === selectedClassroomId)
  const selectedDevice = devices.find((d) => d.id === selectedDeviceId)

  const getDeviceIcon = (type: Device['type']) => {
    switch (type) {
      case 'PROJECTOR':
        return <Tv className="w-4 h-4 text-forest-700" />
      case 'MICROPHONE':
        return <Mic className="w-4 h-4 text-forest-700" />
      case 'SMART_BOARD':
        return <Monitor className="w-4 h-4 text-forest-700" />
      case 'HDMI_SWITCHER':
      case 'AUDIO_AMPLIFIER':
        return <Radio className="w-4 h-4 text-forest-700" />
      default:
        return <Layers className="w-4 h-4 text-forest-700" />
    }
  }

  const getDeviceStatusBadge = (status: Device['status']) => {
    switch (status) {
      case 'ONLINE':
        return <Badge variant="success" size="sm" dot>Online</Badge>
      case 'WARNING':
        return <Badge variant="warning" size="sm" dot>Warning</Badge>
      case 'OFFLINE':
        return <Badge variant="danger" size="sm" dot>Offline</Badge>
      case 'MAINTENANCE':
        return <Badge variant="neutral" size="sm">Maintenance</Badge>
      default:
        return <Badge variant="neutral" size="sm">{status}</Badge>
    }
  }

  return (
    <div className="space-y-4">
      {/* 1. Classroom Selection */}
      <div>
        <label className="block text-xs font-semibold text-charcoal-700 uppercase tracking-wider mb-2">
          1. Select Classroom Location *
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
          {classrooms.map((cls) => {
            const isSelected = cls.id === selectedClassroomId
            return (
              <button
                key={cls.id}
                type="button"
                disabled={disabled}
                onClick={() => onSelectClassroom(cls.id)}
                className={`text-left p-3 rounded-lg border transition-all ${
                  isSelected
                    ? 'border-forest-600 bg-forest-50/70 shadow-xs ring-2 ring-forest-600/20'
                    : 'border-warm-grey-300 bg-white hover:bg-ivory-100 hover:border-warm-grey-400'
                } ${disabled ? 'opacity-60 cursor-not-allowed' : ''}`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-sm text-charcoal-900">{cls.roomNumber}</span>
                  <Badge
                    variant={cls.status === 'OPERATIONAL' ? 'success' : cls.status === 'DEGRADED' ? 'warning' : 'danger'}
                    size="sm"
                  >
                    {cls.status === 'OPERATIONAL' ? 'Operational' : cls.status === 'DEGRADED' ? 'Degraded' : 'Offline'}
                  </Badge>
                </div>
                <div className="text-xs text-charcoal-500 line-clamp-1">{cls.building} &bull; Fl {cls.floor}</div>
                <div className="text-[11px] text-charcoal-400 mt-1">Cap: {cls.capacity} seats</div>
              </button>
            )
          })}
        </div>
      </div>

      {/* 2. Registered Devices Selection */}
      <div>
        <label className="block text-xs font-semibold text-charcoal-700 uppercase tracking-wider mb-2">
          2. Select Registered Classroom Device *
        </label>

        {isLoadingDevices ? (
          <div className="p-4 rounded-lg border border-dashed border-warm-grey-300 bg-ivory-100 text-center text-xs text-charcoal-500">
            Fetching registered devices for {selectedClassroom?.roomNumber}...
          </div>
        ) : devices.length === 0 ? (
          <div className="p-4 rounded-lg border border-dashed border-warm-grey-300 bg-ivory-100 text-center text-xs text-charcoal-500">
            No devices registered to {selectedClassroom?.roomNumber || 'this room'}.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
            {devices.map((dev) => {
              const isSelected = dev.id === selectedDeviceId
              return (
                <button
                  key={dev.id}
                  type="button"
                  disabled={disabled}
                  onClick={() => onSelectDevice(dev.id)}
                  className={`text-left p-3 rounded-lg border transition-all ${
                    isSelected
                      ? 'border-forest-600 bg-forest-50/70 shadow-xs ring-2 ring-forest-600/20'
                      : 'border-warm-grey-300 bg-white hover:bg-ivory-100 hover:border-warm-grey-400'
                  } ${disabled ? 'opacity-60 cursor-not-allowed' : ''}`}
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <div className="flex items-center gap-1.5 font-semibold text-xs text-charcoal-900 line-clamp-1">
                      {getDeviceIcon(dev.type)}
                      <span>{dev.name}</span>
                    </div>
                    {getDeviceStatusBadge(dev.status)}
                  </div>
                  <div className="text-[11px] text-charcoal-600">
                    <span className="font-semibold">{dev.brand}</span> &bull; {dev.model}
                  </div>
                  <div className="font-mono text-[10px] text-charcoal-400 mt-1">
                    S/N: {dev.serialNumber}
                  </div>
                </button>
              )
            })}
          </div>
        )}
      </div>

      {/* Selected Device Information Strip */}
      {selectedDevice && (
        <div className="p-3 bg-ivory-200/70 rounded-md border border-warm-grey-300 flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-charcoal-800">Selected Equipment:</span>
            <span className="font-bold text-forest-700">{selectedDevice.brand} {selectedDevice.model}</span>
            <span className="text-charcoal-500 font-mono text-[11px]">({selectedDevice.serialNumber})</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-charcoal-500 text-[11px]">Room: {selectedClassroom?.roomNumber}</span>
            {selectedDevice.ipAddress && (
              <span className="font-mono text-[11px] text-charcoal-500">IP: {selectedDevice.ipAddress}</span>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

