import React, { useState } from 'react'
import type { Complaint, ComplaintResolutionRequest } from '@/types'
import { complaintService } from '@/services'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/features/auth/AuthContext'
import {
  X,
  CheckCircle2,
  Wrench,
  AlertTriangle,
  Clock,
  School,
  Monitor,
  UserCheck,
  Bot,
  BookOpen,
  ArrowUpRight,
  ShieldAlert,
} from 'lucide-react'

interface ComplaintDetailDrawerProps {
  complaint: Complaint | null
  onClose: () => void
  onComplaintUpdated: (updated: Complaint) => void
}

export const ComplaintDetailDrawer: React.FC<ComplaintDetailDrawerProps> = ({
  complaint,
  onClose,
  onComplaintUpdated,
}) => {
  const { currentUser } = useAuth()

  // Resolution Form State
  const [isResolving, setIsResolving] = useState(false)
  const [confirmedCause, setConfirmedCause] = useState('')
  const [repairAction, setRepairAction] = useState('')
  const [resolutionNotes, setResolutionNotes] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  if (!complaint) return null

  const isPending = complaint.status === 'PENDING'
  const isInProgress = complaint.status === 'IN_PROGRESS'
  const isResolved = complaint.status === 'RESOLVED'
  const isEscalated = complaint.status === 'ESCALATED'

  // Claim Ticket
  const handleClaim = async () => {
    if (!currentUser) {
      setActionError('Authenticated technician session required.')
      return
    }
    setIsSubmitting(true)
    setActionError(null)
    try {
      const updated = await complaintService.assignTo(
        complaint.id,
        currentUser.id,
        currentUser.name
      )
      onComplaintUpdated(updated)
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Failed to claim complaint ticket.')
    } finally {
      setIsSubmitting(false)
    }
  }

  // Escalate
  const handleEscalate = async () => {
    setIsSubmitting(true)
    setActionError(null)
    try {
      const updated = await complaintService.updateStatus(complaint.id, 'ESCALATED')
      onComplaintUpdated(updated)
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Failed to escalate ticket.')
    } finally {
      setIsSubmitting(false)
    }
  }

  // Submit Resolution
  const handleResolveSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!confirmedCause.trim() || !repairAction.trim()) {
      setActionError('Please specify confirmed cause and repair action taken.')
      return
    }

    setIsSubmitting(true)
    setActionError(null)

    try {
      const payload: ComplaintResolutionRequest = {
        confirmed_cause: confirmedCause.trim(),
        repair_action: repairAction.trim(),
        resolution_notes: resolutionNotes.trim() || 'Repaired and verified operational.',
      }
      const updated = await complaintService.resolveComplaint(complaint.id, payload)
      onComplaintUpdated(updated)
      setIsResolving(false)
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Failed to submit repair resolution.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-charcoal-900/30 backdrop-blur-xs z-50 transition-opacity"
        onClick={onClose}
      />

      {/* Slide-over Drawer */}
      <div className="fixed inset-y-0 right-0 max-w-xl w-full bg-white shadow-2xl z-50 flex flex-col justify-between border-l border-warm-grey-200 animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="p-5 border-b border-warm-grey-200 flex items-center justify-between bg-app-soft/50">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm font-bold text-forest-700">
                {complaint.ticketNumber}
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
                {complaint.status}
              </Badge>
              <Badge
                variant={
                  complaint.severity === 'CRITICAL'
                    ? 'danger'
                    : complaint.severity === 'HIGH'
                    ? 'warning'
                    : 'neutral'
                }
                size="sm"
              >
                {complaint.severity}
              </Badge>
            </div>
            <div className="text-xs text-charcoal-500 font-medium">
              Category: {complaint.category} &bull; Created {new Date(complaint.createdAt).toLocaleString()}
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-md text-charcoal-400 hover:text-charcoal-700 hover:bg-warm-grey-200 transition-colors"
            aria-label="Close details"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Body Content */}
        <div className="p-6 overflow-y-auto space-y-5 text-xs">
          {actionError && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded text-rose-800 flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>{actionError}</span>
            </div>
          )}

          {/* Issue Summary & Description */}
          <div className="space-y-1.5">
            <h3 className="text-sm font-bold text-charcoal-900 leading-snug">
              {complaint.title}
            </h3>
            <p className="text-charcoal-700 leading-relaxed bg-app-bg p-3 rounded-md border border-warm-grey-200">
              {complaint.description}
            </p>
          </div>

          {/* Location & Hardware Specifications */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-md border border-warm-grey-200 bg-white space-y-1">
              <div className="text-[11px] font-semibold text-charcoal-400 flex items-center gap-1">
                <School className="w-3.5 h-3.5 text-forest-700" />
                Classroom Location
              </div>
              <div className="font-bold text-charcoal-900 text-xs">{complaint.classroomName}</div>
            </div>

            <div className="p-3 rounded-md border border-warm-grey-200 bg-white space-y-1">
              <div className="text-[11px] font-semibold text-charcoal-400 flex items-center gap-1">
                <Monitor className="w-3.5 h-3.5 text-forest-700" />
                Assigned Device
              </div>
              <div className="font-bold text-charcoal-900 text-xs truncate">
                {complaint.deviceName || 'General AV System'}
              </div>
              {complaint.deviceBrand && (
                <div className="text-[10px] text-charcoal-500">
                  {complaint.deviceBrand} {complaint.deviceModel}
                </div>
              )}
            </div>
          </div>

          {/* Reporter & Assignment Card */}
          <div className="p-3 rounded-md border border-warm-grey-200 bg-app-soft/60 space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-charcoal-500 font-semibold">Reported By:</span>
              <span className="font-medium text-charcoal-800">{complaint.reportedByName}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-charcoal-500 font-semibold">Assigned Technician:</span>
              <span className="font-bold text-forest-700">
                {complaint.assignedToName || 'Unassigned — Awaiting Claim'}
              </span>
            </div>
          </div>

          {/* AI Troubleshooting & RAG Context */}
          {complaint.aiSuggestedAction && (
            <div className="p-3.5 rounded-md bg-forest-50 border border-forest-200 space-y-1.5 text-forest-900">
              <div className="flex items-center gap-1.5 font-bold text-forest-800 text-xs">
                <Bot className="w-4 h-4 text-forest-700" />
                AI Diagnostic Context & Manual Citations
              </div>
              <p className="text-xs leading-relaxed text-forest-950">
                {complaint.aiSuggestedAction}
              </p>
            </div>
          )}

          {/* Resolution Card (if already resolved) */}
          {isResolved && (
            <div className="p-4 rounded-md bg-emerald-50 border border-emerald-200 space-y-2 text-emerald-900">
              <div className="flex items-center gap-1.5 font-bold text-emerald-800 text-xs">
                <CheckCircle2 className="w-4 h-4 text-emerald-700" />
                Field Resolution Record
              </div>
              {complaint.confirmedCause && (
                <div>
                  <strong className="text-emerald-950">Confirmed Root Cause:</strong>{' '}
                  {complaint.confirmedCause}
                </div>
              )}
              {complaint.repairAction && (
                <div>
                  <strong className="text-emerald-950">Action Taken:</strong> {complaint.repairAction}
                </div>
              )}
              {complaint.resolutionNotes && (
                <div>
                  <strong className="text-emerald-950">Notes:</strong> {complaint.resolutionNotes}
                </div>
              )}
              <div className="text-[10px] text-emerald-700 pt-1 border-t border-emerald-200">
                Resolved by field operations at {new Date(complaint.resolvedAt || complaint.updatedAt).toLocaleString()}
              </div>
            </div>
          )}

          {/* Inline Resolution Form (if resolving active ticket) */}
          {isResolving && (
            <form onSubmit={handleResolveSubmit} className="p-4 rounded-md bg-app-soft border border-forest-300 space-y-3">
              <h4 className="font-bold text-xs text-charcoal-900">Record Field Repair & Resolution</h4>

              <div>
                <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">
                  Confirmed Cause *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Loose Crestron HDMI Tx cable under lectern"
                  value={confirmedCause}
                  onChange={(e) => setConfirmedCause(e.target.value)}
                  className="w-full text-xs p-2 rounded border border-warm-grey-300 text-charcoal-900 bg-white focus:outline-forest-600"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">
                  Repair Action Taken *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Reseated HDMI connector, secured strain relief, tested 4K video handshake"
                  value={repairAction}
                  onChange={(e) => setRepairAction(e.target.value)}
                  className="w-full text-xs p-2 rounded border border-warm-grey-300 text-charcoal-900 bg-white focus:outline-forest-600"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">
                  Resolution Notes
                </label>
                <textarea
                  rows={2}
                  placeholder="Additional technician notes for knowledge base and faculty review..."
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  className="w-full text-xs p-2 rounded border border-warm-grey-300 text-charcoal-900 bg-white focus:outline-forest-600"
                />
              </div>

              <div className="flex justify-end gap-2 pt-1">
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  onClick={() => setIsResolving(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  variant="primary"
                  isLoading={isSubmitting}
                >
                  Save & Complete Ticket
                </Button>
              </div>
            </form>
          )}
        </div>

        {/* Action Footer */}
        <div className="p-4 border-t border-warm-grey-200 bg-white flex items-center justify-between gap-3">
          <Button size="sm" variant="outline" onClick={onClose}>
            Close Panel
          </Button>

          <div className="flex items-center gap-2">
            {isPending && (
              <Button
                size="sm"
                variant="primary"
                onClick={handleClaim}
                isLoading={isSubmitting}
                leftIcon={<UserCheck className="w-3.5 h-3.5" />}
              >
                Claim Ticket & Start Triage
              </Button>
            )}

            {(isInProgress || isEscalated) && !isResolving && (
              <>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleEscalate}
                  disabled={isSubmitting}
                  leftIcon={<ArrowUpRight className="w-3.5 h-3.5" />}
                >
                  Escalate
                </Button>

                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => setIsResolving(true)}
                  disabled={isSubmitting}
                  leftIcon={<CheckCircle2 className="w-3.5 h-3.5" />}
                >
                  Resolve Incident
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  )
}

