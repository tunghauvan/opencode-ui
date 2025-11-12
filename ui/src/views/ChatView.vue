<template>
  <div class="h-screen flex bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50">
      <!-- Sidebar -->
      <SessionSidebar
        class="w-80 flex-shrink-0 shadow-2xl"
        @new-session="handleNewSession"
        @settings-open="openSettings"
      />    <!-- Main Chat Area -->
    <div class="flex-1 flex flex-col">
      <ChatWindow v-if="sessionStore.currentSessionId" />
      <EmptyState v-else />
    </div>

    <!-- Settings Dialog -->
    <SettingsDialog
      :is-open="showSettingsDialog"
      @close="closeSettings"
    />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useSessionStore } from '../stores/session'
import { useUserStore } from '../stores/user'
import SessionSidebar from '../components/SessionSidebar.vue'
import ChatWindow from '../components/ChatWindow.vue'
import EmptyState from '../components/EmptyState.vue'
import SettingsDialog from '../components/SettingsDialog.vue'

const sessionStore = useSessionStore()
const userStore = useUserStore()

// Settings dialog state
const showSettingsDialog = ref(false)

onMounted(async () => {
  await sessionStore.fetchSessions()
  await userStore.fetchUser()

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

function openSettings() {
  showSettingsDialog.value = true
}

function closeSettings() {
  showSettingsDialog.value = false
}
</script>
