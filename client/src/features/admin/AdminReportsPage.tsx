import React, { useState, useEffect } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { LoadingState } from '@/components/ui/LoadingState'
import { ErrorState } from '@/components/ui/ErrorState'
import { adminService } from '@/services'
import type { AdminReportsSummary } from '@/types'
import { BarChart3, Clock, AlertTriangle, CheckCircle2, ShieldCheck, Activity } from 'lucide-react'

export const AdminReportsPage: React.FC = () => {
  const [reports, setReports] = useState<AdminReportsSummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await adminService.getReportsSummary()
      setReports(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve operations report.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  if (isLoading) {
    return <LoadingState message="Aggregating Campus AV Incident SLA Reports..." />
  }

  if (error || !reports) {
    return <ErrorState message={error || 'No report data returned.'} onRetry={loadData} />
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Operations Analytics & Incident Reports"
        description="Campus SLA performance, AV breakdown categories, and resolution telemetry."
        breadcrumbs={[
          { label: 'Home', href: '#' },
          { label: 'Admin', href: '/admin' },
          { label: 'Reports' },
        ]}
      />

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="border-warm-grey-200 shadow-subtle bg-white">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <div className="text-[11px] font-semibold text-charcoal-400 uppercase tracking-wider">
                System Availability
              </div>
              <div className="text-2xl font-bold text-forest-700 mt-0.5">
                {reports.systemUptimePercentage}%
              </div>
              <div className="text-[11px] text-emerald-700 font-medium mt-0.5">
                Exceeding 99.0% SLA
              </div>
            </div>
            <div className="w-9 h-9 rounded-md bg-app-secondary text-forest-700 flex items-center justify-center">
              <ShieldCheck className="w-4 h-4" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-warm-grey-200 shadow-subtle bg-white">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <div className="text-[11px] font-semibold text-charcoal-400 uppercase tracking-wider">
                Avg Resolution Time
              </div>
              <div className="text-2xl font-bold text-charcoal-900 mt-0.5">
                {reports.avgResolutionTimeMinutes} min
              </div>
              <div className="text-[11px] text-charcoal-500 mt-0.5">Campus benchmark: &lt;30m</div>
            </div>
            <div className="w-9 h-9 rounded-md bg-emerald-50 text-emerald-700 flex items-center justify-center">
              <Clock className="w-4 h-4" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-warm-grey-200 shadow-subtle bg-white">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <div className="text-[11px] font-semibold text-charcoal-400 uppercase tracking-wider">
                Resolved Today
              </div>
              <div className="text-2xl font-bold text-charcoal-900 mt-0.5">
                {reports.resolvedTodayCount} tickets
              </div>
              <div className="text-[11px] text-charcoal-500 mt-0.5">
                {reports.activeTickets} open tickets remaining
              </div>
            </div>
            <div className="w-9 h-9 rounded-md bg-app-soft text-forest-700 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Categorical Breakdown Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Breakdown by Equipment Category */}
        <Card className="border-warm-grey-200 shadow-subtle bg-white">
          <CardHeader className="bg-app-soft/40 border-b border-warm-grey-200">
            <CardTitle>Incidents by Hardware Category</CardTitle>
          </CardHeader>
          <CardContent className="p-5 space-y-3">
            {Object.entries(reports.ticketsByCategory).map(([cat, count]) => (
              <div key={cat} className="space-y-1 text-xs">
                <div className="flex justify-between font-medium">
                  <span className="text-charcoal-700">{cat}</span>
                  <span className="font-bold text-charcoal-900">{count} incident{count === 1 ? '' : 's'}</span>
                </div>
                <div className="w-full bg-warm-grey-200 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-forest-600 h-2 rounded-full transition-all"
                    style={{
                      width: `${Math.min(100, (count / Math.max(1, reports.activeTickets + reports.resolvedTodayCount)) * 100)}%`,
                    }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Breakdown by Severity */}
        <Card className="border-warm-grey-200 shadow-subtle bg-white">
          <CardHeader className="bg-app-soft/40 border-b border-warm-grey-200">
            <CardTitle>Incidents by Severity Classification</CardTitle>
          </CardHeader>
          <CardContent className="p-5 space-y-3">
            {Object.entries(reports.ticketsBySeverity).map(([sev, count]) => {
              const isCrit = sev === 'CRITICAL'
              const isHigh = sev === 'HIGH'
              return (
                <div key={sev} className="space-y-1 text-xs">
                  <div className="flex justify-between font-medium">
                    <span className="text-charcoal-700">{sev}</span>
                    <span className="font-bold text-charcoal-900">{count} ticket{count === 1 ? '' : 's'}</span>
                  </div>
                  <div className="w-full bg-warm-grey-200 h-2 rounded-full overflow-hidden">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        isCrit ? 'bg-rose-600' : isHigh ? 'bg-amber-600' : 'bg-forest-600'
                      }`}
                      style={{
                        width: `${Math.min(100, (count / Math.max(1, reports.activeTickets + reports.resolvedTodayCount)) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
              )
            })}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

