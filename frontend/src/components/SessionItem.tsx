import { useState, useRef, useEffect } from 'react'
import type { Session } from '../api/types'
import { ConfirmDialog } from './ConfirmDialog'

interface Props {
  session: Session
  isActive: boolean
  onClick: () => void
  onDelete: () => void
  onRename: (title: string) => void
}

function timeAgo(iso: string): string {
  const now = Date.now()
  const then = new Date(iso).getTime()
  const sec = Math.floor((now - then) / 1000)
  if (sec < 60) return '刚刚'
  if (sec < 3600) return `${Math.floor(sec / 60)}分钟前`
  if (sec < 86400) return `${Math.floor(sec / 3600)}小时前`
  return `${Math.floor(sec / 86400)}天前`
}

export function SessionItem({ session, isActive, onClick, onDelete, onRename }: Props) {
  const [showConfirm, setShowConfirm] = useState(false)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(session.title)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (editing) {
      setDraft(session.title || '')
      requestAnimationFrame(() => {
        inputRef.current?.focus()
        inputRef.current?.select()
      })
    }
  }, [editing, session.title])

  const commitRename = () => {
    const trimmed = draft.trim().slice(0, 20)
    if (trimmed && trimmed !== session.title) {
      onRename(trimmed)
    }
    setEditing(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      commitRename()
    } else if (e.key === 'Escape') {
      setEditing(false)
    }
  }

  return (
    <>
      <div
        onClick={editing ? undefined : onClick}
        className={`session-item ${isActive ? 'active' : ''}`}
        style={{ alignItems: 'center' }}
      >
        {/* Avatar */}
        <div
          className="avatar"
          style={
            isActive
              ? { background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)' }
              : {}
          }
        >
          {(session.title || '新')[0]}
        </div>

        {/* Content */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            {editing ? (
              <input
                ref={inputRef}
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={handleKeyDown}
                onBlur={commitRename}
                maxLength={20}
                onClick={(e) => e.stopPropagation()}
                style={{
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  color: '#4338CA',
                  border: '1px solid #818CF8',
                  borderRadius: '6px',
                  outline: 'none',
                  background: 'white',
                  padding: '3px 8px',
                  margin: 0,
                  width: '100%',
                  maxWidth: '190px',
                  boxShadow: '0 0 0 2px rgba(99,102,241,0.15)',
                  lineHeight: 1.4,
                }}
              />
            ) : (
              <p
                style={{
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  margin: 0,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  color: isActive ? '#4338CA' : '#334155',
                  cursor: 'text',
                }}
                onDoubleClick={(e) => {
                  e.stopPropagation()
                  setEditing(true)
                }}
                title="双击编辑名称"
              >
                {session.title || '新会话'}
              </p>
            )}
            <span style={{ fontSize: '10px', color: '#94A3B8', flexShrink: 0, marginLeft: '8px' }}>
              {session.updated_at ? timeAgo(session.updated_at) : ''}
            </span>
          </div>
          <p
            style={{
              fontSize: '0.75rem',
              color: '#94A3B8',
              margin: '2px 0 0 0',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {session.last_message || (session.message_count > 0 ? `${session.message_count} 条消息` : '暂无消息')}
          </p>
        </div>

        {/* Action buttons — visible on row hover via CSS */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '2px', flexShrink: 0, marginLeft: '4px' }}>
          <button
            onClick={(e) => {
              e.stopPropagation()
              setEditing(true)
            }}
            className="session-action-btn"
            title="重命名"
            style={{
              width: '28px',
              height: '28px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: '6px',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: '#94A3B8',
              transition: 'all 0.15s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.opacity = '1'
              e.currentTarget.style.color = '#6366F1'
              e.currentTarget.style.background = '#EEF2FF'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.opacity = ''
              e.currentTarget.style.color = ''
              e.currentTarget.style.background = ''
            }}
          >
            <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
              <path
                d="M11.5 1.5l3 3L5 14H2v-3L11.5 1.5zM10 3l3 3"
                stroke="currentColor"
                strokeWidth="1.25"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>

          <button
            onClick={(e) => {
              e.stopPropagation()
              setShowConfirm(true)
            }}
            className="session-action-btn"
            title="删除会话"
            style={{
              width: '28px',
              height: '28px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: '6px',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: '#94A3B8',
              transition: 'all 0.15s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.opacity = '1'
              e.currentTarget.style.color = '#EF4444'
              e.currentTarget.style.background = '#FEF2F2'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.opacity = ''
              e.currentTarget.style.color = ''
              e.currentTarget.style.background = ''
            }}
          >
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
              <path
                d="M5 2h6M2 4h12M12.667 4l-.467 7.467c-.065 1.037-.097 1.556-.333 1.952a2 2 0 0 1-.863.81C10.592 14.5 10.072 14.5 9.03 14.5H6.97c-1.042 0-1.563 0-1.975-.271a2 2 0 0 1-.863-.81c-.236-.396-.268-.915-.333-1.952L3.333 4M6.333 7v4M9.667 7v4"
                stroke="currentColor"
                strokeWidth="1.25"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
      </div>

      <ConfirmDialog
        open={showConfirm}
        title="确定删除对话？"
        message="删除后，聊天记录将不可恢复。"
        confirmLabel="删除"
        cancelLabel="取消"
        onConfirm={() => {
          setShowConfirm(false)
          onDelete()
        }}
        onCancel={() => setShowConfirm(false)}
      />
    </>
  )
}
