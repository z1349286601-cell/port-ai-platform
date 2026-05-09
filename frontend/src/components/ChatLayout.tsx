import { useEffect, useState } from 'react'
import { useChatStore } from '../store/chatStore'
import { ChatSidebar } from './ChatSidebar'
import { ChatWindow } from './ChatWindow'
import { KnowledgePanel } from './KnowledgePanel'

type Tab = 'chat' | 'knowledge'

export function ChatLayout() {
  const {
    sessions,
    currentSessionId,
    messages,
    isStreaming,
    currentReply,
    currentIntent,
    currentThinking,
    error,
    loadSessions,
    createSession,
    switchSession,
    deleteSession,
    updateSessionTitle,
    sendMessage,
    setError,
  } = useChatStore()

  const [activeTab, setActiveTab] = useState<Tab>('chat')

  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  const handleNewSession = async () => {
    const id = await createSession()
    if (id) switchSession(id)
  }

  return (
    <div className="h-screen flex flex-col" style={{background: '#F8FAFC'}}>
      {/* Top bar */}
      <header style={{
        height: '56px',
        background: 'white',
        borderBottom: '1px solid #E2E8F0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 20px',
        flexShrink: 0,
        zIndex: 10,
      }}>
        <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
          <div style={{
            width: '34px',
            height: '34px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 700,
            fontSize: '15px',
          }}>
            P
          </div>
          <span style={{fontWeight: 600, color: '#1E293B', fontSize: '1rem'}}>港口AI智能平台</span>
          <span style={{
            fontSize: '10px',
            background: '#EEF2FF',
            color: '#4F46E5',
            padding: '2px 8px',
            borderRadius: '999px',
            fontWeight: 500,
          }}>
            Phase 1
          </span>
        </div>

        {/* Tab nav */}
        <nav className="tab-wrap" style={{display: 'flex'}}>
          <button
            onClick={() => setActiveTab('chat')}
            className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
          >
            对话
          </button>
          <button
            onClick={() => setActiveTab('knowledge')}
            className={`tab-btn ${activeTab === 'knowledge' ? 'active' : ''}`}
          >
            知识库
          </button>
        </nav>

        <div style={{width: '120px'}} />
      </header>

      {/* Main area */}
      <div style={{flex: 1, display: 'flex', overflow: 'hidden'}}>
        {activeTab === 'knowledge' ? (
          <KnowledgePanel />
        ) : (
          <>
            <ChatSidebar
              sessions={sessions}
              currentSessionId={currentSessionId}
              onSelectSession={(id) => { switchSession(id); }}
              onNewSession={handleNewSession}
              onDeleteSession={deleteSession}
              onRenameSession={(id, title) => updateSessionTitle(id, title)}
            />
            <ChatWindow
              messages={messages}
              streamingContent={currentReply}
              isStreaming={isStreaming}
              streamingIntent={currentIntent}
              streamingThinking={currentThinking}
              error={error}
              onSend={(content) => sendMessage(content)}
              onDismissError={() => setError(null)}
              onHintClick={(hint) => sendMessage(hint)}
            />
          </>
        )}
      </div>
    </div>
  )
}
