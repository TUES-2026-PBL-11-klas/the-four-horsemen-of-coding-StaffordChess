<template>
  <div class="profile-page">
    <header class="topbar">
      <div class="topbar-logo"><span class="logo-icon">♟</span><span class="logo-text">StaffordChess</span></div>
      <nav class="topbar-nav">
        <router-link to="/play">Play</router-link>
        <router-link to="/profile">Profile</router-link>
        <button class="logout-btn" @click="handleLogout">Logout</button>
      </nav>
    </header>

    <div v-if="loading" class="loading-state">Loading profile...</div>
    <main v-else class="main">
      <!-- Profile card -->
      <div class="profile-card">
        <div class="avatar">{{ profile?.username?.[0]?.toUpperCase() }}</div>
        <div class="profile-info">
          <h1 class="username">{{ profile?.username }}</h1>
          <p class="email">{{ authStore.user?.email }}</p>
        </div>
        <div class="rating-badge">
          <span class="rating-num">{{ profile?.current_rating ?? '—' }}</span>
          <span class="rating-label">Rating</span>
        </div>
      </div>

      <!-- Stats -->
      <div class="stats-row">
        <div class="stat-card">
          <span class="stat-num">{{ profile?.games_played ?? 0 }}</span>
          <span class="stat-label">Games</span>
        </div>
        <div class="stat-card wins">
          <span class="stat-num">{{ profile?.wins ?? 0 }}</span>
          <span class="stat-label">Wins</span>
        </div>
        <div class="stat-card draws">
          <span class="stat-num">{{ profile?.draws ?? 0 }}</span>
          <span class="stat-label">Draws</span>
        </div>
        <div class="stat-card losses">
          <span class="stat-num">{{ profile?.losses ?? 0 }}</span>
          <span class="stat-label">Losses</span>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tabs">
        <button :class="{ active: tab === 'history' }" @click="tab = 'history'">Game History</button>
        <button :class="{ active: tab === 'rating' }" @click="tab = 'rating'; loadRating()">Rating</button>
      </div>

      <!-- Game History -->
      <div v-if="tab === 'history'" class="history-list">
        <div v-if="games.length === 0" class="empty-state">No games played yet.</div>
        <div v-for="game in games" :key="game.game_id" class="game-row"
          @click="openGame(game)">
          <div class="game-vs">
            <span class="game-opponent">vs {{ game.opponent_username }}</span>
            <span class="game-date">{{ formatDate(game.started_at) }}</span>
          </div>
          <div class="game-meta">
            <span class="game-played-as">{{ game.played_as === 'white' ? '⬜' : '⬛' }} {{ game.played_as }}</span>
            <span class="game-result" :class="game.outcome">{{ outcomeLabel(game.outcome) }}</span>
          </div>
        </div>
      </div>

      <!-- Rating chart (SVG) -->
      <div v-if="tab === 'rating'" class="rating-section">
        <div v-if="ratingHistory.length === 0" class="empty-state">No rating history yet.</div>
        <div v-else class="rating-chart-wrap">
          <svg :viewBox="`0 0 ${chartW} ${chartH}`" class="rating-chart">
            <defs>
              <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#5a9e42" stop-opacity="0.3"/>
                <stop offset="100%" stop-color="#5a9e42" stop-opacity="0"/>
              </linearGradient>
            </defs>
            <!-- Fill area under line -->
            <path v-if="chartCoords.length > 1" :d="areaPath" fill="url(#chartGrad)" />
            <!-- Line -->
            <polyline :points="chartPoints" fill="none" stroke="#5a9e42" stroke-width="2.5" stroke-linejoin="round" />
            <!-- Dots -->
            <circle v-for="(pt, i) in chartCoords" :key="i"
              :cx="pt.x" :cy="pt.y" r="4" fill="#7cb662"
              @mouseenter="hovered = i" @mouseleave="hovered = null"
              style="cursor:pointer"
            />
            <!-- Tooltip -->
            <g v-if="hovered !== null && chartCoords[hovered]">
              <rect
                :x="Math.min(chartCoords[hovered].x - 30, chartW - 70)"
                :y="chartCoords[hovered].y - 36"
                width="62" height="26" rx="5"
                fill="#2e2e2e" stroke="#5a9e42" stroke-width="1"
              />
              <text
                :x="Math.min(chartCoords[hovered].x - 30, chartW - 70) + 31"
                :y="chartCoords[hovered].y - 17"
                text-anchor="middle" fill="#e8e0d5" font-size="13" font-family="DM Sans, sans-serif"
              >{{ ratingHistory[hovered]?.rating }}</text>
            </g>
          </svg>
          <div class="rating-range">
            <span>{{ minRating }} LP</span>
            <span>{{ maxRating }} LP</span>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { apiFetch, ApiError } from '../api/http'

const router = useRouter()
const authStore = useAuthStore()

const profile = ref(null)
const games = ref([])
const ratingHistory = ref([])
const loading = ref(true)
const tab = ref('history')
const hovered = ref(null)

const chartW = 480, chartH = 160

const chartCoords = computed(() => {
  if (!ratingHistory.value.length) return []
  const ratings = ratingHistory.value.map(r => r.rating)
  const mn = Math.min(...ratings), mx = Math.max(...ratings)
  const range = mx - mn || 1
  return ratings.map((r, i) => ({
    x: (i / (ratings.length - 1 || 1)) * (chartW - 40) + 20,
    y: chartH - 20 - ((r - mn) / range) * (chartH - 40)
  }))
})

const chartPoints = computed(() => chartCoords.value.map(p => `${p.x},${p.y}`).join(' '))

const areaPath = computed(() => {
  if (chartCoords.value.length < 2) return ''
  const pts = chartCoords.value
  const first = pts[0], last = pts[pts.length - 1]
  const line = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ')
  return `${line} L${last.x},${chartH - 20} L${first.x},${chartH - 20} Z`
})

const minRating = computed(() => ratingHistory.value.length ? Math.min(...ratingHistory.value.map(r => r.rating)) : 0)
const maxRating = computed(() => ratingHistory.value.length ? Math.max(...ratingHistory.value.map(r => r.rating)) : 0)

function formatDate(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function outcomeLabel(outcome) {
  if (outcome === 'win') return 'Win'
  if (outcome === 'loss') return 'Loss'
  if (outcome === 'draw') return 'Draw'
  if (outcome === 'ongoing') return 'Ongoing'
  return outcome ?? '—'
}

// FIX: ongoing games can't be reviewed (no PGN yet) — send the user back into
// the live game session instead. Finished games go to the replay screen.
function openGame(game) {
  if (game.outcome === 'ongoing') {
    router.push(`/game/${game.game_id}`)
  } else {
    router.push(`/review/${game.game_id}`)
  }
}

async function loadProfile() {
  try {
    const [p, g] = await Promise.all([
      apiFetch('/profile/me', { auth: true }),
      apiFetch('/profile/me/games', { auth: true }),
    ])
    profile.value = p
    // FIX: backend returns games in repository order (no guarantee). For a
    // history view we want newest first; sort by started_at descending and
    // push games with no timestamp to the bottom.
    games.value = [...g].sort((a, b) => {
      const ta = a.started_at ? Date.parse(a.started_at) : 0
      const tb = b.started_at ? Date.parse(b.started_at) : 0
      return tb - ta
    })
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      authStore.logout()
      router.push('/login')
    }
    // Other errors leave profile/games empty; the template's `?? 0` / empty
    // state takes over. We could surface a toast here later.
  } finally {
    loading.value = false
  }
}

async function loadRating() {
  if (ratingHistory.value.length) return
  try {
    const history = await apiFetch('/profile/me/rating', { auth: true })
    // FIX: defensive chronological sort so the chart line never zig-zags
    // backwards if the repo returns snapshots in an unexpected order.
    ratingHistory.value = [...history].sort((a, b) => {
      const ta = a.date ? Date.parse(a.date) : 0
      const tb = b.date ? Date.parse(b.date) : 0
      return ta - tb
    })
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      authStore.logout()
      router.push('/login')
    }
  }
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

onMounted(loadProfile)
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@400;500;600&display=swap');
.profile-page { min-height: 100vh; background: #1a1a1a; font-family: 'DM Sans', sans-serif; color: #e8e0d5; }
.topbar { display: flex; align-items: center; justify-content: space-between; padding: 0 2rem; height: 60px; background: #111; border-bottom: 1px solid #2e2e2e; }
.topbar-logo { display: flex; align-items: center; gap: 0.5rem; }
.logo-icon { font-size: 1.5rem; } .logo-text { font-family: 'Playfair Display', serif; font-size: 1.2rem; }
.topbar-nav { display: flex; align-items: center; gap: 1.5rem; }
.topbar-nav a { color: #aaa; text-decoration: none; font-size: 0.95rem; }
.topbar-nav a:hover, .topbar-nav a.router-link-active { color: #e8e0d5; }
.logout-btn { background: none; border: 1px solid #3a3a3a; color: #aaa; padding: 0.3rem 0.9rem; border-radius: 6px; cursor: pointer; font-family: 'DM Sans', sans-serif; font-size: 0.9rem; }
.logout-btn:hover { border-color: #e05252; color: #e05252; }
.loading-state { text-align: center; padding: 4rem; color: #777; }
.main { max-width: 700px; margin: 0 auto; padding: 2rem 1rem; display: flex; flex-direction: column; gap: 1.5rem; }
.profile-card { background: #252525; border-radius: 16px; padding: 1.5rem; display: flex; align-items: center; gap: 1.2rem; }
.avatar { width: 64px; height: 64px; background: #3a3a3a; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.8rem; font-weight: 700; color: #7cb662; flex-shrink: 0; }
.profile-info { flex: 1; }
.username { font-family: 'Playfair Display', serif; font-size: 1.4rem; margin-bottom: 0.2rem; }
.email { color: #777; font-size: 0.85rem; }
.rating-badge { display: flex; flex-direction: column; align-items: center; }
.rating-num { font-size: 1.8rem; font-weight: 700; color: #7cb662; }
.rating-label { font-size: 0.75rem; color: #777; }
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.8rem; }
.stat-card { background: #252525; border-radius: 12px; padding: 1rem; text-align: center; display: flex; flex-direction: column; gap: 0.2rem; }
.stat-num { font-size: 1.5rem; font-weight: 700; }
.stat-label { font-size: 0.75rem; color: #777; }
.wins .stat-num { color: #5a9e42; }
.draws .stat-num { color: #c9a227; }
.losses .stat-num { color: #e05252; }
.tabs { display: flex; gap: 0.5rem; border-bottom: 1px solid #2e2e2e; }
.tabs button { background: none; border: none; color: #777; font-family: 'DM Sans', sans-serif; font-size: 0.95rem; padding: 0.6rem 1rem; cursor: pointer; border-bottom: 2px solid transparent; }
.tabs button.active { color: #e8e0d5; border-bottom-color: #5a9e42; }
.history-list { display: flex; flex-direction: column; gap: 0.6rem; }
.game-row { background: #252525; border-radius: 10px; padding: 0.8rem 1rem; display: flex; justify-content: space-between; align-items: center; cursor: pointer; transition: background 0.15s; }
.game-row:hover { background: #2e2e2e; }
.game-vs { display: flex; flex-direction: column; gap: 0.2rem; }
.game-opponent { font-weight: 600; font-size: 0.95rem; }
.game-date { color: #777; font-size: 0.8rem; }
.game-meta { display: flex; flex-direction: column; align-items: flex-end; gap: 0.2rem; }
.game-played-as { font-size: 0.78rem; color: #777; text-transform: capitalize; }
.game-result { font-size: 0.85rem; font-weight: 600; padding: 0.15rem 0.5rem; border-radius: 4px; }
.game-result.win { color: #5a9e42; background: rgba(90,158,66,0.15); }
.game-result.loss { color: #e05252; background: rgba(224,82,82,0.15); }
.game-result.draw { color: #c9a227; background: rgba(201,162,39,0.15); }
.game-result.ongoing { color: #6aa6d8; background: rgba(106,166,216,0.15); }
.empty-state { text-align: center; color: #555; padding: 2rem; }
.rating-section { background: #252525; border-radius: 14px; padding: 1.2rem; }
.rating-chart-wrap { display: flex; flex-direction: column; gap: 0.5rem; }
.rating-chart { width: 100%; height: 160px; }
.rating-range { display: flex; justify-content: space-between; font-size: 0.8rem; color: #777; }
</style>