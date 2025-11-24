<template>
  <div
    class="group relative mx-2 px-3 py-2.5 rounded-lg cursor-pointer transition-all duration-300 border border-transparent overflow-hidden"
    :class="[
      active 
        ? 'bg-white shadow-sm border-gray-200' 
        : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900',
      isCollapsed ? 'justify-center px-0 !mx-0 !py-1 !bg-transparent !border-0 !shadow-none hover:!bg-transparent' : ''
    ]"
    @click="$emit('click')"
  >
    <!-- Active Accent (Expanded Only) -->
    <div 
      v-if="active && !isCollapsed" 
      class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 bg-primary-600 rounded-r-full"
    ></div>

    <div class="flex items-center gap-2" :class="{ 'justify-center w-full': isCollapsed, 'pl-1': !isCollapsed }">
      <!-- Collapsed Icon (Letter) -->
      <div 
        v-if="isCollapsed" 
        ref="iconRef"
        class="w-10 h-10 !rounded-full shrink-0 flex items-center justify-center text-sm font-bold shadow-sm transition-all select-none relative"
        :class="active 
          ? 'bg-primary-100 text-primary-700 ring-2 ring-primary-500 ring-offset-2' 
          : 'bg-white border border-gray-200 text-gray-500 hover:border-primary-300 hover:text-primary-600 hover:shadow-md'"
        @mouseenter="showTooltip = true; updateTooltipPosition()"
        @mouseleave="showTooltip = false"
      >
        {{ sessionLetter }}
        <!-- Status Dot -->
        <div 
          class="absolute bottom-0 right-0 w-3 h-3 border-2 border-white rounded-full"
          :class="statusColor"
        ></div>
      </div>

      <!-- Expanded Content -->
      <template v-else>
        <div class="flex-1 min-w-0 flex items-center gap-2">
          <!-- Status Dot (Expanded) -->
          <div 
            class="w-2 h-2 rounded-full shrink-0"
            :class="statusColor"
          ></div>

          <!-- Edit Mode -->
          <input
            v-if="isEditing"
            ref="titleInput"
            v-model="editTitle"
            type="text"
            class="w-full px-1 py-0.5 text-sm bg-white border border-primary-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
            @click.stop
            @keydown.enter="saveTitle"
            @keydown.esc="cancelEditing"
            @blur="saveTitle"
          />
          <!-- Display Mode -->
          <div 
            v-else
            class="text-sm truncate transition-colors"
            :class="active ? 'font-semibold text-gray-900' : 'font-medium'"
          >
            {{ sessionTitle }}
          </div>
        </div>
        
        <!-- Actions -->
        <div v-if="!isEditing" class="flex items-center opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            @click.stop="startEditing"
            class="p-1 rounded-md text-gray-400 hover:text-primary-600 hover:bg-primary-50 transition-all mr-1"
            title="Rename session"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
          </button>
          <button
            @click.stop="$emit('delete')"
            class="p-1 rounded-md text-gray-400 hover:text-red-600 hover:bg-red-50 transition-all"
            title="Delete session"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </template>
    </div>
  </div>

  <!-- Teleported Tooltip -->
  <Teleport to="body">
    <div
      v-if="isCollapsed && showTooltip"
      class="fixed z-[9999] px-3 py-1.5 bg-gray-900 text-white text-xs font-medium rounded-md shadow-lg pointer-events-none whitespace-nowrap transition-opacity duration-200"
      :style="{
        top: tooltipTop + 'px',
        left: tooltipLeft + 'px',
        transform: 'translateY(-50%)'
      }"
    >
      {{ sessionTitle }}
      <!-- Arrow -->
      <div class="absolute top-1/2 -left-1 -translate-y-1/2 border-4 border-transparent border-r-gray-900"></div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { useSessionStore } from '../stores/session'

const props = defineProps({
  session: {
    type: Object,
    required: true
  },
  active: {
    type: Boolean,
    default: false
  },
  isCollapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click', 'delete'])
const sessionStore = useSessionStore()

const isEditing = ref(false)
const editTitle = ref('')
const titleInput = ref(null)
const iconRef = ref(null)
const showTooltip = ref(false)
const tooltipTop = ref(0)
const tooltipLeft = ref(0)

const sessionTitle = computed(() => {
  return props.session.title || props.session.name || 'New Chat'
})

const sessionLetter = computed(() => {
  return sessionTitle.value.charAt(0).toUpperCase()
})

const statusColor = computed(() => {
  const status = props.session.container_status?.toLowerCase()
  if (status === 'running') return 'bg-green-500'
  if (status === 'error' || status === 'failed') return 'bg-red-500'
  return 'bg-gray-400' // stopped, created, etc.
})

function updateTooltipPosition() {
  if (iconRef.value) {
    const rect = iconRef.value.getBoundingClientRect()
    tooltipTop.value = rect.top + rect.height / 2
    tooltipLeft.value = rect.right + 10 // 10px offset
  }
}

function startEditing() {
  editTitle.value = sessionTitle.value
  isEditing.value = true
  nextTick(() => {
    titleInput.value?.focus()
  })
}

async function saveTitle() {
  if (!isEditing.value) return
  
  const newTitle = editTitle.value.trim()
  if (newTitle && newTitle !== sessionTitle.value) {
    try {
      await sessionStore.updateSession(props.session.session_id, { 
        name: newTitle,
        description: props.session.description 
      })
    } catch (e) {
      console.error('Failed to rename session:', e)
      // Revert on error (optional: show toast)
    }
  }
  isEditing.value = false
}

function cancelEditing() {
  isEditing.value = false
  editTitle.value = ''
}
</script>
