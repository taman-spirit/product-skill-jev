'use client'
import { useRef, useState, useEffect, useCallback } from 'react'
import { Send, Paperclip, X, Loader2 } from 'lucide-react'
import { MessageItem } from '@/components/chat/MessageItem'
import { FileViewer } from '@/components/chat/FileViewer'
import { useChatStore, type Message } from '@/stores/chatStore'
import { friendlyError, friendlySseError } from '@/lib/errors'

export default function ChatPage() {
  const { messages, isStreaming, addMessage, updateLastMessage, setStreaming } = useChatStore()
  const [input, setInput] = useState('')
  const [viewFile, setViewFile] = useState<string | null>(null)
  const [attachments, setAttachments] = useState<File[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const uploadFile = async (file: File): Promise<string> => {
    const fd = new FormData()
    fd.append('file', file)
    const r = await fetch('/api/attachments/upload', { method: 'POST', body: fd })
    const d = await r.json()
    return `[Attached file: ${file.name}]\n${d.content || ''}`
  }

  const sendMessage = useCallback(async () => {
    if (!input.trim() && attachments.length === 0) return
    if (isStreaming) return

    let text = input.trim()

    // Upload attachments
    if (attachments.length > 0) {
      const parts = await Promise.all(attachments.map(uploadFile))
      text = parts.join('\n\n') + (text ? '\n\n' + text : '')
      setAttachments([])
    }

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    }
    addMessage(userMsg)
    setInput('')
    setStreaming(true)

    // Add empty assistant message
    const assistantMsg: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      isStreaming: true,
      toolUses: [],
      timestamp: new Date(),
    }
    addMessage(assistantMsg)

    // Stream from API
    let fullText = ''
    const toolUses: Message['toolUses'] = []

    try {
      const activeProject = useChatStore.getState().activeProjectId || ''
      const res = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: 'web-default', project_id: activeProject }),
      })

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const lines = decoder.decode(value).split('\n')
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const evt = JSON.parse(line.slice(6))
            if (evt.type === 'text_delta') {
              fullText += evt.text
              updateLastMessage(fullText, undefined)
            } else if (evt.type === 'tool_use') {
              toolUses.push({ name: evt.name, input: evt.input })
              if (evt.input?.path) setViewFile(evt.input.path)
            } else if (evt.type === 'done') {
              updateLastMessage(fullText, evt.suggestions)
            } else if (evt.type === 'error') {
              updateLastMessage(friendlySseError(evt.message || ''), ['Open Settings'])
              return
            }
          } catch { /* skip */ }
        }
      }
    } catch (e: any) {
      const errMsg = e?.message || String(e) || 'Unknown error'
      let friendly = 'Something went wrong.'
      if (errMsg.includes('401') || errMsg.includes('key')) {
        friendly = 'API key error. Check Settings.'
      } else if (errMsg.includes('429') || errMsg.includes('rate')) {
        friendly = 'Rate limit. Please wait and try again.'
      } else if (errMsg.includes('404')) {
        friendly = 'Model not found. Check Settings.'
      }
      updateLastMessage(friendly, ['Open Settings'])
    } finally {
      setStreaming(false)
      // Update tool uses on last message
      const msgs = useChatStore.getState().messages
      const last = msgs[msgs.length - 1]
      if (last && last.role === 'assistant') {
        useChatStore.setState({
          messages: msgs.map((m, i) =>
            i === msgs.length - 1 ? { ...m, toolUses, isStreaming: false } : m
          )
        })
      }
    }
  }, [input, attachments, isStreaming, addMessage, updateLastMessage, setStreaming])

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  return (
    <div className="flex h-full">
      {/* ── Left: Chat ─────────────────────────────────── */}
      <div className="flex flex-col flex-1 min-w-0 border-r border-gray-800">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto py-4 space-y-1">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-gray-600 px-6 text-center">
              <p className="text-lg font-medium text-gray-400 mb-2">Product Management Skill Jev</p>
              <p className="text-sm mb-6">Start a conversation or pick a suggestion</p>
              <div className="flex flex-wrap gap-2 justify-center">
                {['Show all projects', 'Create a new project for [name]', 'Create a feature request for [description]'].map(s => (
                  <button key={s} onClick={() => setInput(s)}
                    className="text-xs px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-300 hover:border-blue-500 hover:text-white transition">
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map(msg => (
            <MessageItem key={msg.id} message={msg} onFileClick={setViewFile} />
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Attachments preview */}
        {attachments.length > 0 && (
          <div className="flex gap-2 px-4 py-2 border-t border-gray-800 flex-wrap">
            {attachments.map((f, i) => (
              <div key={i} className="flex items-center gap-1.5 px-2 py-1 bg-gray-800 rounded text-xs text-gray-300">
                {f.name}
                <button onClick={() => setAttachments(a => a.filter((_, j) => j !== i))}>
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Input */}
        <div className="flex items-end gap-2 px-4 py-3 border-t border-gray-800">
          <input ref={fileInputRef} type="file" className="hidden"
            accept=".md,.docx,.pdf,.xlsx,.csv,.txt"
            multiple onChange={e => setAttachments(a => [...a, ...Array.from(e.target.files || [])])} />
          <button onClick={() => fileInputRef.current?.click()}
            className="p-2 text-gray-500 hover:text-white transition shrink-0">
            <Paperclip className="w-5 h-5" />
          </button>
          <textarea
            id="chat-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            rows={1}
            placeholder="Type a message... (Enter to send, Shift+Enter for new line)"
            className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 resize-none focus:outline-none focus:border-gray-500 leading-relaxed"
            style={{ maxHeight: '120px', overflowY: 'auto' }}
          />
          <button onClick={sendMessage} disabled={isStreaming || (!input.trim() && attachments.length === 0)}
            className="p-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed transition shrink-0">
            {isStreaming ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* ── Right: File Viewer ──────────────────────────── */}
      <div className="hidden lg:flex flex-col w-[45%] xl:w-[50%] bg-gray-900/50">
        <div className="px-4 py-3 border-b border-gray-800 shrink-0">
          <h2 className="text-sm font-medium text-gray-400">File Viewer</h2>
        </div>
        <FileViewer path={viewFile} onClose={() => setViewFile(null)} />
      </div>
    </div>
  )
}
