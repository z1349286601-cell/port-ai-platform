export interface ChatRequest {
  message: string
  session_id?: string
  channel?: string
  user_id?: string
}

export interface IntentEvent {
  intent: string
  confidence: number
  reasoning: string
}

export interface TokenEvent {
  token: string
}

export interface SourceItem {
  doc_name: string
  doc_title: string
  section_title: string
  relevance_score: number
  excerpt: string
}

export interface SourcesEvent {
  sources: SourceItem[]
}

export interface DoneEvent {
  session_id: string
  message_id: number
  intent: string
  latency_ms: number
}

export interface ErrorEvent {
  code: string
  detail: string
  trace_id: string
}

export type SSEEvent =
  | { type: 'intent'; data: IntentEvent }
  | { type: 'token'; data: TokenEvent }
  | { type: 'sources'; data: SourcesEvent }
  | { type: 'done'; data: DoneEvent }
  | { type: 'error'; data: ErrorEvent }

export interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  intent?: string
  sources?: SourceItem[]
}

export interface Session {
  session_id: string
  title: string
  last_message: string
  message_count: number
  updated_at: string
}
