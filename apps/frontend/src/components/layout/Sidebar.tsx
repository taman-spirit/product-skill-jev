'use client'
import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { MessageSquare, FolderOpen, ClipboardList, Settings } from 'lucide-react'
import { clsx } from 'clsx'

const NAV = [
  { href: '/chat',     icon: MessageSquare, label: 'Chat' },
  { href: '/projects', icon: FolderOpen,    label: 'Projects' },
  { href: '/audit',    icon: ClipboardList, label: 'Audit Log' },
  { href: '/settings', icon: Settings,      label: 'Settings' },
]

function ActiveProjectIndicator() {
  const [active, setActive] = React.useState('')
  React.useEffect(() => {
    fetch('/api/settings/workspace').then(r => r.json())
      .then(d => { if (d.active_project) setActive(d.active_project.split('/').pop() || '') })
      .catch(() => {})
  }, [])
  if (!active) return null
  return (
    <div className="px-4 py-2 border-t border-gray-800">
      <p className="hidden lg:block text-xs text-gray-600">Active:</p>
      <p className="hidden lg:block text-xs text-blue-400 truncate">{active}</p>
    </div>
  )
}

export function Sidebar() {
  const path = usePathname()
  return (
    <aside className="flex flex-col w-16 lg:w-56 h-screen bg-gray-900 border-r border-gray-800 shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-gray-800">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg shrink-0 overflow-hidden">
          <img src="/logo.png" alt="AISilicons" className="w-8 h-8 object-cover" />
        </div>
        <span className="hidden lg:block text-sm font-semibold text-white truncate">AISilicons</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 space-y-1 px-2">
        {NAV.map(({ href, icon: Icon, label }) => {
          const active = path.startsWith(href)
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                'flex items-center gap-3 px-2 py-2.5 rounded-lg text-sm font-medium transition-colors',
                active
                  ? 'bg-gray-800 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/60'
              )}
            >
              <Icon className="w-5 h-5 shrink-0" />
              <span className="hidden lg:block">{label}</span>
            </Link>
          )
        })}
      </nav>

      {/* Version */}
      <ActiveProjectIndicator />
      <div className="px-4 py-3 border-t border-gray-800">
        <span className="hidden lg:block text-xs text-gray-600">v1.0 Foundation</span>
      </div>
    </aside>
  )
}
