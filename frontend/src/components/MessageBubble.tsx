import type { Message, ThinkingData } from '../api/types'
import { IntentBadge } from './IntentBadge'
import { SourceCitation } from './SourceCitation'
import { StreamingText } from './StreamingText'
import { ThinkingProcess } from './ThinkingProcess'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Props {
  message: Message
  isStreaming?: boolean
  streamingThinking?: ThinkingData | null
}

export function MessageBubble({ message, isStreaming, streamingThinking }: Props) {
  const isUser = message.role === 'user'

  return (
    <div className={`msg-row ${isUser ? 'user' : ''}`}>
      {/* Avatar */}
      <div className="msg-avatar" style={isUser ? {background: 'linear-gradient(135deg, #4F46E5 0%, #6366F1 100%)'} : {background: 'linear-gradient(135deg, #8B5CF6 0%, #A78BFA 100%)'}}>
        {isUser ? 'U' : 'AI'}
      </div>

      {/* Content */}
      <div style={{maxWidth: '75%', minWidth: 0, display: 'flex', flexDirection: 'column', alignItems: isUser ? 'flex-end' : 'flex-start'}}>
        {/* Name + intent row */}
        <div style={{display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px', flexDirection: isUser ? 'row-reverse' : 'row'}}>
          <span style={{fontSize: '11px', color: '#94A3B8', fontWeight: 500}}>
            {isUser ? '我' : '港口AI'}
          </span>
          {!isUser && message.intent && <IntentBadge intent={message.intent} />}
        </div>

        {/* Thinking process (assistant only) */}
        {!isUser && (message.thinkingData || streamingThinking) && (
          <ThinkingProcess
            thinking={(message.thinkingData || streamingThinking)!}
            latencyMs={message.latencyMs}
          />
        )}

        {/* Bubble */}
        <div className={isUser ? 'msg-bubble user' : 'msg-bubble ai'}>
          {isUser ? (
            <p style={{whiteSpace: 'pre-wrap', margin: 0}}>{message.content}</p>
          ) : isStreaming ? (
            <StreamingText content={message.content} isStreaming={true} />
          ) : (
            <div className="prose-custom">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            </div>
          )}

          {/* Sources (assistant only, non-streaming) */}
          {!isUser && !isStreaming && message.sources && message.sources.length > 0 && (
            <SourceCitation sources={message.sources} />
          )}
        </div>
      </div>
    </div>
  )
}
