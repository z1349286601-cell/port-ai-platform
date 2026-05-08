import { create } from 'zustand'
import type { Message, Session } from '../api/types'

interface ChatState {
  sessions: Session[]
  currentSessionId: string | null
  messages: Message[]
  isStreaming: boolean
  currentReply: string

  setSessions: (sessions: Session[]) => void
  setCurrentSession: (id: string | null) => void
  addMessage: (msg: Message) => void
  setStreaming: (v: boolean) => void
  appendToken: (token: string) => void
  commitReply: (msgId: number, intent: string, sources?: any[]) => void
  clearMessages: () => void
}

export const useChatStore = create<ChatState>((set) => ({
  sessions: [],
  currentSessionId: null,
  messages: [],
  isStreaming: false,
  currentReply: '',

  setSessions: (sessions) => set({ sessions }),
  setCurrentSession: (id) => set({ currentSessionId: id }),
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  setStreaming: (v) => set({ isStreaming: v }),
  appendToken: (token) => set((s) => ({ currentReply: s.currentReply + token })),
  commitReply: (msgId, intent, sources) =>
    set((s) => {
      const msg: Message = {
        id: msgId,
        role: 'assistant',
        content: s.currentReply,
        intent,
        sources,
      }
      return { messages: [...s.messages, msg], currentReply: '', isStreaming: false }
    }),
  clearMessages: () => set({ messages: [], currentReply: '' }),
}))
