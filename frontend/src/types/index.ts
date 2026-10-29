/**
 * ClassFix AI — Central TypeScript Domain Definitions
 * University AV Operations & Smart Classroom Troubleshooting Assistant
 */

// User and Auth Types
export type UserRole = 'faculty' | 'technician' | 'admin'

export interface User {
  id: string // UUID
  name: string
  email: string
  role: UserRole
  department?: string
  avatarUrl?: string
  phone?: string
  createdAt: string // ISO 8601
}

export interface CreateUserDTO {
  name: string
  email: string
  role: UserRole
  department?: string
  phone?: string
}

export interface UpdateUserDTO {
  name?: string
  email?: string
  role?: UserRole
  department?: string
  phone?: string
}

// Classroom Types
export type ClassroomStatus = 'OPERATIONAL' | 'DEGRADED' | 'OUT_OF_SERVICE'

export interface Classroom {
  id: string // UUID
  roomNumber: string
  building: string
  floor: number
  capacity: number
  status: ClassroomStatus
  features: string[]
  activeTicketsCount: number
  createdAt: string // ISO 8601
  updatedAt: string // ISO 8601
}

export interface CreateClassroomDTO {
  roomNumber: string
  building: string
  floor: number
  capacity: number
  status?: ClassroomStatus
  features?: string[]
}

export interface UpdateClassroomDTO {
  roomNumber?: string
  building?: string
  floor?: number
  capacity?: number
  status?: ClassroomStatus
  features?: string[]
}

// Device Types
export type DeviceType =
  | 'PROJECTOR'
  | 'MICROPHONE'
  | 'SMART_BOARD'
  | 'AUDIO_AMPLIFIER'
  | 'DOCUMENT_CAMERA'
  | 'HDMI_SWITCHER'

export type DeviceStatus = 'ONLINE' | 'OFFLINE' | 'WARNING' | 'MAINTENANCE'

export interface Device {
  id: string // UUID
  name: string
  brand: string // Brand name e.g. "Epson", "Shure", "ViewSonic"
  type: DeviceType
  classroomId: string // UUID
  classroomName: string
  serialNumber: string
  model: string
  status: DeviceStatus
  ipAddress?: string
  lastPingAt: string // ISO 8601
  installedAt: string // ISO 8601
}

export interface CreateDeviceDTO {
  name: string
  brand: string
  model: string
  type: DeviceType
  classroomId: string
  serialNumber: string
  ipAddress?: string
  status?: DeviceStatus
}

export interface UpdateDeviceDTO {
  name?: string
  brand?: string
  model?: string
  type?: DeviceType
  serialNumber?: string
  ipAddress?: string
  status?: DeviceStatus
}

// Complaint / Incident Types
export type ComplaintSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export type ComplaintStatus =
  | 'PENDING'
  | 'IN_PROGRESS'
  | 'RESOLVED'
  | 'ESCALATED'
  | 'CLOSED'

export type ComplaintCategory =
  | 'DISPLAY'
  | 'AUDIO'
  | 'CONNECTIVITY'
  | 'POWER'
  | 'SOFTWARE'
  | 'OTHER'

export interface Complaint {
  id: string // UUID
  ticketNumber: string // e.g., "CF-2026-1042"
  classroomId: string // UUID
  classroomName: string
  deviceId?: string // UUID
  deviceName?: string
  deviceBrand?: string
  deviceModel?: string
  reportedByUserId: string // UUID
  reportedByName: string
  assignedToUserId?: string // UUID
  assignedToName?: string
  title: string
  description: string
  severity: ComplaintSeverity
  status: ComplaintStatus
  category: ComplaintCategory
  aiSuggestedAction?: string
  confirmedCause?: string
  repairAction?: string
  resolutionNotes?: string
  troubleshootingSessionId?: string
  createdAt: string // ISO 8601
  updatedAt: string // ISO 8601
  resolvedAt?: string // ISO 8601
}

export interface CreateComplaintDTO {
  classroomId: string
  deviceId?: string
  title: string
  description: string
  severity: ComplaintSeverity
  category: ComplaintCategory
}

export interface ComplaintResolutionRequest {
  confirmed_cause: string
  repair_action: string
  resolution_notes: string
}

export interface ComplaintAssignmentRequest {
  technician_id: string
  technician_name?: string
}

// ==========================================
// Troubleshooting Contract Schemas
// ==========================================

export interface StartSessionRequest {
  device_id: string
  symptom_text: string
}

export type StepResultType = 'resolved' | 'not_resolved' | 'unknown' | 'unable_to_perform'

export interface StepResultRequest {
  result: StepResultType
  result_note?: string
}

export interface QuestionChoice {
  id: string
  label: string
}

export interface DiagnosticQuestion {
  text: string
  input_type: 'choice' | 'boolean' | 'text'
  choices?: QuestionChoice[]
}

export interface DiagnosticStep {
  step_id: string
  session_id: string
  step_number: number
  total_steps_estimate?: number
  instruction: string
  reason: string
  expected_observation: string
  source_manual?: string
  source_section?: string
  source_page?: number
  question?: DiagnosticQuestion
  is_final_step?: boolean
  recommended_escalation?: boolean
}

export interface StepResultResponse {
  step_id: string
  result: StepResultType
  result_note?: string
  session_status: 'active' | 'resolved' | 'unresolved' | 'escalated' | 'completed'
  can_escalate: boolean
  is_resolved: boolean
  message?: string
}

export interface CompleteSessionResponse {
  session_id: string
  status: 'completed'
  outcome: 'resolved' | 'unresolved' | 'escalated'
  completed_at: string
}

export interface CreateComplaintFromSessionRequest {
  description: string
  preferred_technician_id?: string | null
}

export interface TroubleshootingSession {
  id: string // UUID
  device_id: string
  classroom_id: string
  classroom_name: string
  device_name: string
  device_brand: string
  device_model: string
  symptom_text: string
  status: 'active' | 'resolved' | 'unresolved' | 'escalated' | 'completed'
  current_step_number: number
  current_step?: DiagnosticStep | null
  submitted_results: Array<{
    step_id: string
    step_number: number
    instruction: string
    result: StepResultType
    result_note?: string
    timestamp: string
  }>
  complaint_id?: string
  created_at: string
  updated_at: string
  completed_at?: string
}

// Knowledge Base & RAG Documents
export type DocumentCategory =
  | 'MANUAL'
  | 'TROUBLESHOOTING_GUIDE'
  | 'CAMPUS_POLICY'
  | 'VENDOR_SPEC'

export type DocumentStatus = 'INDEXED' | 'PROCESSING' | 'FAILED' | 'PENDING'

export interface KnowledgeDocument {
  id: string // UUID
  title: string
  fileName: string
  fileSizeBytes: number
  fileType: string
  category: DocumentCategory
  status: DocumentStatus
  chunkCount: number
  vectorCount: number
  uploadedBy: string
  uploadedAt: string // ISO 8601
  updatedAt: string // ISO 8601
  errorMessage?: string
}

// Admin Overview & Telemetry Metrics
export interface AdminOverviewStats {
  totalClassrooms: number
  operationalClassrooms: number
  totalDevices: number
  onlineDevices: number
  activeTickets: number
  criticalTickets: number
  resolvedTodayCount: number
  avgResolutionTimeMinutes: number
  knowledgeDocumentsCount: number
  indexedChunksCount: number
}

export interface AdminReportsSummary {
  totalClassrooms: number
  operationalClassrooms: number
  totalDevices: number
  onlineDevices: number
  activeTickets: number
  criticalTickets: number
  resolvedTodayCount: number
  avgResolutionTimeMinutes: number
  ticketsByCategory: Record<ComplaintCategory, number>
  ticketsBySeverity: Record<ComplaintSeverity, number>
  systemUptimePercentage: number
}

// Filter Options
export interface ComplaintFilter {
  status?: ComplaintStatus
  severity?: ComplaintSeverity
  classroomId?: string
  assignedToUserId?: string
  search?: string
}

export interface ClassroomFilter {
  building?: string
  status?: ClassroomStatus
  search?: string
}

// Standard API Response Wrapper
export interface ApiResponse<T> {
  data: T
  meta?: {
    limit: number
    offset: number
    total: number
  }
  error?: {
    code: string
    message: string
    details?: unknown
  }
}
