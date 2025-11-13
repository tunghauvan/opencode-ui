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
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSessionStore } from '../stores/session'
import { useUserStore } from '../stores/user'
import { backendApi } from '../services/api'
import SessionSidebar from '../components/SessionSidebar.vue'
import ChatWindow from '../components/ChatWindow.vue'
import EmptyState from '../components/EmptyState.vue'
import SettingsDialog from '../components/SettingsDialog.vue'

const route = useRoute()
const router = useRouter()
const sessionStore = useSessionStore()
const userStore = useUserStore()

// Settings dialog state
const showSettingsDialog = ref(false)

onMounted(async () => {
  await sessionStore.fetchSessions()
  await userStore.fetchUser()

  // Handle sessionId from URL params
  const sessionId = route.params.sessionId
  if (sessionId) {
    // Check if session exists in store
    const existingSession = sessionStore.sessions.find(s => s.session_id === sessionId)
    if (existingSession) {
      sessionStore.selectSession(sessionId)
    } else {
      // Session not found, redirect to /session
      router.replace('/session')
    }
  } else if (sessionStore.sessions.length > 0 && !sessionStore.currentSessionId) {
    // No sessionId in URL but we have sessions, select the first one
    sessionStore.selectSession(sessionStore.sessions[0].session_id)
  }
})

// Watch for currentSessionId changes and update URL
watch(() => sessionStore.currentSessionId, (newSessionId) => {
  if (newSessionId) {
    router.replace(`/session/${newSessionId}`)
  } else {
    router.replace('/session')
  }
}, { immediate: true })

// Watch for URL params changes (when user navigates via browser back/forward)
watch(() => route.params.sessionId, async (newSessionId) => {
  if (newSessionId && newSessionId !== sessionStore.currentSessionId) {
    const existingSession = sessionStore.sessions.find(s => s.session_id === newSessionId)
    if (existingSession) {
      sessionStore.selectSession(newSessionId)
    } else {
      // Try to fetch the session from API
      try {
        const session = await backendApi.getSession(newSessionId)
        if (session) {
          sessionStore.sessions.unshift(session)
          sessionStore.selectSession(newSessionId)
        }
      } catch (error) {
        console.error('Error fetching session:', error)
        router.replace('/session')
      }
    }
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
