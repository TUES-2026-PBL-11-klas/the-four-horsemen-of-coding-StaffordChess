<template>
  <div class="game-page">
    <header class="topbar">
      <div class="topbar-logo"><span class="logo-icon">♟</span><span class="logo-text">StaffordChess</span></div>
      <div class="topbar-status">{{ statusLabel }}</div>
    </header>

    <!-- Bail-out screens for the unhappy paths -->
    <div v-if="bootError" class="centered">
      <div class="centered-card">
        <h2>{{ bootError }}</h2>
        <button class="btn-primary" @click="router.push('/play')">Back to lobby</button>
      </div>
    </div>

    <div v-else-if="loading" class="centered">
      <div class="centered-card">Loading game...</div>
    </div>

    <div v-else class="game-layout">
      <!-- Opponent strip -->
      <div class="player-bar opponent">
        <div class="player-info">
          <span class="player-avatar">{{ opponent?.username?.[0]?.toUpperCase() }}</span>
          <span class="player-name">{{ opponent?.username }}</span>
          <span v-if="opponent?.rating != null" class="player-rating">({{ opponent.rating }})</span>
        </div>
        <div class="clock" :class="{ active: !gameStore.isMyTurn && !gameStore.isGameOver }">
          {{ formatTime(opponentClockSec) }}
        </div>
      </div>

      <!-- Board -->
      <div class="board-wrap">
        <TheChessboard
          :board-config="boardConfig"
          :player-color="gameStore.myColor"
          @board-created="onBoardCreated"
          @move="onBoardMove"
        />
      </div>

      <!-- Me strip -->
      <div class="player-bar me">
        <div class="player-info">
          <span class="player-avatar">{{ me?.username?.[0]?.toUpperCase() }}</span>
          <span class="player-name">{{ me?.username }} <span class="you-tag">(You)</span></span>
          <span v-if="me?.rating != null" class="player-rating">({{ me.rating }})</span>
        </div>
        <div class="clock" :class="{ active: gameStore.isMyTurn && !gameStore.isGameOver }">
          {{ formatTime(myClockSec) }}
        </div>
      </div>

      <div class="controls">
        <button class="btn-action" @click="handleResign" :disabled="gameStore.isGameOver">
          Resign
        </button>
        <!-- Draw offer not wired on backend yet (engine.request_draw exists
             but the game WS handler doesn't dispatch it). Disabled for now. -->
        <button class="btn-action" disabled title="Coming soon">Draw</button>
      </div>

      <p v-if="gameStore.error" class="error-banner">{{ gameStore.error }}</p>
    </div>

    <!-- Game over modal -->
    <div v-if="gameStore.isGameOver && !bootError" class="modal-overlay">
      <div class="modal">
        <div class="modal-icon">{{ resultIcon }}</div>
        <h2 class="modal-title">{{ resultTitle }}</h2>
        <p class="modal-sub">{{ resultSub }}</p>
        <div class="modal-actions">
          <button class="btn-primary" @click="router.push('/play')">Play Again</button>
          <button class="btn-secondary" @click="router.push(`/review/${gameStore.gameId}`)">Review Game</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { TheChessboard } from 'vue3-chessboard'
import 'vue3-chessboard/style.css'
import { Chess } from 'chess.js'

import { useAuthStore } from '../stores/auth'
import { useGameStore } from '../stores/game'
import { gameApi } from '../api/game'
import { useGameSocket } from '../composables/useGameSocket'
import { ApiError } from '../api/http'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const gameStore = useGameStore()
const socket = useGameSocket()

const loading = ref(true)
const bootError = ref(null)
const boardApi = ref(null)

// chess.js is used purely as a local oracle for legal moves so we can show
// move-dots without a server round-trip. The server remains the source of
// truth — every WS state push reloads chess.js from the canonical FEN.
const chess = new Chess()

const me = computed(() => gameStore.me)
const opponent = computed(() => gameStore.opponent)

// Display ticking clocks between server updates. The server's clock is
// deadline-based, so we don't need to estimate increments — we just count
// down from the last server-known time using a local timer. Every fresh
// state push from the WS resets this baseline.
const lastUpdateAt = ref(0)
const myClockSec = ref(null)
const opponentClockSec = ref(null)
let tickTimer = null

watch(
  () => [gameStore.whiteTime, gameStore.blackTime, gameStore.turn, gameStore.isGameOver],
  () => {
    lastUpdateAt.value = performance.now()
    myClockSec.value = gameStore.myTime
    opponentClockSec.value = gameStore.opponentTime
  },
)

function recomputeClocks() {
  if (gameStore.isGameOver || gameStore.myTime == null) return
  const elapsed = (performance.now() - lastUpdateAt.value) / 1000
  // Only the side whose turn it is has its clock burning.
  if (gameStore.isMyTurn) {
    myClockSec.value = Math.max(0, gameStore.myTime - elapsed)
    opponentClockSec.value = gameStore.opponentTime
  } else {
    opponentClockSec.value = Math.max(0, gameStore.opponentTime - elapsed)
    myClockSec.value = gameStore.myTime
  }
}

const boardConfig = computed(() => ({
  orientation: gameStore.myColor || 'white',
  coordinates: true,
  movable: {
    free: false,
    color: gameStore.isMyTurn ? gameStore.myColor : undefined,
    dests: legalDests.value,
    showDests: true,
  },
  premovable: { enabled: false },
  drawable: { enabled: true },
  highlight: { lastMove: true, check: true },
  check: gameStore.isCheck,
  turnColor: gameStore.turn,
}))

// chess.js → chessground "dests" Map. Recomputed whenever the position
// changes; the board picks it up via the reactive boardConfig.
const legalDests = computed(() => {
  // Touch the ref so the computed re-runs on every FEN change.
  // eslint-disable-next-line no-unused-expressions
  gameStore.fen
  const dests = new Map()
  if (!gameStore.isMyTurn) return dests
  const moves = chess.moves({ verbose: true })
  for (const m of moves) {
    if (!dests.has(m.from)) dests.set(m.from, [])
    dests.get(m.from).push(m.to)
  }
  return dests
})

function onBoardCreated(api) {
  boardApi.value = api
  // If the WS already delivered a state before the board mounted, sync now.
  if (gameStore.fen) syncBoardToServer()
}

// Watch every server state push and re-sync the board + chess.js to it.
// This is the reconciliation step: if our optimistic local move matches
// the server's resulting FEN, this is effectively a no-op. If the server
// rejected (sent an error and no state), this watcher doesn't fire — we
// handle the revert in the error path of onBoardMove.
watch(() => gameStore.fen, (fen) => {
  if (!fen) return
  try { chess.load(fen) } catch {
    // If chess.js can't parse, fall back to a fresh game; shouldn't happen.
    chess.reset()
  }
  syncBoardToServer()
})

function syncBoardToServer() {
  const api = boardApi.value
  if (!api || !gameStore.fen) return
  // setPosition is the cleanest way to force-align the board to a FEN.
  // Library API: vue3-chessboard's BoardApi exposes setPosition(fen).
  if (typeof api.setPosition === 'function') {
    api.setPosition(gameStore.fen)
  }
}

function onBoardMove(move) {
  // The board library has already applied this move optimistically. We
  // forward it to the server and let the next state push reconcile.
  //
  // vue3-chessboard auto-handles the promotion UI; the move object's
  // `promotion` field is the user's choice (or undefined for non-promotion).
  // If for some reason promotion is required but not supplied, we default
  // to queen — matching the backend's queen-fallback in _find_legal_move.
  const promotion = move?.promotion
    ?? (isPromotionMove(move?.from, move?.to) ? 'q' : null)
  socket.sendMove(move.from, move.to, promotion)
}

function isPromotionMove(from, to) {
  if (!from || !to) return false
  const piece = chess.get(from)
  if (!piece || piece.type !== 'p') return false
  const targetRank = to[1]
  return (piece.color === 'w' && targetRank === '8') || (piece.color === 'b' && targetRank === '1')
}

function handleResign() {
  if (!confirm('Resign this game?')) return
  socket.sendResign()
}

function formatTime(sec) {
  if (sec == null) return '--:--'
  const total = Math.max(0, Math.floor(sec))
  const m = Math.floor(total / 60).toString().padStart(2, '0')
  const s = (total % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

const statusLabel = computed(() => {
  if (gameStore.isGameOver) return 'Game over'
  if (gameStore.fen == null) return 'Waiting for opponent...'
  return gameStore.isMyTurn ? 'Your turn' : "Opponent's turn"
})

const resultIcon = computed(() => {
  if (!gameStore.result) return '🏁'
  if (gameStore.winnerId == null) return '🤝'
  return gameStore.winnerId === authStore.user?.id ? '🏆' : '😔'
})

const resultTitle = computed(() => {
  if (gameStore.winnerId == null) return "It's a Draw"
  return gameStore.winnerId === authStore.user?.id ? 'You Won!' : 'You Lost'
})

const resultSub = computed(() => {
  // Use the backend's result string (e.g. "White wins", "Black resigns") as
  // a concise reason, since the WS final state carries the GameResult enum.
  return gameStore.result || ''
})

onMounted(async () => {
  const gameId = route.params.id
  if (!gameId) {
    bootError.value = 'Missing game id.'
    loading.value = false
    return
  }

  try {
    const meta = await gameApi.get(gameId)
    gameStore.setMeta(meta)

    // Refuse to render if for some reason this user isn't part of the game.
    // (The HTTP endpoint already 403s on that, but if we got here through
    // some edge case, the WS would still refuse with 4003.)
    if (!gameStore.myColor) {
      bootError.value = 'You are not a participant in this game.'
      return
    }
    socket.connect(gameId)
    tickTimer = setInterval(recomputeClocks, 200)
  } catch (err) {
    if (err instanceof ApiError) {
      if (err.status === 404) bootError.value = 'Game not found.'
      else if (err.status === 403) bootError.value = 'You are not a participant in this game.'
      else if (err.status === 401) { authStore.logout(); router.push('/login'); return }
      else bootError.value = err.message
    } else {
      bootError.value = 'Could not load game.'
    }
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  clearInterval(tickTimer)
  tickTimer = null
  socket.disconnect()
  gameStore.reset()
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@400;500;600&display=swap');

.game-page { min-height: 100vh; background: #1a1a1a; font-family: 'DM Sans', sans-serif; color: #e8e0d5; }
.topbar { display: flex; align-items: center; justify-content: space-between; padding: 0 2rem; height: 60px; background: #111; border-bottom: 1px solid #2e2e2e; }
.topbar-logo { display: flex; align-items: center; gap: 0.5rem; }
.logo-icon { font-size: 1.5rem; }
.logo-text { font-family: 'Playfair Display', serif; font-size: 1.2rem; }
.topbar-status { font-size: 0.9rem; color: #7cb662; font-weight: 600; }

.centered { display: flex; align-items: center; justify-content: center; min-height: calc(100vh - 60px); }
.centered-card { background: #252525; border-radius: 14px; padding: 2rem 2.5rem; display: flex; flex-direction: column; align-items: center; gap: 1rem; color: #aaa; }

.game-layout { display: flex; flex-direction: column; align-items: center; padding: 1rem; gap: 0.6rem; }
.player-bar { display: flex; justify-content: space-between; align-items: center; width: 100%; max-width: 480px; background: #252525; padding: 0.6rem 1rem; border-radius: 10px; }
.player-info { display: flex; align-items: center; gap: 0.6rem; }
.player-avatar { width: 32px; height: 32px; background: #3a3a3a; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 0.9rem; }
.player-name { font-size: 0.95rem; font-weight: 500; }
.player-rating { font-size: 0.78rem; color: #777; font-variant-numeric: tabular-nums; }
.you-tag { font-size: 0.75rem; color: #777; }
.clock { font-size: 1.3rem; font-weight: 700; font-variant-numeric: tabular-nums; color: #aaa; background: #1a1a1a; padding: 0.3rem 0.8rem; border-radius: 6px; border: 2px solid transparent; }
.clock.active { color: #e8e0d5; border-color: #5a9e42; }

.board-wrap { width: 100%; max-width: 480px; aspect-ratio: 1; }
/* vue3-chessboard renders its own .cg-wrap inside; we just give it a square. */
.board-wrap :deep(.cg-wrap) { width: 100%; height: 100%; }

.controls { display: flex; gap: 1rem; width: 100%; max-width: 480px; }
.btn-action { flex: 1; padding: 0.65rem; background: #252525; border: 1px solid #3a3a3a; border-radius: 8px; color: #aaa; font-family: 'DM Sans', sans-serif; font-size: 0.9rem; cursor: pointer; transition: all 0.2s; }
.btn-action:hover:not(:disabled) { border-color: #e05252; color: #e05252; }
.btn-action:disabled { opacity: 0.4; cursor: not-allowed; }

.error-banner { width: 100%; max-width: 480px; padding: 0.6rem; background: rgba(224,82,82,0.1); border: 1px solid rgba(224,82,82,0.3); border-radius: 8px; color: #e05252; font-size: 0.85rem; text-align: center; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #252525; border-radius: 20px; padding: 2.5rem 2rem; width: 90%; max-width: 360px; display: flex; flex-direction: column; align-items: center; gap: 1rem; box-shadow: 0 20px 60px rgba(0,0,0,0.6); }
.modal-icon { font-size: 3.5rem; }
.modal-title { font-family: 'Playfair Display', serif; font-size: 1.8rem; }
.modal-sub { color: #777; font-size: 0.9rem; text-align: center; }
.modal-actions { display: flex; gap: 0.8rem; width: 100%; margin-top: 0.5rem; }
.btn-primary { flex: 1; padding: 0.75rem; background: #5a9e42; border: none; border-radius: 8px; color: #fff; font-family: 'DM Sans', sans-serif; font-weight: 600; cursor: pointer; font-size: 0.95rem; }
.btn-primary:hover { background: #7cb662; }
.btn-secondary { flex: 1; padding: 0.75rem; background: transparent; border: 1px solid #3a3a3a; border-radius: 8px; color: #aaa; font-family: 'DM Sans', sans-serif; cursor: pointer; font-size: 0.95rem; }
.btn-secondary:hover { border-color: #5a9e42; color: #e8e0d5; }
</style>