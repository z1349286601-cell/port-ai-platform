import { useState } from 'react'
import type { SourceItem } from '../api/types'

interface Props {
  sources: SourceItem[]
}

export function SourceCitation({ sources }: Props) {
  const [open, setOpen] = useState(false)

  if (!sources || sources.length === 0) return null

  return (
    <div style={{marginTop: '12px', borderTop: '1px solid #F1F5F9', paddingTop: '8px'}}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          fontSize: '0.75rem',
          color: '#6366F1',
          fontWeight: 500,
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: 0,
          transition: 'color 0.15s',
        }}
      >
        <svg
          width="12" height="12" viewBox="0 0 12 12" fill="none"
          style={{transition: 'transform 0.2s', transform: open ? 'rotate(90deg)' : ''}}
        >
          <path d="M4 2l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M6 1v10M2 3v6M10 3v6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
        参考来源 ({sources.length})
      </button>

      {open && (
        <div style={{marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '6px'}}>
          {sources.map((s, i) => (
            <div
              key={i}
              style={{
                background: '#F8FAFC',
                borderRadius: '10px',
                padding: '10px 12px',
                border: '1px solid #F1F5F9',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                <span style={{
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  color: '#4F46E5',
                  flex: 1,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}>
                  {s.doc_title || s.doc_name}
                </span>
                <span style={{
                  fontSize: '10px',
                  color: '#94A3B8',
                  background: 'white',
                  borderRadius: '4px',
                  padding: '2px 6px',
                }}>
                  {(s.relevance_score * 100).toFixed(0)}%
                </span>
              </div>
              {s.section_title && (
                <p style={{fontSize: '10px', color: '#94A3B8', margin: '2px 0 0 0'}}>{s.section_title}</p>
              )}
              {s.excerpt && (
                <p style={{
                  fontSize: '11px',
                  color: '#64748B',
                  margin: '4px 0 0 0',
                  lineHeight: 1.5,
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                }}>
                  {s.excerpt}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
