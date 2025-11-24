<template>
  <div 
    class="h-full flex flex-col bg-gray-50 border-r border-gray-200 transition-[width] duration-300 ease-in-out overflow-hidden whitespace-nowrap"
    :class="isCollapsed ? 'w-[72px]' : 'w-80'"
  >
    <!-- Header -->
    <div class="shrink-0 transition-all duration-300" :class="isCollapsed ? 'py-4 flex flex-col items-center gap-4 w-[72px]' : 'p-4 flex items-center justify-between min-w-[20rem]'">
      
      <!-- Logo Area -->
      <div v-if="!isCollapsed" class="flex items-center gap-3 overflow-hidden min-w-0">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center shadow-md shrink-0">
          <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <h2 class="text-sm font-bold text-gray-800 tracking-tight whitespace-nowrap opacity-100 transition-opacity duration-300">OpenCode</h2>
      </div>
      
      <!-- Collapsed Logo & Expand -->
      <div v-else class="flex flex-col items-center gap-2 animate-fade-in">
        <div class="w-10 h-10 rounded-full bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center shadow-md cursor-pointer hover:shadow-lg transition-all" @click="toggleCollapse" title="Expand Sidebar">
          <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <button 
          @click="toggleCollapse"
          class="p-1 rounded-full text-gray-400 hover:bg-gray-200 hover:text-gray-600 transition-colors"
          title="Expand Sidebar"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      <!-- Expanded Header Actions -->
      <div class="flex items-center gap-1" v-if="!isCollapsed">
        <button 
          @click="$emit('new-session')"
          class="p-2 rounded-lg bg-white border border-gray-200 text-gray-600 hover:text-primary-600 hover:border-primary-200 hover:shadow-sm transition-all duration-200 group"
          title="New Chat"
        >
          <svg class="w-5 h-5 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
        </button>
        <button 
          @click="toggleCollapse"
          class="p-2 rounded-lg text-gray-400 hover:bg-gray-200 hover:text-gray-600 transition-colors"
          title="Collapse Sidebar"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        </button>
      </div>

      <!-- Collapsed Actions Stack -->
      <template v-if="isCollapsed">
        <!-- New Chat (Prominent) -->
        <button 
          @click="$emit('new-session')"
          class="w-10 h-10 rounded-full bg-primary-600 text-white shadow-lg hover:bg-primary-700 hover:scale-105 transition-all flex items-center justify-center group z-10"
          title="New Chat"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
        </button>

        <!-- Search Trigger -->
        <button 
          @click="expandAndSearch"
          class="w-10 h-10 rounded-full text-gray-400 hover:text-primary-600 hover:bg-primary-50 transition-all flex items-center justify-center group"
          title="Search Chats"
        >
          <svg class="w-6 h-6 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </button>

        <!-- Separator -->
        <div class="w-8 h-px bg-gray-200 my-1"></div>
      </template>
    </div>

    <!-- Search (Expanded Only) -->
    <div class="px-4 pb-4 shrink-0 min-w-[20rem]" v-if="!isCollapsed">
      <div class="relative group">
        <input 
          ref="searchInput"
          v-model="searchQuery"
          type="text" 
          placeholder="Search..." 
          class="w-full pl-10 pr-4 py-2 text-sm bg-white border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100 transition-all placeholder-gray-400 shadow-sm group-hover:border-gray-300"
        />
        <svg class="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2 group-focus-within:text-primary-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
    </div>

    <!-- Sessions List -->
    <div class="flex-1 overflow-y-auto px-2 py-2 scrollbar-thin overflow-x-hidden" :class="isCollapsed ? 'w-[72px]' : 'min-w-[20rem]'">
      <div v-if="sessionStore.loading && sessionStore.sessions.length === 0" class="p-4 text-center">
        <div class="w-6 h-6 border-2 border-gray-200 border-t-gray-600 rounded-full animate-spin mx-auto mb-2"></div>
        <p class="text-xs text-gray-500" v-if="!isCollapsed">Loading...</p>
      </div>
      
      <div v-else-if="filteredSessions.length === 0" class="p-8 text-center">
        <p class="text-sm text-gray-500" v-if="!isCollapsed">No chats found</p>
        <div v-else class="w-2 h-2 bg-gray-300 rounded-full mx-auto"></div>
      </div>
      
      <div v-else class="space-y-6">
        <div v-for="(group, label) in groupedSessions" :key="label" class="animate-fade-in">
          <h3 v-if="group.length > 0 && !isCollapsed" class="px-3 mb-2 text-xs font-medium text-gray-400 uppercase tracking-wider whitespace-nowrap">
            {{ label }}
          </h3>
          <!-- Separator removed in collapsed mode for cleaner look -->
          <TransitionGroup 
            name="list" 
            tag="div" 
            class="space-y-0.5"
          >
            <SessionItem
              v-for="session in group"
              :key="session.session_id"
              :session="session"
              :active="session.session_id === sessionStore.currentSessionId"
              :is-collapsed="isCollapsed"
              @click="sessionStore.selectSession(session.session_id)"
              @delete="handleDeleteSession(session.session_id)"
            />
          </TransitionGroup>
        </div>
      </div>
    </div>

    <!-- User Profile Footer -->
    <div class="p-2 border-t border-gray-200 bg-white/50" :class="isCollapsed ? 'w-[72px]' : 'min-w-[20rem]'">
      <UserProfile 
        :is-collapsed="isCollapsed"
        @settings-open="$emit('settings-open')" 
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useSessionStore } from '../stores/session'
import SessionItem from './SessionItem.vue'
import UserProfile from './UserProfile.vue'

const sessionStore = useSessionStore()
const searchQuery = ref('')
const isCollapsed = ref(false)
const searchInput = ref(null)

defineProps({
  showSettings: {
    type: Boolean,
    default: false
  }
})

defineEmits(['new-session', 'settings-open'])

onMounted(() => {
  const saved = localStorage.getItem('sidebar-collapsed')
  if (saved !== null) {
    isCollapsed.value = JSON.parse(saved)
  }
})

watch(isCollapsed, (newVal) => {
  localStorage.setItem('sidebar-collapsed', JSON.stringify(newVal))
})

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
}

function expandAndSearch() {
  isCollapsed.value = false
  // Wait for transition/render
  setTimeout(() => {
    searchInput.value?.focus()
  }, 300)
}

// Filter sessions by search query
const filteredSessions = computed(() => {
  if (!searchQuery.value.trim()) return sessionStore.sessions
  
  const query = searchQuery.value.toLowerCase()
  return sessionStore.sessions.filter(session => {
    const title = (session.title || session.name || '').toLowerCase()
    return title.includes(query)
  })
})

// Group sessions by time
const groupedSessions = computed(() => {
  const groups = {
    'Today': [],
    'Yesterday': [],
    'Previous 7 Days': [],
    'Previous 30 Days': [],
    'Older': []
  }

  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)
  const last7Days = new Date(today)
  last7Days.setDate(last7Days.getDate() - 7)
  const last30Days = new Date(today)
  last30Days.setDate(last30Days.getDate() - 30)

  filteredSessions.value.forEach(session => {
    const date = new Date(session.created_at || session.createdAt || Date.now())
    
    if (date >= today) {
      groups['Today'].push(session)
    } else if (date >= yesterday) {
      groups['Yesterday'].push(session)
    } else if (date >= last7Days) {
      groups['Previous 7 Days'].push(session)
    } else if (date >= last30Days) {
      groups['Previous 30 Days'].push(session)
    } else {
      groups['Older'].push(session)
    }
  })

  // Remove empty groups
  return Object.fromEntries(
    Object.entries(groups).filter(([_, items]) => items.length > 0)
  )
})

async function handleDeleteSession(sessionId) {
  if (confirm('Are you sure you want to delete this session?')) {
    await sessionStore.deleteSession(sessionId)
  }
}
</script>

<style scoped>
.scrollbar-thin::-webkit-scrollbar {
  width: 4px;
}
.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}
.scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: #e5e7eb;
  border-radius: 20px;
}
.scrollbar-thin:hover::-webkit-scrollbar-thumb {
  background-color: #d1d5db;
}

/* List Transitions */
.list-move,
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.list-leave-active {
  position: absolute;
  width: 100%;
}
</style>
