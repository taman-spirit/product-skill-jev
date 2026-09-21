'use client'
import { clsx } from 'clsx'
import { Bot, User, FileText, Wrench } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Message } from '@/stores/chatStore'

interface Props {
  message: Message
  onFileClick?: (path: string) => void
}

export function MessageItem({ message, onFileClick }: Props) {
  const isUser = message.role === 'user'
  return (
    <div className={clsx('flex gap-3 px-4 py-3', isUser ? 'flex-row-reverse' : 'flex-row')}>
      {/* Avatar */}
      <div className={clsx(
        'flex items-center justify-center w-7 h-7 rounded-full shrink-0 mt-0.5',
        isUser ? 'bg-blue-600' : 'bg-gray-700'
      )}>
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Content */}
      <div className={clsx('flex-1 max-w-[85%]', isUser && 'flex flex-col items-end')}>
        {/* Tool uses */}
        {message.toolUses && message.toolUses.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-2">
            {message.toolUses.map((t, i) => (
              <button
                key={i}
                onClick={() => t.input?.path && onFileClick?.(t.input.path as string)}
                className="flex items-center gap-1 px-2 py-0.5 text-xs bg-gray-800 border border-gray-700 rounded-full text-gray-400 hover:text-white hover:border-gray-500 transition"
              >
                {t.name === 'write_file' || t.name === 'read_file'
                  ? <FileText className="w-3 h-3" />
                  : <Wrench className="w-3 h-3" />}
                {t.name}: {String(t.input?.path || t.input?.query || '').split('/').pop()}
              </button>
            ))}
          </div>
        )}

        {/* Message bubble */}
        <div className={clsx(
          'rounded-xl px-4 py-2.5 text-sm leading-relaxed',
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-gray-800 text-gray-100'
        )}>
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
              {message.isStreaming && (
                <span className="inline-block w-1.5 h-4 bg-gray-400 ml-0.5 cursor-blink" />
              )}
            </div>
          )}
        </div>

        {/* Suggestions */}
        {message.suggestions && message.suggestions.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {message.suggestions.map((s, i) => (
              <button
                key={i}
                onClick={() => {
                  const input = document.getElementById('chat-input') as HTMLTextAreaElement
                  if (input) { input.value = s; input.focus() }
                }}
                className="text-xs px-3 py-1.5 bg-gray-900 border border-gray-700 rounded-full text-gray-300 hover:border-blue-500 hover:text-white transition"
              >
                {s}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
