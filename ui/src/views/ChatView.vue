<template>
  <div class="h-screen flex bg-gray-50">
    <!-- Sidebar -->
    <SessionSidebar
      class="w-80 flex-shrink-0"
      @new-session="handleNewSession"
    />

    <!-- Main Chat Area -->
    <div class="flex-1 flex flex-col">
      <!-- Header -->
      <div class="bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
        <h1 class="text-xl font-semibold text-gray-800">OpenCode UI</h1>
        <div class="flex items-center gap-4">
          <!-- User Profile Dropdown -->
          <div class="relative">
            <button
              @click="toggleDropdown"
              class="flex items-center gap-2 text-gray-600 hover:text-gray-800 px-3 py-2 rounded-md text-sm font-medium transition-colors"
              title="User Profile"
            >
              <img
                v-if="userStore.user?.avatar_url"
                :src="userStore.user.avatar_url"
                :alt="userStore.user.github_login"
                class="w-6 h-6 rounded-full"
              />
              <span v-else class="w-6 h-6 bg-gray-300 rounded-full flex items-center justify-center text-xs">
                {{ userStore.user?.github_login?.charAt(0)?.toUpperCase() || '?' }}
              </span>
              <span class="hidden sm:inline">{{ userStore.user?.github_login || 'User' }}</span>
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
              </svg>
            </button>

            <!-- Dropdown Menu -->
            <div
              v-if="showDropdown"
              class="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 z-50"
              @click.stop
            >
              <div class="py-1">
                <div class="px-4 py-2 text-sm text-gray-500 border-b border-gray-200">
                  <div class="font-medium text-gray-900">{{ userStore.user?.github_login }}</div>
                  <div class="text-xs">{{ userStore.user?.email }}</div>
                </div>
                <button
                  @click="openSettings"
                  class="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  <svg class="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                  </svg>
                  Settings
                </button>
                <button
                  @click="handleLogout"
                  class="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
                >
                  <svg class="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
                  </svg>
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <ChatWindow v-if="sessionStore.currentSessionId" />
      <EmptyState v-else />
    </div>

    <!-- Click outside to close dropdown -->
    <div
      v-if="showDropdown"
      class="fixed inset-0 z-40"
      @click="showDropdown = false"
    ></div>

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

// Dropdown state
const showDropdown = ref(false)
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
  showDropdown.value = false
  showSettingsDialog.value = true
}

function closeSettings() {
  showSettingsDialog.value = false
}

function toggleDropdown() {
  showDropdown.value = !showDropdown.value
}

async function handleLogout() {
  showDropdown.value = false
  await userStore.logout()
}
</script>
