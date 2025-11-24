<template>
  <div class="relative">
    <button
      @click="toggleDropdown"
      class="w-full flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-gray-200 transition-all duration-200 group"
      :class="{ 'justify-center px-2': isCollapsed }"
      title="User Profile"
    >
      <img
        v-if="userStore.user?.avatar_url"
        :src="userStore.user.avatar_url"
        :alt="userStore.user.github_login"
        class="w-8 h-8 rounded-lg border border-gray-200 shadow-sm shrink-0"
      />
      <span v-else class="w-8 h-8 bg-gray-800 rounded-lg flex items-center justify-center text-xs font-bold text-white shadow-sm shrink-0">
        {{ userStore.user?.github_login?.charAt(0)?.toUpperCase() || '?' }}
      </span>
      
      <div class="flex-1 min-w-0 text-left" v-if="!isCollapsed">
        <div class="text-sm font-semibold text-gray-900 truncate">{{ userStore.user?.github_login || 'User' }}</div>
        <div class="text-xs text-gray-500 truncate">{{ userStore.user?.email || 'No email' }}</div>
      </div>
      
      <svg v-if="!isCollapsed" class="w-4 h-4 text-gray-400 group-hover:text-gray-600 transition-colors" :class="{ 'rotate-180': showDropdown }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
      </svg>
    </button>

    <!-- Dropdown Menu -->
    <div
      v-if="showDropdown"
      class="absolute bg-white rounded-xl shadow-xl border border-gray-100 ring-1 ring-black/5 z-50 overflow-hidden transition-all duration-200"
      :class="[
        isCollapsed 
          ? 'left-full bottom-0 ml-2 w-56 origin-bottom-left' 
          : 'bottom-full left-0 right-0 mb-2 w-full origin-bottom'
      ]"
      @click.stop
    >
      <div class="p-1.5 space-y-0.5">
        <div v-if="isCollapsed" class="px-3 py-2 border-b border-gray-100 mb-1">
           <div class="text-sm font-semibold text-gray-900 truncate">{{ userStore.user?.github_login || 'User' }}</div>
           <div class="text-xs text-gray-500 truncate">{{ userStore.user?.email || 'No email' }}</div>
        </div>
        <button
          @click="openSettings"
          class="flex items-center w-full px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg transition-colors group"
        >
          <svg class="w-4 h-4 mr-3 text-gray-400 group-hover:text-primary-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
          </svg>
          Settings
        </button>
        <button
          @click="handleLogout"
          class="flex items-center w-full px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors group"
        >
          <svg class="w-4 h-4 mr-3 group-hover:translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
          </svg>
          Logout
        </button>
      </div>
    </div>

    <!-- Click outside to close dropdown -->
    <div
      v-if="showDropdown"
      class="fixed inset-0 z-40"
      @click="showDropdown = false"
    ></div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const showDropdown = ref(false)

const props = defineProps({
  isCollapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['settings-open'])

function toggleDropdown() {
  showDropdown.value = !showDropdown.value
}

function openSettings() {
  showDropdown.value = false
  emit('settings-open')
}

function handleLogout() {
  showDropdown.value = false
  userStore.logout()
}
</script>
