<template>
  <div class="login-container">
    <div class="login-card">
      <h1>OpenCode UI</h1>
      <p class="subtitle">Login with GitHub to get started</p>
      
      <!-- Device Code Flow -->
      <div v-if="authMode === 'device'" class="device-auth-section">
        <div v-if="!deviceCode" class="loading-section">
          <div class="spinner"></div>
          <p>Preparing device authentication...</p>
        </div>
        
        <div v-else-if="!isAuthenticated" class="device-code-section">
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
          
          <button @click="cancelAuth" class="cancel-button">
            Cancel
          </button>
        </div>
        
        <div v-else class="success-section">
          <div class="success-icon">✓</div>
          <p>Authentication successful! Redirecting...</p>
        </div>
      </div>
      
      <!-- Fallback to traditional OAuth -->
      <div v-else>
        <button 
          @click="loginWithGithub" 
          :disabled="isLoading"
          class="github-login-button"
        >
          <svg class="github-icon" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v 3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
          </svg>
          <span v-if="!isLoading">Sign in with GitHub</span>
          <span v-else>Redirecting...</span>
        </button>
      </div>

      <p class="terms-text">
        By signing in, you agree to our Terms of Service and Privacy Policy
      </p>
    </div>

    <!-- Debug info (remove in production) -->
    <div class="debug-info" v-if="debugInfo">
      <details>
        <summary>Debug Information</summary>
        <pre>{{ debugInfo }}</pre>
      </details>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'

const router = useRouter()
const chatStore = useChatStore()

// Device code authentication state
const authMode = ref('device') // 'device' or 'redirect'
const deviceCode = ref(null)
const isAuthenticated = ref(false)
const pollingController = ref(null) // AbortController for polling request
const pollingTimeLeft = ref(0)
const copied = ref(false)
const pollingStarted = ref(false)

// Legacy redirect flow state
const isLoading = ref(false)
const debugInfo = ref('')

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

onMounted(async () => {
  // Check if user is already logged in
  const token = localStorage.getItem('access_token')
  const userId = localStorage.getItem('user_id')
  
  if (token && userId) {
    router.push('/chat')
    return
  }

  // Check if returning from OAuth callback (legacy support)
  const params = new URLSearchParams(window.location.search)
  const callbackToken = params.get('token')
  const callbackRefreshToken = params.get('refresh_token')
  const callbackUserId = params.get('user_id')
  const error = params.get('error')

  if (error) {
    debugInfo.value = `Login error: ${error}`
    return
  }

  if (callbackToken && callbackUserId) {
    // Store tokens from callback
    localStorage.setItem('access_token', callbackToken)
    localStorage.setItem('user_id', callbackUserId)
    if (callbackRefreshToken) {
      localStorage.setItem('refresh_token', callbackRefreshToken)
    }

    // Clean up URL
    window.history.replaceState({}, document.title, '/login')

    // Redirect to chat
    router.push('/chat')
    return
  }

  // Start device code authentication
  if (authMode.value === 'device') {
    await startDeviceAuth()
  }
})

onUnmounted(() => {
  // Cancel any ongoing polling request
  if (pollingController.value) {
    pollingController.value.abort()
  }
})

const startDeviceAuth = async () => {
  try {
    const response = await fetch(`${API_URL}/auth/device`)
    if (!response.ok) {
      throw new Error(`Failed to get device code: ${response.statusText}`)
    }

    const data = await response.json()
    deviceCode.value = data
    
    // Wait 5 seconds for user to copy the code, then start polling automatically
    debugInfo.value = 'Device code ready. Copy the code and authorize on GitHub. Polling will start in 5 seconds...'
    setTimeout(() => {
      if (!pollingStarted.value && deviceCode.value) {
        pollingStarted.value = true
        startPolling(data.device_code, data.interval || 5, data.expires_in || 900)
      }
    }, 5000)
  } catch (error) {
    console.error('Device auth error:', error)
    debugInfo.value = `Device auth error: ${error.message}`
    // Fallback to redirect flow
    authMode.value = 'redirect'
  }
}

const startPolling = async (deviceCodeValue, interval, expiresIn) => {
  try {
    // Create abort controller for this request
    pollingController.value = new AbortController()
    
    // Show polling status - use actual expires_in value
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
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        device_code: deviceCodeValue,
        expires_in: expiresIn || 900
      }),
      signal: pollingController.value.signal
    })
    
    // Clear countdown
    clearInterval(countdownInterval)
    pollingController.value = null
    pollingStarted.value = false
    
    if (response.ok) {
      const data = await response.json()
      
      // Store user ID only (token is stored in database on backend)
      localStorage.setItem('user_id', data.user.id)
      
      // Show success and redirect
      isAuthenticated.value = true
      setTimeout(() => {
        router.push('/chat')
      }, 1500)
      
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
  debugInfo.value = 'Authentication cancelled'
}
const loginWithGithub = async () => {
  try {
    isLoading.value = true

    const response = await fetch(`${API_URL}/auth/login`)
    if (!response.ok) {
      throw new Error(`Failed to get login URL: ${response.statusText}`)
    }

    const data = await response.json()
    
    // Store state for validation (optional, for production)
    sessionStorage.setItem('oauth_state', data.state)

    // Redirect to GitHub
    window.location.href = data.authorization_url
  } catch (error) {
    console.error('Login error:', error)
    debugInfo.value = error.message
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 1rem;
}

.login-card {
  background: white;
  border-radius: 12px;
  padding: 3rem 2rem;
  max-width: 400px;
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

.github-login-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.875rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: white;
  background: #24292e;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 1.5rem;
}

.github-login-button:hover:not(:disabled) {
  background: #1a1f26;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(36, 41, 46, 0.3);
}

.github-login-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.github-icon {
  width: 20px;
  height: 20px;
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

.cancel-button {
  padding: 0.5rem 1.5rem;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: background-color 0.2s;
  margin-top: 0.5rem;
}

.cancel-button:hover {
  background: #c82333;
}

.success-section {
  color: #28a745;
}

.success-icon {
  font-size: 3rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.success-section p {
  margin: 0;
  font-weight: 500;
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
  .login-card {
    padding: 2rem 1.5rem;
  }

  h1 {
    font-size: 1.75rem;
  }

  .github-login-button {
    font-size: 0.95rem;
    padding: 0.75rem 1rem;
  }
}
</style>
