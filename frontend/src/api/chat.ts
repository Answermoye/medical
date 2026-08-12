import request from './request'
import type { Session, Message, ChatMode } from '@/types'

export const chatApi = {
  createSession(mode: ChatMode): Promise<Session> {
    return request.post('/chat/sessions', { mode })
  },

  getSessions(): Promise<Session[]> {
    return request.get('/chat/sessions')
  },

  getSession(sessionId: string): Promise<Session> {
    return request.get(`/chat/sessions/${sessionId}`)
  },

  getMessages(sessionId: string): Promise<Message[]> {
    return request.get(`/chat/sessions/${sessionId}/messages`)
  },

  sendMessage(sessionId: string, content: string, image?: File): Promise<any> {
    const formData = new FormData()
    formData.append('content', content)
    if (image) {
      formData.append('image', image)
    }
    return request.post(`/chat/sessions/${sessionId}/messages`, formData)
  },

  // SSE流式发送消息
  streamMessage(
    sessionId: string,
    content: string,
    onMessage: (data: string) => void,
    onError?: (error: Error) => void,
    image?: File
  ): EventSource {
    const token = localStorage.getItem('token')
    const formData = new FormData()
    formData.append('content', content)
    if (image) {
      formData.append('image', image)
    }

    // 使用fetch实现SSE
    fetch(`/api/v1/chat/sessions/${sessionId}/messages/stream`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        const reader = response.body?.getReader()
        if (!reader) return

        const decoder = new TextDecoder()
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          const text = decoder.decode(value, { stream: true })
          const lines = text.split('\n')
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              onMessage(line.slice(6))
            }
          }
        }
      })
      .catch((error) => {
        onError?.(error)
      })

    // 返回一个伪EventSource对象
    return {} as EventSource
  },
}
