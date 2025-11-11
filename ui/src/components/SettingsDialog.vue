<template>
  <Teleport to="body">
    <div v-if="isOpen" class="settings-modal-overlay" @click="closeModal">
      <div class="settings-modal-content" @click.stop>
        <!-- Modal Header -->
        <div class="settings-modal-header">
          <h2>Settings</h2>
          <button @click="closeModal" class="close-button">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <!-- Tab Navigation -->
        <div class="tab-navigation">
          <button
            @click="activeTab = 'profile'"
            :class="['tab-button', { active: activeTab === 'profile' }]"
          >
            Profile
          </button>
          <button
            @click="activeTab = 'agents'"
            :class="['tab-button', { active: activeTab === 'agents' }]"
          >
            Agents
          </button>
          <button
            @click="activeTab = 'preferences'"
            :class="['tab-button', { active: activeTab === 'preferences' }]"
          >
            Preferences
          </button>
        </div>

        <!-- Tab Content -->
        <div class="tab-content">
          <!-- Profile Tab -->
          <div v-if="activeTab === 'profile'" class="tab-panel">
            <div class="profile-section">
              <h3>User Profile</h3>
              <div v-if="user" class="user-info">
                <div class="user-avatar">
                  <img :src="user.avatar_url" :alt="user.github_login" />
                </div>
                <div class="user-details">
                  <h4>{{ user.github_login }}</h4>
                  <p class="user-email">{{ user.email }}</p>
                  <p class="user-id">ID: {{ user.id }}</p>
                </div>
              </div>
              <div v-else class="loading">
                <div class="spinner"></div>
                <p>Loading user information...</p>
              </div>
            </div>
          </div>

          <!-- Agents Tab -->
          <div v-if="activeTab === 'agents'" class="tab-panel">
            <div class="agents-section">
              <div class="agents-header">
                <h3>AI Agents</h3>
                <button @click="handleCreateAgent" class="create-agent-button">
                  + Create New Agent
                </button>
              </div>

              <div v-if="loadingAgents" class="loading">
                <div class="spinner"></div>
                <p>Loading agents...</p>
              </div>

              <div v-else-if="agents.length === 0" class="empty-state">
                <div class="empty-icon">🤖</div>
                <h4>No agents yet</h4>
                <p>Create your first AI agent to get started</p>
                <button @click="handleCreateAgent" class="create-first-agent-button">
                  Create Your First Agent
                </button>
              </div>

              <div v-else class="agents-list">
                <div
                  v-for="agent in agents"
                  :key="agent.id"
                  class="agent-card"
                >
                  <div class="agent-info">
                    <div class="agent-header">
                      <h4>{{ agent.name }}</h4>
                      <span class="agent-status active">Active</span>
                    </div>
                    <p class="agent-description">{{ agent.description || 'No description' }}</p>
                    <div class="agent-meta">
                      <span class="created-date">
                        Created: {{ formatDate(agent.created_at) }}
                      </span>
                      <span v-if="agent.last_used" class="last-used">
                        Last used: {{ formatDate(agent.last_used) }}
                      </span>
                    </div>
                  </div>
                  <div class="agent-actions">
                    <button @click="editAgent(agent)" class="edit-button" title="Edit Agent">
                      ✏️
                    </button>
                    <button @click="deleteAgent(agent)" class="delete-button" title="Delete Agent">
                      🗑️
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Preferences Tab -->
          <div v-if="activeTab === 'preferences'" class="tab-panel">
            <div class="preferences-section">
              <h3>Preferences</h3>
              <div class="preference-item">
                <label for="theme">Theme:</label>
                <select id="theme" v-model="theme" @change="savePreferences">
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="auto">Auto</option>
                </select>
              </div>
              <div class="preference-item">
                <label for="language">Language:</label>
                <select id="language" v-model="language" @change="savePreferences">
                  <option value="en">English</option>
                  <option value="vi">Tiếng Việt</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- Delete Confirmation Modal -->
        <div v-if="showDeleteModal" class="delete-modal-overlay" @click="cancelDelete">
          <div class="delete-modal-content" @click.stop>
            <h4>Delete Agent</h4>
            <p>Are you sure you want to delete agent "{{ agentToDelete?.name }}"?</p>
            <p class="warning-text">This action cannot be undone.</p>
            <div class="delete-modal-actions">
              <button @click="cancelDelete" class="cancel-button">Cancel</button>
              <button @click="confirmDelete" class="delete-confirm-button">Delete</button>
            </div>
          </div>
        </div>

        <!-- Agent Creation Modal -->
        <div v-if="showAgentModal" class="agent-modal-overlay" @click="closeAgentModal">
          <div class="agent-modal-content" @click.stop>
            <div class="agent-modal-header">
              <h3>Create New Agent</h3>
              <button @click="closeAgentModal" class="close-button">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>

            <div class="agent-modal-body">
              <!-- Agent Info Section -->
              <div class="agent-info-section">
                <div class="agent-details">
                  <div class="agent-form">
                    <div class="form-group">
                      <label for="agent-name">Agent Name:</label>
                      <input
                        id="agent-name"
                        v-model="agentName"
                        type="text"
                        placeholder="Enter agent name"
                        :disabled="isAuthenticating"
                      />
                    </div>
                    <div class="form-group">
                      <label for="agent-description">Description (optional):</label>
                      <textarea
                        id="agent-description"
                        v-model="agentDescription"
                        placeholder="Describe what this agent does"
                        :disabled="isAuthenticating"
                        rows="3"
                      ></textarea>
                    </div>
                    <div class="action-buttons">
                      <button
                        @click="createAgent"
                        class="create-agent-button"
                        :disabled="!agentName.trim() || isAuthenticating"
                      >
                        {{ isAuthenticating ? 'Creating Agent...' : 'Create Agent' }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Device Code Flow -->
              <div v-if="deviceCode" class="device-auth-section">
                <div v-if="!isAuthenticated" class="device-code-section">
                  <h4>Device Authentication</h4>
                  <p class="instruction-text">
                    Copy this code and paste it on the GitHub authorization page:
                  </p>

                  <div class="code-display">
                    <code>{{ deviceCode.user_code }}</code>
                    <button @click="copyCode" class="copy-button" :disabled="copied">
                      {{ copied ? 'Copied!' : 'Copy' }}
                    </button>
                  </div>

                  <div class="link-section">
                    <p>Then visit this link to enter the code:</p>
                    <a :href="deviceCode.verification_uri" target="_blank" class="github-link">
                      {{ deviceCode.verification_uri }}
                    </a>
                  </div>

                  <div v-if="pollingStarted" class="polling-status">
                    <div class="spinner small"></div>
                    <p>Waiting for authorization... ({{ pollingTimeLeft }}s)</p>
                  </div>

                  <div class="action-buttons">
                    <button @click="cancelAuth" class="cancel-button">
                      Cancel
                    </button>
                  </div>
                </div>

                <div v-else class="success-section">
                  <div class="success-icon">✓</div>
                  <p>Agent authentication successful!</p>
                  <p class="agent-info">Agent "{{ agentName }}" has been created and authenticated.</p>
                  <div class="success-actions">
                    <button @click="createAnotherAgent" class="create-another-button">
                      Create Another Agent
                    </button>
                    <button @click="closeAgentModal" class="back-home-button">
                      Close
                    </button>
                  </div>
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
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'

// Props
const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['close', 'create-agent'])

// Tab management
const activeTab = ref('agents')

// User data
const user = ref(null)

// Agents data
const agents = ref([])
const loadingAgents = ref(false)

// Preferences
const theme = ref('light')
const language = ref('en')

// Delete modal
const showDeleteModal = ref(false)
const agentToDelete = ref(null)

// Agent modal
const showAgentModal = ref(false)

// Agent auth data
const agentName = ref('')
const agentDescription = ref('')
const deviceCode = ref(null)
const isAuthenticated = ref(false)
const isAuthenticating = ref(false)
const pollingController = ref(null)
const pollingTimeLeft = ref(0)
const copied = ref(false)
const pollingStarted = ref(false)

const router = useRouter()
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Watch for modal opening to load data
watch(() => props.isOpen, async (newValue) => {
  if (newValue) {
    activeTab.value = 'agents' // Reset to agents tab
    await loadUserInfo()
    await loadAgents()
    loadPreferences()
  }
})

const loadUserInfo = async () => {
  try {
    const response = await fetch(`${API_URL}/auth/me`, {
      credentials: 'include'
    })

    if (response.ok) {
      user.value = await response.json()
    }
  } catch (error) {
    console.error('Error loading user info:', error)
  }
}

const loadAgents = async () => {
  loadingAgents.value = true
  try {
    const response = await fetch(`${API_URL}/api/agents`, {
      credentials: 'include'
    })

    if (response.ok) {
      agents.value = await response.json()
    }
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
  // Apply theme
  document.documentElement.setAttribute('data-theme', theme.value)
}

const handleCreateAgent = () => {
  showAgentModal.value = true
}

const editAgent = (agent) => {
  // TODO: Implement edit agent functionality
  alert(`Edit agent: ${agent.name}`)
}

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
      // Remove agent from list
      agents.value = agents.value.filter(a => a.id !== agentToDelete.value.id)
      showDeleteModal.value = false
      agentToDelete.value = null
    } else {
      alert('Failed to delete agent')
    }
  } catch (error) {
    console.error('Error deleting agent:', error)
    alert('Error deleting agent')
  }
}

const cancelDelete = () => {
  showDeleteModal.value = false
  agentToDelete.value = null
}

const closeAgentModal = () => {
  showAgentModal.value = false
  // Reset form state
  agentName.value = ''
  agentDescription.value = ''
  deviceCode.value = null
  isAuthenticated.value = false
  isAuthenticating.value = false
  pollingStarted.value = false
}

const closeModal = () => {
  emit('close')
}

const formatDate = (dateString) => {
  if (!dateString) return 'Never'
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

// Agent auth functions
const createAgent = async () => {
  if (!agentName.value.trim()) {
    alert('Please enter an agent name')
    return
  }

  isAuthenticating.value = true

  try {
    const response = await fetch(`${API_URL}/auth/device`, {
      credentials: 'include'
    })

    if (!response.ok) {
      throw new Error(`Failed to get device code: ${response.statusText}`)
    }

    const data = await response.json()
    deviceCode.value = data

    // Start polling immediately
    startPolling(deviceCode.value.device_code, deviceCode.value.interval || 5, deviceCode.value.expires_in || 900)

  } catch (error) {
    console.error('Create agent error:', error)
    isAuthenticating.value = false
    alert('Failed to create agent: ' + error.message)
  }
}

const startPolling = async (deviceCodeValue, interval, expiresIn) => {
  try {
    pollingController.value = new AbortController()

    pollingStarted.value = true
    pollingTimeLeft.value = expiresIn || 900

    const countdownInterval = setInterval(() => {
      pollingTimeLeft.value = Math.max(0, pollingTimeLeft.value - 1)
      if (pollingTimeLeft.value <= 0) {
        clearInterval(countdownInterval)
        if (pollingController.value) {
          pollingController.value.abort()
        }
      }
    }, 1000)

    const response = await fetch(`${API_URL}/auth/device/poll`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({
        device_code: deviceCodeValue,
        expires_in: expiresIn || 900,
        agent_name: agentName.value,
        agent_description: agentDescription.value
      }),
      signal: pollingController.value.signal
    })

    clearInterval(countdownInterval)
    pollingController.value = null
    pollingStarted.value = false
    isAuthenticating.value = false

    if (response.ok) {
      const data = await response.json()
      isAuthenticated.value = true
      // Reload agents list
      await loadAgents()
    } else {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      alert(`Authorization failed: ${errorData.detail}`)
    }

  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('Authentication cancelled or timed out')
    } else {
      console.error('Polling error:', error)
      alert('Polling error: ' + error.message)
    }
    pollingController.value = null
    pollingStarted.value = false
    isAuthenticating.value = false
  }
}

const copyCode = async () => {
  try {
    await navigator.clipboard.writeText(deviceCode.value.user_code)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (error) {
    console.error('Copy failed:', error)
    const textArea = document.createElement('textarea')
    textArea.value = deviceCode.value.user_code
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  }
}

const cancelAuth = () => {
  if (pollingController.value) {
    pollingController.value.abort()
    pollingController.value = null
  }
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
  // Keep modal open for creating another agent
}
</script>

<style scoped>
.settings-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.settings-modal-content {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 800px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
}

/* Modal Header */
.settings-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #e9ecef;
  background: #f8f9fa;
}

.settings-modal-header h2 {
  margin: 0;
  color: #1a1a1a;
  font-size: 1.5rem;
}

.close-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  color: #6c757d;
  transition: all 0.2s;
}

.close-button:hover {
  background: #e9ecef;
  color: #495057;
}

/* Tab Navigation */
.tab-navigation {
  display: flex;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.tab-button {
  flex: 1;
  padding: 1rem 1.5rem;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  color: #6c757d;
  transition: all 0.2s;
  border-bottom: 3px solid transparent;
}

.tab-button:hover {
  background: #e9ecef;
  color: #495057;
}

.tab-button.active {
  color: #007bff;
  border-bottom-color: #007bff;
  background: white;
}

/* Tab Content */
.tab-content {
  padding: 1.5rem 2rem;
  overflow-y: auto;
  flex: 1;
}

.tab-panel {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Profile Tab */
.profile-section h3 {
  margin: 0 0 1rem;
  color: #1a1a1a;
  font-size: 1.25rem;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.user-avatar img {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: 2px solid #007bff;
}

.user-details h4 {
  margin: 0 0 0.25rem;
  color: #1a1a1a;
  font-size: 1.1rem;
}

.user-email, .user-id {
  margin: 0.125rem 0;
  color: #6c757d;
  font-size: 0.85rem;
}

/* Agents Tab */
.agents-section h3 {
  margin: 0 0 1rem;
  color: #1a1a1a;
  font-size: 1.25rem;
}

.agents-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.create-agent-button {
  background: #28a745;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: background-color 0.2s;
}

.create-agent-button:hover {
  background: #218838;
}

.agents-list {
  display: grid;
  gap: 0.75rem;
}

.agent-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  transition: all 0.2s;
}

.agent-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.agent-info {
  flex: 1;
}

.agent-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.25rem;
}

.agent-header h4 {
  margin: 0;
  color: #1a1a1a;
  font-size: 1rem;
}

.agent-status {
  padding: 0.2rem 0.5rem;
  background: #28a745;
  color: white;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 500;
}

.agent-description {
  margin: 0.25rem 0;
  color: #6c757d;
  font-size: 0.8rem;
}

.agent-meta {
  display: flex;
  gap: 0.75rem;
  font-size: 0.75rem;
  color: #6c757d;
}

.agent-actions {
  display: flex;
  gap: 0.25rem;
}

.edit-button, .delete-button {
  background: none;
  border: none;
  padding: 0.375rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.2s;
}

.edit-button:hover {
  background: #007bff;
}

.delete-button:hover {
  background: #dc3545;
}

.edit-button:hover, .delete-button:hover {
  color: white;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 2rem 1rem;
  color: #6c757d;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 0.75rem;
}

.empty-state h4 {
  margin: 0 0 0.25rem;
  color: #495057;
}

.empty-state p {
  margin: 0 0 1.5rem;
  font-size: 0.85rem;
}

.create-first-agent-button {
  background: #007bff;
  color: white;
  border: none;
  padding: 0.5rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: background-color 0.2s;
}

.create-first-agent-button:hover {
  background: #0056b3;
}

/* Preferences Tab */
.preferences-section h3 {
  margin: 0 0 1rem;
  color: #1a1a1a;
  font-size: 1.25rem;
}

.preference-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.75rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
}

.preference-item label {
  min-width: 80px;
  font-weight: 500;
  color: #495057;
  font-size: 0.9rem;
}

.preference-item select {
  flex: 1;
  padding: 0.375rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.85rem;
}

/* Loading */
.loading {
  text-align: center;
  padding: 1.5rem;
  color: #6c757d;
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 0.75rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.spinner.small {
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0;
}

/* Delete Modal */
.delete-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
}

.delete-modal-content {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  max-width: 350px;
  width: 90%;
  text-align: center;
}

.delete-modal-content h4 {
  margin: 0 0 0.75rem;
  color: #1a1a1a;
}

.delete-modal-content p {
  margin: 0.375rem 0;
  color: #6c757d;
  font-size: 0.9rem;
}

.warning-text {
  color: #dc3545 !important;
  font-weight: 500;
}

.delete-modal-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
  margin-top: 1.25rem;
}

.cancel-button {
  background: #6c757d;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
}

.delete-confirm-button {
  background: #dc3545;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
}

.cancel-button:hover {
  background: #5a6268;
}

.delete-confirm-button:hover {
  background: #c82333;
}

/* Agent Creation Modal */
.agent-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1200;
}

.agent-modal-content {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
}

.agent-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #e9ecef;
  background: #f8f9fa;
}

.agent-modal-header h3 {
  margin: 0;
  color: #1a1a1a;
  font-size: 1.25rem;
}

.agent-modal-body {
  padding: 1.5rem 2rem;
  overflow-y: auto;
  flex: 1;
}

/* Agent Auth Tab */
.agent-auth-section h3 {
  margin: 0 0 1rem;
  color: #1a1a1a;
  font-size: 1.25rem;
}

.agent-info-section {
  margin-bottom: 2rem;
}

.agent-details .agent-form {
  background: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.agent-details .form-group {
  margin-bottom: 1rem;
}

.agent-details .form-group:last-child {
  margin-bottom: 0;
}

.agent-details .form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #333;
  font-size: 0.9rem;
}

.agent-details .form-group input,
.agent-details .form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.agent-details .form-group input:focus,
.agent-details .form-group textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.agent-details .form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.agent-details .create-agent-button {
  padding: 0.75rem 2rem;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: background-color 0.2s;
  width: 100%;
}

.agent-details .create-agent-button:hover:not(:disabled) {
  background: #218838;
}

.agent-details .create-agent-button:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.action-buttons {
  display: flex;
  justify-content: center;
  margin-top: 1rem;
}

.device-auth-section {
  width: 100%;
}

.device-code-section h4 {
  margin: 0 0 0.5rem;
  color: #1a1a1a;
  font-size: 1.1rem;
}

.device-code-section .instruction-text {
  text-align: center;
  color: #666;
  margin: 0 0 1rem;
  font-size: 0.9rem;
  line-height: 1.4;
}

.code-display {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: #f8f9fa;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  padding: 1rem;
  margin: 1rem 0;
  width: 100%;
  max-width: 300px;
  margin-left: auto;
  margin-right: auto;
}

.code-display code {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 1.2rem;
  font-weight: bold;
  color: #24292e;
  letter-spacing: 0.1em;
  flex: 1;
  text-align: center;
}

.code-display .copy-button {
  padding: 0.5rem 1rem;
  background: #24292e;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: background-color 0.2s;
}

.code-display .copy-button:hover:not(:disabled) {
  background: #1a1f26;
}

.code-display .copy-button:disabled {
  background: #28a745;
  cursor: default;
}

.link-section {
  text-align: center;
  margin: 1rem 0;
}

.link-section p {
  margin: 0 0 0.5rem;
  color: #666;
  font-size: 0.85rem;
}

.github-link {
  display: inline-block;
  color: #0366d6;
  text-decoration: none;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border: 1px solid #0366d6;
  border-radius: 6px;
  transition: all 0.2s;
}

.github-link:hover {
  background: #0366d6;
  color: white;
}

.polling-status {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: #666;
  font-size: 0.85rem;
  margin: 1rem 0;
  justify-content: center;
}

.device-code-section .action-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
  justify-content: center;
}

.device-code-section .cancel-button {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.2s;
  background: #dc3545;
  color: white;
}

.device-code-section .cancel-button:hover {
  background: #c82333;
}

.success-section {
  color: #28a745;
  text-align: center;
}

.success-section .success-icon {
  font-size: 3rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.success-section p {
  margin: 0 0 0.5rem;
  font-weight: 500;
}

.success-section .agent-info {
  color: #666;
  font-size: 0.85rem;
  margin-bottom: 1rem;
}

.success-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 1.5rem;
  flex-wrap: wrap;
}

.create-another-button {
  padding: 0.75rem 1.5rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: background-color 0.2s;
}

.create-another-button:hover {
  background: #5a67d8;
}

.success-section .back-home-button {
  padding: 0.75rem 1.5rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: background-color 0.2s;
}

.success-section .back-home-button:hover {
  background: #0056b3;
}

/* Responsive */
@media (max-width: 768px) {

  .settings-modal-header {
    padding: 1rem 1.5rem;
  }

  .settings-modal-header h2 {
    font-size: 1.25rem;
  }

  .tab-content {
    padding: 1rem 1.5rem;
  }

  .agents-header {
    flex-direction: column;
    gap: 0.75rem;
    align-items: stretch;
  }

  .agent-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }

  .agent-actions {
    align-self: flex-end;
  }

  .user-info {
    flex-direction: column;
    text-align: center;
    gap: 0.75rem;
  }

  .preference-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.375rem;
  }

  .delete-modal-actions {
    flex-direction: column;
  }

  /* Agent Modal Responsive */
  .agent-modal-content {
    max-width: 95vw;
    max-height: 95vh;
  }

  .agent-modal-header {
    padding: 1rem 1.5rem;
  }

  .agent-modal-header h3 {
    font-size: 1.1rem;
  }

  .agent-modal-body {
    padding: 1rem 1.5rem;
  }

  /* Agent Auth Responsive */
  .agent-details .agent-form {
    padding: 1rem;
  }

  .code-display {
    max-width: 100%;
    flex-direction: column;
    gap: 0.5rem;
  }

  .code-display code {
    font-size: 1rem;
  }

  .device-code-section .action-buttons {
    flex-direction: column;
  }

  .success-actions {
    flex-direction: column;
  }
}
</style>