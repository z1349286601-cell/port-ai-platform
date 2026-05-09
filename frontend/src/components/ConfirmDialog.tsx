import { useEffect, useRef } from 'react'

interface Props {
  open: boolean
  title?: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = '确定',
  cancelLabel = '取消',
  onConfirm,
  onCancel,
}: Props) {
  const confirmRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (open) {
      confirmRef.current?.focus()
      const handler = (e: KeyboardEvent) => {
        if (e.key === 'Escape') onCancel()
      }
      document.addEventListener('keydown', handler)
      return () => document.removeEventListener('keydown', handler)
    }
  }, [open, onCancel])

  if (!open) return null

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(15, 23, 42, 0.35)',
        backdropFilter: 'blur(4px)',
        animation: 'fadeInUp 0.2s ease-out',
      }}
      onClick={onCancel}
    >
      <div
        style={{
          background: 'white',
          borderRadius: '16px',
          padding: '24px',
          maxWidth: '360px',
          width: '90%',
          boxShadow: '0 0 0 0.5px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.12), 0 16px 48px rgba(0,0,0,0.08)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {title && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <div style={{
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              background: '#FEF3C7',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}>
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path d="M8 2v8M8 13v1" stroke="#F59E0B" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </div>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#1E293B', margin: 0 }}>
              {title}
            </h3>
          </div>
        )}
        <p style={{ fontSize: '0.875rem', lineHeight: 1.6, color: '#475569', margin: 0, whiteSpace: 'pre-line' }}>
          {message}
        </p>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
          <button
            onClick={onCancel}
            style={{
              padding: '8px 20px',
              borderRadius: '8px',
              border: '1px solid #E2E8F0',
              background: 'white',
              color: '#475569',
              fontSize: '0.875rem',
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = '#F8FAFC' }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'white' }}
          >
            {cancelLabel}
          </button>
          <button
            ref={confirmRef}
            onClick={onConfirm}
            style={{
              padding: '8px 20px',
              borderRadius: '8px',
              border: 'none',
              background: 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)',
              color: 'white',
              fontSize: '0.875rem',
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'all 0.15s ease',
              boxShadow: '0 2px 8px rgba(239, 68, 68, 0.35)',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 4px 12px rgba(239, 68, 68, 0.5)'; e.currentTarget.style.transform = 'translateY(-1px)' }}
            onMouseLeave={(e) => { e.currentTarget.style.boxShadow = '0 2px 8px rgba(239, 68, 68, 0.35)'; e.currentTarget.style.transform = 'none' }}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
