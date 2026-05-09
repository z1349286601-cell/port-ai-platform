import ReactMarkdown from 'react-markdown'

interface Props {
  content: string
  isStreaming: boolean
}

export function StreamingText({ content, isStreaming }: Props) {
  return (
    <div className="prose-custom">
      <ReactMarkdown>{content}</ReactMarkdown>
      {isStreaming && (
        <span style={{
          display: 'inline-block',
          width: '8px',
          height: '18px',
          background: '#6366F1',
          borderRadius: '2px',
          marginLeft: '2px',
          verticalAlign: 'middle',
          animation: 'pulse 0.8s ease-in-out infinite',
        }} />
      )}
    </div>
  )
}
