import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

// API service for OpenCode
export const opencodeApi = {
  // Session management
  async listSessions() {
    const response = await api.get('/sessions')
    return response.data
  },

  async createSession(title = null) {
    const response = await api.post('/sessions', { title })
    return response.data
  },

  async getSession(sessionId) {
    const response = await api.get(`/sessions/${sessionId}`)
    return response.data
  },

  async deleteSession(sessionId) {
    const response = await api.delete(`/sessions/${sessionId}`)
    return response.data
  },

  // Chat
  async sendMessage(sessionId, prompt) {
    const response = await api.post(`/sessions/${sessionId}/chat`, { prompt })
    return response.data
  },

  async streamMessage(sessionId, prompt, onChunk) {
    const response = await fetch(`/api/sessions/${sessionId}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ prompt })
    })

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') continue
          try {
            const parsed = JSON.parse(data)
            onChunk(parsed)
          } catch (e) {
            console.error('Error parsing SSE data:', e)
          }
        }
      }
    }
  }
}

export default api
