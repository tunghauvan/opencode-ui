<template>
  <div
    class="group mx-1 rounded-xl cursor-pointer transition-all duration-200 overflow-hidden"
    :class="[
      active 
        ? 'sidebar-item-active shadow-md' 
        : 'sidebar-item hover:shadow-sm'
    ]"
    @click="$emit('click')"
  >
    <div class="flex items-center justify-between px-3 py-2">
      <div class="flex-1 min-w-0 flex items-center gap-3">
        <div class="flex-shrink-0 w-6 h-6 rounded-lg flex items-center justify-center"
             :class="active ? 'bg-white/20' : 'bg-primary-100'"
        >
          <svg class="w-3 h-3" :class="active ? 'text-white' : 'text-primary-600'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-xs font-semibold truncate" :class="active ? 'text-white' : 'text-gray-900'">
            {{ sessionTitle }}
          </div>
          <div class="text-xs mt-0 flex items-center gap-1.5" :class="active ? 'text-white/80' : 'text-gray-500'">
            <!-- Container status indicator -->
            <span v-if="containerStatus" class="flex items-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full" :class="containerStatusClass"></span>
              <span class="text-xs">{{ containerStatusText }}</span>
            </span>
            <svg v-else class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {{ formattedDate }}
          </div>
        </div>
      </div>
      
      <button
        @click.stop="$emit('delete')"
        class="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg transition-all hover:scale-110"
        :class="active ? 'hover:bg-white/20 text-white' : 'hover:bg-red-50 text-red-600'"
        title="Delete session"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  session: {
    type: Object,
    required: true
  },
  active: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click', 'delete'])

const sessionTitle = computed(() => {
  return props.session.title || props.session.name || `Session ${(props.session.session_id || props.session.id).slice(0, 8)}`
})

const containerStatus = computed(() => {
  return props.session.container_status
})

const containerStatusClass = computed(() => {
  const status = props.session.container_status
  if (status === 'running') return 'bg-green-500'
  if (status === 'stopped' || status === 'exited') return 'bg-red-500'
  if (status === 'starting' || status === 'created') return 'bg-yellow-500'
  return 'bg-gray-400'
})

const containerStatusText = computed(() => {
  const status = props.session.container_status
  if (!status) return ''
  return status.charAt(0).toUpperCase() + status.slice(1)
})

const formattedDate = computed(() => {
  const date = new Date(props.session.created_at || props.session.createdAt || Date.now())
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  
  return date.toLocaleDateString()
})
</script>
