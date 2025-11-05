import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { opencodeApi } from '../services/api'

export const useChatStore = defineStore('chat', () => {
  // Map of sessionId -> messages array
  const messagesBySession = ref({})
  const loading = ref(false)
  const error = ref(null)
  const streaming = ref(false)
  
  // Model selection state
  const selectedProvider = ref('github-copilot')
  const selectedModel = ref('gpt-5-mini')
  const availableModels = ref(null)
  const modelsLoading = ref(false)

  // Load messages from localStorage on initialization
  const loadMessagesFromStorage = () => {
    try {
      const stored = localStorage.getItem('opencode_chat_messages')
      if (stored) {
        messagesBySession.value = JSON.parse(stored)
      }
    } catch (e) {
      console.error('Failed to load messages from localStorage:', e)
    }
  }

  // Save messages to localStorage
  const saveMessagesToStorage = () => {
    try {
      localStorage.setItem('opencode_chat_messages', JSON.stringify(messagesBySession.value))
    } catch (e) {
      console.error('Failed to save messages to localStorage:', e)
    }
  }

  // Initialize from localStorage
  loadMessagesFromStorage()

  // Watch for changes and save to localStorage
  watch(messagesBySession, saveMessagesToStorage, { deep: true })

  function getMessages(sessionId) {
    if (!messagesBySession.value[sessionId]) {
      messagesBySession.value[sessionId] = []
    }
    return messagesBySession.value[sessionId]
  }

  function addMessage(sessionId, message) {
    if (!messagesBySession.value[sessionId]) {
      messagesBySession.value[sessionId] = []
    }
    messagesBySession.value[sessionId].push(message)
  }

  function updateLastMessage(sessionId, content) {
    const messages = messagesBySession.value[sessionId]
    if (messages && messages.length > 0) {
      const lastMsg = messages[messages.length - 1]
      lastMsg.content = content
    }
  }

  async function sendMessage(sessionId, prompt) {
    loading.value = true
    error.value = null
    streaming.value = false

    // Add user message
    addMessage(sessionId, {
      role: 'user',
      content: prompt,
      timestamp: new Date().toISOString()
    })

    try {
      const response = await opencodeApi.sendMessage(sessionId, prompt, {
        provider_id: selectedProvider.value,
        model_id: selectedModel.value
      })

      // Add assistant message
      addMessage(sessionId, {
        role: 'assistant',
        content: response.content || response.message || JSON.stringify(response),
        timestamp: new Date().toISOString()
      })
    } catch (e) {
      error.value = 'Failed to send message'
      console.error(e)

      // Add error message
      addMessage(sessionId, {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your message.',
        timestamp: new Date().toISOString(),
        isError: true
      })
      throw e
    } finally {
      loading.value = false
    }
  }

  async function sendMessageStream(sessionId, prompt) {
    loading.value = true
    error.value = null
    streaming.value = true

    // Add user message
    addMessage(sessionId, {
      role: 'user',
      content: prompt,
      timestamp: new Date().toISOString()
    })

    // Add empty assistant message that will be updated
    addMessage(sessionId, {
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString()
    })

    try {
      await opencodeApi.streamMessage(sessionId, prompt, (chunk) => {
        if (chunk.content) {
          const messages = messagesBySession.value[sessionId]
          const lastMsg = messages[messages.length - 1]
          lastMsg.content += chunk.content
        }
      })
    } catch (e) {
      error.value = 'Failed to stream message'
      console.error(e)
      updateLastMessage(sessionId, 'Sorry, I encountered an error processing your message.')
      throw e
    } finally {
      loading.value = false
      streaming.value = false
    }
  }

  function clearMessages(sessionId) {
    messagesBySession.value[sessionId] = []
  }

  function deleteSessionMessages(sessionId) {
    if (messagesBySession.value[sessionId]) {
      delete messagesBySession.value[sessionId]
    }
  }

  async function fetchModels() {
    modelsLoading.value = true
    try {
      const data = await opencodeApi.getModels()
      availableModels.value = data
      
      // Set default provider and model if available
      if (data.default) {
        const firstProvider = Object.keys(data.default)[0]
        if (firstProvider) {
          selectedProvider.value = firstProvider
          selectedModel.value = data.default[firstProvider]
        }
      }
    } catch (e) {
      console.error('Failed to fetch models:', e)
    } finally {
      modelsLoading.value = false
    }
  }

  function setModel(providerId, modelId) {
    selectedProvider.value = providerId
    selectedModel.value = modelId
  }

  return {
    messagesBySession,
    loading,
    error,
    streaming,
    selectedProvider,
    selectedModel,
    availableModels,
    modelsLoading,
    getMessages,
    addMessage,
    sendMessage,
    sendMessageStream,
    clearMessages,
    deleteSessionMessages,
    fetchModels,
    setModel
  }
})
