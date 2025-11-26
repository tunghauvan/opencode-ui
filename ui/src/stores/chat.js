import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { opencodeApi, backendApi } from '../services/api'

export const useChatStore = defineStore('chat', () => {
  // Map of sessionId -> messages array
  const messagesBySession = ref({})
  const loading = ref(false)
  const error = ref(null)
  const streaming = ref(false)
  const messagesLoading = ref(false)
  
  // Model selection state
  const selectedProvider = ref('github-copilot')
  const selectedModel = ref('gpt-5-mini')
  const availableModels = ref(null)
  const modelsLoading = ref(false)

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

  function setMessages(sessionId, messages) {
    messagesBySession.value[sessionId] = messages
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
      if (response.content || (response.parts && response.parts.length > 0)) {
        addMessage(sessionId, {
          info: {
            role: 'assistant',
            time: { created: Date.now() }
          },
          parts: response.parts || [{
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
    messagesLoading.value = true
    try {
      // Fetch messages from backend API (which gets them from OpenCode agent)
      const response = await backendApi.getMessages(sessionId)
      
      if (response.status === 'success' && response.messages) {
        // Messages from OpenCode agent are already in the correct format
        setMessages(sessionId, response.messages)
        console.log(`Loaded ${response.messages.length} messages for session ${sessionId}`)
      } else {
        // Initialize empty array if no messages
        if (!messagesBySession.value[sessionId]) {
          messagesBySession.value[sessionId] = []
        }
      }
    } catch (e) {
      console.error('Failed to load messages from server:', e)
      // Ensure messages array exists even on error
      if (!messagesBySession.value[sessionId]) {
        messagesBySession.value[sessionId] = []
      }
    } finally {
      messagesLoading.value = false
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
    messagesLoading,
    selectedProvider,
    selectedModel,
    availableModels,
    modelsLoading,
    getMessages,
    addMessage,
    setMessages,
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
