import type { KnowledgeDocument, DocumentCategory } from '@/types'

export interface IKnowledgeService {
  getDocuments(category?: DocumentCategory): Promise<KnowledgeDocument[]>
  getDocumentById(id: string): Promise<KnowledgeDocument | null>
  uploadDocument(formData: FormData): Promise<KnowledgeDocument>
  triggerReindex(id: string): Promise<KnowledgeDocument>
}
