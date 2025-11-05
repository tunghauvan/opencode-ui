<template>
  <div class="h-full flex flex-col bg-white border-r border-gray-200">
    <!-- Header -->
    <div class="p-4 border-b border-gray-200">
      <button 
        @click="$emit('new-session')"
        class="w-full btn btn-secondary flex items-center justify-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        New Chat
      </button>
    </div>

    <!-- Sessions List -->
    <div class="flex-1 overflow-y-auto">
      <div v-if="sessionStore.loading && sessionStore.sessions.length === 0" class="p-4 text-center text-gray-500">
        Loading sessions...
      </div>
      
      <div v-else-if="sessionStore.sessions.length === 0" class="p-4 text-center text-gray-500">
        <div class="mb-2">No sessions available.</div>
        <div class="text-sm">Click "New Chat" to create your first session.</div>
      </div>
      
      <div v-else class="py-2">
        <SessionItem
          v-for="session in sessionStore.sessions"
          :key="session.id"
          :session="session"
          :active="session.id === sessionStore.currentSessionId"
          @click="sessionStore.selectSession(session.id)"
          @delete="handleDeleteSession(session.id)"
        />
      </div>
    </div>

    <!-- Footer -->
    <div class="p-4 border-t border-gray-200 text-xs text-gray-500">
      <div class="flex items-center justify-between">
        <span>OpenCode UI</span>
        <div class="flex items-center gap-1">
          <svg class="w-3 h-3 text-green-500" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
          </svg>
          <span>{{ sessionStore.sessions.length }} sessions</span>
        </div>
      </div>
      <div class="mt-1 text-xs text-gray-400">
        Chat history saved locally
      </div>
    </div>
  </div>
</template>

<script setup>
import { useSessionStore } from '../stores/session'
import SessionItem from './SessionItem.vue'

const sessionStore = useSessionStore()

defineEmits(['new-session'])

async function handleDeleteSession(sessionId) {
  if (confirm('Are you sure you want to delete this session?')) {
    await sessionStore.deleteSession(sessionId)
  }
}
</script>
