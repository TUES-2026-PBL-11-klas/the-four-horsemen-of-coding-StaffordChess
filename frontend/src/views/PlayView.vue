<template>
  <div class="play-page">
    <header class="topbar">
      <div class="topbar-logo">
        <span class="logo-icon">♟</span>
        <span class="logo-text">StaffordChess</span>
      </div>
      <nav class="topbar-nav">
        <router-link to="/play">Play</router-link>
        <router-link to="/profile">Profile</router-link>
        <button class="logout-btn" @click="handleLogout">Logout</button>
      </nav>
    </header>

    <main class="main">
      <h1 class="title">Play Chess</h1>

      <!-- CREATE CHALLENGE -->
      <section class="panel">
        <h2 class="panel-title">Create Game</h2>

        <div class="lobby-grid">
          <div class="time-card" v-for="mode in timeModes" :key="mode.label"
            :class="{ selected: selectedMode === mode.label }"
            @click="selectedMode = mode.label">
            <span class="time-icon">{{ mode.icon }}</span>
            <span class="time-label">{{ mode.label }}</span>
            <span class="time-sub">{{ mode.value }}</span>
          </div>
        </div>

        <div class="color-row">
          <span class="color-row-label">Play as</span>
          <div class="color-picker">
            <button :class="{ active: color === 'random' }" @click="color = 'random'">
              <span class="color-icon">◐</span> Random
            </button>
            <button :class="{ active: color === 'white' }" @click="color = 'white'">
              <span class="color-icon white">♔</span> White
            </button>
            <button :class="{ active: color === 'black' }" @click="color = 'black'">
              <span class="color-icon black">♚</span> Black
            </button>
          </div>
        </div>

        <button class="btn-play" :disabled="!selectedMode || creating" @click="handleCreate">
          <span v-if="creating" class="spinner"></span>
          <span v-else>Create Challenge</span>
        </button>
      </section>

      <!-- OPEN CHALLENGES -->
      <section class="panel">
        <div class="open-header">
          <h2 class="panel-title">Open Challenges</h2>
          <span class="online-dot" :class="{ on: connected }" :title="connected ? 'Live' : 'Disconnected'"></span>
        </div>

        <div v-if="loadingList" class="empty-state">Loading...</div>
        <div v-else-if="visibleChallenges.length === 0" class="empty-state">
          No open challenges. Create one above.
        </div>
        <div v-else class="challenge-list">
          <div v-for="ch in visibleChallenges" :key="ch.id"
            class="challenge-row"
            :class="{ pending: acceptingId === ch.id }"
            @click="handleAccept(ch)">
            <div class="ch-host">
              <strong>{{ ch.host_username }}</strong>
              <span class="ch-rating">{{ ch.host_rating }}</span>
            </div>
            <div class="ch-meta">
              <span class="ch-tc">{{ ch.time_control }}</span>
              <span class="ch-color" :title="colorTitle(ch.color_preference)">
                {{ colorIcon(ch.color_preference) }}
              </span>
            </div>
          </div>
        </div>
      </section>

      <p v-if="error" class="error-msg">{{ error }}</p>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { lobbyApi } from '../api/lobby'
import { useLobbySocket } from '../composables/useLobbySocket'
import { ApiError } from '../api/http'

const router = useRouter()
const authStore = useAuthStore()

const timeModes = [
  { label: 'Bullet', icon: '⚡', value: '1+0' },
  { label: 'Blitz', icon: '🔥', value: '3+0' },
  { label: 'Rapid', icon: '⏱', value: '10+0' },
  { label: 'Classical', icon: '♟', value: '30+0' },
]

const selectedMode = ref(null)
const color = ref('random')
const creating = ref(false)
const acceptingId = ref(null)
const loadingList = ref(true)
const error = ref('')

const challenges = ref([])
const { connected, connect, onEvent } = useLobbySocket()

const visibleChallenges = computed(() =>
  challenges.value.filter(c => c.host_id !== authStore.user?.id)
)

onEvent((ev) => {
  if(!ev) return
  if(ev.type === 'NEW_CHALLENGE') 
  {
    if(!challenges.value.find(c => c.id === ev.challenge.id)) 
    {
      challenges.value.push(ev.challenge)
    }
  } 
  else if(ev.type === 'REMOVE_CHALLENGE' || ev.type === 'MATCH_STARTED') 
  {
    challenges.value = challenges.value.filter(c => c.id !== ev.challenge_id)
  }
})

async function loadChallenges() {
  loadingList.value = true
  try 
  {
    challenges.value = await lobbyApi.list()
  } 
  catch(err) 
  {
    if(err instanceof ApiError && err.status === 401) {
      authStore.logout()
      router.push('/login')
    }
  } 
  finally 
  {
    loadingList.value = false
  }
}

async function handleCreate() {
  const mode = timeModes.find(m => m.label === selectedMode.value)
  if(!mode) return

  creating.value = true
  error.value = ''
  try 
  {
    const challenge = await lobbyApi.create(mode.value, color.value)
    router.push({ name: 'waiting', query: { cid: challenge.id } })
  } 
  catch(err) 
  {
    error.value = err instanceof ApiError ? err.message : 'Could not create challenge.'
  } 
  finally 
  {
    creating.value = false
  }
}

async function handleAccept(ch) {
  if(acceptingId.value) return
  acceptingId.value = ch.id
  error.value = ''
  try 
  {
    const result = await lobbyApi.accept(ch.id)
    router.push(`/game/${result.game_id}`)
  } 
  catch(err) 
  {
    if(err instanceof ApiError && err.status === 400) 
    {
      challenges.value = challenges.value.filter(c => c.id !== ch.id)
      error.value = 'That challenge is no longer available.'
    } 
    else 
    {
      error.value = err instanceof ApiError ? err.message : 'Could not accept challenge.'
    }
  } 
  finally 
  {
    acceptingId.value = null
  }
}

function colorIcon(pref) {
  if (pref === 'white') return '♔'
  if (pref === 'black') return '♚'
  return '◐'
}

function colorTitle(pref) {
  if (pref === 'white') return 'Host plays White'
  if (pref === 'black') return 'Host plays Black'
  return 'Random color'
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

onMounted(() => {
  loadChallenges()
  connect()
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@400;500;600&display=swap');

.play-page { min-height: 100vh; background: #1a1a1a; font-family: 'DM Sans', sans-serif; color: #e8e0d5; }

.topbar { display: flex; align-items: center; justify-content: space-between; padding: 0 2rem; height: 60px; background: #111; border-bottom: 1px solid #2e2e2e; }
.topbar-logo { display: flex; align-items: center; gap: 0.5rem; }
.logo-icon { font-size: 1.5rem; }
.logo-text { font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #e8e0d5; }
.topbar-nav { display: flex; align-items: center; gap: 1.5rem; }
.topbar-nav a { color: #aaa; text-decoration: none; font-size: 0.95rem; }
.topbar-nav a:hover, .topbar-nav a.router-link-active { color: #e8e0d5; }
.logout-btn { background: none; border: 1px solid #3a3a3a; color: #aaa; padding: 0.3rem 0.9rem; border-radius: 6px; cursor: pointer; font-family: 'DM Sans', sans-serif; font-size: 0.9rem; }
.logout-btn:hover { border-color: #e05252; color: #e05252; }

.main { max-width: 520px; margin: 0 auto; padding: 2rem 1rem; display: flex; flex-direction: column; align-items: stretch; gap: 1.5rem; }
.title { font-family: 'Playfair Display', serif; font-size: 2rem; text-align: center; }

.panel { background: #252525; border-radius: 14px; padding: 1.4rem; display: flex; flex-direction: column; gap: 1rem; }
.panel-title { font-family: 'Playfair Display', serif; font-size: 1.15rem; color: #e8e0d5; }

.lobby-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.8rem; }
.time-card { background: #1f1f1f; border: 2px solid #2e2e2e; border-radius: 12px; padding: 1rem; display: flex; flex-direction: column; align-items: center; gap: 0.3rem; cursor: pointer; transition: all 0.15s; }
.time-card:hover { border-color: #5a9e42; background: #232a20; }
.time-card.selected { border-color: #5a9e42; background: #1e2e1a; }
.time-icon { font-size: 1.7rem; }
.time-label { font-weight: 600; font-size: 1rem; }
.time-sub { font-size: 0.78rem; color: #777; font-variant-numeric: tabular-nums; }

.color-row { display: flex; flex-direction: column; gap: 0.5rem; }
.color-row-label { font-size: 0.85rem; color: #999; }
.color-picker { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; }
.color-picker button { background: #1f1f1f; border: 1px solid #2e2e2e; border-radius: 8px; padding: 0.55rem 0.4rem; color: #aaa; font-family: 'DM Sans', sans-serif; font-size: 0.85rem; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 0.35rem; transition: all 0.15s; }
.color-picker button:hover { border-color: #5a9e42; }
.color-picker button.active { border-color: #5a9e42; background: #1e2e1a; color: #e8e0d5; }
.color-icon { font-size: 1.1rem; line-height: 1; }
.color-icon.white { color: #f0ebe0; }
.color-icon.black { color: #777; }

.btn-play { width: 100%; padding: 0.85rem; background: #5a9e42; border: none; border-radius: 10px; color: #fff; font-family: 'DM Sans', sans-serif; font-size: 1rem; font-weight: 600; cursor: pointer; transition: background 0.2s; display: flex; align-items: center; justify-content: center; min-height: 46px; }
.btn-play:hover:not(:disabled) { background: #7cb662; }
.btn-play:disabled { opacity: 0.5; cursor: not-allowed; }

.open-header { display: flex; align-items: center; justify-content: space-between; }
.online-dot { width: 8px; height: 8px; background: #555; border-radius: 50%; transition: background 0.2s; }
.online-dot.on { background: #5a9e42; box-shadow: 0 0 8px rgba(90,158,66,0.6); }

.challenge-list { display: flex; flex-direction: column; gap: 0.5rem; }
.challenge-row { background: #1f1f1f; border: 1px solid #2e2e2e; border-radius: 10px; padding: 0.7rem 0.9rem; display: flex; justify-content: space-between; align-items: center; cursor: pointer; transition: all 0.15s; }
.challenge-row:hover { border-color: #5a9e42; background: #232a20; }
.challenge-row.pending { opacity: 0.5; pointer-events: none; }
.ch-host { display: flex; align-items: baseline; gap: 0.5rem; }
.ch-host strong { font-size: 0.95rem; color: #e8e0d5; }
.ch-rating { font-size: 0.78rem; color: #777; font-variant-numeric: tabular-nums; }
.ch-meta { display: flex; align-items: center; gap: 0.7rem; }
.ch-tc { font-size: 0.85rem; color: #aaa; font-variant-numeric: tabular-nums; }
.ch-color { font-size: 1.05rem; line-height: 1; }

.empty-state { text-align: center; color: #555; padding: 1.5rem 0.5rem; font-size: 0.9rem; }

.spinner { width: 20px; height: 20px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.error-msg { color: #e05252; font-size: 0.9rem; text-align: center; }
</style>