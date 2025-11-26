import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { opencodeApi, backendApi } from '../services/api'
import { useChatStore } from './chat'

export const useSessionStore = defineStore('session', () => {
  const sessions = ref([])
  const currentSessionId = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const currentSession = computed(() => {
    return sessions.value.find(s => s.session_id === currentSessionId.value) || null
  })

  async function fetchSessions() {
    loading.value = true
    error.value = null
    try {
      const response = await backendApi.listSessions()
      sessions.value = response.sessions || []
    } catch (e) {
      error.value = 'Failed to fetch sessions'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  async function createSession(title = null) {
    loading.value = true
    error.value = null
    try {
      const newSession = await backendApi.createSession({
        name: title,
        description: null
      })
      sessions.value.unshift(newSession)
      currentSessionId.value = newSession.session_id
      return newSession
    } catch (e) {
      error.value = 'Failed to create session'
      console.error(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteSession(sessionId) {
    loading.value = true
    error.value = null
    try {
      await backendApi.deleteSession(sessionId)
      sessions.value = sessions.value.filter(s => s.session_id !== sessionId)

      // Clean up chat messages for this session
      const chatStore = useChatStore()
      chatStore.deleteSessionMessages(sessionId)

      if (currentSessionId.value === sessionId) {
        currentSessionId.value = sessions.value[0]?.session_id || null
      }
    } catch (e) {
      error.value = 'Failed to delete session'
      console.error(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function selectSession(sessionId) {
    currentSessionId.value = sessionId

    // Load messages from the OpenCode agent server
    const chatStore = useChatStore()
    await chatStore.loadMessages(sessionId)
  }

  async function startContainer(sessionId, containerConfig = {}) {
    loading.value = true
    error.value = null
    try {
      const config = {
        image: containerConfig.image || 'opencode-agent:latest',
        environment: containerConfig.environment || {},
        is_agent: true
      }
      const result = await backendApi.startContainer(sessionId, config)

      // Update session in list
      const sessionIndex = sessions.value.findIndex(s => s.session_id === sessionId)
      if (sessionIndex !== -1) {
        sessions.value[sessionIndex].container_id = result.container_id
        sessions.value[sessionIndex].container_status = result.status
      }

      return result
    } catch (e) {
      error.value = 'Failed to start container'
      console.error(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function stopContainer(sessionId) {
    loading.value = true
    error.value = null
    try {
      const result = await backendApi.stopContainer(sessionId)

      // Update session in list
      const sessionIndex = sessions.value.findIndex(s => s.session_id === sessionId)
      if (sessionIndex !== -1) {
        sessions.value[sessionIndex].container_status = 'stopped'
      }

      return result
    } catch (e) {
      error.value = 'Failed to stop container'
      console.error(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function getContainerStatus(sessionId) {
    try {
      const status = await backendApi.getContainerStatus(sessionId)

      // Update session in list
      const sessionIndex = sessions.value.findIndex(s => s.session_id === sessionId)
      if (sessionIndex !== -1) {
        sessions.value[sessionIndex].container_status = status.status
      }

      return status
    } catch (e) {
      console.error('Failed to get container status:', e)
      throw e
    }
  }

  async function getContainerLogs(sessionId, tail = 100) {
    try {
      return await backendApi.getContainerLogs(sessionId, tail)
    } catch (e) {
      console.error('Failed to get container logs:', e)
      throw e
    }
  }

  async function updateSession(sessionId, data) {
    loading.value = true
    error.value = null
    try {
      const updatedSession = await backendApi.updateSession(sessionId, data)

      // Update session in list
      const sessionIndex = sessions.value.findIndex(s => s.session_id === sessionId)
      if (sessionIndex !== -1) {
        sessions.value[sessionIndex] = { ...sessions.value[sessionIndex], ...updatedSession }
      }

      return updatedSession
    } catch (e) {
      error.value = 'Failed to update session'
      console.error(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    sessions,
    currentSessionId,
    currentSession,
    loading,
    error,
    fetchSessions,
    createSession,
    deleteSession,
    selectSession,
    startContainer,
    stopContainer,
    getContainerStatus,
    getContainerLogs,
    updateSession
  }
})
