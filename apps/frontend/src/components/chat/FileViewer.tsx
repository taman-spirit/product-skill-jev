'use client'
import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { FileText, RefreshCw, X } from 'lucide-react'

interface Props {
  path: string | null
  onClose?: () => void
}

export function FileViewer({ path, onClose }: Props) {
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!path) return
    setLoading(true)
    setError('')
    fetch(`/api/documents/read?path=${encodeURIComponent(path)}`)
      .then(r => r.json())
      .then(d => { setContent(d.content || ''); setLoading(false) })
      .catch(() => { setError('Failed to load file'); setLoading(false) })
  }, [path])

  if (!path) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-600">
        <FileText className="w-12 h-12 mb-3 opacity-30" />
        <p className="text-sm">File content appears here when the AI reads or writes a file</p>
      </div>
    )
  }

  const filename = path.split('/').pop() || path

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800 shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          <FileText className="w-4 h-4 text-gray-400 shrink-0" />
          <span className="text-sm font-medium text-gray-200 truncate">{filename}</span>
          <span className="text-xs text-gray-600 truncate hidden lg:block">{path}</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => { setContent(''); setLoading(true); fetch(`/api/documents/read?path=${encodeURIComponent(path)}`).then(r=>r.json()).then(d=>{setContent(d.content||'');setLoading(false)}) }}
            className="p-1 text-gray-500 hover:text-white transition"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          {onClose && (
            <button onClick={onClose} className="p-1 text-gray-500 hover:text-white transition">
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        {loading && (
          <div className="flex items-center gap-2 text-gray-500 text-sm">
            <RefreshCw className="w-4 h-4 animate-spin" /> Loading...
          </div>
        )}
        {error && <p className="text-red-400 text-sm">{error}</p>}
        {!loading && !error && content && (
          <div className="prose prose-invert prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}
