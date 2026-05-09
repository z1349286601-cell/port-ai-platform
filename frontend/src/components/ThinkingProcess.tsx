import { useState } from 'react'
import type { ThinkingData } from '../api/types'
import { INTENT_LABELS } from './IntentBadge'

interface Props {
  thinking: ThinkingData
  latencyMs?: number
}

function ConfidenceBar({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100)
  const color = confidence > 0.7 ? '#059669' : confidence > 0.4 ? '#D97706' : '#DC2626'
  const bg = confidence > 0.7 ? '#D1FAE5' : confidence > 0.4 ? '#FEF3C7' : '#FEE2E2'
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '4px',
      fontSize: '11px', fontWeight: 600, color,
      background: bg, padding: '1px 6px', borderRadius: '4px',
    }}>
      {pct}%
      <span style={{ display: 'inline-flex', gap: '1px' }}>
        {Array.from({ length: 10 }).map((_, i) => (
          <span key={i} style={{
            width: '4px', height: '8px', borderRadius: '1px',
            background: i < Math.round(confidence * 10) ? color : '#E2E8F0',
          }} />
        ))}
      </span>
    </span>
  )
}

export function ThinkingProcess({ thinking, latencyMs }: Props) {
  const [expanded, setExpanded] = useState(false)
  const info = INTENT_LABELS[thinking.intent]

  const sections: { label: string; render: () => JSX.Element | null }[] = []

  // Intent section
  sections.push({
    label: '意图识别',
    render: () => (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '12px', color: '#475569' }}>
            {thinking.rule_triggered ? '规则兜底' : 'LLM 判定'}
          </span>
          {info && (
            <span style={{
              fontSize: '10px', padding: '1px 6px', borderRadius: '999px',
              fontWeight: 500, background: info.bg, color: info.text, border: `1px solid ${info.border}`,
            }}>
              {info.icon} {info.label}
            </span>
          )}
          <ConfidenceBar confidence={thinking.confidence} />
          {thinking.rule_triggered && (
            <span style={{
              fontSize: '10px', background: '#FEF3C7', color: '#92400E',
              padding: '1px 6px', borderRadius: '999px', fontWeight: 500,
            }}>
              ⚠ 规则纠正
            </span>
          )}
        </div>
        {thinking.reasoning && (
          <p style={{ fontSize: '11px', color: '#94A3B8', margin: 0, lineHeight: 1.5 }}>
            {thinking.reasoning}
          </p>
        )}
      </div>
    ),
  })

  // RAG section (document_qa / mixed)
  if (thinking.chunks_retrieved != null) {
    sections.push({
      label: '知识检索',
      render: () => (
        <div style={{ fontSize: '12px', color: '#475569', display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
          <span>检索到 <b>{thinking.chunks_retrieved}</b> 个相关片段</span>
          {thinking.top_relevance_score != null && (
            <span>最高相关度 <b>{(thinking.top_relevance_score * 100).toFixed(1)}%</b></span>
          )}
        </div>
      ),
    })
  }

  // NL2SQL section (data_query / mixed)
  if (thinking.sql || thinking.domain) {
    sections.push({
      label: '数据查询',
      render: () => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ fontSize: '12px', color: '#475569', display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            {thinking.domain && <span>域 <b>{thinking.domain}</b></span>}
            {thinking.row_count != null && <span>返回 <b>{thinking.row_count}</b> 行</span>}
            {thinking.execution_ms != null && <span>执行耗时 <b>{thinking.execution_ms}ms</b></span>}
            {thinking.cache_hit && (
              <span style={{ color: '#059669', fontWeight: 500 }}>✓ 命中缓存</span>
            )}
            {thinking.retry_count != null && thinking.retry_count > 0 && (
              <span style={{ color: '#D97706' }}>重试 {thinking.retry_count} 次</span>
            )}
          </div>
          {thinking.sql && (
            <pre style={{
              background: '#1E293B', color: '#E2E8F0', fontSize: '11px',
              padding: '8px 12px', borderRadius: '8px', margin: 0,
              overflowX: 'auto', maxHeight: '120px', overflowY: 'auto',
              lineHeight: 1.5, whiteSpace: 'pre-wrap', wordBreak: 'break-all',
            }}>
              {thinking.sql}
            </pre>
          )}
        </div>
      ),
    })
  }

  return (
    <div className="thinking-process" style={{ maxWidth: '85%' }}>
      {/* Collapsed summary */}
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer',
          userSelect: 'none', padding: '6px 10px',
        }}
      >
        <span style={{ fontSize: '11px', color: '#6366F1', transition: 'transform 0.15s', transform: expanded ? 'rotate(90deg)' : 'rotate(0deg)' }}>
          ▶
        </span>
        <span style={{ fontSize: '11px', fontWeight: 600, color: '#475569' }}>思考过程</span>
        {info && (
          <span style={{
            fontSize: '10px', padding: '1px 6px', borderRadius: '999px',
            fontWeight: 500, background: info.bg, color: info.text,
          }}>
            {info.label}
          </span>
        )}
        <ConfidenceBar confidence={thinking.confidence} />
        {latencyMs != null && (
          <span style={{ fontSize: '10px', color: '#94A3B8' }}>{latencyMs}ms</span>
        )}
      </div>

      {/* Expanded details */}
      {expanded && (
        <div style={{ padding: '0 10px 10px 24px' }}>
          {sections.map((section, i) => {
            const rendered = section.render()
            if (!rendered) return null
            return (
              <div key={i} style={{ marginTop: i > 0 ? '10px' : '0' }}>
                <div style={{ fontSize: '10px', fontWeight: 600, color: '#94A3B8', textTransform: 'uppercase', marginBottom: '4px', letterSpacing: '0.5px' }}>
                  {section.label}
                </div>
                {rendered}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
