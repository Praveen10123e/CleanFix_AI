import React, { useState, useEffect } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { LoadingState } from '@/components/ui/LoadingState'
import { ErrorState } from '@/components/ui/ErrorState'
import { classroomService } from '@/services'
import type { Classroom, ClassroomStatus, CreateClassroomDTO } from '@/types'
import { School, Plus, Search } from 'lucide-react'

export const AdminClassroomsPage: React.FC = () => {
  const [classrooms, setClassrooms] = useState<Classroom[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Add Classroom Modal
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [roomNumber, setRoomNumber] = useState('')
  const [building, setBuilding] = useState('')
  const [floor, setFloor] = useState<number>(1)
  const [capacity, setCapacity] = useState<number>(60)
  const [featuresText, setFeaturesText] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const loadData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const all = await classroomService.getClassrooms()
      setClassrooms(all)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve classroom fleet.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!roomNumber.trim() || !building.trim()) return

    setIsSubmitting(true)
    try {
      const dto: CreateClassroomDTO = {
        roomNumber: roomNumber.trim(),
        building: building.trim(),
        floor: Number(floor),
        capacity: Number(capacity),
        features: featuresText ? featuresText.split(',').map((f) => f.trim()) : ['Laser Projector', 'Podium Mic'],
      }
      await classroomService.createClassroom(dto)
      setIsModalOpen(false)
      setRoomNumber('')
      setBuilding('')
      setFeaturesText('')
    } catch (err) {
      alert('Error creating room: ' + (err instanceof Error ? err.message : 'Unknown'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleStatusChange = async (id: string, newStatus: ClassroomStatus) => {
    try {
      await classroomService.updateClassroom(id, { status: newStatus })
    } catch (err) {
      alert('Error updating status: ' + (err instanceof Error ? err.message : 'Unknown'))
    }
  }

  if (isLoading) {
    return <LoadingState message="Loading Classroom Infrastructure Matrix..." />
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadData} />
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Classroom Fleet & Infrastructure"
        description="Register campus lecture halls, set baseline seating capacities, and monitor AV system statuses."
        breadcrumbs={[
          { label: 'Home', href: '#' },
          { label: 'Admin', href: '/admin' },
          { label: 'Classrooms' },
        ]}
        actions={
          <Button
            size="sm"
            variant="primary"
            leftIcon={<Plus className="w-3.5 h-3.5" />}
            onClick={() => setIsModalOpen(true)}
          >
            Add Classroom
          </Button>
        }
      />

      <Card className="border-warm-grey-200 shadow-subtle bg-white">
        <CardHeader className="bg-app-soft/40 border-b border-warm-grey-200 flex items-center justify-between">
          <CardTitle>Campus Classroom Registry</CardTitle>
          <span className="text-xs text-charcoal-500 font-medium">{classrooms.length} rooms listed</span>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-app-soft text-charcoal-600 border-b border-warm-grey-200">
                <tr>
                  <th className="py-2.5 px-4 font-semibold">Room Number</th>
                  <th className="py-2.5 px-3 font-semibold">Building & Floor</th>
                  <th className="py-2.5 px-3 font-semibold">Capacity</th>
                  <th className="py-2.5 px-3 font-semibold">Active Incidents</th>
                  <th className="py-2.5 px-3 font-semibold">Operational Status</th>
                  <th className="py-2.5 px-4 text-right font-semibold">Update Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-warm-grey-200">
                {classrooms.map((cls) => (
                  <tr key={cls.id} className="hover:bg-app-soft/30 transition-colors">
                    <td className="py-3 px-4 font-bold text-charcoal-900">{cls.roomNumber}</td>
                    <td className="py-3 px-3 text-charcoal-700">
                      {cls.building} &bull; Floor {cls.floor}
                    </td>
                    <td className="py-3 px-3 text-charcoal-700">{cls.capacity} seats</td>
                    <td className="py-3 px-3 font-semibold">
                      <span className={cls.activeTicketsCount > 0 ? 'text-amber-700' : 'text-emerald-700'}>
                        {cls.activeTicketsCount} active
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <Badge
                        variant={
                          cls.status === 'OPERATIONAL'
                            ? 'success'
                            : cls.status === 'DEGRADED'
                            ? 'warning'
                            : 'danger'
                        }
                        size="sm"
                        dot
                      >
                        {cls.status}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <select
                        value={cls.status}
                        onChange={(e) => handleStatusChange(cls.id, e.target.value as ClassroomStatus)}
                        className="text-xs p-1 rounded border border-warm-grey-300 text-charcoal-900 bg-white"
                      >
                        <option value="OPERATIONAL">OPERATIONAL</option>
                        <option value="DEGRADED">DEGRADED</option>
                        <option value="OUT_OF_SERVICE">OUT_OF_SERVICE</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Add Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-charcoal-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-lg shadow-elevated border border-warm-grey-300 max-w-md w-full p-6 animate-in zoom-in-95">
            <h3 className="font-bold text-base text-charcoal-900 mb-3">Add Classroom</h3>
            <form onSubmit={handleCreate} className="space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">
                    Room Number *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. SCI-302"
                    value={roomNumber}
                    onChange={(e) => setRoomNumber(e.target.value)}
                    className="w-full text-xs p-2 rounded border border-warm-grey-300 text-charcoal-900"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">
                    Building *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Science Complex"
                    value={building}
                    onChange={(e) => setBuilding(e.target.value)}
                    className="w-full text-xs p-2 rounded border border-warm-grey-300 text-charcoal-900"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">
                    Floor Level *
                  </label>
                  <input
                    type="number"
                    required
                    min={1}
                    max={20}
                    value={floor}
                    onChange={(e) => setFloor(Number(e.target.value))}
                    className="w-full text-xs p-2 rounded border border-warm-grey-300 text-charcoal-900"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">
                    Capacity (Seats) *
                  </label>
                  <input
                    type="number"
                    required
                    min={10}
                    max={1000}
                    value={capacity}
                    onChange={(e) => setCapacity(Number(e.target.value))}
                    className="w-full text-xs p-2 rounded border border-warm-grey-300 text-charcoal-900"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">
                  Features (Comma-separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g. 4K Laser Projector, Smart Board 86, Dual Wireless Mic"
                  value={featuresText}
                  onChange={(e) => setFeaturesText(e.target.value)}
                  className="w-full text-xs p-2 rounded border border-warm-grey-300 text-charcoal-900"
                />
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
                  Save Classroom
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

