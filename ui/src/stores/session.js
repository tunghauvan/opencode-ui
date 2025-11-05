import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { opencodeApi } from '../services/api'
import { useChatStore } from './chat'

export const useSessionStore = defineStore('session', () => {
  const sessions = ref([])
  const currentSessionId = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const currentSession = computed(() => {
    return sessions.value.find(s => s.id === currentSessionId.value) || null
  })

  async function fetchSessions() {
    loading.value = true
    error.value = null
    try {
      sessions.value = await opencodeApi.listSessions()
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
      const newSession = await opencodeApi.createSession(title)
      sessions.value.unshift(newSession)
      currentSessionId.value = newSession.id
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
      await opencodeApi.deleteSession(sessionId)
      sessions.value = sessions.value.filter(s => s.id !== sessionId)
      
      // Clean up chat messages for this session
      const chatStore = useChatStore()
      chatStore.deleteSessionMessages(sessionId)
      
      if (currentSessionId.value === sessionId) {
        currentSessionId.value = sessions.value[0]?.id || null
      }
    } catch (e) {
      error.value = 'Failed to delete session'
      console.error(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  function selectSession(sessionId) {
    currentSessionId.value = sessionId
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
    selectSession
  }
})
