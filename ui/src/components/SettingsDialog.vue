<template>
  <Teleport to="body">
    <div v-if="isOpen" class="settings-modal-overlay" @click="closeModal">
      <div class="settings-modal-content" @click.stop>
        
        <!-- Sidebar -->
        <div class="settings-sidebar">
          <div class="sidebar-header">
            <h2>Settings</h2>
          </div>
          
          <nav class="sidebar-nav">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="['nav-item', { active: activeTab === tab.id }]"
            >
              <span class="nav-label">{{ tab.label }}</span>
            </button>
          </nav>

          <div class="sidebar-footer" v-if="user">
            <div class="user-mini-profile">
              <img :src="user.avatar_url" :alt="user.github_login" class="mini-avatar" />
              <div class="mini-details">
                <span class="mini-name">{{ user.github_login }}</span>
                <span class="mini-id">ID: {{ user.id }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Main Content -->
        <div class="settings-main">
          <div class="main-header">
            <h3>{{ activeTabLabel }}</h3>
            <button @click="closeModal" class="close-button">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>

          <div class="main-content-scroll">
            
            <!-- General Tab -->
            <div v-if="activeTab === 'general'" class="tab-panel">
              <div class="settings-group">
                <h4>Appearance</h4>
                <div class="setting-item">
                  <label>Theme</label>
                  <div class="select-wrapper">
                    <select v-model="theme" @change="savePreferences">
                      <option value="light">Light</option>
                      <option value="dark">Dark</option>
                      <option value="auto">System</option>
                    </select>
                  </div>
                </div>
                <div class="setting-item">
                  <label>Language</label>
                  <div class="select-wrapper">
                    <select v-model="language" @change="savePreferences">
                      <option value="en">English</option>
                      <option value="vi">Tiếng Việt</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            <!-- Interface Tab (Placeholder) -->
            <div v-if="activeTab === 'interface'" class="tab-panel">
              <div class="construction-banner">
                <span class="construction-icon">🚧</span>
                <div class="construction-text">
                  <h4>Under Construction</h4>
                  <p>These settings are coming soon. Stay tuned!</p>
                </div>
              </div>

              <div class="settings-group disabled">
                <h4>Display</h4>
                <div class="setting-item">
                  <label>Font Size</label>
                  <div class="select-wrapper">
                    <select disabled>
                      <option>Medium</option>
                    </select>
                  </div>
                </div>
                <div class="setting-item">
                  <label>Density</label>
                  <div class="select-wrapper">
                    <select disabled>
                      <option>Comfortable</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            <!-- Models Tab -->
            <div v-if="activeTab === 'models'" class="tab-panel">
              <div class="settings-group">
                <h4>AI Model Configuration</h4>
                <p class="group-description">Select the AI model and provider you want to use for chat.</p>
                <div class="model-selector-container">
                  <ModelSelector />
                </div>
              </div>
            </div>

            <!-- Agents Tab -->
            <div v-if="activeTab === 'agents'" class="tab-panel">
              <div class="agents-header-actions">
                <p class="group-description">Manage your AI agents and their capabilities.</p>
                <button @click="handleCreateAgent" class="primary-button small">
                  + New Agent
                </button>
              </div>

              <div v-if="loadingAgents" class="loading-state">
                <div class="spinner"></div>
                <p>Loading agents...</p>
              </div>

              <div v-else-if="agents.length === 0" class="empty-state">
                <div class="empty-icon">🤖</div>
                <h4>No agents found</h4>
                <p>Create your first AI agent to get started.</p>
                <button @click="handleCreateAgent" class="primary-button">
                  Create Agent
                </button>
              </div>

              <div v-else class="agents-grid">
                <div v-for="agent in agents" :key="agent.id" class="agent-card">
                  <div class="agent-card-header">
                    <div class="agent-icon-wrapper">
                      🤖
                    </div>
                    <div class="agent-title">
                      <h4>{{ agent.name }}</h4>
                      <span class="status-badge active">Active</span>
                    </div>
                    <div class="agent-actions-menu">
                      <button @click="deleteAgent(agent)" class="icon-button danger" title="Delete">
                        🗑️
                      </button>
                    </div>
                  </div>
                  <p class="agent-desc">{{ agent.description || 'No description provided.' }}</p>
                  <div class="agent-footer">
                    <span class="date">Created: {{ formatDate(agent.created_at) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Advanced Tab (Placeholder) -->
            <div v-if="activeTab === 'advanced'" class="tab-panel">
               <div class="construction-banner">
                <span class="construction-icon">🚧</span>
                <div class="construction-text">
                  <h4>Under Construction</h4>
                  <p>Advanced configurations are currently in development.</p>
                </div>
              </div>

              <div class="settings-group disabled">
                <h4>Network</h4>
                <div class="setting-item">
                  <label>API Endpoint</label>
                  <input type="text" value="http://localhost:8000" disabled />
                </div>
              </div>
               <div class="settings-group disabled">
                <h4>Debug</h4>
                <div class="setting-item checkbox-item">
                  <label>Enable Debug Mode</label>
                  <input type="checkbox" disabled />
                </div>
              </div>
            </div>

            <!-- About Tab -->
            <div v-if="activeTab === 'about'" class="tab-panel">
              <div class="about-section">
                <div class="app-logo">
                  🚀
                </div>
                <h3>OpenCode UI</h3>
                <p class="version">Version 1.0.0-beta</p>
                <p class="about-desc">
                  An advanced AI-powered coding assistant interface.
                </p>
                <div class="about-links">
                  <a href="#" class="link-item">Documentation</a>
                  <a href="#" class="link-item">GitHub Repository</a>
                  <a href="#" class="link-item">Report an Issue</a>
                </div>
              </div>
            </div>

          </div>
        </div>

        <!-- Modals (Delete, Agent Creation) -->
        <!-- Delete Confirmation Modal -->
        <div v-if="showDeleteModal" class="modal-overlay-nested" @click="cancelDelete">
          <div class="modal-content-nested" @click.stop>
            <h4>Delete Agent</h4>
            <p>Are you sure you want to delete "{{ agentToDelete?.name }}"?</p>
            <div class="modal-actions">
              <button @click="cancelDelete" class="secondary-button">Cancel</button>
              <button @click="confirmDelete" class="danger-button">Delete</button>
            </div>
          </div>
        </div>

        <!-- Agent Creation Modal -->
        <div v-if="showAgentModal" class="modal-overlay-nested" @click="closeAgentModal">
          <div class="modal-content-nested large" @click.stop>
            <div class="nested-header">
              <h3>Create New Agent</h3>
              <button @click="closeAgentModal" class="close-button-nested">✕</button>
            </div>
            
            <div class="nested-body">
              <!-- Agent Form -->
              <div v-if="!deviceCode && !isAuthenticated" class="agent-form">
                <div class="form-group">
                  <label>Agent Name</label>
                  <input v-model="agentName" type="text" placeholder="e.g., Code Assistant" :disabled="isAuthenticating" />
                </div>
                <div class="form-group">
                  <label>Description</label>
                  <textarea v-model="agentDescription" placeholder="What does this agent do?" rows="3" :disabled="isAuthenticating"></textarea>
                </div>
                <button @click="createAgent" class="primary-button full-width" :disabled="!agentName.trim() || isAuthenticating">
                  {{ isAuthenticating ? 'Initializing...' : 'Create Agent' }}
                </button>
              </div>

              <!-- Device Auth -->
              <div v-if="deviceCode && !isAuthenticated" class="auth-flow">
                <div class="step-indicator">
                  <div class="step active">1. Copy Code</div>
                  <div class="step">2. Authorize</div>
                </div>
                
                <div class="code-box">
                  <code>{{ deviceCode.user_code }}</code>
                  <button @click="copyCode" class="copy-btn">{{ copied ? 'Copied!' : 'Copy' }}</button>
                </div>

                <p class="auth-instruction">
                  Please visit <a :href="deviceCode.verification_uri" target="_blank">{{ deviceCode.verification_uri }}</a> and enter the code above.
                </p>

                <div class="loading-spinner-container">
                  <div class="spinner small"></div>
                  <span>Waiting for authorization...</span>
                </div>

                <button @click="cancelAuth" class="secondary-button full-width">Cancel</button>
              </div>

              <!-- Success -->
              <div v-if="isAuthenticated" class="success-state">
                <div class="success-icon">✓</div>
                <h4>Agent Created!</h4>
                <p>"{{ agentName }}" is ready to use.</p>
                <div class="modal-actions">
                  <button @click="createAnotherAgent" class="secondary-button">Create Another</button>
                  <button @click="closeAgentModal" class="primary-button">Done</button>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import ModelSelector from './ModelSelector.vue'

const props = defineProps({
  isOpen: { type: Boolean, default: false }
})

const emit = defineEmits(['close'])

// Navigation
const activeTab = ref('general')
const tabs = [
  { id: 'general', label: 'General' },
  { id: 'interface', label: 'Interface' },
  { id: 'models', label: 'Models' },
  { id: 'agents', label: 'Agents' },
  { id: 'advanced', label: 'Advanced' },
  { id: 'about', label: 'About' }
]

const activeTabLabel = computed(() => {
  return tabs.find(t => t.id === activeTab.value)?.label || 'Settings'
})

// Data
const user = ref(null)
const agents = ref([])
const loadingAgents = ref(false)
const theme = ref('light')
const language = ref('en')

// Modals
const showDeleteModal = ref(false)
const agentToDelete = ref(null)
const showAgentModal = ref(false)

// Agent Auth
const agentName = ref('')
const agentDescription = ref('')
const deviceCode = ref(null)
const isAuthenticated = ref(false)
const isAuthenticating = ref(false)
const pollingController = ref(null)
const pollingTimeLeft = ref(0)
const copied = ref(false)
const pollingStarted = ref(false)

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Watchers
watch(() => props.isOpen, async (newValue) => {
  if (newValue) {
    // activeTab.value = 'general' // Optional: reset tab on open
    await loadUserInfo()
    if (activeTab.value === 'agents') await loadAgents()
    loadPreferences()
  }
})

watch(activeTab, async (newTab) => {
  if (newTab === 'agents') {
    await loadAgents()
  }
})

// Methods
const loadUserInfo = async () => {
  try {
    const response = await fetch(`${API_URL}/auth/me`, { credentials: 'include' })
    if (response.ok) user.value = await response.json()
  } catch (error) {
    console.error('Error loading user info:', error)
  }
}

const loadAgents = async () => {
  loadingAgents.value = true
  try {
    const response = await fetch(`${API_URL}/api/agents`, { credentials: 'include' })
    if (response.ok) agents.value = await response.json()
  } catch (error) {
    console.error('Error loading agents:', error)
  } finally {
    loadingAgents.value = false
  }
}

const loadPreferences = () => {
  theme.value = localStorage.getItem('theme') || 'light'
  language.value = localStorage.getItem('language') || 'en'
}

const savePreferences = () => {
  localStorage.setItem('theme', theme.value)
  localStorage.setItem('language', language.value)
  document.documentElement.setAttribute('data-theme', theme.value)
}

const closeModal = () => emit('close')

const formatDate = (dateString) => {
  if (!dateString) return 'Never'
  return new Date(dateString).toLocaleDateString()
}

// Agent Management
const handleCreateAgent = () => showAgentModal.value = true

const deleteAgent = (agent) => {
  agentToDelete.value = agent
  showDeleteModal.value = true
}

const confirmDelete = async () => {
  if (!agentToDelete.value) return
  try {
    const response = await fetch(`${API_URL}/api/agents/${agentToDelete.value.id}`, {
      method: 'DELETE',
      credentials: 'include'
    })
    if (response.ok) {
      agents.value = agents.value.filter(a => a.id !== agentToDelete.value.id)
      showDeleteModal.value = false
      agentToDelete.value = null
    }
  } catch (error) {
    console.error('Error deleting agent:', error)
  }
}

const cancelDelete = () => {
  showDeleteModal.value = false
  agentToDelete.value = null
}

// Agent Auth Flow
const closeAgentModal = () => {
  showAgentModal.value = false
  agentName.value = ''
  agentDescription.value = ''
  deviceCode.value = null
  isAuthenticated.value = false
  isAuthenticating.value = false
  if (pollingController.value) pollingController.value.abort()
}

const createAgent = async () => {
  if (!agentName.value.trim()) return
  isAuthenticating.value = true
  try {
    const response = await fetch(`${API_URL}/auth/device`, { credentials: 'include' })
    if (!response.ok) throw new Error('Failed to get device code')
    const data = await response.json()
    deviceCode.value = data
    startPolling(data.device_code, data.interval || 5, data.expires_in || 900)
  } catch (error) {
    console.error('Create agent error:', error)
    isAuthenticating.value = false
    alert('Failed to start agent creation')
  }
}

const startPolling = async (code, interval, expiresIn) => {
  pollingController.value = new AbortController()
  pollingStarted.value = true
  
  // Polling loop handled by recursion or interval
  const poll = async () => {
    if (!pollingStarted.value) return
    try {
      const response = await fetch(`${API_URL}/auth/device/poll`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          device_code: code,
          expires_in: expiresIn,
          agent_name: agentName.value,
          agent_description: agentDescription.value
        }),
        signal: pollingController.value.signal
      })
      
      if (response.ok) {
        isAuthenticated.value = true
        pollingStarted.value = false
        isAuthenticating.value = false
        await loadAgents()
      } else {
        // Continue polling if pending, otherwise stop
        const data = await response.json()
        if (data.detail === 'authorization_pending') {
          setTimeout(poll, interval * 1000)
        } else {
          // Error
          console.error('Polling error:', data)
        }
      }
    } catch (error) {
      if (error.name !== 'AbortError') console.error('Polling error:', error)
    }
  }
  
  poll()
}

const copyCode = async () => {
  await navigator.clipboard.writeText(deviceCode.value.user_code)
  copied.value = true
  setTimeout(() => copied.value = false, 2000)
}

const cancelAuth = () => {
  if (pollingController.value) pollingController.value.abort()
  deviceCode.value = null
  pollingStarted.value = false
  isAuthenticating.value = false
}

const createAnotherAgent = () => {
  agentName.value = ''
  agentDescription.value = ''
  deviceCode.value = null
  isAuthenticated.value = false
  isAuthenticating.value = false
  pollingStarted.value = false
}
</script>

<style scoped>
/* Modal Overlay & Container */
.settings-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease-out;
}

.settings-modal-content {
  background: #ffffff;
  width: 900px;
  height: 600px;
  max-width: 95vw;
  max-height: 90vh;
  border-radius: 16px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  display: flex;
  overflow: hidden;
}

/* Sidebar */
.settings-sidebar {
  width: 240px;
  background: #f8fafc;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  padding: 1.5rem 0;
}

.sidebar-header {
  padding: 0 1.5rem 1.5rem;
}

.sidebar-header h2 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0 0.75rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  color: #64748b;
  font-weight: 500;
  transition: all 0.2s;
  text-align: left;
}

.nav-item:hover {
  background: #f1f5f9;
  color: #334155;
}

.nav-item.active {
  background: #e0f2fe;
  color: #0284c7;
}

.nav-icon {
  font-size: 1.1rem;
}

.sidebar-footer {
  padding: 1rem 1.5rem 0;
  border-top: 1px solid #e2e8f0;
}

.user-mini-profile {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.mini-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 2px solid #e2e8f0;
}

.mini-details {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.mini-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: #334155;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mini-id {
  font-size: 0.7rem;
  color: #94a3b8;
}

/* Main Content */
.settings-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.main-header {
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.main-header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #0f172a;
}

.close-button {
  background: transparent;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 6px;
  transition: all 0.2s;
}

.close-button:hover {
  background: #f1f5f9;
  color: #64748b;
}

.main-content-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.tab-panel {
  animation: slideIn 0.3s ease-out;
}

/* Settings Groups */
.settings-group {
  margin-bottom: 2.5rem;
}

.settings-group.disabled {
  opacity: 0.6;
  pointer-events: none;
}

.settings-group h4 {
  font-size: 1rem;
  color: #334155;
  margin: 0 0 1rem;
  font-weight: 600;
}

.group-description {
  color: #64748b;
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0;
  border-bottom: 1px solid #f1f5f9;
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-item label {
  font-weight: 500;
  color: #475569;
}

.setting-item input[type="text"] {
  padding: 0.5rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  width: 200px;
}

.select-wrapper select {
  padding: 0.5rem 2rem 0.5rem 1rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: #fff;
  color: #334155;
  font-size: 0.9rem;
  cursor: pointer;
}

/* Construction Banner */
.construction-banner {
  background: #fffbeb;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}

.construction-icon {
  font-size: 1.5rem;
}

.construction-text h4 {
  margin: 0 0 0.25rem;
  color: #92400e;
  font-size: 1rem;
}

.construction-text p {
  margin: 0;
  color: #b45309;
  font-size: 0.9rem;
}

/* Agents Grid */
.agents-header-actions {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.agent-card {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.25rem;
  background: #fff;
  transition: all 0.2s;
}

.agent-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.agent-card-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.agent-icon-wrapper {
  width: 40px;
  height: 40px;
  background: #f1f5f9;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
}

.agent-title {
  flex: 1;
}

.agent-title h4 {
  margin: 0;
  font-size: 1rem;
  color: #1e293b;
}

.status-badge {
  font-size: 0.7rem;
  padding: 0.1rem 0.5rem;
  border-radius: 999px;
  background: #dcfce7;
  color: #166534;
  font-weight: 600;
}

.agent-desc {
  color: #64748b;
  font-size: 0.875rem;
  line-height: 1.5;
  margin: 0 0 1rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.agent-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  color: #94a3b8;
}

.icon-button {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.icon-button:hover {
  opacity: 1;
}

.icon-button.danger:hover {
  color: #ef4444;
}

/* About Section */
.about-section {
  text-align: center;
  padding: 3rem 1rem;
}

.app-logo {
  font-size: 4rem;
  margin-bottom: 1rem;
  animation: float 3s ease-in-out infinite;
}

.about-section h3 {
  font-size: 1.5rem;
  color: #1e293b;
  margin: 0 0 0.5rem;
}

.version {
  color: #64748b;
  font-family: monospace;
  background: #f1f5f9;
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  display: inline-block;
  margin-bottom: 1.5rem;
}

.about-links {
  display: flex;
  justify-content: center;
  gap: 1.5rem;
  margin-top: 2rem;
}

.link-item {
  color: #0284c7;
  text-decoration: none;
  font-weight: 500;
}

.link-item:hover {
  text-decoration: underline;
}

/* Buttons */
.primary-button {
  background: #0284c7;
  color: white;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.primary-button:hover {
  background: #0369a1;
}

.primary-button:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.primary-button.small {
  padding: 0.4rem 0.8rem;
  font-size: 0.875rem;
}

.secondary-button {
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #cbd5e1;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.secondary-button:hover {
  background: #e2e8f0;
}

.danger-button {
  background: #ef4444;
  color: white;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
}

.danger-button:hover {
  background: #dc2626;
}

/* Nested Modals */
.modal-overlay-nested {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.modal-content-nested {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  width: 400px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

.modal-content-nested.large {
  width: 600px;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.nested-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nested-header h3 {
  margin: 0;
  font-size: 1.1rem;
}

.nested-body {
  padding: 1.5rem;
}

.close-button-nested {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: #94a3b8;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

/* Form Elements */
.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #334155;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 0.95rem;
  font-family: inherit;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #0284c7;
  box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.1);
}

.full-width {
  width: 100%;
}

/* Auth Flow */
.step-indicator {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.step {
  font-size: 0.875rem;
  color: #94a3b8;
  font-weight: 500;
}

.step.active {
  color: #0284c7;
}

.code-box {
  background: #f8fafc;
  border: 2px dashed #cbd5e1;
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.code-box code {
  font-family: monospace;
  font-size: 1.25rem;
  font-weight: 700;
  letter-spacing: 2px;
  color: #1e293b;
}

.copy-btn {
  background: #fff;
  border: 1px solid #cbd5e1;
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
}

.auth-instruction {
  text-align: center;
  color: #64748b;
  margin-bottom: 1.5rem;
}

.loading-spinner-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  color: #64748b;
  margin-bottom: 1.5rem;
}

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #e2e8f0;
  border-top-color: #0284c7;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner.small {
  width: 16px;
  height: 16px;
  border-width: 2px;
}
</style>