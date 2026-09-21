'use client'
import { useQuery } from '@tanstack/react-query'
import { Clock, FileText, Edit3, CheckCircle, GitBranch, AlertCircle } from 'lucide-react'

interface AuditEntry {
  timestamp: string; project: string; document: string
  action: string; version?: string; user?: string; path: string
}

const ACTION_ICON: Record<string, React.ReactNode> = {
  created: <FileText className="w-4 h-4 text-blue-400" />,
  updated: <Edit3 className="w-4 h-4 text-yellow-400" />,
  approved: <CheckCircle className="w-4 h-4 text-green-400" />,
  versioned: <GitBranch className="w-4 h-4 text-purple-400" />,
  rejected: <AlertCircle className="w-4 h-4 text-red-400" />,
}

function formatTime(ts: string) {
  try {
    const d = new Date(ts)
    return d.toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch { return ts }
}

function groupByDate(entries: AuditEntry[]) {
  const groups: Record<string, AuditEntry[]> = {}
  for (const e of entries) {
    const date = e.timestamp.split('T')[0] || e.timestamp.split(' ')[0] || 'Unknown'
    if (!groups[date]) groups[date] = []
    groups[date].push(e)
  }
  return groups
}

export default function AuditPage() {
  const { data, isLoading, refetch } = useQuery<{ entries: AuditEntry[] }>({
    queryKey: ['audit'],
    queryFn: () => fetch('/api/audit').then(r => r.json()),
  })

  const entries = data?.entries || []
  const grouped = groupByDate(entries)
  const dates = Object.keys(grouped).sort().reverse()

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <div>
          <h1 className="text-lg font-semibold">Audit Log</h1>
          <p className="text-sm text-gray-500">Timeline of document changes</p>
        </div>
        <button onClick={() => refetch()} className="px-3 py-1.5 bg-gray-800 text-gray-300 text-sm rounded-lg hover:bg-gray-700 transition">Refresh</button>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-4">
        {isLoading && <p className="text-sm text-gray-500">Loading audit log...</p>}
        {!isLoading && entries.length === 0 && (
          <div className="flex flex-col items-center justify-center h-48 text-gray-600">
            <Clock className="w-10 h-10 mb-3 opacity-30" />
            <p className="text-sm">No activity recorded yet</p>
          </div>
        )}

        <div className="space-y-6 max-w-2xl">
          {dates.map(date => (
            <div key={date}>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">{date}</p>
              <div className="relative pl-5 border-l border-gray-800 space-y-4">
                {grouped[date].map((entry, i) => (
                  <div key={i} className="relative">
                    <div className="absolute -left-[21px] flex items-center justify-center w-8 h-8 bg-gray-950 border border-gray-800 rounded-full">
                      {ACTION_ICON[entry.action] || <Clock className="w-4 h-4 text-gray-500" />}
                    </div>
                    <div className="pl-4 pb-1">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-medium text-white">
                            <span className="capitalize">{entry.action}</span>
                            {' '}
                            <span className="text-blue-400">{entry.document}</span>
                            {entry.version && <span className="text-gray-500 text-xs ml-1">{entry.version}</span>}
                          </p>
                          <p className="text-xs text-gray-500 mt-0.5">
                            {entry.project}
                            {entry.user && <span className="ml-2">· {entry.user}</span>}
                          </p>
                          <p className="text-xs text-gray-700 font-mono mt-1 truncate max-w-xs">{entry.path}</p>
                        </div>
                        <p className="text-xs text-gray-600 whitespace-nowrap shrink-0">{formatTime(entry.timestamp)}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
