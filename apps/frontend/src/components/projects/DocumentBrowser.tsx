'use client'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Folder, FolderOpen, FileText, ChevronRight, ChevronDown,
  RefreshCw, ArrowLeft
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { clsx } from 'clsx'

interface FsItem {
  name: string; path: string; type: 'file' | 'folder'; ext?: string
  children?: number; size?: number; modified?: number
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function FolderNode({ projectId, item, onFileSelect, depth = 0 }: {
  projectId: string; item: FsItem
  onFileSelect: (path: string, name: string) => void; depth?: number
}) {
  const [open, setOpen] = useState(depth === 0)
  const relFolder = item.path.replace(`my-projects/${projectId}/`, '')
  const { data } = useQuery<{ items: FsItem[] }>({
    queryKey: ['project-files', projectId, relFolder],
    queryFn: () => fetch(`/api/projects/${projectId}/files?folder=${encodeURIComponent(relFolder)}`).then(r => r.json()),
    enabled: open,
  })
  const children = data?.items || []

  return (
    <div>
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-2 w-full px-2 py-1.5 rounded hover:bg-gray-800 transition text-left group"
        style={{ paddingLeft: `${8 + depth * 16}px` }}
      >
        {open ? <ChevronDown className="w-3.5 h-3.5 text-gray-500 shrink-0" /> : <ChevronRight className="w-3.5 h-3.5 text-gray-500 shrink-0" />}
        {open ? <FolderOpen className="w-4 h-4 text-yellow-400 shrink-0" /> : <Folder className="w-4 h-4 text-yellow-500 shrink-0" />}
        <span className="text-sm text-gray-200 truncate">{item.name}</span>
        {item.children !== undefined && (
          <span className="text-xs text-gray-600 ml-auto">{item.children}</span>
        )}
      </button>
      {open && children.map(child =>
        child.type === 'folder' ? (
          <FolderNode key={child.path} projectId={projectId} item={child}
            onFileSelect={onFileSelect} depth={depth + 1} />
        ) : (
          <FileRow key={child.path} item={child}
            onSelect={() => onFileSelect(child.path, child.name)} depth={depth + 1} />
        )
      )}
    </div>
  )
}

function FileRow({ item, onSelect, depth = 0 }: {
  item: FsItem; onSelect: () => void; depth?: number
}) {
  const isMd = item.ext === '.md'
  return (
    <button
      onClick={onSelect}
      className="flex items-center gap-2 w-full px-2 py-1.5 rounded hover:bg-gray-800 transition text-left"
      style={{ paddingLeft: `${8 + depth * 16}px` }}
    >
      <FileText className={clsx('w-4 h-4 shrink-0', isMd ? 'text-blue-400' : 'text-gray-500')} />
      <span className={clsx('text-sm truncate', isMd ? 'text-gray-200' : 'text-gray-400')}>{item.name}</span>
      {item.size !== undefined && (
        <span className="text-xs text-gray-700 ml-auto shrink-0">{formatSize(item.size)}</span>
      )}
    </button>
  )
}

function DocViewer({ path, onClose }: { path: string; onClose: () => void }) {
  const filename = path.split('/').pop() || path
  const { data, isLoading, refetch } = useQuery<{ content: string }>({
    queryKey: ['doc', path],
    queryFn: () => fetch(`/api/documents/read?path=${encodeURIComponent(path)}`).then(r => r.json()),
    retry: false,
  })

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-800 shrink-0">
        <button onClick={onClose} className="p-1 text-gray-500 hover:text-white transition">
          <ArrowLeft className="w-4 h-4" />
        </button>
        <FileText className="w-4 h-4 text-blue-400 shrink-0" />
        <span className="text-sm font-medium text-gray-200 truncate flex-1">{filename}</span>
        <button onClick={() => refetch()} className="p-1 text-gray-600 hover:text-white transition">
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>
      <div className="flex-1 overflow-auto p-4">
        {isLoading && <p className="text-sm text-gray-500">Loading...</p>}
        {data?.content && (
          <div className="prose prose-invert prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{data.content}</ReactMarkdown>
          </div>
        )}
        {!isLoading && !data?.content && (
          <p className="text-sm text-gray-600">Could not load file content.</p>
        )}
      </div>
    </div>
  )
}

export function DocumentBrowser({
  projectId,
  onFileSelect: externalOnFileSelect,
}: {
  projectId: string
  onFileSelect?: (path: string, content: string) => void
}) {
  const { data: rootData } = useQuery<{ items: FsItem[] }>({
    queryKey: ['project-files', projectId, ''],
    queryFn: () => fetch(`/api/projects/${projectId}/files`).then(r => r.json()),
  })

  const rootItems = rootData?.items || []
  const folders = rootItems.filter(i => i.type === 'folder')
  const files = rootItems.filter(i => i.type === 'file')

  const handleFileSelect = async (path: string, name: string) => {
    if (externalOnFileSelect) {
      // Show in right panel
      const r = await fetch(`/api/documents/read?path=${encodeURIComponent(path)}`)
      const d = await r.json()
      externalOnFileSelect(path, d.content || '')
    }
  }

  return (
    <div className="w-full overflow-y-auto py-2">
      {folders.map(item => (
        <FolderNode key={item.path} projectId={projectId} item={item}
          onFileSelect={handleFileSelect} depth={0} />
      ))}
      {files.map(item => (
        <FileRow key={item.path} item={item}
          onSelect={() => handleFileSelect(item.path, item.name)} depth={0} />
      ))}
      {rootItems.length === 0 && (
        <p className="text-sm text-gray-600 px-4 py-8 text-center">No documents yet</p>
      )}
    </div>
  )
}
