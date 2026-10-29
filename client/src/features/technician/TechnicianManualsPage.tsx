import React, { useState, useEffect } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { LoadingState } from '@/components/ui/LoadingState'
import { EmptyState } from '@/components/ui/EmptyState'
import { ErrorState } from '@/components/ui/ErrorState'
import { knowledgeService } from '@/services'
import type { KnowledgeDocument, DocumentCategory } from '@/types'
import { BookOpen, Upload, FileText, RefreshCw, CheckCircle2 } from 'lucide-react'

export const TechnicianManualsPage: React.FC = () => {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [docTitle, setDocTitle] = useState('')
  const [docCategory, setDocCategory] = useState<DocumentCategory>('TROUBLESHOOTING_GUIDE')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const loadData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const docs = await knowledgeService.getDocuments()
      setDocuments(docs)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve knowledge documents.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!docTitle.trim()) return

    setIsUploading(true)
    try {
      const formData = new FormData()
      formData.append('title', docTitle.trim())
      formData.append('category', docCategory)
      if (selectedFile) {
        formData.append('file', selectedFile)
      }
      await knowledgeService.uploadDocument(formData)
      setShowUploadModal(false)
      setDocTitle('')
      setSelectedFile(null)
    } catch (err) {
      alert('Upload failed: ' + (err instanceof Error ? err.message : 'Unknown error'))
    } finally {
      setIsUploading(false)
    }
  }

  const handleReindex = async (id: string) => {
    try {
      await knowledgeService.triggerReindex(id)
    } catch (err) {
      alert('Reindex request failed: ' + (err instanceof Error ? err.message : 'Unknown'))
    }
  }

  if (isLoading) {
    return <LoadingState message="Connecting to Campus AV Technical Manual Knowledge Base..." />
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadData} />
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="AV Equipment Service Manuals & SOPs"
        description="Vectorized technical manuals and diagnostic references powering ClassFix AI RAG suggestions."
        breadcrumbs={[
          { label: 'Home', href: '#' },
          { label: 'Technician', href: '/technician' },
          { label: 'Service Manuals' },
        ]}
        actions={
          <Button
            size="sm"
            variant="primary"
            leftIcon={<Upload className="w-3.5 h-3.5" />}
            onClick={() => setShowUploadModal(true)}
          >
            Upload SOP / Manual
          </Button>
        }
      />

      <Card className="border-warm-grey-200 shadow-subtle bg-white">
        <CardHeader className="bg-app-soft/40 border-b border-warm-grey-200">
          <CardTitle>Indexed Technical Documentation</CardTitle>
          <p className="text-xs text-charcoal-500 mt-0.5">
            Documents actively referenced during faculty troubleshooting workflows.
          </p>
        </CardHeader>
        <CardContent className="p-0">
          {documents.length === 0 ? (
            <EmptyState
              title="No documentation found"
              description="Upload manufacturer service manuals to enable AI citations."
            />
          ) : (
            <div className="divide-y divide-warm-grey-200">
              {documents.map((doc) => {
                const isIndexed = doc.status === 'INDEXED'
                const isProcessing = doc.status === 'PROCESSING'

                return (
                  <div
                    key={doc.id}
                    className="p-4 sm:p-5 hover:bg-app-soft/30 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-md bg-forest-50 text-forest-700 flex items-center justify-center shrink-0 mt-0.5">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div className="space-y-0.5">
                        <div className="font-bold text-charcoal-900 text-xs sm:text-sm">
                          {doc.title}
                        </div>
                        <div className="text-charcoal-500 text-[11px] font-mono">
                          {doc.fileName} &bull; {(doc.fileSizeBytes / (1024 * 1024)).toFixed(1)} MB
                        </div>
                        <div className="text-charcoal-400 text-[11px]">
                          Category: <span className="text-charcoal-700 font-medium">{doc.category.replace('_', ' ')}</span> &bull; {doc.chunkCount} vectorized chunks
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 shrink-0 pt-2 sm:pt-0">
                      <Badge
                        variant={isIndexed ? 'success' : isProcessing ? 'warning' : 'danger'}
                        size="sm"
                        dot
                      >
                        {doc.status}
                      </Badge>

                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleReindex(doc.id)}
                        disabled={isProcessing}
                        leftIcon={<RefreshCw className={`w-3 h-3 ${isProcessing ? 'animate-spin' : ''}`} />}
                      >
                        Reindex
                      </Button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-charcoal-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-lg shadow-elevated border border-warm-grey-300 max-w-md w-full p-6 animate-in zoom-in-95">
            <h3 className="font-bold text-base text-charcoal-900 mb-2">Upload Technical Document</h3>
            <p className="text-xs text-charcoal-500 mb-4">
              Upload a manufacturer manual or campus AV SOP to vectorize into the RAG diagnostic database.
            </p>

            <form onSubmit={handleUploadSubmit} className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">
                  Document Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Shure QLX-D Wireless Frequency Coordination SOP"
                  value={docTitle}
                  onChange={(e) => setDocTitle(e.target.value)}
                  className="w-full text-xs p-2 rounded border border-warm-grey-300 text-charcoal-900"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">
                  Category *
                </label>
                <select
                  value={docCategory}
                  onChange={(e) => setDocCategory(e.target.value as DocumentCategory)}
                  className="w-full text-xs p-2 rounded border border-warm-grey-300 text-charcoal-900 bg-white"
                >
                  <option value="TROUBLESHOOTING_GUIDE">TROUBLESHOOTING_GUIDE</option>
                  <option value="MANUAL">MANUAL</option>
                  <option value="CAMPUS_POLICY">CAMPUS_POLICY</option>
                  <option value="VENDOR_SPEC">VENDOR_SPEC</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">
                  Select PDF File
                </label>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="w-full text-xs p-1.5 rounded border border-warm-grey-300 text-charcoal-700 bg-white"
                />
              </div>

              <div className="pt-3 border-t border-warm-grey-200 flex justify-end gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowUploadModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  isLoading={isUploading}
                >
                  Upload & Vectorize
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

