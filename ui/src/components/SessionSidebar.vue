<template>
  <div class="h-full flex flex-col glass border-r border-white/20 backdrop-blur-xl">
    <!-- Branding Header -->
    <div class="p-3 border-b border-white/20">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-600 to-purple-600 flex items-center justify-center shadow-lg shadow-primary-500/30">
          <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <div>
          <h2 class="text-sm font-bold text-gradient">OpenCode UI</h2>
          <p class="text-xs text-gray-500">Chat Interface</p>
        </div>
      </div>
    </div>

    <!-- New Chat Button -->
    <div class="p-3 border-b border-white/20">
      <button 
        @click="$emit('new-session')"
        class="w-full btn btn-primary flex items-center justify-center gap-2 shadow-lg hover:shadow-xl group text-sm"
      >
        <svg class="w-5 h-5 group-hover:rotate-90 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        <span class="font-semibold">New Chat</span>
      </button>
    </div>

    <!-- Sessions List -->
    <div class="flex-1 overflow-y-auto p-2">
      <div v-if="sessionStore.loading && sessionStore.sessions.length === 0" class="p-4 text-center">
        <div class="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin mx-auto mb-2"></div>
        <p class="text-sm text-gray-500">Loading sessions...</p>
      </div>
      
      <div v-else-if="sessionStore.sessions.length === 0" class="p-6 text-center animate-fade-in">
        <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center">
          <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
        <p class="text-sm font-medium text-gray-700 mb-1">No sessions yet</p>
        <p class="text-xs text-gray-500">Click "New Chat" to start</p>
      </div>
      
      <div v-else class="space-y-1 animate-fade-in">
        <SessionItem
          v-for="session in sessionStore.sessions"
          :key="session.id"
          :session="session"
          :active="session.id === sessionStore.currentSessionId"
          @click="sessionStore.selectSession(session.id)"
          @delete="handleDeleteSession(session.id)"
          class="animate-slide-up"
        />
      </div>
    </div>

    <!-- Session Stats -->
    <div class="p-3 border-t border-white/20">
      <div class="card px-3 py-2 hover:shadow-lg transition-shadow">
        <div class="flex items-center gap-2 mb-1">
          <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-glow"></div>
          <span class="text-xs font-medium text-gray-700">{{ sessionStore.sessions.length }} sessions</span>
        </div>
        <div class="flex items-center gap-2">
          <svg class="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <span class="text-xs text-gray-500">History saved</span>
        </div>
      </div>
    </div>

    <!-- User Profile -->
    <UserProfile @settings-open="$emit('settings-open')" />
  </div>
</template>

<script setup>
import { useSessionStore } from '../stores/session'
import SessionItem from './SessionItem.vue'
import UserProfile from './UserProfile.vue'

const sessionStore = useSessionStore()

defineProps({
  showSettings: {
    type: Boolean,
    default: false
  }
})

defineEmits(['new-session', 'settings-open'])

async function handleDeleteSession(sessionId) {
  if (confirm('Are you sure you want to delete this session?')) {
    await sessionStore.deleteSession(sessionId)
  }
}
</script>
