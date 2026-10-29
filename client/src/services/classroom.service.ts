import type { Classroom, ClassroomFilter, Device, CreateClassroomDTO, UpdateClassroomDTO } from '@/types'

export interface IClassroomService {
  getClassrooms(filter?: ClassroomFilter): Promise<Classroom[]>
  getClassroomById(id: string): Promise<Classroom | null>
  getClassroomDevices(classroomId: string): Promise<Device[]>
  createClassroom(dto: CreateClassroomDTO): Promise<Classroom>
  updateClassroom(id: string, dto: UpdateClassroomDTO): Promise<Classroom>
}
