<template>
  <div class="container-controls">
    <div class="status-bar" :class="statusClass">
      <div class="status-indicator">
        <span class="status-dot" :class="statusDotClass"></span>
        <span class="status-text">{{ statusText }}</span>
      </div>
      
      <div class="control-buttons">
        <button
          v-if="canStart"
          @click="handleStart"
          :disabled="loading"
          class="control-btn start-btn"
          title="Start container"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {{ loading ? 'Starting...' : 'Start' }}
        </button>
        
        <button
          v-if="canStop"
          @click="handleStop"
          :disabled="loading"
          class="control-btn stop-btn"
          title="Stop container"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
          </svg>
          {{ loading ? 'Stopping...' : 'Stop' }}
        </button>
        
        <button
          v-if="hasContainer"
          @click="handleRefresh"
          :disabled="loading"
          class="control-btn refresh-btn"
          title="Refresh status"
        >
          <svg class="w-4 h-4" :class="{ 'animate-spin': loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
        
        <button
          v-if="hasContainer"
          @click="handleViewLogs"
          class="control-btn logs-btn"
          title="View logs"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </button>
      </div>
    </div>
    
    <!-- Error message -->
    <div v-if="error" class="error-message">
      {{ error }}
    </div>
    
    <!-- Logs modal -->
    <teleport to="body">
      <div v-if="showLogs" class="modal-overlay" @click="showLogs = false">
        <div class="logs-modal" @click.stop>
          <div class="logs-header">
            <h3>Container Logs</h3>
            <button @click="showLogs = false" class="close-btn">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="logs-content">
            <pre v-if="logs">{{ logs }}</pre>
            <div v-else class="loading-logs">Loading logs...</div>
          </div>
          <div class="logs-footer">
            <button @click="handleRefreshLogs" class="refresh-logs-btn">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
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

const statusClass = computed(() => {
  if (!props.containerStatus) return 'status-none'
  const status = props.containerStatus.toLowerCase()
  if (status === 'running') return 'status-running'
  if (status === 'stopped' || status === 'exited') return 'status-stopped'
  if (status === 'starting' || status === 'created') return 'status-starting'
  return 'status-unknown'
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

<style scoped>
.container-controls {
  margin-bottom: 1rem;
}

.status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  border: 1px solid;
  transition: all 0.2s;
}

.status-bar.status-running {
  background: #f0fdf4;
  border-color: #86efac;
}

.status-bar.status-stopped {
  background: #fef2f2;
  border-color: #fca5a5;
}

.status-bar.status-starting {
  background: #fffbeb;
  border-color: #fde047;
}

.status-bar.status-none,
.status-bar.status-unknown {
  background: #f9fafb;
  border-color: #e5e7eb;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-text {
  font-weight: 600;
  font-size: 0.875rem;
  color: #374151;
}

.control-buttons {
  display: flex;
  gap: 0.5rem;
}

.control-btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.start-btn {
  background: #10b981;
  color: white;
}

.start-btn:hover:not(:disabled) {
  background: #059669;
}

.stop-btn {
  background: #ef4444;
  color: white;
}

.stop-btn:hover:not(:disabled) {
  background: #dc2626;
}

.refresh-btn {
  background: #3b82f6;
  color: white;
  padding: 0.5rem;
}

.refresh-btn:hover:not(:disabled) {
  background: #2563eb;
}

.logs-btn {
  background: #6366f1;
  color: white;
  padding: 0.5rem;
}

.logs-btn:hover {
  background: #4f46e5;
}

.error-message {
  margin-top: 0.5rem;
  padding: 0.75rem;
  background: #fef2f2;
  border: 1px solid #fca5a5;
  border-radius: 6px;
  color: #dc2626;
  font-size: 0.875rem;
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.logs-modal {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 800px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.logs-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #6b7280;
  padding: 0.5rem;
  border-radius: 6px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.logs-content {
  flex: 1;
  overflow: auto;
  padding: 1.5rem;
  background: #1f2937;
}

.logs-content pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.875rem;
  line-height: 1.5;
  color: #f9fafb;
  white-space: pre-wrap;
  word-break: break-all;
}

.loading-logs {
  text-align: center;
  color: #9ca3af;
  padding: 2rem;
}

.logs-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
}

.refresh-logs-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.refresh-logs-btn:hover {
  background: #2563eb;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>
