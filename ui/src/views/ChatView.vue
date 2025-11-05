<template>
  <div class="h-screen flex bg-gray-50">
    <!-- Sidebar -->
    <SessionSidebar 
      class="w-80 flex-shrink-0"
      @new-session="handleNewSession"
    />
    
    <!-- Main Chat Area -->
    <div class="flex-1 flex flex-col">
      <ChatWindow v-if="sessionStore.currentSessionId" />
      <EmptyState v-else />
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useSessionStore } from '../stores/session'
import SessionSidebar from '../components/SessionSidebar.vue'
import ChatWindow from '../components/ChatWindow.vue'
import EmptyState from '../components/EmptyState.vue'

const sessionStore = useSessionStore()

onMounted(async () => {
  await sessionStore.fetchSessions()
  if (sessionStore.sessions.length > 0 && !sessionStore.currentSessionId) {
    sessionStore.selectSession(sessionStore.sessions[0].id)
  }
})

async function handleNewSession() {
  try {
    await sessionStore.createSession()
  } catch (error) {
    console.error('Error creating session:', error)
    alert('Failed to create new session: ' + (error.message || 'Unknown error'))
  }
}
</script>
