import type { AdminOverviewStats, AdminReportsSummary, User, UserRole, CreateUserDTO, UpdateUserDTO } from '@/types'

export interface IAdminService {
  getOverviewStats(): Promise<AdminOverviewStats>
  getReportsSummary(): Promise<AdminReportsSummary>
  getUsers(role?: UserRole): Promise<User[]>
  createUser(dto: CreateUserDTO): Promise<User>
  updateUser(userId: string, dto: UpdateUserDTO): Promise<User>
  updateUserRole(userId: string, newRole: UserRole): Promise<User>
}
