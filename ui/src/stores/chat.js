import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { opencodeApi, backendApi } from '../services/api'

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

    // Add user message immediately for instant display
    addMessage(sessionId, {
      info: {
        role: 'user',
        time: { created: Date.now() }
      },
      parts: [{
        type: 'text',
        text: prompt
      }]
    })

    try {
      // Use backend API for chat
      const response = await backendApi.sendMessage(sessionId, prompt)

      // Add assistant response
      if (response.content) {
        addMessage(sessionId, {
          info: {
            role: 'assistant',
            time: { created: Date.now() }
          },
          parts: [{
            type: 'text',
            text: response.content
          }]
        })
      }

      // Messages are now managed locally, no need to reload from API
    } catch (e) {
      error.value = 'Failed to send message'
      console.error(e)

      // Add error message
      addMessage(sessionId, {
        info: {
          role: 'assistant',
          time: { created: Date.now() }
        },
        parts: [{
          type: 'text',
          text: `Error: ${e.response?.data?.detail || e.message || 'Failed to send message'}`
        }]
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

    // Add user message immediately for instant display
    addMessage(sessionId, {
      info: {
        role: 'user',
        time: { created: Date.now() }
      },
      parts: [{
        type: 'text',
        text: prompt
      }]
    })

    // Add empty assistant message that will be updated during streaming
    addMessage(sessionId, {
      info: {
        role: 'assistant',
        time: { created: Date.now() }
      },
      parts: [{
        type: 'text',
        text: ''
      }]
    })

    try {
      // Currently streaming is not supported with backend API
      // Use regular sendMessage instead
      throw new Error('Streaming is not currently supported. Please use regular message sending.')
    } catch (e) {
      error.value = 'Failed to stream message'
      console.error(e)
      
      // Add error message
      addMessage(sessionId, {
        info: {
          role: 'assistant',
          time: { created: Date.now() }
        },
        parts: [{
          type: 'text',
          text: `Error: ${e.message}`
        }]
      })
      
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
    delete messagesBySession.value[sessionId]
  }

  async function loadMessages(sessionId) {
    try {
      // Messages are now stored locally in messagesBySession
      // No need to fetch from agent since we manage them via backend API
      if (!messagesBySession.value[sessionId]) {
        messagesBySession.value[sessionId] = []
      }
    } catch (e) {
      console.error('Failed to load messages:', e)
      // Ensure messages array exists
      if (!messagesBySession.value[sessionId]) {
        messagesBySession.value[sessionId] = []
      }
    }
  }

  function initializeSession(sessionId) {
    // Initialize empty message storage for a new session
    if (!messagesBySession.value[sessionId]) {
      messagesBySession.value[sessionId] = []
    }
  }

  async function fetchModels() {
    modelsLoading.value = true
    try {
      // Fetch models from backend API
      const data = await backendApi.getModels()
      
      if (data && data.providers) {
        availableModels.value = data
        
        // Set default provider and model if available
        if (data.default) {
          const firstProvider = Object.keys(data.default)[0]
          if (firstProvider) {
            selectedProvider.value = firstProvider
            selectedModel.value = data.default[firstProvider]
          }
        }
      }
    } catch (e) {
      console.error('Failed to fetch models:', e)
      // Set default models as fallback
      availableModels.value = {
        providers: [
          {
            id: 'github-copilot',
            name: 'GitHub Copilot',
            models: [
              { id: 'gpt-5-mini', name: 'GPT-5 Mini' },
              { id: 'gpt-5', name: 'GPT-5' }
            ]
          }
        ],
        default: {
          'github-copilot': 'gpt-5-mini'
        }
      }
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
    loadMessages,
    initializeSession,
    fetchModels,
    setModel
  }
})
