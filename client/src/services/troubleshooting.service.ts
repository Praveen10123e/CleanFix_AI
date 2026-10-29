import type {
  TroubleshootingSession,
  StartSessionRequest,
  DiagnosticStep,
  StepResultRequest,
  StepResultResponse,
  CompleteSessionResponse,
  CreateComplaintFromSessionRequest,
  Complaint,
} from '@/types'

export interface ITroubleshootingService {
  /**
   * POST /troubleshooting/sessions
   * Creates an interactive troubleshooting session for a specific device and symptom
   */
  startSession(payload: StartSessionRequest): Promise<TroubleshootingSession>

  /**
   * POST /troubleshooting/sessions/{id}/steps/next
   * Requests the next diagnostic step from the backend
   */
  getNextStep(sessionId: string): Promise<DiagnosticStep | null>

  /**
   * POST /troubleshooting/sessions/{id}/steps/{step_id}/result
   * Submits the Faculty's observation / result for the active step
   */
  submitStepResult(
    sessionId: string,
    stepId: string,
    payload: StepResultRequest
  ): Promise<StepResultResponse>

  /**
   * POST /troubleshooting/sessions/{id}/complete
   * Explicitly concludes a resolved troubleshooting session
   */
  completeSession(sessionId: string): Promise<CompleteSessionResponse>

  /**
   * POST /troubleshooting/sessions/{id}/complaint
   * Escalates the unresolved session to a campus field technician ticket
   */
  createComplaintFromSession(
    sessionId: string,
    payload: CreateComplaintFromSessionRequest
  ): Promise<Complaint>

  /**
   * GET /troubleshooting/sessions/{id}
   * Retrieves active session details and previous step history
   */
  getSessionById(sessionId: string): Promise<TroubleshootingSession | null>
}
