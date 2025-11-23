<template>
  <div :class="['container-controls', variant === 'default' ? 'mb-6' : '']">
    <div 
      class="flex items-center justify-between transition-all duration-200"
      :class="[
        variant === 'default' ? 'p-1 pl-1 pr-1 bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md' : 'gap-3'
      ]"
    >
      
      <!-- Status Indicator -->
      <div class="flex items-center gap-3" :class="{ 'pl-3': variant === 'default' }">
        <div 
          class="flex items-center gap-2 rounded-full text-xs font-semibold border transition-colors"
          :class="[
            statusBadgeClass,
            variant === 'default' ? 'px-2.5 py-1' : 'px-2 py-0.5 bg-opacity-50 border-transparent'
          ]"
        >
          <span class="w-1.5 h-1.5 rounded-full" :class="statusDotClass"></span>
          {{ statusText }}
        </div>
        <span v-if="error" class="text-xs text-red-500 truncate max-w-[200px]" :title="error">
          {{ error }}
        </span>
      </div>
      
      <!-- Control Buttons -->
      <div class="flex items-center gap-1">
        <button
          v-if="canStart"
          @click="handleStart"
          :disabled="loading"
          class="flex items-center gap-1.5 text-xs font-medium text-green-700 bg-green-50 hover:bg-green-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :class="[variant === 'default' ? 'px-3 py-1.5' : 'px-2 py-1']"
          title="Start container"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span v-if="variant === 'default' || loading">{{ loading ? 'Starting...' : 'Start' }}</span>
        </button>
        
        <button
          v-if="canStop"
          @click="handleStop"
          :disabled="loading"
          class="flex items-center gap-1.5 text-xs font-medium text-red-700 bg-red-50 hover:bg-red-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :class="[variant === 'default' ? 'px-3 py-1.5' : 'px-2 py-1']"
          title="Stop container"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
          </svg>
          <span v-if="variant === 'default' || loading">{{ loading ? 'Stopping...' : 'Stop' }}</span>
        </button>
        
        <div class="w-px h-4 bg-gray-200 mx-1" v-if="hasContainer && variant === 'default'"></div>

        <button
          v-if="hasContainer"
          @click="handleRefresh"
          :disabled="loading"
          class="text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-lg transition-colors disabled:opacity-50"
          :class="[variant === 'default' ? 'p-1.5' : 'p-1']"
          title="Refresh status"
        >
          <svg class="w-4 h-4" :class="{ 'animate-spin': loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
        
        <button
          v-if="hasContainer"
          @click="handleViewLogs"
          class="text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
          :class="[variant === 'default' ? 'p-1.5' : 'p-1']"
          title="View logs"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </button>
      </div>
    </div>
    
    <!-- Logs modal -->
    <teleport to="body">
      <div v-if="showLogs" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4" @click="showLogs = false">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[85vh] flex flex-col overflow-hidden" @click.stop>
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
            <h3 class="text-lg font-semibold text-gray-800">Container Logs</h3>
            <button @click="showLogs = false" class="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <div class="flex-1 overflow-auto bg-[#1e1e1e] p-6 font-mono text-sm">
            <pre v-if="logs" class="text-gray-300 whitespace-pre-wrap break-all leading-relaxed">{{ logs }}</pre>
            <div v-else class="flex items-center justify-center h-full text-gray-500">
              <svg class="w-6 h-6 animate-spin mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Loading logs...
            </div>
          </div>
          
          <div class="px-6 py-4 border-t border-gray-100 bg-gray-50 flex justify-end">
            <button @click="handleRefreshLogs" class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg shadow-sm transition-colors">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh Logs
            </button>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useSessionStore } from '../stores/session'

const props = defineProps({
  sessionId: {
    type: String,
    required: true
  },
  containerStatus: {
    type: String,
    default: null
  },
  containerId: {
    type: String,
    default: null
  },
  variant: {
    type: String,
    default: 'default', // 'default' | 'inline'
    validator: (value) => ['default', 'inline'].includes(value)
  }
})

const sessionStore = useSessionStore()
const loading = ref(false)
const error = ref(null)
const showLogs = ref(false)
const logs = ref(null)

const statusText = computed(() => {
  if (!props.containerStatus) return 'No container'
  const status = props.containerStatus.toLowerCase()
  if (status === 'running') return 'Running'
  if (status === 'stopped' || status === 'exited') return 'Stopped'
  if (status === 'starting' || status === 'created') return 'Starting'
  return status.charAt(0).toUpperCase() + status.slice(1)
})

const statusBadgeClass = computed(() => {
  if (!props.containerStatus) return 'bg-gray-50 text-gray-600 border-gray-200'
  const status = props.containerStatus.toLowerCase()
  if (status === 'running') return 'bg-green-50 text-green-700 border-green-200'
  if (status === 'stopped' || status === 'exited') return 'bg-red-50 text-red-700 border-red-200'
  if (status === 'starting' || status === 'created') return 'bg-yellow-50 text-yellow-700 border-yellow-200'
  return 'bg-gray-50 text-gray-600 border-gray-200'
})

const statusDotClass = computed(() => {
  if (!props.containerStatus) return 'bg-gray-400'
  const status = props.containerStatus.toLowerCase()
  if (status === 'running') return 'bg-green-500 animate-pulse'
  if (status === 'stopped' || status === 'exited') return 'bg-red-500'
  if (status === 'starting' || status === 'created') return 'bg-yellow-500 animate-pulse'
  return 'bg-gray-400'
})

const hasContainer = computed(() => !!props.containerId)
const canStart = computed(() => !props.containerStatus || props.containerStatus === 'stopped' || props.containerStatus === 'exited')
const canStop = computed(() => props.containerStatus === 'running' || props.containerStatus === 'starting')

const handleStart = async () => {
  loading.value = true
  error.value = null
  try {
    await sessionStore.startContainer(props.sessionId)
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || 'Failed to start container'
  } finally {
    loading.value = false
  }
}

const handleStop = async () => {
  loading.value = true
  error.value = null
  try {
    await sessionStore.stopContainer(props.sessionId)
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || 'Failed to stop container'
  } finally {
    loading.value = false
  }
}

const handleRefresh = async () => {
  loading.value = true
  error.value = null
  try {
    await sessionStore.getContainerStatus(props.sessionId)
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || 'Failed to refresh status'
  } finally {
    loading.value = false
  }
}

const handleViewLogs = async () => {
  showLogs.value = true
  logs.value = null
  try {
    const response = await sessionStore.getContainerLogs(props.sessionId, 500)
    logs.value = response.logs || 'No logs available'
  } catch (e) {
    logs.value = `Error loading logs: ${e.response?.data?.detail || e.message}`
  }
}

const handleRefreshLogs = async () => {
  logs.value = null
  try {
    const response = await sessionStore.getContainerLogs(props.sessionId, 500)
    logs.value = response.logs || 'No logs available'
  } catch (e) {
    logs.value = `Error loading logs: ${e.response?.data?.detail || e.message}`
  }
}
</script>
