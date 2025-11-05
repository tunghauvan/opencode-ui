<template>
  <div
    class="group px-3 py-2 mx-2 rounded-lg cursor-pointer transition-all"
    :class="[
      active 
        ? 'bg-primary-100 text-primary-900' 
        : 'hover:bg-gray-100 text-gray-700'
    ]"
    @click="$emit('click')"
  >
    <div class="flex items-center justify-between">
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2">
          <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          <span class="text-sm font-medium truncate">
            {{ sessionTitle }}
          </span>
        </div>
        <div class="text-xs text-gray-500 mt-1">
          {{ formattedDate }}
        </div>
      </div>
      
      <button
        v-if="active"
        @click.stop="$emit('delete')"
        class="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded transition-opacity"
        title="Delete session"
      >
        <svg class="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
  return props.session.title || props.session.name || `Session ${props.session.id.slice(0, 8)}`
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
