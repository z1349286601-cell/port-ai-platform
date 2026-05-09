import type { Message, ThinkingData } from '../api/types'
import { MessageList } from './MessageList'
import { MessageInput } from './MessageInput'

interface Props {
  messages: Message[]
  streamingContent: string
  isStreaming: boolean
  streamingIntent: string | null
  streamingThinking: ThinkingData | null
  error: string | null
  onSend: (content: string) => void
  onDismissError: () => void
  onHintClick?: (hint: string) => void
}

export function ChatWindow({
  messages,
  streamingContent,
  isStreaming,
  streamingIntent,
  streamingThinking,
  error,
  onSend,
  onDismissError,
  onHintClick,
}: Props) {
  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Error banner */}
      {error && (
        <div style={{
          background: '#FEF2F2',
          borderBottom: '1px solid #FECACA',
          padding: '10px 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
        }}>
          <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
            <span style={{fontSize: '12px'}}>⚠️</span>
            <span style={{fontSize: '0.875rem', color: '#DC2626'}}>{error}</span>
          </div>
          <button
            onClick={onDismissError}
            style={{
              color: '#F87171',
              fontSize: '0.875rem',
              fontWeight: 500,
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '2px 6px',
            }}
          >
            ✕
          </button>
        </div>
      )}

      <MessageList
        messages={messages}
        streamingContent={streamingContent}
        isStreaming={isStreaming}
        streamingIntent={streamingIntent}
        streamingThinking={streamingThinking}
        onHintClick={onHintClick}
      />

      <MessageInput onSend={onSend} disabled={isStreaming} />
    </div>
  )
}
