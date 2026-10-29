import React, { useState, useEffect } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { LoadingState } from '@/components/ui/LoadingState'
import { EmptyState } from '@/components/ui/EmptyState'
import { ErrorState } from '@/components/ui/ErrorState'
import { deviceService, classroomService } from '@/services'
import type { Device, Classroom, DeviceStatus, CreateDeviceDTO, DeviceType } from '@/types'
import { Radio, Plus, Search, Tv, Mic, Monitor, Layers, CheckCircle2 } from 'lucide-react'

export const TechnicianEquipmentPage: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([])
  const [classrooms, setClassrooms] = useState<Classroom[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState<string>('ALL')

  // Register Device Modal State
  const [isRegisterModalOpen, setIsRegisterModalOpen] = useState(false)
  const [deviceName, setDeviceName] = useState('')
  const [deviceBrand, setDeviceBrand] = useState('')
  const [deviceModel, setDeviceModel] = useState('')
  const [deviceType, setDeviceType] = useState<DeviceType>('PROJECTOR')
  const [classroomId, setClassroomId] = useState('')
  const [serialNumber, setSerialNumber] = useState('')
  const [ipAddress, setIpAddress] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const loadData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const [allDevices, allClassrooms] = await Promise.all([
        deviceService.getDevices(),
        classroomService.getClassrooms(),
      ])
      setDevices(allDevices)
      setClassrooms(allClassrooms)
      if (allClassrooms.length > 0 && !classroomId) {
        setClassroomId(allClassrooms[0].id)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load device inventory.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleCreateDevice = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!deviceName.trim() || !serialNumber.trim() || !classroomId) return

    setIsSubmitting(true)
    try {
      const dto: CreateDeviceDTO = {
        name: deviceName.trim(),
        brand: deviceBrand.trim() || 'Generic',
        model: deviceModel.trim() || 'Standard',
        type: deviceType,
        classroomId,
        serialNumber: serialNumber.trim(),
        ipAddress: ipAddress.trim() || undefined,
        status: 'ONLINE',
      }
      await deviceService.createDevice(dto)
      setIsRegisterModalOpen(false)
      setDeviceName('')
      setDeviceBrand('')
      setDeviceModel('')
      setSerialNumber('')
      setIpAddress('')
    } catch (err) {
      alert('Error registering device: ' + (err instanceof Error ? err.message : 'Unknown'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleUpdateStatus = async (id: string, newStatus: DeviceStatus) => {
    try {
      await deviceService.updateDeviceStatus(id, newStatus)
    } catch (err) {
      alert('Failed to update status: ' + (err instanceof Error ? err.message : 'Unknown'))
    }
  }

  const filteredDevices = devices.filter((d) => {
    if (typeFilter !== 'ALL' && d.type !== typeFilter) return false
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      return (
        d.name.toLowerCase().includes(q) ||
        d.brand.toLowerCase().includes(q) ||
        d.model.toLowerCase().includes(q) ||
        d.serialNumber.toLowerCase().includes(q) ||
        d.classroomName.toLowerCase().includes(q)
      )
    }
    return true
  })

  if (isLoading) {
    return <LoadingState message="Connecting to Classroom AV Device Registry..." />
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadData} />
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Classroom Equipment Inventory"
        description="Register, inspect, and manage campus AV projectors, microphones, and touch displays."
        breadcrumbs={[
          { label: 'Home', href: '#' },
          { label: 'Technician', href: '/technician' },
          { label: 'Equipment Inventory' },
        ]}
        actions={
          <Button
            size="sm"
            variant="primary"
            leftIcon={<Plus className="w-3.5 h-3.5" />}
            onClick={() => setIsRegisterModalOpen(true)}
          >
            Register AV Device
          </Button>
        }
      />

      <Card className="border-warm-grey-200 shadow-subtle bg-white">
        {/* Filters */}
        <div className="p-4 border-b border-warm-grey-200 flex flex-col sm:flex-row items-center justify-between gap-3 bg-app-soft/30">
          <div className="relative w-full sm:max-w-xs">
            <Search className="w-3.5 h-3.5 text-charcoal-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by device, brand, S/N, room..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full text-xs pl-8 pr-3 py-1.5 rounded-md border border-warm-grey-300 text-charcoal-900 bg-white focus:outline-forest-600"
            />
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto">
            {['ALL', 'PROJECTOR', 'MICROPHONE', 'SMART_BOARD', 'HDMI_SWITCHER'].map((type) => (
              <button
                key={type}
                onClick={() => setTypeFilter(type)}
                className={`px-2.5 py-1 text-xs rounded-md font-medium whitespace-nowrap transition-colors ${
                  typeFilter === type
                    ? 'bg-forest-600 text-white font-semibold'
                    : 'bg-white text-charcoal-700 border border-warm-grey-300 hover:bg-app-soft'
                }`}
              >
                {type.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Device Table */}
        <CardContent className="p-0">
          {filteredDevices.length === 0 ? (
            <EmptyState
              title="No devices found"
              description="No registered equipment matching your filter criteria."
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-app-soft text-charcoal-600 border-b border-warm-grey-200">
                  <tr>
                    <th className="py-2.5 px-4 font-semibold">Equipment Name & Model</th>
                    <th className="py-2.5 px-3 font-semibold">Classroom</th>
                    <th className="py-2.5 px-3 font-semibold">Hardware Type</th>
                    <th className="py-2.5 px-3 font-semibold">Serial Number</th>
                    <th className="py-2.5 px-3 font-semibold">Status</th>
                    <th className="py-2.5 px-4 text-right font-semibold">Manage Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-warm-grey-200">
                  {filteredDevices.map((dev) => (
                    <tr key={dev.id} className="hover:bg-app-soft/40 transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-semibold text-charcoal-900">{dev.name}</div>
                        <div className="text-[11px] text-charcoal-500">
                          {dev.brand} {dev.model}
                        </div>
                      </td>
                      <td className="py-3 px-3 font-medium text-charcoal-800">{dev.classroomName}</td>
                      <td className="py-3 px-3">
                        <Badge variant="neutral" size="sm">
                          {dev.type}
                        </Badge>
                      </td>
                      <td className="py-3 px-3 font-mono text-[11px] text-charcoal-600">
                        {dev.serialNumber}
                      </td>
                      <td className="py-3 px-3">
                        <Badge
                          variant={
                            dev.status === 'ONLINE'
                              ? 'success'
                              : dev.status === 'WARNING'
                              ? 'warning'
                              : 'danger'
                          }
                          size="sm"
                          dot
                        >
                          {dev.status}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <select
                          value={dev.status}
                          onChange={(e) => handleUpdateStatus(dev.id, e.target.value as DeviceStatus)}
                          className="text-xs p-1 rounded border border-warm-grey-300 text-charcoal-900 bg-white"
                        >
                          <option value="ONLINE">ONLINE</option>
                          <option value="WARNING">WARNING</option>
                          <option value="OFFLINE">OFFLINE</option>
                          <option value="MAINTENANCE">MAINTENANCE</option>
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Register Modal */}
      {isRegisterModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-charcoal-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-lg shadow-elevated border border-warm-grey-300 max-w-md w-full p-6 animate-in zoom-in-95">
            <h3 className="font-bold text-base text-charcoal-900 mb-3">Register New Classroom Device</h3>
            <form onSubmit={handleCreateDevice} className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">
                  Device Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Primary Laser Projector B"
                  value={deviceName}
                  onChange={(e) => setDeviceName(e.target.value)}
                  className="w-full text-xs p-2 rounded border border-warm-grey-300 text-charcoal-900"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">
                    Brand *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Epson"
                    value={deviceBrand}
                    onChange={(e) => setDeviceBrand(e.target.value)}
                    className="w-full text-xs p-2 rounded border border-warm-grey-300 text-charcoal-900"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">
                    Model *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. EB-L630U"
                    value={deviceModel}
                    onChange={(e) => setDeviceModel(e.target.value)}
                    className="w-full text-xs p-2 rounded border border-warm-grey-300 text-charcoal-900"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">
                    Type *
                  </label>
                  <select
                    value={deviceType}
                    onChange={(e) => setDeviceType(e.target.value as DeviceType)}
                    className="w-full text-xs p-2 rounded border border-warm-grey-300 text-charcoal-900 bg-white"
                  >
                    <option value="PROJECTOR">PROJECTOR</option>
                    <option value="MICROPHONE">MICROPHONE</option>
                    <option value="SMART_BOARD">SMART_BOARD</option>
                    <option value="HDMI_SWITCHER">HDMI_SWITCHER</option>
                    <option value="AUDIO_AMPLIFIER">AUDIO_AMPLIFIER</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">
                    Classroom *
                  </label>
                  <select
                    value={classroomId}
                    onChange={(e) => setClassroomId(e.target.value)}
                    className="w-full text-xs p-2 rounded border border-warm-grey-300 text-charcoal-900 bg-white"
                    required
                  >
                    {classrooms.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.roomNumber} ({c.building})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">
                    Serial Number *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. EP-EB630-881"
                    value={serialNumber}
                    onChange={(e) => setSerialNumber(e.target.value)}
                    className="w-full text-xs p-2 rounded border border-warm-grey-300 text-charcoal-900 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">
                    IP Address (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. 10.24.12.90"
                    value={ipAddress}
                    onChange={(e) => setIpAddress(e.target.value)}
                    className="w-full text-xs p-2 rounded border border-warm-grey-300 text-charcoal-900 font-mono"
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-warm-grey-200 flex justify-end gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsRegisterModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  isLoading={isSubmitting}
                >
                  Save Equipment
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

