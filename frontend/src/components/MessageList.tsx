import { useEffect, useRef } from 'react'
import type { Message, ThinkingData } from '../api/types'
import { MessageBubble } from './MessageBubble'

interface Props {
  messages: Message[]
  streamingContent: string
  isStreaming: boolean
  streamingIntent: string | null
  streamingThinking: ThinkingData | null
  onHintClick?: (hint: string) => void
}

export function MessageList({ messages, streamingContent, isStreaming, streamingIntent, streamingThinking, onHintClick }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  return (
    <div className="flex-1 overflow-y-auto grad-chat-bg">
      <div style={{maxWidth: '900px', margin: '0 auto', padding: '24px 16px'}}>
        {messages.length === 0 && !isStreaming && (
          <div style={{textAlign: 'center', color: '#94A3B8', marginTop: '96px'}}>
            <div style={{
              width: '64px',
              height: '64px',
              margin: '0 auto 16px',
              borderRadius: '16px',
              background: 'linear-gradient(135deg, #818CF8 0%, #A78BFA 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontSize: '28px',
              boxShadow: '0 8px 24px rgba(99,102,241,0.2)',
            }}>
              🚢
            </div>
            <p style={{fontSize: '1.125rem', fontWeight: 600, color: '#475569', margin: '0 0 6px 0'}}>港口AI助手已就绪</p>
            <p style={{fontSize: '0.875rem', color: '#94A3B8', maxWidth: '420px', margin: '0 auto', lineHeight: 1.6}}>
              可以问我船舶动态、集装箱位置、堆场容量、安全规程等问题
            </p>
            <div style={{display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center', marginTop: '20px'}}>
              {['查询集装箱位置', '查看靠泊计划', '安全管理规定', '设备维修记录'].map((hint) => (
                <span key={hint} onClick={() => onHintClick?.(hint)} style={{
                  fontSize: '0.75rem',
                  background: 'white',
                  color: '#64748B',
                  padding: '6px 14px',
                  borderRadius: '999px',
                  border: '1px solid #E2E8F0',
                  boxShadow: '0 1px 2px rgba(0,0,0,0.03)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.background = '#EEF2FF'; e.currentTarget.style.borderColor = '#818CF8'; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = 'white'; e.currentTarget.style.borderColor = '#E2E8F0'; }}
                >
                  {hint}
                </span>
              ))}
            </div>
          </div>
        )}

        {messages.filter((msg) => msg.content.trim() !== '').map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {/* Streaming message */}
        {isStreaming && streamingContent && (
          <MessageBubble
            message={{
              id: 0,
              role: 'assistant',
              content: streamingContent,
              intent: streamingIntent || undefined,
            }}
            isStreaming
            streamingThinking={streamingThinking}
          />
        )}

        {/* Processing indicator */}
        {isStreaming && !streamingContent && (
          <div className="msg-row">
            <div className="msg-avatar" style={{background: 'linear-gradient(135deg, #8B5CF6 0%, #A78BFA 100%)'}}>AI</div>
            <div className="msg-bubble ai" style={{display: 'flex', alignItems: 'center', gap: '6px'}}>
              <span style={{width: '6px', height: '6px', background: '#818CF8', borderRadius: '50%', display: 'inline-block', animation: 'bounce 0.6s infinite'}} />
              <span style={{width: '6px', height: '6px', background: '#818CF8', borderRadius: '50%', display: 'inline-block', animation: 'bounce 0.6s 0.15s infinite'}} />
              <span style={{width: '6px', height: '6px', background: '#818CF8', borderRadius: '50%', display: 'inline-block', animation: 'bounce 0.6s 0.3s infinite'}} />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  )
}
