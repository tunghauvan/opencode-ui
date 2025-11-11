<template>
  <div class="login-container">
    <div class="login-card">
      <h1>OpenCode UI</h1>
      <p class="subtitle">Login with GitHub to get started</p>
      
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Main login state
const isLoading = ref(false)
const debugInfo = ref('')

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

onMounted(async () => {
  // Check if user is already logged in by making an API call
  try {
    const response = await fetch(`${API_URL}/auth/me`, {
      credentials: 'include'
    })
    if (response.ok) {
      router.push('/')
      return
    }
  } catch (error) {
    // Not logged in, continue
  }

  // Check if returning from OAuth callback
  const params = new URLSearchParams(window.location.search)
  const error = params.get('error')

  if (error) {
    debugInfo.value = `Login error: ${error}`
    return
  }

  // If we have any callback params, assume login was successful and cookies are set
  const callbackToken = params.get('token')
  if (callbackToken) {
    // Clean up URL
    window.history.replaceState({}, document.title, '/login')

    // Redirect to chat
    router.push('/')
    return
  }
})

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

.terms-text {
  color: #666;
  font-size: 0.85rem;
  margin: 0;
  line-height: 1.4;
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
