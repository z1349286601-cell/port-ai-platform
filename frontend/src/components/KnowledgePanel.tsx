import { useState, useEffect, useCallback, DragEvent } from 'react'

const API_BASE = '/api/v1'

interface DocInfo {
  doc_name: string
  chunk_count: number
  status: 'ready' | 'processing'
}

interface KnowledgeStatus {
  collection: string
  chunk_count: number
  documents: DocInfo[]
}

export function KnowledgePanel() {
  const [status, setStatus] = useState<KnowledgeStatus | null>(null)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<{ answer: string; sources: Array<{ doc_name: string; excerpt: string; relevance_score: number }> } | null>(null)
  const [searching, setSearching] = useState(false)

  const fetchStatus = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/knowledge/status`)
      const data = await r.json()
      // Backend returns {collection, chunk_count}. Also try to get doc list if available.
      setStatus({
        collection: data.collection || 'port_docs',
        chunk_count: data.chunk_count || data.total_chunks || 0,
        documents: data.documents || data.docs || [],
      })
    } catch {
      // silently fail
    }
  }, [])

  useEffect(() => { fetchStatus() }, [fetchStatus])

  const doUpload = async (file: File) => {
    if (file.size > 10 * 1024 * 1024) {
      setMessage('文件大小不能超过 10MB')
      return
    }

    const ext = file.name.split('.').pop()?.toLowerCase()
    if (!['md', 'txt', 'pdf', 'docx'].includes(ext || '')) {
      setMessage('不支持的文件格式，请上传 .md / .txt / .pdf / .docx')
      return
    }

    setUploading(true)
    setMessage('')

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_BASE}/knowledge/upload`, { method: 'POST', body: formData })
      const data = await res.json()
      if (res.ok) {
        setMessage(`上传成功：${data.filename} (${data.chunks} 个文本块)`)
        fetchStatus()
      } else {
        setMessage(`上传失败: ${data.detail || '未知错误'}`)
      }
    } catch {
      setMessage('上传失败: 网络错误')
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = useCallback((e: DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file) doUpload(file)
  }, [])

  const handleDragOver = (e: DragEvent) => { e.preventDefault(); setDragOver(true) }
  const handleDragLeave = () => setDragOver(false)

  const handleDeleteDoc = async (docName: string) => {
    try {
      const res = await fetch(`${API_BASE}/knowledge/documents/${encodeURIComponent(docName)}`, { method: 'DELETE' })
      if (res.ok || res.status === 404) {
        setMessage(`已删除 ${docName}`)
        fetchStatus()
      } else {
        const data = await res.json()
        setMessage(`删除失败: ${data.detail || '未知错误'}`)
      }
    } catch {
      setMessage('删除失败: 网络错误')
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    setSearching(true)
    setSearchResults(null)
    try {
      const formData = new FormData()
      formData.append('query', searchQuery)
      formData.append('top_k', '3')
      const res = await fetch(`${API_BASE}/knowledge/search`, { method: 'POST', body: formData })
      const data = await res.json()
      if (res.ok) {
        setSearchResults(data)
      }
    } catch {
      setMessage('搜索失败: 网络错误')
    } finally {
      setSearching(false)
    }
  }

  const statCards = [
    { label: '知识库名称', value: status?.collection ?? '...', icon: '📚', gradient: 'linear-gradient(135deg, #EFF6FF, #EEF2FF)', textColor: '#2563EB' },
    { label: '文本块总数', value: String(status?.chunk_count ?? '...'), icon: '📊', gradient: 'linear-gradient(135deg, #ECFDF5, #F0FDF4)', textColor: '#059669' },
    { label: '文档数量', value: String(status?.documents?.length ?? '...'), icon: '📄', gradient: 'linear-gradient(135deg, #F5F3FF, #FAF5FF)', textColor: '#7C3AED' },
  ]

  return (
    <div className="h-full flex flex-col" style={{background: '#F8FAFC'}}>
      {/* Header */}
      <div style={{background: 'white', borderBottom: '1px solid #E2E8F0', padding: '16px 24px'}}>
        <h2 style={{fontSize: '1.125rem', fontWeight: 700, color: '#1E293B', margin: 0}}>知识库管理</h2>
        <p style={{fontSize: '0.75rem', color: '#94A3B8', margin: '2px 0 0 0'}}>管理港口文档、规程和手册的知识库</p>
      </div>

      <div style={{flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px'}}>
        {/* Stats row */}
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px'}}>
          {statCards.map((s) => (
            <div key={s.label} style={{
              background: s.gradient,
              borderRadius: '14px',
              padding: '16px',
              border: '1px solid #F1F5F9',
            }}>
              <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
                <span style={{fontSize: '1.5rem'}}>{s.icon}</span>
                <span style={{fontSize: '0.75rem', color: '#94A3B8'}}>{s.label}</span>
              </div>
              <p style={{fontSize: '1.75rem', fontWeight: 700, color: s.textColor, margin: '8px 0 0 0'}}>{s.value}</p>
            </div>
          ))}
        </div>

        {/* Upload zone */}
        <label
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          style={{
            display: 'block',
            border: `2px dashed ${dragOver ? '#818CF8' : '#E2E8F0'}`,
            borderRadius: '14px',
            padding: '32px',
            textAlign: 'center',
            cursor: 'pointer',
            background: dragOver ? '#EEF2FF' : 'white',
            transition: 'all 0.2s ease',
          }}
        >
          <input
            type="file"
            accept=".md,.txt,.pdf,.docx"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) doUpload(f); }}
            style={{display: 'none'}}
            disabled={uploading}
          />
          {uploading ? (
            <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px'}}>
              <span style={{
                display: 'inline-block',
                width: '32px',
                height: '32px',
                border: '2px solid #818CF8',
                borderTopColor: 'transparent',
                borderRadius: '50%',
                animation: 'spin 0.8s linear infinite',
              }} />
              <p style={{fontSize: '0.875rem', color: '#64748B', margin: 0}}>正在上传并处理文档...</p>
            </div>
          ) : (
            <>
              <div style={{
                width: '48px',
                height: '48px',
                margin: '0 auto 12px',
                borderRadius: '50%',
                background: '#EEF2FF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.5rem',
              }}>
                📁
              </div>
              <p style={{fontSize: '0.875rem', fontWeight: 500, color: '#475569', margin: 0}}>拖拽文件到此处或点击上传</p>
              <p style={{fontSize: '0.75rem', color: '#94A3B8', margin: '4px 0 0 0'}}>支持 .md / .txt / .pdf / .docx，最大 10MB</p>
            </>
          )}
        </label>

        {/* Upload message */}
        {message && (
          <div style={{
            fontSize: '0.875rem',
            padding: '12px 16px',
            borderRadius: '12px',
            background: message.includes('失败') || message.includes('错误') ? '#FEF2F2' : '#ECFDF5',
            color: message.includes('失败') || message.includes('错误') ? '#DC2626' : '#059669',
            border: `1px solid ${message.includes('失败') || message.includes('错误') ? '#FECACA' : '#A7F3D0'}`,
          }}>
            {message}
          </div>
        )}

        {/* Quick search */}
        <div style={{display: 'flex', gap: '8px'}}>
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleSearch(); }}
            placeholder="搜索知识库内容..."
            className="input-box"
            style={{flex: 1, padding: '8px 16px', fontSize: '0.875rem'}}
          />
          <button
            onClick={handleSearch}
            disabled={searching || !searchQuery.trim()}
            className="btn-gradient"
            style={{padding: '8px 20px', fontSize: '0.875rem', border: 'none', cursor: 'pointer', whiteSpace: 'nowrap'}}
          >
            {searching ? '搜索中...' : '搜索'}
          </button>
        </div>

        {/* Search results */}
        {searchResults && (
          <div style={{background: 'white', borderRadius: '12px', border: '1px solid #E2E8F0', padding: '16px'}}>
            <h3 style={{fontSize: '0.875rem', fontWeight: 600, color: '#475569', margin: '0 0 12px 0'}}>搜索结果</h3>
            <p style={{fontSize: '0.8125rem', color: '#334155', lineHeight: 1.7, margin: '0 0 12px 0'}}>{searchResults.answer}</p>
            {searchResults.sources?.length > 0 && (
              <div style={{borderTop: '1px solid #F1F5F9', paddingTop: '10px'}}>
                {searchResults.sources.map((src, i) => (
                  <div key={i} style={{fontSize: '11px', color: '#64748B', marginBottom: '6px', display: 'flex', gap: '8px'}}>
                    <span style={{color: '#818CF8', flexShrink: 0}}>[{i + 1}]</span>
                    <span>{src.doc_name} — {(src.relevance_score * 100).toFixed(0)}% — {src.excerpt?.slice(0, 100)}...</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Document list */}
        {status?.documents && status.documents.length > 0 && (
          <div>
            <h3 style={{fontSize: '0.875rem', fontWeight: 600, color: '#475569', margin: '0 0 12px 0'}}>已上传文档</h3>
            <div style={{display: 'flex', flexDirection: 'column', gap: '8px'}}>
              {status.documents.map((doc, i) => (
                <div
                  key={i}
                  style={{
                    background: 'white',
                    borderRadius: '12px',
                    border: '1px solid #F1F5F9',
                    padding: '12px 16px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div style={{display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0}}>
                    <div style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '10px',
                      background: '#EEF2FF',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '1.125rem',
                      flexShrink: 0,
                    }}>
                      📄
                    </div>
                    <div style={{minWidth: 0}}>
                      <p style={{fontSize: '0.875rem', fontWeight: 500, color: '#334155', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>
                        {doc.doc_name}
                      </p>
                      <p style={{fontSize: '11px', color: '#94A3B8', margin: '2px 0 0 0'}}>
                        {doc.chunk_count} 个文本块
                      </p>
                    </div>
                  </div>
                  <div style={{display: 'flex', alignItems: 'center', gap: '12px', flexShrink: 0}}>
                    <span style={{
                      fontSize: '10px',
                      padding: '2px 10px',
                      borderRadius: '999px',
                      fontWeight: 500,
                      background: doc.status === 'ready' ? '#ECFDF5' : '#FFFBEB',
                      color: doc.status === 'ready' ? '#059669' : '#D97706',
                    }}>
                      {doc.status === 'ready' ? '已就绪' : '处理中'}
                    </span>
                    <button
                      onClick={() => handleDeleteDoc(doc.doc_name)}
                      style={{
                        color: '#94A3B8',
                        fontSize: '0.75rem',
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        padding: '2px',
                      }}
                      title="删除文档"
                    >
                      🗑
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {(!status?.documents || status.documents.length === 0) && status && (
          <div style={{textAlign: 'center', color: '#94A3B8', padding: '32px 0'}}>
            <p style={{fontSize: '2rem', marginBottom: '8px'}}>📭</p>
            <p style={{fontSize: '0.875rem', margin: 0}}>暂无已上传文档</p>
            <p style={{fontSize: '0.75rem', margin: '4px 0 0 0'}}>上传文档后，文档将自动分块并存入向量数据库</p>
          </div>
        )}
      </div>
    </div>
  )
}
