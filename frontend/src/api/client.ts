import type { SSEEvent } from './types'

const BASE_URL = '/api/v1'

export async function postChatStream(
  message: string,
  sessionId: string | null,
  onEvent: (event: SSEEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${BASE_URL}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
    signal,
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  const reader = response.body?.getReader()
  if (!reader) throw new Error('No response body')

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    let eventType = ''
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        eventType = line.slice(7).trim()
      } else if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6))
        onEvent({ type: eventType, data } as SSEEvent)
      }
    }
  }
}
