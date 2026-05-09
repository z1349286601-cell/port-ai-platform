import type { Session } from '../api/types'
import { SessionItem } from './SessionItem'

interface Props {
  sessions: Session[]
  currentSessionId: string | null
  onSelectSession: (id: string) => void
  onNewSession: () => void
  onDeleteSession: (id: string) => void
  onRenameSession: (id: string, title: string) => void
}

export function ChatSidebar({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  onRenameSession,
}: Props) {
  return (
    <aside className="sidebar w-[280px] flex flex-col h-full shrink-0">
      {/* New session button */}
      <div style={{padding: '16px'}}>
        <button
          onClick={onNewSession}
          className="btn-gradient"
          style={{width: '100%', padding: '10px 0', fontSize: '0.875rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px'}}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          新建会话
        </button>
      </div>

      {/* Session list */}
      <div style={{flex: 1, overflowY: 'auto', padding: '0 8px'}}>
        {sessions.length === 0 && (
          <div style={{textAlign: 'center', color: '#94A3B8', fontSize: '0.875rem', marginTop: '64px'}}>
            <p style={{fontSize: '1.5rem', marginBottom: '8px'}}>💬</p>
            <p>暂无会话记录</p>
            <p style={{fontSize: '0.75rem', marginTop: '4px'}}>点击上方按钮开始新对话</p>
          </div>
        )}
        {sessions.map((s) => (
          <SessionItem
            key={s.session_id}
            session={s}
            isActive={s.session_id === currentSessionId}
            onClick={() => onSelectSession(s.session_id)}
            onDelete={() => onDeleteSession(s.session_id)}
            onRename={(title) => onRenameSession(s.session_id, title)}
          />
        ))}
      </div>

      {/* Footer */}
      <div style={{padding: '12px', borderTop: '1px solid #F1F5F9', textAlign: 'center'}}>
        <p style={{fontSize: '11px', color: '#94A3B8'}}>港口AI智能平台 · Phase 1 MVP</p>
      </div>
    </aside>
  )
}
