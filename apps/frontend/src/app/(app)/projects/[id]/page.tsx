'use client'
import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ChevronLeft, FileText, GitBranch, Users, AlertTriangle,
  Edit3, Check, X, Plus, AlertCircle, RefreshCw, Zap
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { DocumentBrowser } from '@/components/projects/DocumentBrowser'
import { clsx } from 'clsx'

const TABS = ['Overview', 'Discovery', 'PRDs', 'Change Requests', 'Stakeholders', 'Decisions', 'Documents']

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-blue-900/40 text-blue-300 border-blue-800',
  'in-review': 'bg-yellow-900/40 text-yellow-300 border-yellow-800',
  approved: 'bg-green-900/40 text-green-300 border-green-800',
  archived: 'bg-gray-800 text-gray-500 border-gray-700',
}
const STATUS_OPTIONS = ['draft', 'in-review', 'approved', 'archived']

// ── Add-item forms ────────────────────────────────────────────────────────────

function AddForm({ title, fields, onSubmit, onCancel, loading }: {
  title: string
  fields: { key: string; label: string; type?: string; options?: string[] }[]
  onSubmit: (data: Record<string, string>) => void
  onCancel: () => void
  loading?: boolean
}) {
  const [data, setData] = useState<Record<string, string>>({})
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 space-y-3">
      <h4 className="text-sm font-semibold">{title}</h4>
      {fields.map(f => (
        <div key={f.key}>
          <label className="block text-xs text-gray-500 mb-1">{f.label}</label>
          {f.options ? (
            <select value={data[f.key] || ''} onChange={e => setData(d => ({ ...d, [f.key]: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-gray-500">
              <option value="">Select...</option>
              {f.options.map(o => <option key={o} value={o}>{o}</option>)}
            </select>
          ) : f.type === 'textarea' ? (
            <textarea value={data[f.key] || ''} onChange={e => setData(d => ({ ...d, [f.key]: e.target.value }))} rows={2}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-gray-500 resize-none" />
          ) : (
            <input type="text" value={data[f.key] || ''} onChange={e => setData(d => ({ ...d, [f.key]: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-gray-500" />
          )}
        </div>
      ))}
      <div className="flex gap-2 pt-1">
        <button onClick={() => onSubmit(data)} disabled={loading}
          className="flex-1 py-2 bg-white text-gray-900 text-sm font-semibold rounded-lg hover:bg-gray-100 disabled:opacity-50 transition">
          {loading ? 'Creating...' : 'Create'}
        </button>
        <button onClick={onCancel} className="px-4 py-2 bg-gray-800 text-gray-300 text-sm rounded-lg hover:bg-gray-700 transition">Cancel</button>
      </div>
    </div>
  )
}

// ── Conflict banner ───────────────────────────────────────────────────────────

function ConflictBanner({ projectId, visible, onDismiss }: { projectId: string; visible: boolean; onDismiss: () => void }) {
  const [scanned, setScanned] = useState(false)
  const { data, refetch, isFetching } = useQuery({
    queryKey: ['conflicts', projectId],
    queryFn: () => fetch(`/api/projects/${projectId}/conflicts`).then(r => r.json()),
    enabled: false,
  })

  if (!visible) return null

  const conflicts = data?.conflicts || []
  const hasConflicts = data?.has_conflicts

  return (
    <div className={clsx('flex items-start gap-3 p-3 rounded-xl border text-sm',
      hasConflicts ? 'border-red-800 bg-red-900/20' : scanned ? 'border-green-800 bg-green-900/20' : 'border-yellow-800 bg-yellow-900/20')}>
      <AlertCircle className={clsx('w-4 h-4 mt-0.5 shrink-0',
        hasConflicts ? 'text-red-400' : scanned ? 'text-green-400' : 'text-yellow-400')} />
      <div className="flex-1">
        {!scanned ? (
          <>
            <p className="text-yellow-300 font-medium">Document changed</p>
            <p className="text-yellow-500 text-xs mt-0.5">Run a conflict scan to check for tag collisions across all project PRDs?</p>
          </>
        ) : hasConflicts ? (
          <>
            <p className="text-red-300 font-medium">{conflicts.length} conflict{conflicts.length > 1 ? 's' : ''} found</p>
            {conflicts.map((c: any, i: number) => (
              <p key={i} className="text-red-400 text-xs mt-1">{c.tag}: {c.prds.join(', ')}</p>
            ))}
          </>
        ) : (
          <p className="text-green-300 font-medium">No conflicts found across {data?.total_prds} PRDs</p>
        )}
      </div>
      <div className="flex gap-2 shrink-0">
        {!scanned && (
          <button onClick={async () => { await refetch(); setScanned(true) }} disabled={isFetching}
            className="flex items-center gap-1 px-2.5 py-1 bg-yellow-700/40 text-yellow-300 text-xs rounded-lg hover:bg-yellow-700/60 transition">
            {isFetching ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Zap className="w-3 h-3" />}
            Scan
          </button>
        )}
        <button onClick={onDismiss} className="p-1 text-gray-600 hover:text-white transition"><X className="w-4 h-4" /></button>
      </div>
    </div>
  )
}

// ── Status badge ──────────────────────────────────────────────────────────────

function StatusBadge({ status, path, onUpdate }: { status: string; path: string; onUpdate: () => void }) {
  const [editing, setEditing] = useState(false)
  const mut = useMutation({
    mutationFn: (newStatus: string) => fetch(`/api/documents/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, status: newStatus }),
    }).then(r => r.json()),
    onSuccess: () => { setEditing(false); onUpdate() },
  })

  if (editing) {
    return (
      <select autoFocus defaultValue={status}
        onChange={e => mut.mutate(e.target.value)}
        onBlur={() => setEditing(false)}
        className="text-xs bg-gray-800 border border-gray-600 rounded px-2 py-0.5 text-white">
        {STATUS_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
      </select>
    )
  }
  return (
    <button onClick={() => setEditing(true)}
      className={clsx('text-xs px-2 py-0.5 rounded-full border font-medium hover:opacity-80 transition', STATUS_COLORS[status] || STATUS_COLORS.draft)}>
      {status}
    </button>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────


// ── Decisions list ────────────────────────────────────────────────────────────

function DecisionsList({ projectId, onOpen }: { projectId: string; onOpen: (path: string) => void }) {
  const { data } = useQuery<{ items: any[] }>({
    queryKey: ['project-files', projectId, 'decisions'],
    queryFn: () => fetch(`/api/projects/${projectId}/files?folder=decisions`).then(r => r.json()),
  })
  const items = (data?.items || []).filter((i: any) => i.type === 'file' && i.name.endsWith('.md') && i.name !== 'README.md')

  if (items.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-sm text-gray-600 mb-3">No decision records yet</p>
        <p className="text-xs text-gray-700">Use the AI to log decisions: "Log decision: [description]"</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {items.map((item: any) => (
        <button key={item.path} onClick={() => onOpen(item.path)}
          className="w-full flex items-center gap-3 p-3 bg-gray-900 border border-gray-800 rounded-lg hover:border-gray-700 transition text-left">
          <FileText className="w-4 h-4 text-purple-400 shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{item.name.replace('.md', '').replace(/-/g, ' ')}</p>
            <p className="text-xs text-gray-600 font-mono">{item.path}</p>
          </div>
        </button>
      ))}
    </div>
  )
}

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const qc = useQueryClient()
  const [tab, setTab] = useState('Overview')
  const [selectedDoc, setSelectedDoc] = useState<{ path: string; content: string } | null>(null)
  const [editMode, setEditMode] = useState(false)
  const [editContent, setEditContent] = useState('')
  const [versionBump, setVersionBump] = useState(false)
  const [showConflict, setShowConflict] = useState(false)
  const [addingFR, setAddingFR] = useState(false)
  const [addingCR, setAddingCR] = useState(false)
  const [addingSH, setAddingSH] = useState(false)

  const { data: project, isLoading } = useQuery({
    queryKey: ['project', id],
    queryFn: async () => {
      // Auto-activate this project so AI knows which project to work on
      await fetch(`/api/projects/${id}/activate`, { method: 'POST' }).catch(() => {})
      return fetch(`/api/projects/${id}`).then(r => r.json())
    },
  })
  const { data: discovery, refetch: refetchDiscovery } = useQuery({
    queryKey: ['discovery', id],
    queryFn: () => fetch(`/api/projects/${id}/discovery`).then(r => r.json()),
    enabled: tab === 'Discovery',
  })
  const { data: prds, refetch: refetchPrds } = useQuery({
    queryKey: ['prds', id],
    queryFn: () => fetch(`/api/projects/${id}/prd`).then(r => r.json()),
    enabled: tab === 'PRDs',
  })
  const { data: crs, refetch: refetchCrs } = useQuery({
    queryKey: ['crs', id],
    queryFn: () => fetch(`/api/projects/${id}/cr`).then(r => r.json()),
    enabled: tab === 'Change Requests',
  })
  const { data: stakeholders, refetch: refetchSH } = useQuery({
    queryKey: ['stakeholders', id],
    queryFn: () => fetch(`/api/projects/${id}/stakeholders`).then(r => r.json()),
    enabled: tab === 'Stakeholders',
  })

  const saveMut = useMutation({
    mutationFn: ({ path, content }: { path: string; content: string }) =>
      fetch('/api/documents/write', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path, content }) }).then(r => r.json()),
    onSuccess: () => { setEditMode(false); setVersionBump(false); setShowConflict(true); if (selectedDoc) setSelectedDoc({ ...selectedDoc, content: editContent }) },
  })

  const frMut = useMutation({
    mutationFn: (data: any) => fetch(`/api/projects/${id}/fr`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }).then(r => r.json()),
    onSuccess: () => { setAddingFR(false); refetchDiscovery(); setShowConflict(true) },
  })
  const crMut = useMutation({
    mutationFn: (data: any) => fetch(`/api/projects/${id}/cr`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }).then(r => r.json()),
    onSuccess: () => { setAddingCR(false); refetchCrs(); setShowConflict(true) },
  })
  const shMut = useMutation({
    mutationFn: (data: any) => fetch(`/api/projects/${id}/stakeholders`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }).then(r => r.json()),
    onSuccess: () => { setAddingSH(false); refetchSH() },
  })

  const openDoc = async (path: string) => {
    const r = await fetch(`/api/documents/read?path=${encodeURIComponent(path)}`)
    const d = await r.json()
    setSelectedDoc({ path, content: d.content || '' })
    setEditContent(d.content || '')
    setEditMode(false)
  }

  const handleEdit = () => {
    if (!selectedDoc) return
    const isApproved = /^status:\s*approved/m.test(selectedDoc.content)
    if (isApproved) { setVersionBump(true); return }
    setEditMode(true)
  }

  const handleSave = () => {
    if (!selectedDoc) return
    saveMut.mutate({ path: selectedDoc.path, content: editContent })
  }

  if (isLoading) return <div className="flex items-center justify-center h-full text-gray-500 text-sm">Loading...</div>
  if (!project || project.detail) return <div className="flex items-center justify-center h-full text-red-400 text-sm">Project not found</div>

  const milestones = project.milestones || []
  const MS_COLOR: Record<string, string> = { Done: 'text-green-400', 'In Progress': 'text-blue-400', Pending: 'text-gray-500', 'At Risk': 'text-red-400' }

  return (
    <div className="flex h-full">
      {/* ── Left panel ── */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header */}
        <div className="flex items-center gap-3 px-5 py-3 border-b border-gray-800 shrink-0">
          <button onClick={() => router.push('/projects')} className="p-1 text-gray-500 hover:text-white transition">
            <ChevronLeft className="w-5 h-5" />
          </button>
          <div className="flex-1 min-w-0">
            <h1 className="text-base font-semibold truncate">{project.name}</h1>
            <p className="text-xs text-gray-500">{id}</p>
          </div>
          <StatusBadge status={project.status || 'planning'}
            path={`my-projects/${id}/PROJECT.md`}
            onUpdate={() => { qc.invalidateQueries({ queryKey: ['project', id] }); setShowConflict(true) }} />
        </div>

        {/* Conflict banner */}
        <div className="px-4 pt-2">
          <ConflictBanner projectId={id} visible={showConflict} onDismiss={() => setShowConflict(false)} />
        </div>

        {/* Tabs */}
        <div className="flex gap-1 px-4 py-2 border-b border-gray-800 overflow-x-auto">
          {TABS.map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={clsx('px-3 py-1.5 text-xs rounded-md whitespace-nowrap transition', tab === t ? 'bg-gray-700 text-white' : 'text-gray-500 hover:text-white')}>
              {t}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {/* ── Overview ── */}
          {tab === 'Overview' && (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: 'FRs', value: project.health?.fr_count || 0, sub: `${project.health?.fr_gate_approved || 0} gate approved` },
                  { label: 'PRDs', value: project.health?.prd_count || 0, sub: `${project.health?.prd_approved || 0} approved` },
                  { label: 'Open CRs', value: project.health?.open_crs || 0, sub: 'in progress' },
                ].map(s => (
                  <div key={s.label} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                    <p className="text-2xl font-bold">{s.value}</p>
                    <p className="text-xs font-medium text-gray-300 mt-1">{s.label}</p>
                    <p className="text-xs text-gray-600">{s.sub}</p>
                  </div>
                ))}
              </div>
              {milestones.length > 0 && (
                <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                  <h3 className="text-sm font-semibold mb-3">Milestones</h3>
                  <div className="space-y-2">
                    {milestones.map((m: any, i: number) => (
                      <div key={i} className="flex items-center gap-3">
                        <span className={clsx('text-xs font-medium w-12', MS_COLOR[m.status] || 'text-gray-500')}>{m.id}</span>
                        <div className="flex-1 h-1.5 bg-gray-800 rounded-full">
                          <div className={clsx('h-full rounded-full', m.status === 'Done' ? 'bg-green-500 w-full' : m.status === 'In Progress' ? 'bg-blue-500 w-1/2' : 'w-0')} />
                        </div>
                        <span className="text-xs text-gray-400 min-w-[80px] truncate">{m.name}</span>
                        <span className={clsx('text-xs', MS_COLOR[m.status] || 'text-gray-500')}>{m.status}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              <button onClick={() => openDoc(`my-projects/${id}/PROJECT.md`)}
                className="w-full flex items-center gap-3 p-4 bg-gray-900 border border-gray-800 rounded-xl hover:border-gray-700 transition text-left">
                <FileText className="w-5 h-5 text-gray-500" />
                <div>
                  <p className="text-sm font-medium">PROJECT.md</p>
                  <p className="text-xs text-gray-500">View full project definition</p>
                </div>
              </button>
            </div>
          )}

          {/* ── Discovery ── */}
          {tab === 'Discovery' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs text-gray-500">Feature Requests</p>
                <button onClick={() => setAddingFR(v => !v)}
                  className="flex items-center gap-1 px-2.5 py-1 bg-gray-800 text-gray-300 text-xs rounded-lg hover:bg-gray-700 transition">
                  <Plus className="w-3.5 h-3.5" /> Add FR
                </button>
              </div>
              {addingFR && (
                <AddForm title="New Feature Request"
                  fields={[
                    { key: 'title', label: 'Feature title' },
                    { key: 'description', label: 'Problem statement', type: 'textarea' },
                    { key: 'source', label: 'Source', options: ['user-feedback', 'internal', 'data', 'stakeholder'] },
                  ]}
                  onSubmit={data => frMut.mutate(data)}
                  onCancel={() => setAddingFR(false)}
                  loading={frMut.isPending} />
              )}
              {(discovery?.frs || []).map((fr: any) => (
                <button key={fr.id} onClick={() => openDoc(fr.file || `my-projects/${id}/discovery/inbox/${fr.id}.md`)}
                  className="w-full flex items-center gap-3 p-3 bg-gray-900 border border-gray-800 rounded-lg hover:border-gray-700 transition text-left">
                  <FileText className="w-4 h-4 text-gray-500 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{fr.title}</p>
                    <p className="text-xs text-gray-500">RICE: {fr.rice_score} · Gate: {fr.gate_status}</p>
                  </div>
                  <StatusBadge status={fr.status} path={fr.file || ''} onUpdate={() => { refetchDiscovery(); setShowConflict(true) }} />
                </button>
              ))}
              {(discovery?.frs || []).length === 0 && !addingFR && <p className="text-sm text-gray-600">No feature requests yet</p>}
            </div>
          )}

          {/* ── PRDs with versions ── */}
          {tab === 'PRDs' && (
            <div className="space-y-3">
              {(prds?.prds || []).map((prd: any) => (
                <div key={prd.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-medium">{prd.id}</p>
                    <StatusBadge status={prd.status} path={(prd.versions?.slice(-1)[0]?.path) || ''} onUpdate={() => { refetchPrds(); setShowConflict(true) }} />
                  </div>
                  <p className="text-xs text-gray-500 mb-2">Versions</p>
                  <div className="flex flex-wrap gap-2">
                    {(prd.versions || []).map((v: any, vi: number) => {
                      const isLatest = vi === (prd.versions?.length || 1) - 1
                      return (
                        <button key={v.file} onClick={() => openDoc(v.path)}
                          className={clsx('flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition',
                            v.status === 'approved' ? 'border-green-800 text-green-400 bg-green-900/20 hover:bg-green-900/30'
                              : v.status === 'draft' ? 'border-blue-800 text-blue-400 bg-blue-900/20 hover:bg-blue-900/30'
                              : 'border-gray-700 text-gray-400 bg-gray-800 hover:bg-gray-700')}>
                          <GitBranch className="w-3 h-3" />
                          {v.version}
                          {isLatest && <span className="text-xs opacity-60 ml-0.5">latest</span>}
                          {v.status === 'approved' && <Check className="w-3 h-3" />}
                        </button>
                      )
                    })}
                  </div>
                  {prd.versions?.[prd.versions.length - 1]?.approved_by && (
                    <p className="text-xs text-gray-600 mt-2">Approved by: {prd.versions[prd.versions.length - 1].approved_by}</p>
                  )}
                </div>
              ))}
              {(prds?.prds || []).length === 0 && <p className="text-sm text-gray-600">No PRDs yet</p>}
            </div>
          )}

          {/* ── Change Requests ── */}
          {tab === 'Change Requests' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs text-gray-500">Change Requests</p>
                <button onClick={() => setAddingCR(v => !v)}
                  className="flex items-center gap-1 px-2.5 py-1 bg-gray-800 text-gray-300 text-xs rounded-lg hover:bg-gray-700 transition">
                  <Plus className="w-3.5 h-3.5" /> Add CR
                </button>
              </div>
              {addingCR && (
                <AddForm title="New Change Request"
                  fields={[
                    { key: 'title', label: 'Change title' },
                    { key: 'linked_prd', label: 'Linked PRD (e.g. PRD-001)' },
                    { key: 'description', label: 'What needs to change?', type: 'textarea' },
                    { key: 'urgency', label: 'Urgency', options: ['critical', 'high', 'medium', 'low'] },
                  ]}
                  onSubmit={data => crMut.mutate(data)}
                  onCancel={() => setAddingCR(false)}
                  loading={crMut.isPending} />
              )}
              {(crs?.crs || []).map((cr: any) => (
                <button key={cr.id} onClick={() => openDoc(cr.file)}
                  className="w-full flex items-center gap-3 p-3 bg-gray-900 border border-gray-800 rounded-lg hover:border-gray-700 transition text-left">
                  <AlertTriangle className="w-4 h-4 text-yellow-500 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{cr.id} — {cr.title || cr.id}</p>
                    <p className="text-xs text-gray-500">{cr.stage} · {cr.urgency}</p>
                  </div>
                  <StatusBadge status={cr.stage || 'intake'} path={cr.file || ''} onUpdate={() => { refetchCrs(); setShowConflict(true) }} />
                </button>
              ))}
              {(crs?.crs || []).length === 0 && !addingCR && <p className="text-sm text-gray-600">No change requests</p>}
            </div>
          )}

          {/* ── Stakeholders ── */}
          {tab === 'Stakeholders' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs text-gray-500">Stakeholders</p>
                <button onClick={() => setAddingSH(v => !v)}
                  className="flex items-center gap-1 px-2.5 py-1 bg-gray-800 text-gray-300 text-xs rounded-lg hover:bg-gray-700 transition">
                  <Plus className="w-3.5 h-3.5" /> Add
                </button>
              </div>
              {addingSH && (
                <AddForm title="New Stakeholder"
                  fields={[
                    { key: 'name', label: 'Full name' },
                    { key: 'title', label: 'Role / title' },
                    { key: 'power', label: 'Power level', options: ['high', 'medium', 'low'] },
                    { key: 'interest', label: 'Interest level', options: ['high', 'medium', 'low'] },
                    { key: 'notes', label: 'Notes (optional)', type: 'textarea' },
                  ]}
                  onSubmit={data => shMut.mutate(data)}
                  onCancel={() => setAddingSH(false)}
                  loading={shMut.isPending} />
              )}
              {(stakeholders?.stakeholders || []).map((sh: any) => (
                <button key={sh.id} onClick={() => openDoc(`my-projects/${id}/stakeholders/${sh.id}.md`)}
                  className="w-full flex items-center gap-3 p-3 bg-gray-900 border border-gray-800 rounded-lg hover:border-gray-700 transition text-left">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-gray-700 shrink-0 text-xs font-bold">{sh.name?.[0] || '?'}</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{sh.name}</p>
                    <p className="text-xs text-gray-500">{sh.title} · {sh.quadrant}</p>
                  </div>
                  <span className="text-xs px-2 py-0.5 bg-gray-800 rounded text-gray-500">P:{sh.power}</span>
                </button>
              ))}
            </div>
          )}

          {/* ── Documents ── */}
          {tab === 'Decisions' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs text-gray-500">Decision Records</p>
                <button
                  onClick={() => openDoc(`my-projects/${id}/decisions/README.md`)}
                  className="flex items-center gap-1 px-2.5 py-1 bg-gray-800 text-gray-300 text-xs rounded-lg hover:bg-gray-700 transition"
                >
                  View Index
                </button>
              </div>
              <DecisionsList projectId={id} onOpen={openDoc} />
            </div>
          )}

          {tab === 'Documents' && (
            <DocumentBrowser
              projectId={id}
              onFileSelect={(path, content) => setSelectedDoc({ path, content })}
            />
          )}
        </div>
      </div>

      {/* ── Right: Document viewer ── */}
      {selectedDoc && (
        <div className="hidden lg:flex flex-col w-[48%] xl:w-1/2 border-l border-gray-800 bg-gray-900/40">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800 shrink-0">
            <div className="flex items-center gap-2 min-w-0">
              <FileText className="w-4 h-4 text-gray-400 shrink-0" />
              <span className="text-sm font-medium truncate">{selectedDoc.path.split('/').pop()}</span>
            </div>
            <div className="flex items-center gap-2">
              {editMode ? (
                <>
                  <button onClick={handleSave} disabled={saveMut.isPending}
                    className="flex items-center gap-1 px-3 py-1 bg-green-600 text-white text-xs rounded-lg hover:bg-green-500 transition">
                    <Check className="w-3 h-3" />{saveMut.isPending ? 'Saving...' : 'Save'}
                  </button>
                  <button onClick={() => setEditMode(false)} className="p-1 text-gray-500 hover:text-white"><X className="w-4 h-4" /></button>
                </>
              ) : (
                <button onClick={handleEdit}
                  className="flex items-center gap-1 px-3 py-1 bg-gray-700 text-gray-200 text-xs rounded-lg hover:bg-gray-600 transition">
                  <Edit3 className="w-3 h-3" />Edit
                </button>
              )}
              <button onClick={() => setSelectedDoc(null)} className="p-1 text-gray-500 hover:text-white"><X className="w-4 h-4" /></button>
            </div>
          </div>
          <div className="flex-1 overflow-auto p-4">
            {editMode ? (
              <textarea value={editContent} onChange={e => setEditContent(e.target.value)}
                className="w-full h-full bg-transparent text-sm text-gray-200 font-mono resize-none focus:outline-none leading-relaxed" />
            ) : (
              <div className="prose prose-invert prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{selectedDoc.content}</ReactMarkdown>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Version bump warning */}
      {versionBump && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4">
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 max-w-md w-full">
            <h3 className="text-base font-semibold mb-2">Document is approved</h3>
            <p className="text-sm text-gray-400 mb-4">
              This document is <strong className="text-white">approved and immutable</strong>.
              To make changes, create a new version first.
            </p>
            <div className="flex gap-3">
              <button onClick={() => setVersionBump(false)} className="flex-1 px-4 py-2 bg-gray-800 text-gray-300 text-sm rounded-lg hover:bg-gray-700 transition">Cancel</button>
              <button onClick={() => { setVersionBump(false); setEditMode(true) }} className="flex-1 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-500 transition">Edit as new version</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
