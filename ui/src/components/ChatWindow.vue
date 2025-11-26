<template>
  <div class="h-full flex flex-col animate-fade-in">
    <!-- Chat Header with Gradient -->
    <div class="glass border-b border-white/20 px-6 py-2.5 backdrop-blur-xl">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center shadow-lg shadow-primary-500/30">
            <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          </div>
          <div>
            <h1 class="text-lg font-bold text-gradient">
              {{ sessionTitle }}
            </h1>
            <div class="flex items-center gap-2 mt-0.5">
              <p class="text-xs text-gray-500">
                Session: {{ sessionStore.currentSessionId?.slice(0, 8) }}
              </p>
              <span class="text-xs text-gray-300">•</span>
              <p class="text-xs text-gray-500 flex items-center gap-1">
                <span class="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
                {{ currentModelDisplay }}
              </p>
              <span v-if="messages.length > 0" class="status-badge status-online ml-1">
                {{ messages.length }} messages
              </span>
            </div>
          </div>
        </div>
        
        <div class="flex items-center gap-2">
          <!-- Container Controls (Inline) -->
          <div v-if="sessionStore.currentSession" class="mr-2 border-r border-gray-200 pr-2">
            <ContainerControls
              :session-id="sessionStore.currentSessionId"
              :container-status="sessionStore.currentSession.container_status"
              :container-id="sessionStore.currentSession.container_id"
              variant="inline"
            />
          </div>

          <!-- Toggle Editor Button -->
          <button
            @click="$emit('toggle-editor')"
            class="btn btn-ghost text-sm group"
            :class="{ 'bg-primary-100 text-primary-600': isEditorVisible }"
            title="Toggle Code Editor"
          >
            <svg class="w-5 h-5 group-hover:text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
            </svg>
          </button>

          <button
            @click="exportChat"
            class="btn btn-ghost text-sm group"
            title="Export chat history"
          >
            <svg class="w-5 h-5 group-hover:text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </button>
          
          <button
            @click="handleClearChat"
            class="btn btn-ghost text-sm group"
            title="Clear chat history"
          >
            <svg class="w-5 h-5 group-hover:text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Messages Area with Modern Design -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto px-6 py-6 bg-gradient-to-br from-gray-50/50 via-blue-50/30 to-purple-50/30">
      <div v-if="messages.length === 0" class="h-full flex items-center justify-center animate-fade-in">
        <div class="text-center">
          <div class="w-24 h-24 mx-auto mb-6 rounded-3xl bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center shadow-2xl shadow-primary-500/30 animate-pulse-slow">
            <svg class="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <h3 class="text-2xl font-bold text-gradient mb-3">Start a conversation</h3>
          <p class="text-gray-500 text-base max-w-md mx-auto">
            Type a message below to begin chatting with the AI assistant
          </p>
          <div class="mt-8 flex justify-center gap-4 flex-wrap">
            <div class="card px-4 py-3 hover:scale-105 transition-transform cursor-default">
              <div class="text-sm font-medium text-gray-700">💡 Ask anything</div>
            </div>
            <div class="card px-4 py-3 hover:scale-105 transition-transform cursor-default">
              <div class="text-sm font-medium text-gray-700">🚀 Get code help</div>
            </div>
            <div class="card px-4 py-3 hover:scale-105 transition-transform cursor-default">
              <div class="text-sm font-medium text-gray-700">📝 Learn something</div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-else class="space-y-6 max-w-5xl mx-auto animate-slide-up">
        <MessageBubble
          v-for="(message, index) in messages"
          :key="index"
          :message="message"
          class="animate-fade-in"
          :style="{ animationDelay: `${index * 0.05}s` }"
        />
        
        <div v-if="chatStore.loading || chatStore.streaming" class="flex justify-start animate-fade-in">
          <div class="message-assistant rounded-3xl px-6 py-4">
            <div class="flex items-center gap-3">
              <div class="flex gap-1.5">
                <div class="w-2.5 h-2.5 bg-primary-500 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
                <div class="w-2.5 h-2.5 bg-primary-500 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
                <div class="w-2.5 h-2.5 bg-primary-500 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
              </div>
              <span class="text-sm text-gray-600 font-medium">AI is thinking...</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Input Area with Modern Design -->
    <div class="glass border-t border-white/20 px-6 py-3 backdrop-blur-xl">
      <ChatInput
        v-model="inputMessage"
        :disabled="chatStore.loading || chatStore.streaming"
        @send="handleSendMessage"
      />
      
      <div v-if="chatStore.error" class="mt-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-2 animate-slide-down">
        {{ chatStore.error }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useSessionStore } from '../stores/session'
import { useChatStore } from '../stores/chat'
import { useFileStore } from '../stores/file'
import MessageBubble from './MessageBubble.vue'
import ChatInput from './ChatInput.vue'
import ContainerControls from './ContainerControls.vue'

defineEmits(['toggle-editor'])

const sessionStore = useSessionStore()
const chatStore = useChatStore()
const fileStore = useFileStore()

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

const currentModelDisplay = computed(() => {
  const provider = chatStore.selectedProvider
  const model = chatStore.selectedModel
  return `${provider}/${model}`
})

const isEditorVisible = computed(() => fileStore.isEditorVisible)

// Load models on mount
onMounted(async () => {
  if (!chatStore.availableModels) {
    await chatStore.fetchModels()
  }
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
