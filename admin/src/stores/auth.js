import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('admin_token') || '')
  const email = ref(localStorage.getItem('admin_email') || '')

  const isLoggedIn = computed(() => !!token.value)

  async function login(emailInput, password) {
    const response = await api.post('/admin/login', {
      email: emailInput,
      password
    })
    
    token.value = response.data.token
    email.value = response.data.email
    
    localStorage.setItem('admin_token', token.value)
    localStorage.setItem('admin_email', email.value)
    
    return response.data
  }

  function logout() {
    token.value = ''
    email.value = ''
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_email')
  }

  return {
    token,
    email,
    isLoggedIn,
    login,
    logout
  }
})
