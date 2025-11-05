<template>
  <div class="h-full flex flex-col">
    <!-- Chat Header -->
    <div class="bg-white border-b border-gray-200 px-6 py-4">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-xl font-semibold text-gray-900">
            {{ sessionTitle }}
          </h1>
          <p class="text-sm text-gray-500 mt-1">
            Session ID: {{ sessionStore.currentSessionId?.slice(0, 8) }}
            <span v-if="messages.length > 0" class="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
              {{ messages.length }} messages
            </span>
          </p>
        </div>
        
        <div class="flex items-center gap-2">
          <button
            @click="exportChat"
            class="btn btn-secondary text-sm"
            title="Export chat history"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </button>
          
          <button
            @click="handleClearChat"
            class="btn btn-secondary text-sm"
            title="Clear chat history"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Messages Area -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto bg-gray-50 px-6 py-6">
      <div v-if="messages.length === 0" class="h-full flex items-center justify-center">
        <div class="text-center text-gray-500">
          <svg class="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <p class="text-lg font-medium">Start a conversation</p>
          <p class="text-sm mt-2">Type a message below to begin chatting</p>
        </div>
      </div>
      
      <div v-else class="space-y-6 max-w-4xl mx-auto">
        <MessageBubble
          v-for="(message, index) in messages"
          :key="index"
          :message="message"
        />
        
        <div v-if="chatStore.loading || chatStore.streaming" class="flex justify-start">
          <div class="bg-white rounded-2xl px-4 py-3 shadow-sm border border-gray-200">
            <div class="flex items-center gap-2">
              <div class="flex gap-1">
                <div class="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
                <div class="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
                <div class="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
              </div>
              <span class="text-sm text-gray-500">Thinking...</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="bg-white border-t border-gray-200 px-6 py-4">
      <ChatInput
        v-model="inputMessage"
        :disabled="chatStore.loading || chatStore.streaming"
        @send="handleSendMessage"
      />
      
      <div v-if="chatStore.error" class="mt-2 text-sm text-red-600">
        {{ chatStore.error }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useSessionStore } from '../stores/session'
import { useChatStore } from '../stores/chat'
import MessageBubble from './MessageBubble.vue'
import ChatInput from './ChatInput.vue'

const sessionStore = useSessionStore()
const chatStore = useChatStore()

const inputMessage = ref('')
const messagesContainer = ref(null)

const messages = computed(() => {
  if (!sessionStore.currentSessionId) return []
  return chatStore.getMessages(sessionStore.currentSessionId)
})

const sessionTitle = computed(() => {
  const session = sessionStore.currentSession
  return session?.title || session?.name || 'Chat Session'
})

async function handleSendMessage() {
  if (!inputMessage.value.trim() || !sessionStore.currentSessionId) return
  
  const message = inputMessage.value.trim()
  inputMessage.value = ''
  
  try {
    await chatStore.sendMessage(sessionStore.currentSessionId, message)
    scrollToBottom()
  } catch (error) {
    console.error('Failed to send message:', error)
  }
}

function handleClearChat() {
  if (!sessionStore.currentSessionId) return
  
  if (confirm('Are you sure you want to clear this chat history?')) {
    chatStore.clearMessages(sessionStore.currentSessionId)
  }
}

function exportChat() {
  if (!sessionStore.currentSessionId || messages.length === 0) return
  
  const session = sessionStore.currentSession
  const sessionTitle = session?.title || session?.name || `Session ${sessionStore.currentSessionId.slice(0, 8)}`
  
  const exportData = {
    sessionId: sessionStore.currentSessionId,
    sessionTitle: sessionTitle,
    exportedAt: new Date().toISOString(),
    messages: messages
  }
  
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `chat-${sessionTitle.replace(/[^a-zA-Z0-9]/g, '-')}-${new Date().toISOString().split('T')[0]}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

watch(messages, () => {
  scrollToBottom()
}, { deep: true })

watch(() => sessionStore.currentSessionId, () => {
  inputMessage.value = ''
  scrollToBottom()
})
</script>
