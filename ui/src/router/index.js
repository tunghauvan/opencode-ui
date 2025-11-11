import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import ChatView from '../views/ChatView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/',
      name: 'chat',
      component: ChatView,
      meta: { requiresAuth: true }
    }
  ]
})

// Authentication guard
router.beforeEach(async (to, from, next) => {
  if (to.meta.requiresAuth) {
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await fetch(`${API_URL}/auth/me`, {
        credentials: 'include'
      })
      
      if (response.ok) {
        next()
      } else {
        next('/login')
      }
    } catch (error) {
      next('/login')
    }
  } else {
    next()
  }
})

export default router
