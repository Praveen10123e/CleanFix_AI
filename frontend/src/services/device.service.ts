import type { Device, DeviceStatus, CreateDeviceDTO, UpdateDeviceDTO } from '@/types'

export interface IDeviceService {
  getDevices(classroomId?: string): Promise<Device[]>
  getDeviceById(id: string): Promise<Device | null>
  createDevice(dto: CreateDeviceDTO): Promise<Device>
  updateDevice(id: string, dto: UpdateDeviceDTO): Promise<Device>
  updateDeviceStatus(id: string, status: DeviceStatus): Promise<Device>
}
