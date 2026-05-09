export const INTENT_LABELS: Record<string, { label: string; bg: string; text: string; border: string; icon: string }> = {
  document_qa: { label: '知识检索', bg: '#ECFDF5', text: '#059669', border: '#A7F3D0', icon: '📖' },
  data_query:  { label: '数据查询', bg: '#EFF6FF', text: '#2563EB', border: '#BFDBFE', icon: '🔍' },
  mixed:       { label: '混合查询', bg: '#F5F3FF', text: '#7C3AED', border: '#DDD6FE', icon: '🔗' },
  chitchat:    { label: '闲聊',     bg: '#F8FAFC', text: '#64748B', border: '#E2E8F0', icon: '💬' },
}

interface Props {
  intent: string
}

export function IntentBadge({ intent }: Props) {
  const info = INTENT_LABELS[intent]
  if (!info) return null

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '4px',
      fontSize: '10px',
      padding: '2px 8px',
      borderRadius: '999px',
      fontWeight: 500,
      background: info.bg,
      color: info.text,
      border: `1px solid ${info.border}`,
    }}>
      <span style={{fontSize: '11px'}}>{info.icon}</span>
      {info.label}
    </span>
  )
}
