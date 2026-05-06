/**
 * AttachmentSidebar — shows project-level file attachments in a sidebar panel
 * next to the task list in ProjectDetailPage.
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Paperclip } from 'lucide-react'
import { attachmentsApi } from '../api/client'
import AttachmentList, { AttachmentItem } from './AttachmentList'
import FileUploadDropzone from './FileUploadDropzone'

interface Props {
  projectId: number
}

export default function AttachmentSidebar({ projectId }: Props) {
  const qc = useQueryClient()
  const [uploadError, setUploadError] = useState('')

  const { data: attachments = [], isLoading } = useQuery<AttachmentItem[]>({
    queryKey: ['project-attachments', projectId],
    queryFn: () => attachmentsApi.listProject(projectId).then(r => r.data),
    staleTime: 30_000,
  })

  const uploadMutation = useMutation({
    mutationFn: ({ file, visibility }: { file: File; visibility: 'team' | 'managers' | 'private' }) =>
      attachmentsApi.uploadProject(projectId, file, visibility),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['project-attachments', projectId] })
      setUploadError('')
    },
    onError: (e: any) => setUploadError(e.response?.data?.detail ?? 'Chyba pri nahrávaní'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => attachmentsApi.deleteProject(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['project-attachments', projectId] }),
  })

  const visibilityMutation = useMutation({
    mutationFn: ({ id, visibility }: { id: number; visibility: 'team' | 'managers' | 'private' }) =>
      attachmentsApi.updateProjectVisibility(id, visibility),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['project-attachments', projectId] }),
  })

  return (
    <div className="w-64 flex-shrink-0 border-l border-gray-100 dark:border-gray-800 pl-4 space-y-3">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Paperclip size={14} className="text-gray-400" />
        <span className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">
          Prílohy projektu
        </span>
        {attachments.length > 0 && (
          <span className="text-xs text-gray-400">({attachments.length})</span>
        )}
      </div>

      {/* File list */}
      {isLoading ? (
        <p className="text-xs text-gray-400">Načítavam…</p>
      ) : (
        <AttachmentList
          attachments={attachments}
          onDelete={id => deleteMutation.mutate(id)}
          onVisibilityChange={(id, v) => visibilityMutation.mutate({ id, visibility: v })}
        />
      )}

      {/* Upload */}
      <FileUploadDropzone
        onUpload={(file, visibility) => uploadMutation.mutateAsync({ file, visibility }).then(() => {})}
        uploading={uploadMutation.isPending}
        error={uploadError}
      />
    </div>
  )
}
