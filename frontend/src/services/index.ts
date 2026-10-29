import type { IAuthService } from './auth.service'
import type { IClassroomService } from './classroom.service'
import type { IDeviceService } from './device.service'
import type { IComplaintService } from './complaint.service'
import type { ITroubleshootingService } from './troubleshooting.service'
import type { IKnowledgeService } from './knowledge.service'
import type { IAdminService } from './admin.service'
import type {
  Classroom,
  ClassroomFilter,
  CreateClassroomDTO,
  UpdateClassroomDTO,
  Device,
  DeviceStatus,
  CreateDeviceDTO,
  UpdateDeviceDTO,
  Complaint,
  ComplaintFilter,
  ComplaintStatus,
  CreateComplaintDTO,
  ComplaintResolutionRequest,
  TroubleshootingSession,
  StartSessionRequest,
  DiagnosticStep,
  StepResultRequest,
  StepResultResponse,
  CompleteSessionResponse,
  CreateComplaintFromSessionRequest,
  KnowledgeDocument,
  DocumentCategory,
  User,
  UserRole,
  CreateUserDTO,
  UpdateUserDTO,
  AdminOverviewStats,
  AdminReportsSummary,
} from '@/types'

import { apiClient, ApiError } from './api/client'

// ==========================================
// Real Backend API Service Implementations
// ==========================================

class RealAuthService implements IAuthService {
  async getCurrentUser(): Promise<User | null> {
    try {
      const user = await apiClient.get<User>('/auth/me')
      return user
    } catch (err) {
      if (err instanceof ApiError && (err.statusCode === 401 || err.statusCode === 403)) {
        if (typeof window !== 'undefined') {
          sessionStorage.removeItem('classfix_auth_token')
        }
        return null
      }
      throw err
    }
  }

  async loginWithGoogle(credential: string): Promise<User> {
    if (!credential || !credential.trim()) {
      throw new ApiError(400, 'A valid Google ID token is required for authentication.', 'INVALID_CREDENTIAL')
    }

    const payload = {
      token: credential.trim(),
      id_token: credential.trim(),
      credential: credential.trim(),
    }

    // Call POST /auth/google
    // Backend verifies token against Google & checks user provisioned in database
    const res = await apiClient.post<Record<string, unknown>>('/auth/google', payload)

    // Store returned auth token if provided
    const token =
      (res?.access_token as string) ||
      (res?.token as string) ||
      (res?.session_token as string) ||
      (res?.jwt as string) ||
      credential.trim()

    if (token && typeof window !== 'undefined') {
      sessionStorage.setItem('classfix_auth_token', token)
    }

    // Extract user from response payload or verify via GET /auth/me
    let user: User | null = null
    if (res?.user && typeof res.user === 'object' && 'role' in (res.user as object)) {
      user = res.user as User
    } else if (res?.id && res?.role) {
      user = res as unknown as User
    } else {
      user = await this.getCurrentUser()
    }

    if (!user || !user.role) {
      if (typeof window !== 'undefined') {
        sessionStorage.removeItem('classfix_auth_token')
      }
      throw new ApiError(
        403,
        'User account is not provisioned or active in the campus database.',
        'UNAUTHORIZED_USER'
      )
    }

    return user
  }

  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout')
    } catch {
      // Non-fatal if backend logout is cookie/token based
    } finally {
      if (typeof window !== 'undefined') {
        sessionStorage.removeItem('classfix_auth_token')
      }
    }
  }
}

class RealClassroomService implements IClassroomService {
  async getClassrooms(filter?: ClassroomFilter): Promise<Classroom[]> {
    return apiClient.get<Classroom[]>('/classrooms', filter as Record<string, string | number | boolean | undefined>)
  }

  async getClassroomById(id: string): Promise<Classroom | null> {
    return apiClient.get<Classroom | null>(`/classrooms/${id}`)
  }

  async getClassroomDevices(classroomId: string): Promise<Device[]> {
    return apiClient.get<Device[]>(`/classrooms/${classroomId}/devices`)
  }

  async createClassroom(dto: CreateClassroomDTO): Promise<Classroom> {
    return apiClient.post<Classroom>('/classrooms', dto)
  }

  async updateClassroom(id: string, dto: UpdateClassroomDTO): Promise<Classroom> {
    return apiClient.patch<Classroom>(`/classrooms/${id}`, dto)
  }
}

class RealDeviceService implements IDeviceService {
  async getDevices(classroomId?: string): Promise<Device[]> {
    if (classroomId) {
      return apiClient.get<Device[]>(`/classrooms/${classroomId}/devices`)
    }
    return apiClient.get<Device[]>('/devices')
  }

  async getDeviceById(id: string): Promise<Device | null> {
    return apiClient.get<Device | null>(`/devices/${id}`)
  }

  async createDevice(dto: CreateDeviceDTO): Promise<Device> {
    return apiClient.post<Device>('/devices', dto)
  }

  async updateDevice(id: string, dto: UpdateDeviceDTO): Promise<Device> {
    return apiClient.patch<Device>(`/devices/${id}`, dto)
  }

  async updateDeviceStatus(id: string, status: DeviceStatus): Promise<Device> {
    return apiClient.patch<Device>(`/devices/${id}/status`, { status })
  }
}

class RealComplaintService implements IComplaintService {
  async getComplaints(filter?: ComplaintFilter): Promise<Complaint[]> {
    return apiClient.get<Complaint[]>('/complaints', filter as Record<string, string | number | boolean | undefined>)
  }

  async getComplaintById(id: string): Promise<Complaint | null> {
    return apiClient.get<Complaint | null>(`/complaints/${id}`)
  }

  async createComplaint(dto: CreateComplaintDTO, reporter: { id: string; name: string }): Promise<Complaint> {
    return apiClient.post<Complaint>('/complaints', { ...dto, reporter })
  }

  async updateStatus(id: string, status: ComplaintStatus): Promise<Complaint> {
    return apiClient.patch<Complaint>(`/complaints/${id}/status`, { status })
  }

  async assignTo(id: string, technicianId: string, technicianName?: string): Promise<Complaint> {
    return apiClient.patch<Complaint>(`/complaints/${id}/assignment`, {
      technician_id: technicianId,
      technician_name: technicianName,
    })
  }

  async resolveComplaint(id: string, resolution: ComplaintResolutionRequest): Promise<Complaint> {
    return apiClient.post<Complaint>(`/complaints/${id}/resolution`, resolution)
  }
}

class RealTroubleshootingService implements ITroubleshootingService {
  async startSession(payload: StartSessionRequest): Promise<TroubleshootingSession> {
    return apiClient.post<TroubleshootingSession>('/troubleshooting/sessions', payload)
  }

  async getNextStep(sessionId: string): Promise<DiagnosticStep | null> {
    return apiClient.post<DiagnosticStep | null>(`/troubleshooting/sessions/${sessionId}/steps/next`)
  }

  async submitStepResult(
    sessionId: string,
    stepId: string,
    payload: StepResultRequest
  ): Promise<StepResultResponse> {
    return apiClient.post<StepResultResponse>(
      `/troubleshooting/sessions/${sessionId}/steps/${stepId}/result`,
      payload
    )
  }

  async completeSession(sessionId: string): Promise<CompleteSessionResponse> {
    return apiClient.post<CompleteSessionResponse>(`/troubleshooting/sessions/${sessionId}/complete`)
  }

  async createComplaintFromSession(
    sessionId: string,
    payload: CreateComplaintFromSessionRequest
  ): Promise<Complaint> {
    return apiClient.post<Complaint>(`/troubleshooting/sessions/${sessionId}/complaint`, payload)
  }

  async getSessionById(sessionId: string): Promise<TroubleshootingSession | null> {
    return apiClient.get<TroubleshootingSession | null>(`/troubleshooting/sessions/${sessionId}`)
  }
}

class RealKnowledgeService implements IKnowledgeService {
  async getDocuments(category?: DocumentCategory): Promise<KnowledgeDocument[]> {
    return apiClient.get<KnowledgeDocument[]>('/knowledge/documents', { category })
  }

  async getDocumentById(id: string): Promise<KnowledgeDocument | null> {
    return apiClient.get<KnowledgeDocument | null>(`/knowledge/documents/${id}`)
  }

  async uploadDocument(formData: FormData): Promise<KnowledgeDocument> {
    return apiClient.postFormData<KnowledgeDocument>('/knowledge/documents', formData)
  }

  async triggerReindex(id: string): Promise<KnowledgeDocument> {
    return apiClient.post<KnowledgeDocument>(`/knowledge/documents/${id}/reindex`)
  }
}

class RealAdminService implements IAdminService {
  async getOverviewStats(): Promise<AdminOverviewStats> {
    return apiClient.get<AdminOverviewStats>('/admin/overview')
  }

  async getReportsSummary(): Promise<AdminReportsSummary> {
    return apiClient.get<AdminReportsSummary>('/admin/reports/summary')
  }

  async getUsers(role?: UserRole): Promise<User[]> {
    return apiClient.get<User[]>('/admin/users', { role })
  }

  async createUser(dto: CreateUserDTO): Promise<User> {
    return apiClient.post<User>('/admin/users', dto)
  }

  async updateUser(userId: string, dto: UpdateUserDTO): Promise<User> {
    return apiClient.patch<User>(`/admin/users/${userId}`, dto)
  }

  async updateUserRole(userId: string, newRole: UserRole): Promise<User> {
    return apiClient.patch<User>(`/admin/users/${userId}/role`, { role: newRole })
  }
}

// Single production instances communicating directly with real backend
export const authService: IAuthService = new RealAuthService()
export const classroomService: IClassroomService = new RealClassroomService()
export const deviceService: IDeviceService = new RealDeviceService()
export const complaintService: IComplaintService = new RealComplaintService()
export const troubleshootingService: ITroubleshootingService = new RealTroubleshootingService()
export const knowledgeService: IKnowledgeService = new RealKnowledgeService()
export const adminService: IAdminService = new RealAdminService()

export { apiClient, ApiError } from './api/client'
export { API_CONFIG } from './api/config'
export type { IAuthService } from './auth.service'
export type { IClassroomService } from './classroom.service'
export type { IDeviceService } from './device.service'
export type { IComplaintService } from './complaint.service'
export type { ITroubleshootingService } from './troubleshooting.service'
export type { IKnowledgeService } from './knowledge.service'
export type { IAdminService } from './admin.service'
