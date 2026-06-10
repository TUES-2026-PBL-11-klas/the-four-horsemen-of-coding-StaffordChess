<template>
  <div class="waiting-page">
    <header class="topbar">
      <div class="topbar-logo">
        <span class="logo-icon">♟</span>
        <span class="logo-text">StaffordChess</span>
      </div>
    </header>

    <main class="main">
      <div class="card">
        <div class="chess-anim">
          <span class="piece piece-1">♜</span>
          <span class="piece piece-2">♟</span>
          <span class="piece piece-3">♞</span>
        </div>
        <h2 class="waiting-title">Waiting for opponent...</h2>
        <p class="waiting-sub">Your challenge is in the lobby</p>

        <div v-if="challengeTC" class="challenge-info">
          <span class="info-pill">{{ challengeTC }}</span>
          <span class="info-pill">{{ colorLabel }}</span>
        </div>

        <div class="dots">
          <span></span><span></span><span></span>
        </div>
        <div class="elapsed">{{ elapsedStr }}</div>

        <p v-if="error" class="error-msg">{{ error }}</p>

        <button class="btn-cancel" :disabled="cancelling" @click="handleCancel">
          {{ cancelling ? 'Cancelling...' : 'Cancel' }}
        </button>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { lobbyApi } from '../api/lobby'
import { useLobbySocket } from '../composables/useLobbySocket'
import { ApiError } from '../api/http'

const router = useRouter()
const route = useRoute()

const elapsed = ref(0)
const cancelling = ref(false)
const error = ref('')
const challengeTC = ref(null)
const challengeColor = ref(null)

let timer = null

const challengeId = computed(() => route.query.cid)

const { connect, onEvent } = useLobbySocket()

const elapsedStr = computed(() => {
  const m = Math.floor(elapsed.value / 60).toString().padStart(2, '0')
  const s = (elapsed.value % 60).toString().padStart(2, '0')
  return `${m}:${s}`
})

const colorLabel = computed(() => {
  if (challengeColor.value === 'white') return 'You play White'
  if (challengeColor.value === 'black') return 'You play Black'
  return 'Random color'
})

onEvent((ev) => {
  if(!ev || !challengeId.value) return

  if(ev.type === 'MATCH_STARTED' && ev.challenge_id === challengeId.value) 
  {
    router.replace(`/game/${ev.game_id}`)
  }
  else if(ev.type === 'REMOVE_CHALLENGE' && ev.challenge_id === challengeId.value) 
  {
  }
})

async function loadChallengeInfo() {
  if(!challengeId.value) return
  try 
  {
    const list = await lobbyApi.list()
    const mine = list.find(c => c.id === challengeId.value)
    if(!mine) 
    {
      return
    }
    challengeTC.value = mine.time_control
    challengeColor.value = mine.color_preference
  } 
  catch {}
}

async function handleCancel() {
  if(!challengeId.value) 
  {
    router.push({ name: 'play' })
    return
  }
  cancelling.value = true
  try 
  {
    await lobbyApi.cancel(challengeId.value)
    router.push({ name: 'play' })
  } 
  catch(err) 
  {
    if(err instanceof ApiError && err.status === 404) 
    {
      router.push({ name: 'play' })
    } 
    else 
    {
      error.value = err instanceof ApiError ? err.message : 'Could not cancel.'
      cancelling.value = false
    }
  }
}

onMounted(() => {
  if(!challengeId.value) 
  {
    router.replace({ name: 'play' })
    return
  }
  timer = setInterval(() => elapsed.value++, 1000)
  connect()
  loadChallengeInfo()
})

onUnmounted(() => {
  clearInterval(timer)
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@400;500;600&display=swap');

.waiting-page { min-height: 100vh; background: #1a1a1a; font-family: 'DM Sans', sans-serif; color: #e8e0d5; }
.topbar { display: flex; align-items: center; padding: 0 2rem; height: 60px; background: #111; border-bottom: 1px solid #2e2e2e; }
.topbar-logo { display: flex; align-items: center; gap: 0.5rem; }
.logo-icon { font-size: 1.5rem; }
.logo-text { font-family: 'Playfair Display', serif; font-size: 1.2rem; }

.main { display: flex; align-items: center; justify-content: center; min-height: calc(100vh - 60px); }
.card { background: #252525; border-radius: 20px; padding: 3rem 2.5rem; width: 100%; max-width: 380px; display: flex; flex-direction: column; align-items: center; gap: 1.2rem; box-shadow: 0 8px 32px rgba(0,0,0,0.4); }

.chess-anim { display: flex; gap: 1rem; font-size: 2.5rem; }
.piece { animation: bob 1.5s ease-in-out infinite; }
.piece-1 { animation-delay: 0s; }
.piece-2 { animation-delay: 0.3s; }
.piece-3 { animation-delay: 0.6s; }
@keyframes bob { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }

.waiting-title { font-family: 'Playfair Display', serif; font-size: 1.5rem; text-align: center; }
.waiting-sub { color: #777; font-size: 0.9rem; text-align: center; }

.challenge-info { display: flex; gap: 0.5rem; flex-wrap: wrap; justify-content: center; }
.info-pill { background: #1f1f1f; border: 1px solid #2e2e2e; border-radius: 999px; padding: 0.25rem 0.7rem; font-size: 0.8rem; color: #aaa; font-variant-numeric: tabular-nums; }

.dots { display: flex; gap: 6px; }
.dots span { width: 8px; height: 8px; background: #5a9e42; border-radius: 50%; animation: blink 1.2s infinite; }
.dots span:nth-child(2) { animation-delay: 0.2s; }
.dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0%,80%,100% { opacity: 0.2; } 40% { opacity: 1; } }

.elapsed { font-size: 1.4rem; font-weight: 600; color: #7cb662; font-variant-numeric: tabular-nums; }

.error-msg { color: #e05252; font-size: 0.85rem; text-align: center; }

.btn-cancel { width: 100%; padding: 0.75rem; background: transparent; border: 1px solid #3a3a3a; border-radius: 8px; color: #aaa; font-family: 'DM Sans', sans-serif; font-size: 0.95rem; cursor: pointer; transition: all 0.2s; margin-top: 0.5rem; }
.btn-cancel:hover:not(:disabled) { border-color: #e05252; color: #e05252; }
.btn-cancel:disabled { opacity: 0.5; cursor: not-allowed; }
</style>