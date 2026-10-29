import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { LoadingState } from '@/components/ui/LoadingState'
import { EmptyState } from '@/components/ui/EmptyState'
import { ErrorState } from '@/components/ui/ErrorState'
import { classroomService } from '@/services'
import type { Classroom } from '@/types'
import { School, Search, ArrowRight, Tv } from 'lucide-react'

export const FacultyClassroomsPage: React.FC = () => {
  const [classrooms, setClassrooms] = useState<Classroom[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  const loadData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const all = await classroomService.getClassrooms()
      setClassrooms(all)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to connect to the server. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  if (isLoading) {
    return <LoadingState message="Loading campus classroom directory..." />
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadData} />
  }

  const filteredClassrooms = classrooms.filter((c) => {
    if (!searchQuery.trim()) return true
    const q = searchQuery.toLowerCase()
    return c.roomNumber.toLowerCase().includes(q) || c.building.toLowerCase().includes(q)
  })

  return (
    <div className="space-y-6">
      <PageHeader
        title="Campus Classroom AV Directory"
        description="Review AV hardware readiness, seating capacity, and active ticket alerts across campus buildings."
        breadcrumbs={[
          { label: 'Home', href: '#' },
          { label: 'Faculty', href: '/faculty' },
          { label: 'Classrooms' },
        ]}
      />

      {/* Search Input */}
      <div className="relative max-w-sm">
        <Search className="w-3.5 h-3.5 text-charcoal-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          placeholder="Search by room or building..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full text-xs pl-8 pr-3 py-1.5 rounded-md border border-warm-grey-300 text-charcoal-900 bg-white focus:outline-forest-600"
        />
      </div>

      {classrooms.length === 0 ? (
        <EmptyState
          icon={<School className="w-8 h-8 text-charcoal-400" />}
          title="No classrooms are available yet."
          description="Campus administrators have not registered any lecture halls or classrooms in the database."
          actionLabel="Refresh Directory"
          onAction={loadData}
        />
      ) : filteredClassrooms.length === 0 ? (
        <EmptyState
          title="No matching classrooms"
          description={`No classrooms found matching "${searchQuery}".`}
          actionLabel="Clear Search"
          onAction={() => setSearchQuery('')}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {filteredClassrooms.map((cls) => {
            const isOp = cls.status === 'OPERATIONAL'
            const isDeg = cls.status === 'DEGRADED'

            return (
              <Card key={cls.id} className="border-warm-grey-200 shadow-subtle bg-white hover:border-forest-400 transition-all">
                <CardHeader className="p-4 border-b border-warm-grey-200 bg-app-soft/30 flex items-center justify-between">
                  <div>
                    <CardTitle className="text-sm font-bold">{cls.roomNumber}</CardTitle>
                    <p className="text-[11px] text-charcoal-500">{cls.building}</p>
                  </div>
                  <Badge variant={isOp ? 'success' : isDeg ? 'warning' : 'danger'} size="sm" dot>
                    {cls.status}
                  </Badge>
                </CardHeader>
                <CardContent className="p-4 space-y-3 text-xs">
                  <div className="flex justify-between text-charcoal-600">
                    <span>Floor Level:</span>
                    <span className="font-semibold text-charcoal-900">Floor {cls.floor}</span>
                  </div>
                  <div className="flex justify-between text-charcoal-600">
                    <span>Seating Capacity:</span>
                    <span className="font-semibold text-charcoal-900">{cls.capacity} seats</span>
                  </div>
                  <div className="flex justify-between text-charcoal-600">
                    <span>Active AV Tickets:</span>
                    <span className={`font-semibold ${cls.activeTicketsCount > 0 ? 'text-amber-700' : 'text-emerald-700'}`}>
                      {cls.activeTicketsCount} open
                    </span>
                  </div>

                  {cls.features && cls.features.length > 0 && (
                    <div className="pt-2 border-t border-warm-grey-200 space-y-1">
                      <span className="text-[10px] uppercase font-bold text-charcoal-400">Features:</span>
                      <div className="flex flex-wrap gap-1">
                        {cls.features.map((feat, idx) => (
                          <span key={idx} className="text-[10px] px-1.5 py-0.5 rounded bg-app-soft text-charcoal-700 border border-warm-grey-200">
                            {feat}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="pt-3 border-t border-warm-grey-200">
                    <Link
                      to={`/faculty/classrooms/${cls.id}`}
                      className="w-full flex items-center justify-between px-3 py-1.5 rounded bg-forest-50 hover:bg-forest-100 text-forest-700 font-semibold text-xs transition-colors"
                    >
                      <span className="flex items-center gap-1.5">
                        <Tv className="w-3.5 h-3.5" />
                        <span>View Room Equipment</span>
                      </span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
