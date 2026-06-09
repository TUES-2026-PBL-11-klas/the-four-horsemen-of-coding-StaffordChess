import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { apiFetch } from '../api/http'

export const useAuthStore = defineStore('auth', () => 
{
  const token = ref(localStorage.getItem('token') || null)
  const user = ref(null)

  const isLoggedIn = computed(() => !!token.value)

  function setToken(t) 
  {
    token.value = t
    if(t) 
      localStorage.setItem('token', t)
    else 
      localStorage.removeItem('token')
  }

  async function bootstrap() 
  {
    if(!token.value) return
    try 
    {
      user.value = await apiFetch('/auth/me', { auth: true })
    } 
    catch 
    {
      logout()
    }
  }

  async function fetchUser() 
  {
    if(!token.value) return null
    try 
    {
      user.value = await apiFetch('/auth/me', { auth: true })
      return user.value
    } 
    catch 
    {
      logout()
      return null
    }
  }

  async function login(email, password) 
  {
    const data = await apiFetch('/auth/login', 
    {
      method: 'POST',
      body: { email, password },
    })
    setToken(data.access_token)
    user.value = { username: data.username }
    fetchUser()
  }

  async function register({ username, email, password }) {
    return apiFetch('/auth/register', {
      method: 'POST',
      body: { username, email, password },
    })
  }

  async function verifyEmail(email, token) 
  {
    return apiFetch('/auth/verify-email', 
    {
      method: 'POST',
      body: { email, token },
    })
  }

  async function resendVerification(email) 
  {
    return apiFetch('/auth/resend-verification',
    {
      method: 'POST',
      body: { email },
    })
  }

  function logout() {
    setToken(null)
    user.value = null
  }

  return {
    token, user, isLoggedIn,
    bootstrap, fetchUser, login, register, verifyEmail, resendVerification, logout,
  }
})