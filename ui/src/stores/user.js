import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  async function fetchUser() {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`${API_URL}/auth/me`, {
        credentials: 'include'
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch user: ${response.status}`)
      }

      const userData = await response.json()
      user.value = userData
    } catch (err) {
      error.value = err.message
      user.value = null
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      await fetch(`${API_URL}/auth/logout`, {
        credentials: 'include'
      })

      // Clear user data
      user.value = null

      // Redirect to login
      window.location.href = '/login'
    } catch (err) {
      console.error('Logout error:', err)
      // Force redirect even if logout API fails
      window.location.href = '/login'
    }
  }

  return {
    user,
    loading,
    error,
    fetchUser,
    logout
  }
})