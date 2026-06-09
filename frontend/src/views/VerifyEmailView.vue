<template>
  <div class="verify-page">
    <header class="topbar">
      <div class="topbar-logo">
        <span class="logo-icon">♟</span>
        <span class="logo-text">StaffordChess</span>
      </div>
    </header>

    <main class="main">
      <h1 class="title">Verify Your Email</h1>
      <div class="card">
        <div class="pawn-wrap">
          <span class="pawn-icon">✉</span>
          <div class="pawn-shadow"></div>
        </div>

        <p class="subtitle">
          Enter the 6-digit code sent to<br>
          <strong>{{ email || 'your email' }}</strong>
        </p>

        <div class="code-inputs">
          <input
            v-for="(_, i) in 6"
            :key="i"
            :ref="el => { if (el) inputs[i] = el }"
            v-model="digits[i]"
            type="text"
            inputmode="numeric"
            maxlength="1"
            class="code-input"
            :class="{ error: hasError }"
            @input="onInput(i)"
            @keydown.backspace="onBackspace(i, $event)"
            @paste.prevent="onPaste($event)"
          />
        </div>

        <span v-if="errorMsg" class="error-msg">{{ errorMsg }}</span>
        <span v-if="successMsg" class="success-msg">{{ successMsg }}</span>

        <button class="btn-primary" :disabled="loading || digits.join('').length < 6" @click="handleVerify">
          <span v-if="loading" class="spinner"></span>
          <span v-else>Verify Email</span>
        </button>

        <p class="resend-text">
          Didn't receive a code?
          <button class="link-btn" :disabled="resendCooldown > 0 || resendLoading" @click="handleResend">
            {{ resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend' }}
          </button>
        </p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ApiError } from '../api/http'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const email = ref(route.query.email || localStorage.getItem('pending_email') || '')
const digits = ref(Array(6).fill(''))
const inputs = ref([])
const loading = ref(false)
const resendLoading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')
const hasError = ref(false)
const resendCooldown = ref(0)
let cooldownTimer = null

function onInput(i) {
  hasError.value = false
  errorMsg.value = ''
  // Allow only digits; if the user types a letter, strip it.
  const cleaned = (digits.value[i] || '').replace(/\D/g, '').slice(0, 1)
  if (cleaned !== digits.value[i]) digits.value[i] = cleaned
  if (digits.value[i] && i < 5) inputs.value[i + 1]?.focus()
}

function onBackspace(i, e) {
  if (!digits.value[i] && i > 0) {
    e.preventDefault()
    inputs.value[i - 1]?.focus()
  }
}

function onPaste(e) {
  const text = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
  for (let i = 0; i < 6; i++) digits.value[i] = text[i] || ''
  inputs.value[Math.min(text.length, 5)]?.focus()
}

// Auto-submit as soon as 6 digits are entered (paste or type-through).
// Saves the user a click without forcing it — they can still hit the button.
watch(() => digits.value.join(''), (code) => {
  if (code.length === 6 && !loading.value) handleVerify()
})

async function handleVerify() {
  const code = digits.value.join('')
  if (code.length < 6) return
  loading.value = true
  errorMsg.value = ''
  successMsg.value = ''

  try {
    // FIX: store sends the field as `token`, which is what the backend's
    // VerifyEmail DTO expects. Previously this view sent `code`, which was
    // silently dropped — verification could never succeed.
    await authStore.verifyEmail(email.value, code)
    successMsg.value = 'Email verified! Redirecting...'
    localStorage.removeItem('pending_email')
    setTimeout(() => router.push('/login'), 1200)
  } catch (err) {
    errorMsg.value = err instanceof ApiError
      ? err.message
      : 'Network error. Please try again.'
    hasError.value = true
    digits.value = Array(6).fill('')
    inputs.value[0]?.focus()
  } finally {
    loading.value = false
  }
}

async function handleResend() {
  if (!email.value) {
    errorMsg.value = 'Missing email — please register again.'
    return
  }
  resendLoading.value = true
  errorMsg.value = ''
  successMsg.value = ''
  try {
    await authStore.resendVerification(email.value)
    successMsg.value = 'If this email exists and is unverified, a new code has been sent.'
    startCooldown(60)
  } catch (err) {
    // The backend returns the generic message even on success (enumeration-
    // resistant), so the only real failures here are network or 500-class.
    errorMsg.value = err instanceof ApiError
      ? err.message
      : 'Could not resend. Try again.'
  } finally {
    resendLoading.value = false
  }
}

function startCooldown(seconds) {
  resendCooldown.value = seconds
  clearInterval(cooldownTimer)
  cooldownTimer = setInterval(() => {
    resendCooldown.value--
    if (resendCooldown.value <= 0) clearInterval(cooldownTimer)
  }, 1000)
}

onMounted(() => { inputs.value[0]?.focus() })
onUnmounted(() => clearInterval(cooldownTimer))
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@400;500;600&display=swap');

.verify-page { min-height: 100vh; background: #1a1a1a; font-family: 'DM Sans', sans-serif; color: #e8e0d5; }

.topbar { display: flex; align-items: center; padding: 0 2rem; height: 60px; background: #111; border-bottom: 1px solid #2e2e2e; }
.topbar-logo { display: flex; align-items: center; gap: 0.5rem; }
.logo-icon { font-size: 1.5rem; }
.logo-text { font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #e8e0d5; }

.main { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: calc(100vh - 60px); padding: 2rem; }
.title { font-family: 'Playfair Display', serif; font-size: 2rem; text-align: center; margin-bottom: 2rem; }

.card { background: #252525; border-radius: 16px; padding: 2.5rem 2rem; width: 100%; max-width: 420px; display: flex; flex-direction: column; align-items: center; gap: 1.2rem; box-shadow: 0 8px 32px rgba(0,0,0,0.4); }

.pawn-wrap { position: relative; display: flex; flex-direction: column; align-items: center; margin-bottom: 0.5rem; }
.pawn-icon { font-size: 2.5rem; }
.pawn-shadow { width: 40px; height: 8px; background: rgba(0,0,0,0.3); border-radius: 50%; margin-top: 4px; }

.subtitle { text-align: center; color: #999; font-size: 0.95rem; line-height: 1.6; }
.subtitle strong { color: #e8e0d5; }

.code-inputs { display: flex; gap: 0.6rem; }
.code-input { width: 46px; height: 56px; background: #1a1a1a; border: 2px solid #3a3a3a; border-radius: 10px; color: #e8e0d5; font-size: 1.5rem; text-align: center; font-family: 'DM Sans', sans-serif; outline: none; transition: border-color 0.2s; }
.code-input:focus { border-color: #5a9e42; }
.code-input.error { border-color: #e05252; }

.error-msg { color: #e05252; font-size: 0.85rem; text-align: center; }
.success-msg { color: #5a9e42; font-size: 0.85rem; text-align: center; }

.btn-primary { width: 100%; padding: 0.85rem; background: #5a9e42; border: none; border-radius: 8px; color: #fff; font-family: 'DM Sans', sans-serif; font-size: 1rem; font-weight: 600; cursor: pointer; transition: background 0.2s; display: flex; align-items: center; justify-content: center; gap: 0.5rem; }
.btn-primary:hover:not(:disabled) { background: #7cb662; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.spinner { width: 18px; height: 18px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.resend-text { font-size: 0.85rem; color: #777; text-align: center; }
.link-btn { background: none; border: none; color: #7cb662; cursor: pointer; font-size: 0.85rem; font-family: 'DM Sans', sans-serif; padding: 0; text-decoration: underline; }
.link-btn:disabled { color: #555; cursor: not-allowed; text-decoration: none; }
</style>