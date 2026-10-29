import React, { useState } from 'react'
import type {
  Device,
  TroubleshootingSession,
  DiagnosticStep,
  StepResultType,
  Complaint,
} from '@/types'
import { troubleshootingService } from '@/services'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { LoadingSpinner } from '@/components/ui/LoadingState'
import {
  Sparkles,
  Bot,
  AlertCircle,
  CheckCircle2,
  HelpCircle,
  XCircle,
  Wrench,
  BookOpen,
  ArrowRight,
  RotateCcw,
  ShieldAlert,
  Send,
  Check,
} from 'lucide-react'

interface InteractiveTroubleshooterProps {
  device: Device
  onSessionStarted?: (session: TroubleshootingSession) => void
  onComplaintCreated?: (complaint: Complaint) => void
  initialSession?: TroubleshootingSession | null
  onResetSession?: () => void
}

export const InteractiveTroubleshooter: React.FC<InteractiveTroubleshooterProps> = ({
  device,
  onSessionStarted,
  onComplaintCreated,
  initialSession,
  onResetSession,
}) => {
  // Session State
  const [symptomText, setSymptomText] = useState('')
  const [session, setSession] = useState<TroubleshootingSession | null>(initialSession || null)
  const [currentStep, setCurrentStep] = useState<DiagnosticStep | null>(
    initialSession?.current_step || null
  )

  // Step interaction state
  const [selectedResult, setSelectedResult] = useState<StepResultType | null>(null)
  const [resultNote, setResultNote] = useState('')
  const [selectedQuestionChoice, setSelectedQuestionChoice] = useState<string>('')

  // Loading & Error States
  const [isStartingSession, setIsStartingSession] = useState(false)
  const [isSubmittingResult, setIsSubmittingResult] = useState(false)
  const [isRequestingNextStep, setIsRequestingNextStep] = useState(false)
  const [isRequestingTechnician, setIsRequestingTechnician] = useState(false)
  const [isCompletingSession, setIsCompletingSession] = useState(false)

  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [stepFeedback, setStepFeedback] = useState<string | null>(null)

  // Created complaint (after escalation)
  const [createdComplaint, setCreatedComplaint] = useState<Complaint | null>(null)
  const [isResolved, setIsResolved] = useState(initialSession?.status === 'resolved')

  // Common quick symptom presets for fast lecture troubleshooting
  const symptomPresets: Record<string, string[]> = {
    PROJECTOR: [
      'Projector powers on but shows "No Signal" on HDMI',
      'Image color is tinted cyan / discolored',
      'Display flickers repeatedly during presentation',
    ],
    MICROPHONE: [
      'Microphone has audio dropouts and loud static',
      'Lavalier mic powers on but no sound from ceiling speakers',
      'Battery low warning blinking on beltpack LCD',
    ],
    SMART_BOARD: [
      'Touch stylus is not registering on Windows OPS screen',
      'Board shows blank screen after waking up PC',
      'Touch tracking is misaligned by several inches',
    ],
  }

  const defaultPresets = symptomPresets[device.type] || [
    'Device does not respond to podium touch panel commands',
    'Hardware powers on but fails to pass input signal',
  ]

  // 1. Start Session
  const handleStartSession = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!symptomText.trim()) {
      setErrorMessage('Please describe the symptom or issue before starting troubleshooting.')
      return
    }

    setErrorMessage(null)
    setIsStartingSession(true)

    try {
      const newSession = await troubleshootingService.startSession({
        device_id: device.id,
        symptom_text: symptomText.trim(),
      })
      setSession(newSession)
      setCurrentStep(newSession.current_step || null)
      if (onSessionStarted) {
        onSessionStarted(newSession)
      }
    } catch (err) {
      setErrorMessage(
        err instanceof Error
          ? err.message
          : 'Failed to initialize troubleshooting session. Verify API connectivity.'
      )
    } finally {
      setIsStartingSession(false)
    }
  }

  // 2. Submit Step Result
  const handleSubmitStepResult = async () => {
    if (!session || !currentStep || !selectedResult) {
      setErrorMessage('Please select an observation result for this step.')
      return
    }

    setErrorMessage(null)
    setIsSubmittingResult(true)

    try {
      const combinedNote = [
        selectedQuestionChoice ? `Question Answer: ${selectedQuestionChoice}` : '',
        resultNote.trim(),
      ]
        .filter(Boolean)
        .join(' | ')

      const response = await troubleshootingService.submitStepResult(
        session.id,
        currentStep.step_id,
        {
          result: selectedResult,
          result_note: combinedNote || undefined,
        }
      )

      setStepFeedback(response.message || 'Observation recorded.')

      if (response.is_resolved) {
        setIsResolved(true)
        // Conclude session via completion endpoint
        await handleCompleteResolvedSession(session.id)
      } else {
        // Automatically request next step from backend
        await handleFetchNextStep(session.id)
      }
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Failed to record diagnostic step result.'
      )
    } finally {
      setIsSubmittingResult(false)
    }
  }

  // 3. Fetch Next Step from Backend
  const handleFetchNextStep = async (sessionId: string) => {
    setIsRequestingNextStep(true)
    try {
      const nextStep = await troubleshootingService.getNextStep(sessionId)
      setCurrentStep(nextStep)
      // Reset step input states
      setSelectedResult(null)
      setResultNote('')
      setSelectedQuestionChoice('')
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Failed to retrieve subsequent diagnostic step.'
      )
    } finally {
      setIsRequestingNextStep(false)
    }
  }

  // 4. Complete Session (Resolved)
  const handleCompleteResolvedSession = async (sessionId: string) => {
    setIsCompletingSession(true)
    try {
      await troubleshootingService.completeSession(sessionId)
    } catch (err) {
      console.warn('Non-fatal error finalizing session completion:', err)
    } finally {
      setIsCompletingSession(false)
    }
  }

  // 5. Request Field Technician (Mandatory Feature)
  const handleRequestTechnician = async () => {
    if (!session) {
      setErrorMessage('Cannot request technician without an active troubleshooting session.')
      return
    }

    if (createdComplaint) {
      return // Prevent duplicate submissions
    }

    setErrorMessage(null)
    setIsRequestingTechnician(true)

    try {
      const complaintDesc = `Faculty reported issue during lecture with ${device.brand} ${device.model}: "${session.symptom_text}". Troubleshooter reached step ${session.current_step_number} without full resolution. Immediate field triage requested.`

      const complaint = await troubleshootingService.createComplaintFromSession(session.id, {
        description: complaintDesc,
        preferred_technician_id: null,
      })

      setCreatedComplaint(complaint)
      if (onComplaintCreated) {
        onComplaintCreated(complaint)
      }
    } catch (err) {
      setErrorMessage(
        err instanceof Error
          ? err.message
          : 'Failed to dispatch technician request. Please try again or call AV emergency dispatch.'
      )
    } finally {
      setIsRequestingTechnician(false)
    }
  }

  // Determine if Request Technician button should be visible
  const canRequestTechnician =
    Boolean(session) &&
    !isResolved &&
    !createdComplaint &&
    (selectedResult === 'not_resolved' ||
      selectedResult === 'unable_to_perform' ||
      selectedResult === 'unknown' ||
      Boolean(currentStep?.recommended_escalation) ||
      session?.status === 'unresolved' ||
      session?.status === 'escalated' ||
      currentStep === null)

  return (
    <Card className="border-warm-grey-300 shadow-card bg-white">
      <CardHeader className="bg-ivory-50/70 border-b border-warm-grey-200">
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-md bg-forest-600 text-white flex items-center justify-center">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <CardTitle className="text-sm sm:text-base">
                  Interactive AV Diagnostic Assistant
                </CardTitle>
                <Badge variant="forest" size="sm">
                  RAG-Assisted
                </Badge>
              </div>
              <p className="text-xs text-charcoal-500">
                Target: {device.brand} {device.model} ({device.name})
              </p>
            </div>
          </div>

          {session && (
            <div className="flex items-center gap-2">
              <span className="font-mono text-[11px] text-charcoal-400 hidden sm:inline">
                Session: {session.id.slice(0, 8)}...
              </span>
              {onResetSession && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={onResetSession}
                  leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
                >
                  New Session
                </Button>
              )}
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="p-4 sm:p-6 space-y-5">
        {/* Error Callout */}
        {errorMessage && (
          <div className="p-3 rounded-md bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-start gap-2 animate-in fade-in">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <span className="font-semibold">Error: </span>
              {errorMessage}
            </div>
          </div>
        )}

        {/* STEP A: Session Initialization Form (if no active session) */}
        {!session && (
          <form onSubmit={handleStartSession} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-charcoal-700 uppercase tracking-wider mb-1.5">
                3. Describe the Classroom AV Issue *
              </label>
              <textarea
                rows={3}
                required
                disabled={isStartingSession}
                placeholder={`Describe the observed symptom with the ${device.brand} ${device.name} (e.g. "Projector displays blue screen with No Signal warning")...`}
                value={symptomText}
                onChange={(e) => setSymptomText(e.target.value)}
                className="w-full text-xs p-3 rounded-md border border-warm-grey-300 text-charcoal-900 focus:outline-forest-600 focus:ring-1 focus:ring-forest-600 leading-relaxed"
              />
            </div>

            {/* Quick Symptom Chips */}
            <div>
              <span className="text-[11px] font-semibold text-charcoal-400 uppercase tracking-wider block mb-1.5">
                Common Quick Presets:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {defaultPresets.map((preset, idx) => (
                  <button
                    key={idx}
                    type="button"
                    disabled={isStartingSession}
                    onClick={() => setSymptomText(preset)}
                    className="text-left text-xs px-2.5 py-1 rounded bg-ivory-100 hover:bg-forest-50 hover:text-forest-800 border border-warm-grey-200 text-charcoal-700 transition-colors"
                  >
                    + {preset}
                  </button>
                ))}
              </div>
            </div>

            <div className="pt-2">
              <Button
                type="submit"
                variant="primary"
                size="md"
                isLoading={isStartingSession}
                rightIcon={<Sparkles className="w-4 h-4" />}
                className="w-full sm:w-auto"
              >
                Start AI Troubleshooting Session
              </Button>
            </div>
          </form>
        )}

        {/* STEP B: Active Troubleshooting Diagnostic Step */}
        {session && !isResolved && !createdComplaint && (
          <div className="space-y-5">
            {/* Session Metadata Strip */}
            <div className="p-3 bg-ivory-100 rounded-md border border-warm-grey-200 flex flex-wrap items-center justify-between gap-2 text-xs">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-charcoal-800">Symptom Reported:</span>
                <span className="italic text-charcoal-600">"{session.symptom_text}"</span>
              </div>
              <Badge variant="info" size="sm">
                Status: {session.status.toUpperCase()}
              </Badge>
            </div>

            {/* Current Step Display */}
            {isRequestingNextStep ? (
              <div className="p-8 text-center bg-ivory-50 rounded-lg border border-dashed border-warm-grey-300">
                <LoadingSpinner size="md" label="Querying RAG knowledge vectors for next diagnostic step..." />
              </div>
            ) : currentStep ? (
              <div className="p-5 rounded-lg border border-warm-grey-300 bg-white space-y-4">
                {/* Step Header */}
                <div className="flex items-center justify-between border-b border-warm-grey-200 pb-3">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-forest-600 text-white font-bold text-xs flex items-center justify-center">
                      {currentStep.step_number}
                    </span>
                    <span className="font-bold text-sm text-charcoal-900">
                      Diagnostic Step {currentStep.step_number}
                      {currentStep.total_steps_estimate && (
                        <span className="font-normal text-charcoal-400 text-xs">
                          {' '}of ~{currentStep.total_steps_estimate}
                        </span>
                      )}
                    </span>
                  </div>
                  {currentStep.recommended_escalation && (
                    <Badge variant="warning" size="sm">
                      Escalation Checkpoint
                    </Badge>
                  )}
                </div>

                {/* Step Instruction */}
                <div>
                  <h4 className="text-xs font-semibold text-charcoal-400 uppercase tracking-wider mb-1">
                    Instruction
                  </h4>
                  <p className="text-sm font-semibold text-charcoal-900 leading-snug">
                    {currentStep.instruction}
                  </p>
                </div>

                {/* Reason Callout */}
                {currentStep.reason && (
                  <div className="p-3 rounded-md bg-ivory-100 text-xs text-charcoal-700 border-l-2 border-forest-600">
                    <span className="font-semibold text-charcoal-900">Why this check: </span>
                    {currentStep.reason}
                  </div>
                )}

                {/* Expected Observation */}
                {currentStep.expected_observation && (
                  <div className="text-xs text-charcoal-700 bg-emerald-50/60 p-3 rounded-md border border-emerald-100">
                    <span className="font-semibold text-emerald-900">Expected Observation: </span>
                    {currentStep.expected_observation}
                  </div>
                )}

                {/* Source Manual Reference (Citation) */}
                {currentStep.source_manual && (
                  <div className="p-2.5 rounded bg-ivory-50 border border-warm-grey-200 text-[11px] text-charcoal-500 flex items-center gap-2">
                    <BookOpen className="w-3.5 h-3.5 text-forest-700 shrink-0" />
                    <span>
                      <strong className="text-charcoal-700">Source:</strong> {currentStep.source_manual}
                      {currentStep.source_section && ` &bull; ${currentStep.source_section}`}
                      {currentStep.source_page && ` (Page ${currentStep.source_page})`}
                    </span>
                  </div>
                )}

                {/* Dynamic Diagnostic Question */}
                {currentStep.question && (
                  <div className="pt-2 border-t border-warm-grey-200 space-y-2">
                    <label className="block text-xs font-semibold text-charcoal-800">
                      {currentStep.question.text}
                    </label>
                    {currentStep.question.input_type === 'choice' && currentStep.question.choices && (
                      <div className="space-y-1.5">
                        {currentStep.question.choices.map((choice) => (
                          <label
                            key={choice.id}
                            className={`flex items-center gap-2 p-2 rounded border text-xs cursor-pointer transition-colors ${
                              selectedQuestionChoice === choice.label
                                ? 'bg-forest-50 border-forest-500 font-medium text-forest-900'
                                : 'bg-white border-warm-grey-200 hover:bg-ivory-50 text-charcoal-800'
                            }`}
                          >
                            <input
                              type="radio"
                              name="step-choice"
                              value={choice.label}
                              checked={selectedQuestionChoice === choice.label}
                              onChange={(e) => setSelectedQuestionChoice(e.target.value)}
                              className="text-forest-600 focus:ring-forest-600"
                            />
                            <span>{choice.label}</span>
                          </label>
                        ))}
                      </div>
                    )}

                    {currentStep.question.input_type === 'boolean' && currentStep.question.choices && (
                      <div className="grid grid-cols-2 gap-2">
                        {currentStep.question.choices.map((choice) => (
                          <Button
                            key={choice.id}
                            type="button"
                            size="sm"
                            variant={selectedQuestionChoice === choice.label ? 'primary' : 'outline'}
                            onClick={() => setSelectedQuestionChoice(choice.label)}
                          >
                            {choice.label}
                          </Button>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Step Result Selection */}
                <div className="pt-3 border-t border-warm-grey-200 space-y-2.5">
                  <span className="block text-xs font-semibold text-charcoal-700 uppercase tracking-wider">
                    Record Step Outcome *
                  </span>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    <button
                      type="button"
                      onClick={() => setSelectedResult('resolved')}
                      className={`p-2.5 rounded border text-xs font-medium flex flex-col items-center justify-center gap-1 transition-all ${
                        selectedResult === 'resolved'
                          ? 'bg-emerald-600 text-white border-emerald-700 shadow-xs'
                          : 'bg-white border-warm-grey-300 text-charcoal-800 hover:bg-emerald-50'
                      }`}
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Issue Resolved</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => setSelectedResult('not_resolved')}
                      className={`p-2.5 rounded border text-xs font-medium flex flex-col items-center justify-center gap-1 transition-all ${
                        selectedResult === 'not_resolved'
                          ? 'bg-amber-600 text-white border-amber-700 shadow-xs'
                          : 'bg-white border-warm-grey-300 text-charcoal-800 hover:bg-amber-50'
                      }`}
                    >
                      <XCircle className="w-4 h-4" />
                      <span>Still Broken</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => setSelectedResult('unable_to_perform')}
                      className={`p-2.5 rounded border text-xs font-medium flex flex-col items-center justify-center gap-1 transition-all ${
                        selectedResult === 'unable_to_perform'
                          ? 'bg-terracotta-600 text-white border-terracotta-700 shadow-xs'
                          : 'bg-white border-warm-grey-300 text-charcoal-800 hover:bg-terracotta-50'
                      }`}
                    >
                      <ShieldAlert className="w-4 h-4" />
                      <span>Cannot Perform</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => setSelectedResult('unknown')}
                      className={`p-2.5 rounded border text-xs font-medium flex flex-col items-center justify-center gap-1 transition-all ${
                        selectedResult === 'unknown'
                          ? 'bg-charcoal-700 text-white border-charcoal-800 shadow-xs'
                          : 'bg-white border-warm-grey-300 text-charcoal-800 hover:bg-ivory-100'
                      }`}
                    >
                      <HelpCircle className="w-4 h-4" />
                      <span>Unsure / Unknown</span>
                    </button>
                  </div>

                  {/* Optional observation note */}
                  <div>
                    <input
                      type="text"
                      placeholder="Optional observation note (e.g. 'Power LED blinked red twice')..."
                      value={resultNote}
                      onChange={(e) => setResultNote(e.target.value)}
                      className="w-full text-xs p-2 rounded border border-warm-grey-300 text-charcoal-900"
                    />
                  </div>

                  <div className="pt-2 flex items-center justify-between gap-3">
                    <Button
                      type="button"
                      variant="primary"
                      size="sm"
                      disabled={!selectedResult}
                      isLoading={isSubmittingResult}
                      onClick={handleSubmitStepResult}
                      rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
                    >
                      Submit Step Result & Next
                    </Button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-6 text-center bg-ivory-50 rounded-lg border border-warm-grey-200">
                <p className="text-xs text-charcoal-600 mb-3">
                  All guided troubleshooting steps from technical manuals have been completed for this device.
                </p>
                <Badge variant="terracotta" size="sm">
                  Recommended Action: Dispatch Field Technician
                </Badge>
              </div>
            )}

            {/* Step Feedback Banner */}
            {stepFeedback && (
              <div className="p-3 bg-forest-50 border border-forest-200 rounded text-xs text-forest-900 flex items-center gap-2">
                <Check className="w-4 h-4 text-forest-600 shrink-0" />
                <span>{stepFeedback}</span>
              </div>
            )}
          </div>
        )}

        {/* STEP C: Resolved Outcome Confirmation */}
        {isResolved && (
          <div className="p-6 rounded-lg bg-emerald-50 border border-emerald-200 text-center space-y-3 animate-in fade-in">
            <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-base text-emerald-900">
              Classroom AV Issue Successfully Resolved
            </h3>
            <p className="text-xs text-emerald-800 max-w-md mx-auto">
              The issue with the {device.brand} {device.name} in room {device.classroomName} was
              resolved through guided troubleshooting. The session has been completed and archived.
            </p>
            {onResetSession && (
              <Button size="sm" variant="outline" onClick={onResetSession}>
                Start Another Session
              </Button>
            )}
          </div>
        )}

        {/* STEP D: Created Complaint Confirmation Panel (After Request Technician) */}
        {createdComplaint && (
          <div className="p-6 rounded-lg bg-terracotta-50 border border-terracotta-200 space-y-4 animate-in fade-in">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-md bg-terracotta-600 text-white flex items-center justify-center">
                  <Wrench className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-bold text-sm text-terracotta-900">
                    Field Technician Request Dispatched!
                  </h4>
                  <p className="text-xs text-terracotta-800">
                    Ticket created and prioritized on the campus AV queue.
                  </p>
                </div>
              </div>
              <Badge variant="warning" size="sm" dot>
                {createdComplaint.status}
              </Badge>
            </div>

            <div className="p-3 bg-white rounded border border-warm-grey-200 text-xs space-y-1.5">
              <div className="flex justify-between">
                <span className="text-charcoal-500 font-semibold">Complaint Ticket Number:</span>
                <span className="font-mono font-bold text-forest-700">{createdComplaint.ticketNumber}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-charcoal-500">Classroom:</span>
                <span className="font-medium text-charcoal-800">{createdComplaint.classroomName}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-charcoal-500">Equipment:</span>
                <span className="font-medium text-charcoal-800">{createdComplaint.deviceName}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-charcoal-500">Priority:</span>
                <span className="font-bold text-terracotta-700">{createdComplaint.severity}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-charcoal-500">Dispatched At:</span>
                <span className="text-charcoal-700">{new Date(createdComplaint.createdAt).toLocaleTimeString()}</span>
              </div>
            </div>

            <div className="flex justify-between items-center pt-2">
              <span className="text-[11px] text-terracotta-700">
                A technician en route notification will appear once assigned.
              </span>
              {onResetSession && (
                <Button size="sm" variant="outline" onClick={onResetSession}>
                  Done
                </Button>
              )}
            </div>
          </div>
        )}

        {/* STEP E: Mandatory "Request Technician" Action Bar */}
        {canRequestTechnician && (
          <div className="pt-4 border-t border-warm-grey-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-terracotta-50/50 p-4 rounded-lg border border-terracotta-200/80">
            <div>
              <div className="font-semibold text-xs text-charcoal-900">
                Troubleshooting Unresolved or Equipment Inaccessible?
              </div>
              <p className="text-[11px] text-charcoal-500">
                Dispatch an on-site field technician with full diagnostic logs and manual citations attached.
              </p>
            </div>

            <Button
              type="button"
              variant="secondary"
              size="md"
              disabled={isRequestingTechnician}
              isLoading={isRequestingTechnician}
              onClick={handleRequestTechnician}
              leftIcon={<Wrench className="w-4 h-4" />}
              className="bg-terracotta-600 hover:bg-terracotta-700 active:bg-terracotta-800 shadow-sm shrink-0"
            >
              Request Technician
            </Button>
          </div>
        )}
      </CardContent>

      {/* History of Previous Submitted Steps in Active Session */}
      {session && session.submitted_results.length > 0 && (
        <CardFooter className="flex-col items-start gap-2 text-xs">
          <span className="font-semibold text-charcoal-700 text-[11px] uppercase tracking-wider">
            Diagnostic Progress ({session.submitted_results.length} checks performed):
          </span>
          <div className="w-full space-y-1">
            {session.submitted_results.map((res, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-2 rounded bg-white border border-warm-grey-200 text-charcoal-700 text-[11px]"
              >
                <div className="flex items-center gap-1.5">
                  <span className="font-bold text-forest-700">Step {res.step_number}:</span>
                  <span className="line-clamp-1">{res.instruction}</span>
                </div>
                <Badge
                  variant={
                    res.result === 'resolved'
                      ? 'success'
                      : res.result === 'not_resolved'
                      ? 'danger'
                      : 'warning'
                  }
                  size="sm"
                >
                  {res.result.replace('_', ' ')}
                </Badge>
              </div>
            ))}
          </div>
        </CardFooter>
      )}
    </Card>
  )
}

