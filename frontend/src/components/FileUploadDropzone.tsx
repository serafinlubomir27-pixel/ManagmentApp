/**
 * FileUploadDropzone — drag & drop file upload with visibility selector.
 * Calls onUpload(file, visibility) when user submits.
 */
import { useState, useRef, DragEvent } from 'react'
import { Upload, X } from 'lucide-react'
import VisibilitySelector from './VisibilitySelector'

interface Props {
  onUpload: (file: File, visibility: 'team' | 'managers' | 'private') => Promise<void>
  uploading?: boolean
  error?: string
}

export default function FileUploadDropzone({ onUpload, uploading, error }: Props) {
  const [dragOver, setDragOver] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [visibility, setVisibility] = useState<'team' | 'managers' | 'private'>('team')
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) setSelectedFile(file)
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) setSelectedFile(file)
  }

  const handleSubmit = async () => {
    if (!selectedFile) return
    await onUpload(selectedFile, visibility)
    setSelectedFile(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div className="space-y-2">
      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-colors ${
          dragOver
            ? 'border-brand-400 bg-brand-50 dark:bg-brand-900/10'
            : 'border-gray-200 dark:border-gray-700 hover:border-brand-300 dark:hover:border-brand-600'
        }`}
      >
        <input ref={inputRef} type="file" className="hidden" onChange={handleFileChange} />
        <Upload size={18} className="mx-auto mb-1 text-gray-400" />
        {selectedFile ? (
          <p className="text-xs text-gray-700 dark:text-gray-300 font-medium">{selectedFile.name}</p>
        ) : (
          <p className="text-xs text-gray-400">Pretiahni súbor alebo klikni</p>
        )}
      </div>

      {/* Visibility + submit */}
      {selectedFile && (
        <div className="space-y-2">
          <div>
            <p className="text-xs text-gray-500 mb-1">Kto vidí súbor:</p>
            <VisibilitySelector value={visibility} onChange={setVisibility} />
          </div>
          {error && <p className="text-xs text-red-500">{error}</p>}
          <div className="flex gap-2">
            <button
              onClick={handleSubmit}
              disabled={uploading}
              className="btn-primary text-xs py-1 px-3"
            >
              {uploading ? 'Nahrávam…' : 'Nahrať'}
            </button>
            <button
              onClick={() => { setSelectedFile(null); if (inputRef.current) inputRef.current.value = '' }}
              className="btn-ghost text-xs py-1 px-3"
            >
              <X size={12} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
