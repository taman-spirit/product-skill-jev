'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { FolderOpen, Plus, Trash2, AlertCircle, CheckCircle, Clock } from 'lucide-react'

interface Project {
  id: string; name: string; status: string; priority: string
  product: string; pm: string; target_end: string
  health: { fr_count: number; prd_count: number; open_crs: number }
}

const STATUS_COLOR: Record<string, string> = {
  active: 'text-green-400 bg-green-400/10',
  planning: 'text-blue-400 bg-blue-400/10',
  'on-hold': 'text-yellow-400 bg-yellow-400/10',
  completed: 'text-gray-400 bg-gray-400/10',
}
const STATUS_ICON: Record<string, React.ReactNode> = {
  active: <CheckCircle className="w-3 h-3" />,
  planning: <Clock className="w-3 h-3" />,
  'on-hold': <AlertCircle className="w-3 h-3" />,
}

export default function ProjectsPage() {
  const router = useRouter()
  const qc = useQueryClient()
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)

  const { data, isLoading } = useQuery<{ projects: Project[] }>({
    queryKey: ['projects'],
    queryFn: async () => {
      const d = await fetch('/api/projects').then(r => r.json())
      // Auto-activate if only one project
      if (d.projects?.length === 1) {
        fetch(`/api/projects/${d.projects[0].id}/activate`, { method: 'POST' }).catch(() => {})
      }
      return d
    },
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => fetch(`/api/projects/${id}`, { method: 'DELETE' }).then(r => r.json()),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['projects'] }); setConfirmDelete(null) },
  })

  const projects = data?.projects || []

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <div>
          <h1 className="text-lg font-semibold">Projects</h1>
          <p className="text-sm text-gray-500">{projects.length} project{projects.length !== 1 ? 's' : ''}</p>
        </div>
        <button
          onClick={() => router.push('/chat')}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-500 transition"
        >
          <Plus className="w-4 h-4" /> New Project
        </button>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto p-6">
        {isLoading && <p className="text-gray-500 text-sm">Loading projects...</p>}
        {!isLoading && !projects.length && !data && (
          <p className="text-sm text-amber-400 bg-amber-900/20 border border-amber-800 rounded-lg px-4 py-3">
            Could not load projects. Please check that the workspace is configured correctly.
          </p>
        )}
        {!isLoading && projects.length === 0 && (
          <div className="flex flex-col items-center justify-center h-64 text-gray-600">
            <FolderOpen className="w-12 h-12 mb-3 opacity-30" />
            <p className="text-sm mb-4">No projects yet</p>
            <button onClick={() => router.push('/chat')}
              className="px-4 py-2 bg-gray-800 text-gray-300 text-sm rounded-lg hover:bg-gray-700 transition">
              Create your first project
            </button>
          </div>
        )}
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {projects.map(p => (
            <div key={p.id} className="group bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-gray-700 transition cursor-pointer"
              onClick={() => router.push(`/projects/${p.id}`)}>
              <div className="flex items-start justify-between mb-3">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-white truncate">{p.name}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{p.id}</p>
                </div>
                <button
                  onClick={e => { e.stopPropagation(); setConfirmDelete(p.id) }}
                  className="opacity-0 group-hover:opacity-100 p-1 text-gray-600 hover:text-red-400 transition ml-2"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              <div className="flex items-center gap-2 mb-3">
                <span className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLOR[p.status] || 'text-gray-400 bg-gray-800'}`}>
                  {STATUS_ICON[p.status]}
                  {p.status}
                </span>
                {p.priority && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-gray-800 text-gray-400">{p.priority}</span>
                )}
              </div>

              <div className="grid grid-cols-3 gap-2 text-center">
                {[
                  { label: 'FRs', value: p.health?.fr_count || 0 },
                  { label: 'PRDs', value: p.health?.prd_count || 0 },
                  { label: 'CRs', value: p.health?.open_crs || 0 },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-gray-800/60 rounded-lg py-1.5">
                    <p className="text-sm font-semibold text-white">{value}</p>
                    <p className="text-xs text-gray-500">{label}</p>
                  </div>
                ))}
              </div>

              {p.target_end && (
                <p className="text-xs text-gray-600 mt-2">Target: {p.target_end}</p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Delete confirm modal */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4">
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 max-w-md w-full">
            <h3 className="text-base font-semibold mb-2">Delete project?</h3>
            <p className="text-sm text-gray-400 mb-1">
              <strong className="text-white">{confirmDelete}</strong> will be moved to <code className="text-xs bg-gray-800 px-1 rounded">_deleted/</code>
            </p>
            <p className="text-xs text-gray-500 mb-5">Kept for 3 months before permanent deletion.</p>
            <div className="flex gap-3">
              <button onClick={() => setConfirmDelete(null)}
                className="flex-1 px-4 py-2 bg-gray-800 text-gray-300 text-sm rounded-lg hover:bg-gray-700 transition">
                Cancel
              </button>
              <button onClick={() => deleteMut.mutate(confirmDelete)}
                disabled={deleteMut.isPending}
                className="flex-1 px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-500 disabled:opacity-50 transition">
                {deleteMut.isPending ? 'Deleting...' : 'Move to Trash'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
