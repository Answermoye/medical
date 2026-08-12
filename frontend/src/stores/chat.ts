import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chatApi } from '@/api/chat'
import type { Session, Message, ChatMode } from '@/types'

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<Session[]>([])
  const currentSessionId = ref<string>('')
  const messages = ref<Message[]>([])
  const currentMode = ref<ChatMode>('triage')
  const isLoading = ref(false)

  async function fetchSessions() {
    try {
      const res = await chatApi.getSessions()
      sessions.value = res
    } catch {
      sessions.value = []
    }
  }

  async function createSession(mode: ChatMode) {
    try {
      const res = await chatApi.createSession(mode)
      sessions.value.unshift(res)
      currentSessionId.value = res.id
      messages.value = []
      currentMode.value = mode
      return res
    } catch {
      return null
    }
  }

  async function fetchMessages(sessionId: string) {
    try {
      const res = await chatApi.getMessages(sessionId)
      messages.value = res
    } catch {
      messages.value = []
    }
  }

  function switchSession(sessionId: string) {
    currentSessionId.value = sessionId
    fetchMessages(sessionId)
    const session = sessions.value.find(s => s.id === sessionId)
    if (session) {
      currentMode.value = session.mode
    }
  }

  function addMessage(message: Message) {
    messages.value.push(message)
  }

  function appendToLastAssistantMessage(content: string) {
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.role === 'assistant') {
      lastMsg.content += content
    } else {
      messages.value.push({
        id: Date.now().toString(),
        session_id: currentSessionId.value,
        role: 'assistant',
        content,
        message_type: 'text',
        created_at: new Date().toISOString(),
      })
    }
  }

  function streamMessage(
    sessionId: string,
    content: string,
    onMessage: (data: string) => void,
    onError?: (error: Error) => void,
    image?: File
  ) {
    const token = localStorage.getItem('token')
    const formData = new FormData()
    formData.append('content', content)
    if (image) {
      formData.append('image', image)
    }

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
  }

  return {
    sessions,
    currentSessionId,
    messages,
    currentMode,
    isLoading,
    fetchSessions,
    createSession,
    fetchMessages,
    switchSession,
    addMessage,
    appendToLastAssistantMessage,
    streamMessage,
  }
})
