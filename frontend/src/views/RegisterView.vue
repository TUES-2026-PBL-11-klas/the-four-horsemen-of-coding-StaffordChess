<template>
  <div class="register-page">

    <!-- Top navbar -->
    <header class="topbar">
      <div class="topbar-logo">
        <span class="logo-icon">♟</span>
        <span class="logo-text">StaffordChess</span>
      </div>
    </header>

    <!-- Main content -->
    <main class="main">
      <h1 class="title">Create Your StaffordChess<br>Account</h1>

      <div class="card">
        <!-- Pawn icon -->
        <div class="pawn-wrap">
          <span class="pawn-icon">♟</span>
          <div class="pawn-shadow"></div>
        </div>

        <!-- Form -->
        <form class="form" @submit.prevent="handleRegister">
          <div class="field">
            <input
              v-model="form.username"
              type="text"
              placeholder="Username"
              class="input"
              :class="{ error: errors.username }"
              autocomplete="username"
            />
            <span v-if="errors.username" class="error-msg">{{ errors.username }}</span>
          </div>

          <div class="field">
            <input
              v-model="form.email"
              type="email"
              placeholder="Email"
              class="input"
              :class="{ error: errors.email }"
              autocomplete="email"
            />
            <span v-if="errors.email" class="error-msg">{{ errors.email }}</span>
          </div>

          <div class="field">
            <input
              v-model="form.password"
              type="password"
              placeholder="Password"
              class="input"
              :class="{ error: errors.password }"
              autocomplete="new-password"
            />
            <span v-if="errors.password" class="error-msg">{{ errors.password }}</span>
          </div>

          <span v-if="errors.general" class="error-msg general">{{ errors.general }}</span>

          <button type="submit" class="btn-submit" :disabled="loading">
            <span v-if="loading" class="spinner"></span>
            <span v-else>Create Account</span>
          </button>
        </form>

        <div class="divider"><span>OR</span></div>

        <p class="login-link">
          Already have an account?
          <router-link to="/login">Log In</router-link>
        </p>
      </div>
    </main>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ApiError } from '../api/http'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({ username: '', email: '', password: '' })
const errors = ref({})
const loading = ref(false)

function validate() {
  errors.value = {}
  if (!form.value.username) errors.value.username = 'Username is required'
  if (!form.value.email) errors.value.email = 'Email is required'
  if (!form.value.password || form.value.password.length < 6)
    errors.value.password = 'Password must be at least 6 characters'
  return Object.keys(errors.value).length === 0
}

async function handleRegister() {
  if (!validate()) return
  loading.value = true
  errors.value = {}

  try {
    await authStore.register(form.value)
    // Remember which email we're verifying so a page refresh on /verify-email
    // doesn't lose context.
    localStorage.setItem('pending_email', form.value.email)
    router.push({ name: 'verify-email', query: { email: form.value.email } })
  } catch (err) {
    if (err instanceof ApiError) {
      // 409 = duplicate username/email, 400 = invalid email, etc.
      // Trust the backend's detail message — auth_service.py crafts these
      // specifically and they're user-facing already.
      errors.value.general = err.message
    } else {
      errors.value.general = 'Something went wrong. Please try again.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@400;500&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

.register-page {
  min-height: 100vh;
  background: #1a1a1a;
  font-family: 'DM Sans', sans-serif;
  color: #e8e4d8;
  display: flex;
  flex-direction: column;
}

/* TOPBAR */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 32px;
}

.topbar-logo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-icon { font-size: 22px; color: #7cb662; }
.logo-text {
  font-family: 'Playfair Display', serif;
  font-size: 16px;
  font-weight: 700;
  color: #7cb662;
}

/* MAIN */
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px 16px 48px;
}

.title {
  font-family: 'Playfair Display', serif;
  font-size: 28px;
  font-weight: 700;
  text-align: center;
  line-height: 1.3;
  margin-bottom: 28px;
  color: #f0ebe0;
}

/* CARD */
.card {
  background: #252525;
  border-radius: 12px;
  padding: 32px 28px;
  width: 100%;
  max-width: 420px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

/* PAWN */
.pawn-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 4px;
}

.pawn-icon {
  font-size: 56px;
  color: #7cb662;
  filter: drop-shadow(0 0 12px rgba(124,182,98,0.4));
  line-height: 1;
}

.pawn-shadow {
  width: 60px;
  height: 10px;
  background: radial-gradient(ellipse, rgba(0,0,0,0.5) 0%, transparent 70%);
  margin-top: -4px;
}

/* FORM */
.form {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.input {
  width: 100%;
  padding: 13px 16px;
  background: #1a1a1a;
  border: 1px solid #3a3a3a;
  border-radius: 8px;
  color: #e8e4d8;
  font-size: 14px;
  font-family: 'DM Sans', sans-serif;
  outline: none;
  transition: border-color 0.15s;
}

.input::placeholder { color: #666; }
.input:focus { border-color: #5a9e42; }
.input.error { border-color: #c0392b; }

.error-msg {
  font-size: 12px;
  color: #e74c3c;
  padding-left: 4px;
}

.error-msg.general {
  text-align: center;
  padding: 8px;
  background: rgba(192,57,43,0.1);
  border-radius: 6px;
  width: 100%;
}

.btn-submit {
  width: 100%;
  padding: 14px;
  background: #5a9e42;
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  margin-top: 4px;
  transition: background 0.15s, transform 0.1s;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 48px;
}

.btn-submit:hover:not(:disabled) {
  background: #4d8c39;
  transform: translateY(-1px);
}

.btn-submit:disabled { opacity: 0.6; cursor: not-allowed; }

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* DIVIDER */
.divider {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  color: #555;
  font-size: 12px;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #333;
}

/* LOGIN LINK */
.login-link {
  font-size: 13px;
  color: #888;
}

.login-link a {
  color: #7cb662;
  text-decoration: none;
  font-weight: 500;
}
.login-link a:hover { text-decoration: underline; }
</style>