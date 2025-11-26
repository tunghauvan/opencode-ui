import axios from 'axios'

const api = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api`,
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true
})

// Add user_id to requests if available
api.interceptors.request.use((config) => {
  // Cookies will be sent automatically with withCredentials: true
  return config
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

  async getSessionMessages(sessionId) {
    const response = await api.get(`/sessions/${sessionId}/messages`)
    return response.data
  },

  async deleteSession(sessionId) {
    const response = await api.delete(`/sessions/${sessionId}`)
    return response.data
  },

  // Chat
  async sendMessage(sessionId, prompt, options = {}) {
    const { provider_id = 'github-copilot', model_id = 'gpt-5-mini' } = options
    const response = await api.post(`/sessions/${sessionId}/chat`, {
      prompt,
      model: {
        providerID: provider_id,
        modelID: model_id
      }
    })
    return response.data
  },

  // Models
  async getModels() {
    const response = await api.get('/models')
    return response.data
  },

  async streamMessage(sessionId, prompt, onChunk) {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const response = await fetch(`${baseUrl}/api/sessions/${sessionId}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
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

// Backend API for session and container management
export const backendApi = {
  // Session management
  async listSessions(filters = {}) {
    const params = new URLSearchParams()
    if (filters.status) params.append('status', filters.status)
    if (filters.is_active !== undefined) params.append('is_active', filters.is_active)

    const response = await api.get(`/backend/sessions?${params}`)
    return response.data
  },

  async createSession(sessionData = {}) {
    const response = await api.post('/backend/sessions', sessionData)
    return response.data
  },

  async getSession(sessionId) {
    const response = await api.get(`/backend/sessions/${sessionId}`)
    return response.data
  },

  async updateSession(sessionId, data) {
    const response = await api.put(`/backend/sessions/${sessionId}`, data)
    return response.data
  },

  async deleteSession(sessionId) {
    const response = await api.delete(`/backend/sessions/${sessionId}`)
    return response.data
  },

  // Container management
  async startContainer(sessionId, containerConfig) {
    const response = await api.post(`/backend/sessions/${sessionId}/container/start`, containerConfig)
    return response.data
  },

  async stopContainer(sessionId) {
    const response = await api.post(`/backend/sessions/${sessionId}/container/stop`)
    return response.data
  },

  async getContainerStatus(sessionId) {
    const response = await api.get(`/backend/sessions/${sessionId}/container/status`)
    return response.data
  },

  async getContainerLogs(sessionId, tail = 100) {
    const response = await api.get(`/backend/sessions/${sessionId}/container/logs?tail=${tail}`)
    return response.data
  },

  // Chat via backend
  async sendMessage(sessionId, prompt) {
    const response = await api.post(`/backend/sessions/${sessionId}/chat`, { prompt })
    return response.data
  },

  // Get messages from OpenCode agent
  async getMessages(sessionId) {
    const response = await api.get(`/backend/sessions/${sessionId}/messages`)
    return response.data
  },

  // Analytics
  async getSessionStats() {
    const response = await api.get('/backend/sessions/stats/overview')
    return response.data
  },

  async getSessionTimeline(sessionId) {
    const response = await api.get(`/backend/sessions/${sessionId}/timeline`)
    return response.data
  },

  async getRecentSessions(limit = 10) {
    const response = await api.get(`/backend/sessions/recent?limit=${limit}`)
    return response.data
  },

  async getModels() {
    const response = await api.get('/models')
    return response.data
  },

  // File Access API
  async listFiles(sessionId, path = '/') {
    const response = await api.get(`/backend/sessions/${sessionId}/files/list`, {
      params: { path }
    })
    return response.data
  },

  async readFile(sessionId, path) {
    const response = await api.get(`/backend/sessions/${sessionId}/files/read`, {
      params: { path }
    })
    return response.data
  },

  async writeFile(sessionId, path, content, encoding = 'utf-8') {
    const response = await api.post(`/backend/sessions/${sessionId}/files/write`, 
      { content, encoding },
      { params: { path } }
    )
    return response.data
  },

  async deleteFile(sessionId, path) {
    const response = await api.delete(`/backend/sessions/${sessionId}/files/delete`, {
      params: { path }
    })
    return response.data
  },

  async createDirectory(sessionId, path) {
    const response = await api.post(`/backend/sessions/${sessionId}/files/mkdir`, null, {
      params: { path }
    })
    return response.data
  },

  async deleteDirectory(sessionId, path, recursive = false) {
    const response = await api.delete(`/backend/sessions/${sessionId}/files/rmdir`, {
      params: { path, recursive }
    })
    return response.data
  }
}

export default api
