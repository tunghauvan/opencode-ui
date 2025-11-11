<template>
  <div class="settings-container">
    <div class="settings-header">
      <h1>Settings</h1>
      <button @click="backToHome" class="back-button">
        ← Back to Home
      </button>
    </div>

    <div class="settings-content">
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
            <h2>User Profile</h2>
            <div v-if="user" class="user-info">
              <div class="user-avatar">
                <img :src="user.avatar_url" :alt="user.login" />
              </div>
              <div class="user-details">
                <h3>{{ user.login }}</h3>
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
              <h2>AI Agents</h2>
              <button @click="goToAgentAuth" class="create-agent-button">
                + Create New Agent
              </button>
            </div>

            <div v-if="loadingAgents" class="loading">
              <div class="spinner"></div>
              <p>Loading agents...</p>
            </div>

            <div v-else-if="agents.length === 0" class="empty-state">
              <div class="empty-icon">🤖</div>
              <h3>No agents yet</h3>
              <p>Create your first AI agent to get started</p>
              <button @click="goToAgentAuth" class="create-first-agent-button">
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
            <h2>Preferences</h2>
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
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="modal-overlay" @click="cancelDelete">
      <div class="modal-content" @click.stop>
        <h3>Delete Agent</h3>
        <p>Are you sure you want to delete agent "{{ agentToDelete?.name }}"?</p>
        <p class="warning-text">This action cannot be undone.</p>
        <div class="modal-actions">
          <button @click="cancelDelete" class="cancel-button">Cancel</button>
          <button @click="confirmDelete" class="delete-confirm-button">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

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

const router = useRouter()
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

onMounted(async () => {
  // Load user info and agents (authentication is handled by router guard)
  await loadUserInfo()
  await loadAgents()
  loadPreferences()
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

const goToAgentAuth = () => {
  router.push('/agent-auth')
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

const backToHome = () => {
  router.push('/')
}

const formatDate = (dateString) => {
  if (!dateString) return 'Never'
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.settings-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem;
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  max-width: 1200px;
  margin-left: auto;
  margin-right: auto;
}

.settings-header h1 {
  color: white;
  font-size: 2.5rem;
  margin: 0;
}

.back-button {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s;
}

.back-button:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.settings-content {
  max-width: 1200px;
  margin: 0 auto;
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

/* Tab Navigation */
.tab-navigation {
  display: flex;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.tab-button {
  flex: 1;
  padding: 1rem 2rem;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
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
  padding: 2rem;
}

.tab-panel {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Profile Tab */
.profile-section h2 {
  margin: 0 0 1.5rem;
  color: #1a1a1a;
  font-size: 1.5rem;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.user-avatar img {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 3px solid #007bff;
}

.user-details h3 {
  margin: 0 0 0.5rem;
  color: #1a1a1a;
  font-size: 1.25rem;
}

.user-email, .user-id {
  margin: 0.25rem 0;
  color: #6c757d;
  font-size: 0.9rem;
}

/* Agents Tab */
.agents-section h2 {
  margin: 0 0 1.5rem;
  color: #1a1a1a;
  font-size: 1.5rem;
}

.agents-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.create-agent-button {
  background: #28a745;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: background-color 0.2s;
}

.create-agent-button:hover {
  background: #218838;
}

.agents-list {
  display: grid;
  gap: 1rem;
}

.agent-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  transition: all 0.2s;
}

.agent-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.agent-info {
  flex: 1;
}

.agent-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.agent-header h4 {
  margin: 0;
  color: #1a1a1a;
  font-size: 1.1rem;
}

.agent-status {
  padding: 0.25rem 0.75rem;
  background: #28a745;
  color: white;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.agent-description {
  margin: 0.5rem 0;
  color: #6c757d;
  font-size: 0.9rem;
}

.agent-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
  color: #6c757d;
}

.agent-actions {
  display: flex;
  gap: 0.5rem;
}

.edit-button, .delete-button {
  background: none;
  border: none;
  padding: 0.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
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
  padding: 3rem 2rem;
  color: #6c757d;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state h3 {
  margin: 0 0 0.5rem;
  color: #495057;
}

.empty-state p {
  margin: 0 0 2rem;
  font-size: 0.9rem;
}

.create-first-agent-button {
  background: #007bff;
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: background-color 0.2s;
}

.create-first-agent-button:hover {
  background: #0056b3;
}

/* Preferences Tab */
.preferences-section h2 {
  margin: 0 0 1.5rem;
  color: #1a1a1a;
  font-size: 1.5rem;
}

.preference-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 6px;
}

.preference-item label {
  min-width: 100px;
  font-weight: 500;
  color: #495057;
}

.preference-item select {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.9rem;
}

/* Loading */
.loading {
  text-align: center;
  padding: 2rem;
  color: #6c757d;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Modal */
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

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  max-width: 400px;
  width: 90%;
  text-align: center;
}

.modal-content h3 {
  margin: 0 0 1rem;
  color: #1a1a1a;
}

.modal-content p {
  margin: 0.5rem 0;
  color: #6c757d;
}

.warning-text {
  color: #dc3545 !important;
  font-weight: 500;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 1.5rem;
}

.cancel-button {
  background: #6c757d;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}

.delete-confirm-button {
  background: #dc3545;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}

.cancel-button:hover {
  background: #5a6268;
}

.delete-confirm-button:hover {
  background: #c82333;
}

/* Responsive */
@media (max-width: 768px) {
  .settings-container {
    padding: 1rem;
  }

  .settings-header {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }

  .settings-header h1 {
    font-size: 2rem;
  }

  .tab-navigation {
    flex-direction: column;
  }

  .tab-button {
    padding: 0.75rem 1rem;
  }

  .tab-content {
    padding: 1rem;
  }

  .agents-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .agent-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .agent-actions {
    align-self: flex-end;
  }

  .user-info {
    flex-direction: column;
    text-align: center;
    gap: 1rem;
  }

  .preference-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .modal-actions {
    flex-direction: column;
  }
}
</style>