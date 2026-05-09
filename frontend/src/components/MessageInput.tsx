import { useState, useRef, useCallback, KeyboardEvent, useEffect } from 'react'

const MAX_ROWS = 10
const LINE_HEIGHT = 21 // 0.875rem * 1.5 = 14px * 1.5 = 21px

interface Props {
  onSend: (content: string) => void
  disabled: boolean
}

export function MessageInput({ onSend, disabled }: Props) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const autoResize = useCallback(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    const maxHeight = LINE_HEIGHT * MAX_ROWS + 20 // 20 = vertical padding (10+10)
    const newHeight = Math.min(el.scrollHeight, maxHeight)
    el.style.height = newHeight + 'px'
    el.style.overflowY = el.scrollHeight > maxHeight ? 'auto' : 'hidden'
  }, [])

  useEffect(() => {
    autoResize()
  }, [input, autoResize])

  const handleSend = () => {
    const trimmed = input.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setInput('')
  }

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div style={{
      borderTop: '1px solid #E2E8F0',
      padding: '16px 24px 20px',
      background: 'white',
      flexShrink: 0,
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'flex-end',
        gap: '10px',
        maxWidth: '900px',
        margin: '0 auto',
      }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入您的问题… (Enter 发送 / Shift+Enter 换行)"
            rows={1}
            className="input-box"
            disabled={disabled}
            maxLength={2000}
          />
          <span style={{
            position: 'absolute',
            right: '12px',
            bottom: '10px',
            fontSize: '10px',
            color: '#94A3B8',
          }}>
            {input.length}/2000
          </span>
        </div>
        <button
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          className="btn-gradient"
          style={{
            padding: '10px 20px',
            fontSize: '0.875rem',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            flexShrink: 0,
            border: 'none',
            cursor: 'pointer',
            alignSelf: 'flex-end',
          }}
        >
          {disabled ? (
            <span style={{
              display: 'inline-block',
              width: '16px',
              height: '16px',
              border: '2px solid white',
              borderTopColor: 'transparent',
              borderRadius: '50%',
              animation: 'spin 0.6s linear infinite',
            }} />
          ) : (
            <>
              <span>发送</span>
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path d="M2 8h12M9 3l5 5-5 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </>
          )}
        </button>
      </div>
    </div>
  )
}
