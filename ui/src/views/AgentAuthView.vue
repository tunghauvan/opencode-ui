<template>
  <div class="agent-auth-container">
    <div class="agent-auth-card">
      <h1>Agent Authentication</h1>
      <p class="subtitle">Authenticate AI Agent with GitHub</p>

      <!-- Agent Info Section -->
      <div class="agent-info-section">
        <div class="agent-details">
          <h3>Create New Agent</h3>
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
          <h3>Device Authentication</h3>
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
            <button @click="backToHome" class="back-home-button">
              Back to Home Page
            </button>
          </div>
        </div>
      </div>

      <!-- Debug info (remove in production) -->
      <div class="debug-info" v-if="debugInfo">
        <details>
          <summary>Debug Information</summary>
          <pre>{{ debugInfo }}</pre>
        </details>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

// Agent details
const agentName = ref('')
const agentDescription = ref('')

// Device code authentication state
const deviceCode = ref(null)
const isAuthenticated = ref(false)
const isAuthenticating = ref(false)
const pollingController = ref(null) // AbortController for polling request
const pollingTimeLeft = ref(0)
const copied = ref(false)
const pollingStarted = ref(false)

// Debug info
const debugInfo = ref('')

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

onMounted(async () => {
  // Check URL parameters for success callback
  const urlParams = new URLSearchParams(window.location.search)
  if (urlParams.get('success') === 'true') {
    const agentId = urlParams.get('agent_id')
    const agentNameParam = urlParams.get('agent_name')
    if (agentNameParam) {
      isAuthenticated.value = true
      agentName.value = agentNameParam
      debugInfo.value = `Agent "${agentNameParam}" created successfully!`
      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname)
    }
  }
})

onUnmounted(() => {
  // Cancel any ongoing polling request
  if (pollingController.value) {
    pollingController.value.abort()
  }
})

const createAgent = async () => {
  if (!agentName.value.trim()) {
    alert('Please enter an agent name')
    return
  }

  isAuthenticating.value = true

  try {
    // Get device code from backend
    const response = await fetch(`${API_URL}/auth/device`, {
      credentials: 'include'
    })

    if (!response.ok) {
      throw new Error(`Failed to get device code: ${response.statusText}`)
    }

    const data = await response.json()
    deviceCode.value = data

    debugInfo.value = 'Device code ready. Copy the code and authorize on GitHub.'

    // Start polling immediately
    startPolling(deviceCode.value.device_code, deviceCode.value.interval || 5, deviceCode.value.expires_in || 900)

  } catch (error) {
    console.error('Create agent error:', error)
    debugInfo.value = `Create agent error: ${error.message}`
    isAuthenticating.value = false
  }
}

const startPolling = async (deviceCodeValue, interval, expiresIn) => {
  try {
    // Create abort controller for this request
    pollingController.value = new AbortController()

    // Show polling status
    pollingStarted.value = true
    pollingTimeLeft.value = expiresIn || 900 // Default to 15 minutes

    // Start countdown timer
    const countdownInterval = setInterval(() => {
      pollingTimeLeft.value = Math.max(0, pollingTimeLeft.value - 1)
      if (pollingTimeLeft.value <= 0) {
        clearInterval(countdownInterval)
        // Auto-cancel if timeout
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

    // Clear countdown
    clearInterval(countdownInterval)
    pollingController.value = null
    pollingStarted.value = false
    isAuthenticating.value = false

    if (response.ok) {
      const data = await response.json()

      // Show success
      isAuthenticated.value = true
      debugInfo.value = `Agent "${agentName.value}" created successfully!`

    } else {
      // Handle error
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      debugInfo.value = `Authorization failed: ${errorData.detail}`
    }

  } catch (error) {
    if (error.name === 'AbortError') {
      debugInfo.value = 'Authentication cancelled or timed out'
    } else {
      console.error('Polling error:', error)
      debugInfo.value = `Polling error: ${error.message}`
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
    // Fallback for older browsers
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
  debugInfo.value = 'Authentication cancelled'
}

const createAnotherAgent = () => {
  // Reset form
  agentName.value = ''
  agentDescription.value = ''
  deviceCode.value = null
  isAuthenticated.value = false
  isAuthenticating.value = false
  pollingStarted.value = false
  debugInfo.value = ''
}

const backToHome = () => {
  router.push('/')
}

const startRedirectAuth = async () => {
  // This function is no longer used - removed redirect flow
}
</script>

<style scoped>
.agent-auth-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 1rem;
}

.agent-auth-card {
  background: white;
  border-radius: 12px;
  padding: 3rem 2rem;
  max-width: 500px;
  width: 100%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  text-align: center;
}

h1 {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 0.5rem;
  color: #1a1a1a;
}

.subtitle {
  color: #666;
  margin: 0 0 2rem;
  font-size: 0.95rem;
}

.agent-info-section {
  margin-bottom: 2rem;
  text-align: left;
}

.agent-details h3 {
  margin: 0 0 1rem;
  color: #1a1a1a;
  font-size: 1.25rem;
}

.agent-form {
  background: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #333;
  font-size: 0.9rem;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.create-agent-button {
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

.create-agent-button:hover:not(:disabled) {
  background: #218838;
}

.create-agent-button:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.device-auth-section {
  width: 100%;
}

.loading-section, .device-code-section, .success-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner.small {
  width: 24px;
  height: 24px;
  border-width: 3px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.device-code-section h3 {
  margin: 0 0 0.5rem;
  color: #1a1a1a;
  font-size: 1.25rem;
}

.instruction-text {
  text-align: center;
  color: #666;
  margin: 0 0 1rem;
  font-size: 0.95rem;
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
}

.code-display code {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 1.5rem;
  font-weight: bold;
  color: #24292e;
  letter-spacing: 0.1em;
  flex: 1;
  text-align: center;
}

.copy-button {
  padding: 0.5rem 1rem;
  background: #24292e;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: background-color 0.2s;
}

.copy-button:hover:not(:disabled) {
  background: #1a1f26;
}

.copy-button:disabled {
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
  font-size: 0.9rem;
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
  font-size: 0.9rem;
  margin: 1rem 0;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
  width: 100%;
  justify-content: center;
}

.cancel-button, .start-auth-button {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s;
}

.cancel-button {
  background: #dc3545;
  color: white;
}

.cancel-button:hover {
  background: #c82333;
}

.start-auth-button {
  background: #28a745;
  color: white;
}

.start-auth-button:hover:not(:disabled) {
  background: #218838;
}

.start-auth-button:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.success-section {
  color: #28a745;
  text-align: center;
}

.success-icon {
  font-size: 3rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.success-section p {
  margin: 0 0 0.5rem;
  font-weight: 500;
}

.agent-info {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.create-another-button {
  padding: 0.75rem 1.5rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: background-color 0.2s;
  margin-top: 1rem;
}

.success-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 1.5rem;
  flex-wrap: wrap;
}

.back-home-button {
  padding: 0.75rem 1.5rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: background-color 0.2s;
}

.back-home-button:hover {
  background: #0056b3;
}

.debug-info {
  margin-top: 2rem;
  background: #f5f5f5;
  padding: 1rem;
  border-radius: 8px;
  max-width: 600px;
  width: 100%;
  text-align: left;
}

.debug-info summary {
  cursor: pointer;
  color: #666;
  font-weight: 500;
  user-select: none;
}

.debug-info pre {
  margin-top: 0.5rem;
  overflow-x: auto;
  font-size: 0.85rem;
  background: white;
  padding: 0.75rem;
  border-radius: 4px;
}

@media (max-width: 480px) {
  .agent-auth-card {
    padding: 2rem 1.5rem;
  }

  h1 {
    font-size: 1.75rem;
  }

  .agent-form {
    padding: 1rem;
  }

  .action-buttons {
    flex-direction: column;
  }

  .cancel-button, .start-auth-button {
    width: 100%;
  }
}
</style>