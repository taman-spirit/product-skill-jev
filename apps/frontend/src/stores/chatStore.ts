import { create } from 'zustand'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  suggestions?: string[]
  toolUses?: { name: string; input: Record<string, unknown> }[]
  isStreaming?: boolean
  timestamp: Date
}

interface ChatStore {
  messages: Message[]
  isStreaming: boolean
  sessionId: string
  activeProjectId: string | null
  addMessage: (msg: Message) => void
  updateLastMessage: (text: string, suggestions?: string[]) => void
  setStreaming: (v: boolean) => void
  setActiveProject: (id: string | null) => void
  clearMessages: () => void
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  isStreaming: false,
  sessionId: 'default',
  activeProjectId: null,
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  updateLastMessage: (text, suggestions) =>
    set((s) => {
      const msgs = [...s.messages]
      const last = msgs[msgs.length - 1]
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, content: text, suggestions, isStreaming: false }
      }
      return { messages: msgs }
    }),
  setStreaming: (v) => set({ isStreaming: v }),
  setActiveProject: (id) => set({ activeProjectId: id }),
  clearMessages: () => set({ messages: [] }),
}))
