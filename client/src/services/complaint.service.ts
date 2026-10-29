import type {
  Complaint,
  ComplaintFilter,
  ComplaintStatus,
  CreateComplaintDTO,
  ComplaintResolutionRequest,
} from '@/types'

export interface IComplaintService {
  getComplaints(filter?: ComplaintFilter): Promise<Complaint[]>
  getComplaintById(id: string): Promise<Complaint | null>
  createComplaint(dto: CreateComplaintDTO, reporter: { id: string; name: string }): Promise<Complaint>
  updateStatus(id: string, status: ComplaintStatus): Promise<Complaint>
  assignTo(id: string, technicianId: string, technicianName?: string): Promise<Complaint>
  resolveComplaint(id: string, resolution: ComplaintResolutionRequest): Promise<Complaint>
}
