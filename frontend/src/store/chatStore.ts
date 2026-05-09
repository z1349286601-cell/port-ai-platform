import { create } from 'zustand'
import type { Message, Session, SourceItem, ThinkingData } from '../api/types'

const API_BASE = '/api/v1'

interface ChatState {
  sessions: Session[]
  currentSessionId: string | null
  messages: Message[]
  isStreaming: boolean
  currentReply: string
  currentIntent: string | null
  currentSources: SourceItem[]
  currentThinking: ThinkingData | null
  error: string | null

  loadSessions: (userId?: string) => Promise<void>
  createSession: (userId?: string) => Promise<string>
  switchSession: (id: string) => Promise<void>
  deleteSession: (id: string) => Promise<void>
  updateSessionTitle: (id: string, title: string) => Promise<void>
  sendMessage: (content: string, userId?: string) => Promise<void>
  appendToken: (token: string) => void
  finalizeMessage: (sessionId: string, messageId: number, intent: string) => void
  setSources: (sources: SourceItem[]) => void
  setError: (error: string | null) => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: [],
  currentSessionId: null,
  messages: [],
  isStreaming: false,
  currentReply: '',
  currentIntent: null,
  currentSources: [],
  currentThinking: null,
  error: null,

  loadSessions: async (userId) => {
    const headers: Record<string, string> = {}
    if (userId) headers['X-Demo-User'] = userId
    const res = await fetch(`${API_BASE}/sessions?user_id=${userId || 'anonymous'}`, { headers })
    if (res.ok) {
      const data = await res.json()
      const items: Session[] = data.items || []
      set({ sessions: items.filter((s) => s.message_count > 0) })
    }
  },

  createSession: async (userId) => {
    // Only create backend session — don't add to sidebar list.
    // Session appears in sidebar after first successful exchange (in done handler).
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (userId) headers['X-Demo-User'] = userId
    const res = await fetch(`${API_BASE}/sessions`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ channel: 'web', user_id: userId || 'anonymous', title: '' }),
    })
    if (res.ok) {
      const data = await res.json()
      return data.session_id
    }
    return ''
  },

  switchSession: async (id) => {
    set({ currentSessionId: id, messages: [], currentReply: '', currentSources: [], currentThinking: null, error: null })
    const res = await fetch(`${API_BASE}/sessions/${id}`)
    if (res.ok) {
      const data = await res.json()
      const msgs: Message[] = data.messages || []
      set({ messages: msgs.filter((m) => m.content && m.content.trim() !== '') })
    }
  },

  deleteSession: async (id) => {
    await fetch(`${API_BASE}/sessions/${id}`, { method: 'DELETE' })
    set((s) => ({
      sessions: s.sessions.filter((ses) => ses.session_id !== id),
      ...(s.currentSessionId === id ? { currentSessionId: null, messages: [] } : {}),
    }))
  },

  updateSessionTitle: async (id, title) => {
    const trimmed = title.trim().slice(0, 20)
    if (!trimmed) return
    set((s) => ({
      sessions: s.sessions.map((ses) =>
        ses.session_id === id ? { ...ses, title: trimmed } : ses
      ),
    }))
    await fetch(`${API_BASE}/sessions/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: trimmed }),
    })
  },

  sendMessage: async (content, userId) => {
    const state = get()
    if (!content.trim() || state.isStreaming) return

    let sessionId = state.currentSessionId
    if (!sessionId) {
      sessionId = await get().createSession(userId)
      if (!sessionId) return
    }

    const userMsg: Message = { id: Date.now(), role: 'user', content }
    set((s) => ({
      messages: [...s.messages, userMsg],
      isStreaming: true,
      currentReply: '',
      currentSources: [],
      currentThinking: null,
      error: null,
      currentSessionId: sessionId,
    }))

    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (userId) headers['X-Demo-User'] = userId

    const res = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ message: content, session_id: sessionId, user_id: userId || 'anonymous' }),
    })

    if (!res.ok) {
      set({ isStreaming: false, error: `请求失败 (${res.status})` })
      return
    }

    const reader = res.body?.getReader()
    if (!reader) {
      set({ isStreaming: false, error: '无法读取响应' })
      return
    }

    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let eventType = ''
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              switch (eventType) {
                case 'connected':
                  break
                case 'intent':
                  set({ currentIntent: data.intent })
                  break
                case 'thinking':
                  set({ currentThinking: data as ThinkingData })
                  break
                case 'token':
                  set((s) => ({ currentReply: s.currentReply + data.token }))
                  break
                case 'sources':
                  set({ currentSources: data.sources || [] })
                  break
                case 'done':
                  {
                    let isFirstExchange = false
                    let firstUserMsg = ''
                    let sid = ''
                    set((s) => {
                      isFirstExchange = s.messages.length === 1 && s.messages[0].role === 'user'
                      if (isFirstExchange) {
                        firstUserMsg = s.messages[0].content
                        sid = s.currentSessionId || ''
                      }
                      const assistantMsg: Message = {
                        id: data.message_id || Date.now(),
                        role: 'assistant',
                        content: s.currentReply,
                        intent: data.intent || s.currentIntent || '',
                        sources: s.currentSources,
                        thinkingData: s.currentThinking || undefined,
                        latencyMs: data.latency_ms,
                      }
                      return {
                        messages: [...s.messages, assistantMsg],
                        currentReply: '',
                        isStreaming: false,
                        currentIntent: null,
                      }
                    })
                    if (isFirstExchange && sid && firstUserMsg) {
                      const title = firstUserMsg.trim().slice(0, 20)
                      // Add session to sidebar list (it wasn't there before first exchange)
                      set((s) => {
                        const exists = s.sessions.find((ses) => ses.session_id === sid)
                        if (!exists) {
                          return {
                            sessions: [{
                              session_id: sid,
                              title,
                              last_message: '',
                              message_count: 2,
                              updated_at: new Date().toISOString(),
                            }, ...s.sessions],
                          }
                        }
                        return {}
                      })
                      get().updateSessionTitle(sid, title)
                    }
                  }
                  break
                case 'error':
                  set({ error: data.detail || '未知错误', isStreaming: false })
                  break
              }
            } catch { /* skip parse errors */ }
          }
        }
      }
    } catch (e: any) {
      set({ isStreaming: false, error: e.message || '连接中断' })
    }
  },

  appendToken: (token) => set((s) => ({ currentReply: s.currentReply + token })),

  finalizeMessage: (_sessionId, messageId, intent) =>
    set((s) => {
      const msg: Message = {
        id: messageId,
        role: 'assistant',
        content: s.currentReply,
        intent,
        sources: s.currentSources,
      }
      return { messages: [...s.messages, msg], currentReply: '', isStreaming: false }
    }),

  setSources: (sources) => set({ currentSources: sources }),
  setError: (error) => set({ error, isStreaming: false }),
}))
