import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { opencodeApi, backendApi, dbApi } from '../services/api'

export const useChatStore = defineStore('chat', () => {
  // Map of sessionId -> messages array
  const messagesBySession = ref({})
  const loading = ref(false)
  const error = ref(null)
  const streaming = ref(false)
  const messagesLoading = ref(false)
  const syncing = ref(false)
  
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
    const userMessage = {
      info: {
        id: `msg_user_${Date.now()}`,
        role: 'user',
        time: { created: Date.now() }
      },
      parts: [{
        type: 'text',
        text: prompt
      }]
    }
    addMessage(sessionId, userMessage)
    
    // Save user message to database immediately
    try {
      await saveMessageToDb(sessionId, userMessage)
    } catch (dbErr) {
      console.warn('Could not save user message to DB:', dbErr)
    }

    try {
      // Use backend API for chat
      await backendApi.sendMessage(sessionId, prompt)
      
      // Reload full messages from agent to get complete response with tool actions
      // The backend response might not include all parts (like tool executions)
      await reloadMessagesFromAgent(sessionId)

      // Sync all messages to database after successful send
      await syncMessagesToDb(sessionId)
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
    let loadedFromDb = false
    
    try {
      // Always try to load from local database first (works even when container is stopped)
      try {
        console.log(`Attempting to load messages from database for session ${sessionId}`)
        const dbResponse = await dbApi.getMessages(sessionId)
        console.log('Database response:', dbResponse)
        if (dbResponse.messages && dbResponse.messages.length > 0) {
          setMessages(sessionId, dbResponse.messages)
          console.log(`Loaded ${dbResponse.messages.length} messages from database for session ${sessionId}`)
          loadedFromDb = true
        } else {
          console.log('No messages found in database')
        }
      } catch (dbError) {
        console.log('Could not load from database:', dbError.response?.status, dbError.message)
        // 404 means session not found, which is expected for new sessions
        if (dbError.response?.status !== 404) {
          console.error('Database error details:', dbError.response?.data)
        }
      }
      
      // Try to sync with OpenCode agent (if container is running)
      // This will get any new messages that haven't been saved to DB yet
      try {
        console.log(`Attempting to load messages from agent for session ${sessionId}`)
        const response = await backendApi.getMessages(sessionId)
        console.log('Agent response:', response)
        
        if (response.status === 'success' && response.messages && response.messages.length > 0) {
          // If we got messages from agent, use those (they're more up-to-date)
          setMessages(sessionId, response.messages)
          console.log(`Loaded ${response.messages.length} messages from agent for session ${sessionId}`)
          
          // Sync to database for persistence
          await syncMessagesToDb(sessionId)
        }
      } catch (agentError) {
        // Agent might not be available (container stopped), that's OK if we loaded from DB
        if (!loadedFromDb) {
          console.log('Agent not available and no messages in database')
        } else {
          console.log('Agent not available, using cached messages from database')
        }
      }
      
      // Initialize empty array if no messages from either source
      if (!messagesBySession.value[sessionId]) {
        messagesBySession.value[sessionId] = []
      }
    } catch (e) {
      console.error('Failed to load messages:', e)
      // Ensure messages array exists even on error
      if (!messagesBySession.value[sessionId]) {
        messagesBySession.value[sessionId] = []
      }
    } finally {
      messagesLoading.value = false
    }
  }

  async function syncMessagesToDb(sessionId) {
    syncing.value = true
    try {
      console.log(`Syncing messages to database for session ${sessionId}...`)
      const response = await dbApi.syncMessages(sessionId, false)
      console.log(`Synced messages to database: ${response.new_count} new, ${response.updated_count} updated`)
      return response
    } catch (e) {
      console.error('Failed to sync messages to database:', e.response?.data || e.message)
    } finally {
      syncing.value = false
    }
  }

  async function reloadMessagesFromAgent(sessionId) {
    try {
      console.log(`Reloading messages from agent for session ${sessionId}...`)
      const response = await backendApi.getMessages(sessionId)
      
      if (response.status === 'success' && response.messages && response.messages.length > 0) {
        setMessages(sessionId, response.messages)
        console.log(`Reloaded ${response.messages.length} messages from agent for session ${sessionId}`)
        return true
      }
      return false
    } catch (e) {
      console.error('Failed to reload messages from agent:', e)
      return false
    }
  }

  async function saveMessageToDb(sessionId, messageData) {
    try {
      await dbApi.saveMessage(sessionId, messageData)
    } catch (e) {
      console.error('Failed to save message to database:', e)
    }
  }

  async function clearMessagesFromDb(sessionId) {
    try {
      await dbApi.clearMessages(sessionId)
    } catch (e) {
      console.error('Failed to clear messages from database:', e)
    }
  }

  async function editAndRetryMessage(sessionId, messageIndex, newText) {
    loading.value = true
    error.value = null
    
    try {
      const messages = messagesBySession.value[sessionId]
      if (!messages || messageIndex < 0 || messageIndex >= messages.length) {
        throw new Error('Invalid message index')
      }

      const originalMessage = messages[messageIndex]
      if (originalMessage.info?.role !== 'user') {
        throw new Error('Can only edit user messages')
      }

      // Get message IDs to delete (all messages after the edited one)
      const messagesToDelete = messages.slice(messageIndex + 1)
      const editedMessageId = originalMessage.info?.id
      
      // Delete messages after the edited one from BOTH database AND OpenCode agent
      if (messagesToDelete.length > 0) {
        // Delete from local database
        try {
          await dbApi.deleteMessagesAfter(sessionId, editedMessageId)
          console.log(`Deleted ${messagesToDelete.length} messages from DB after index ${messageIndex}`)
        } catch (dbErr) {
          console.warn('Could not delete messages from DB:', dbErr)
        }
        
        // Delete from OpenCode agent server
        try {
          await dbApi.deleteMessagesAfterFromAgent(sessionId, editedMessageId)
          console.log(`Deleted messages from OpenCode agent after index ${messageIndex}`)
        } catch (agentErr) {
          console.warn('Could not delete messages from OpenCode agent:', agentErr)
        }
      }
      
      // Update local messages array - remove messages after edited one
      messagesBySession.value[sessionId] = messages.slice(0, messageIndex)
      
      // Create updated user message with new text
      const updatedUserMessage = {
        info: {
          id: editedMessageId || `msg_user_${Date.now()}`,
          role: 'user',
          time: { created: Date.now() }
        },
        parts: [{
          type: 'text',
          text: newText
        }]
      }
      
      // Add the updated user message
      addMessage(sessionId, updatedUserMessage)
      
      // Save updated user message to database
      try {
        await dbApi.saveMessage(sessionId, updatedUserMessage)
      } catch (dbErr) {
        console.warn('Could not save updated user message to DB:', dbErr)
      }
      
      // Send the new message to get a fresh response
      await backendApi.sendMessage(sessionId, newText)
      
      // Reload full messages from agent to get complete response with tool actions
      await reloadMessagesFromAgent(sessionId)

      // Sync all messages to database
      await syncMessagesToDb(sessionId)
      
    } catch (e) {
      error.value = 'Failed to edit and retry message'
      console.error('Edit and retry error:', e)

      // Add error message
      addMessage(sessionId, {
        info: {
          role: 'assistant',
          time: { created: Date.now() }
        },
        parts: [{
          type: 'text',
          text: `Error: ${e.response?.data?.detail || e.message || 'Failed to edit and retry message'}`
        }]
      })
      
      throw e
    } finally {
      loading.value = false
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
    syncing,
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
    setModel,
    syncMessagesToDb,
    saveMessageToDb,
    clearMessagesFromDb,
    editAndRetryMessage
  }
})
