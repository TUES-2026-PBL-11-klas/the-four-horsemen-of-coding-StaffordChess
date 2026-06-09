<template>
  <div class="review-page">
    <header class="topbar">
      <div class="topbar-logo"><span class="logo-icon">♟</span><span class="logo-text">StaffordChess</span></div>
      <router-link to="/profile" class="back-btn">← Back</router-link>
    </header>

    <div v-if="loading" class="centered">Loading game...</div>
    <div v-else-if="bootError" class="centered">
      <div class="boot-card">
        <p>{{ bootError }}</p>
        <button class="btn-primary" @click="router.push('/profile')">Back to profile</button>
      </div>
    </div>

    <div v-else class="review-layout">
      <!-- HEADER: players + result -->
      <div class="game-header">
        <div class="header-side">
          <div class="header-player">
            <span class="hp-color white-dot"></span>
            <strong>{{ game.white_player.username }}</strong>
            <span class="hp-rating" v-if="game.white_player.rating != null">({{ game.white_player.rating }})</span>
          </div>
        </div>
        <div class="header-mid">
          <div class="hm-tc">{{ game.time_control }}</div>
          <div class="hm-result" :class="resultClass">{{ resultLabel }}</div>
        </div>
        <div class="header-side header-side-right">
          <div class="header-player">
            <span class="hp-color black-dot"></span>
            <strong>{{ game.black_player.username }}</strong>
            <span class="hp-rating" v-if="game.black_player.rating != null">({{ game.black_player.rating }})</span>
          </div>
        </div>
      </div>

      <!-- BOARD ROW: eval bar | board | move list -->
      <div class="board-row">
        <!-- Eval bar (white-at-bottom convention, regardless of board orientation) -->
        <div class="eval-bar" :title="evalTooltip">
          <div class="eval-fill-white" :style="{ height: `${whitePercent}%` }"></div>
          <div class="eval-label" :class="{ 'on-white': whitePercent > 50 }">
            {{ evalLabel }}
          </div>
          <div v-if="analyzing" class="eval-overlay">···</div>
        </div>

        <div class="board-wrap">
          <TheChessboard
            :board-config="boardConfig"
            @board-created="onBoardCreated"
          />
        </div>

        <!-- Move list + nav -->
        <aside class="side-panel">
          <h3 class="panel-title">Moves</h3>
          <div class="moves-grid" ref="moveListEl">
            <template v-if="movePairs.length === 0">
              <div class="empty-moves">No moves recorded.</div>
            </template>
            <template v-for="pair in movePairs" :key="pair.number">
              <span class="move-num">{{ pair.number }}.</span>
              <span class="move-san" :class="{ active: currentPly === pair.white.ply }"
                @click="goTo(pair.white.ply)">{{ pair.white.san }}</span>
              <span v-if="pair.black" class="move-san" :class="{ active: currentPly === pair.black.ply }"
                @click="goTo(pair.black.ply)">{{ pair.black.san }}</span>
              <span v-else class="move-san placeholder"></span>
            </template>
          </div>

          <div class="nav-controls">
            <button @click="goTo(0)" :disabled="currentPly === 0" title="Start (Home)">⏮</button>
            <button @click="goTo(currentPly - 1)" :disabled="currentPly === 0" title="Previous (←)">◀</button>
            <button @click="goTo(currentPly + 1)" :disabled="currentPly >= positions.length - 1" title="Next (→)">▶</button>
            <button @click="goTo(positions.length - 1)" :disabled="currentPly >= positions.length - 1" title="End (End)">⏭</button>
          </div>
          <div class="ply-counter">{{ currentPly }} / {{ positions.length - 1 }}</div>

          <p v-if="analyzing" class="analysis-status">Analyzing positions...</p>
          <p v-else-if="analysisError" class="analysis-error">{{ analysisError }}</p>
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { TheChessboard } from 'vue3-chessboard'
import 'vue3-chessboard/style.css'
import { Chess } from 'chess.js'

import { useAuthStore } from '../stores/auth'
import { gameApi } from '../api/game'
import { analysisApi } from '../api/analysis'
import { ApiError } from '../api/http'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const game = ref(null)
const positions = ref([])    // [{ fen, sanMove }]
const evals = ref([])        // [EvaluationResponse] — same index as positions
const currentPly = ref(0)
const loading = ref(true)
const analyzing = ref(false)
const bootError = ref(null)
const analysisError = ref(null)

const boardApi = ref(null)
const moveListEl = ref(null)

// Orient the board for the viewing user — they're a participant per the
// GET /game/{id} 403 check, so this always resolves to white or black.
const myColor = computed(() => {
  if (!game.value || !authStore.user) return 'white'
  return game.value.white_player.id === authStore.user.id ? 'white' : 'black'
})

const boardConfig = computed(() => ({
  orientation: myColor.value,
  coordinates: true,
  viewOnly: true,            // no input — this is a replay
  highlight: { lastMove: true, check: true },
}))

// Parse the UCI movetext written by game_session_service._build_pgn:
//   "e2e4 e7e5 g1f3 e7e8q ..."
// Replay through chess.js to get a FEN and SAN for every ply.
function buildPositions(uciMovetext) {
  const chess = new Chess()
  const out = [{ fen: chess.fen(), sanMove: null }]
  if (!uciMovetext) return out

  for (const token of uciMovetext.trim().split(/\s+/)) {
    if (token.length < 4) continue
    const move = { from: token.slice(0, 2), to: token.slice(2, 4) }
    if (token.length >= 5) move.promotion = token[4]

    const applied = chess.move(move)
    // If a token is malformed, stop here rather than fabricating positions.
    // The frontend then shows however many moves were valid, which is the
    // honest behaviour for replay of a possibly-corrupt record.
    if (!applied) break

    out.push({ fen: chess.fen(), sanMove: applied.san })
  }
  return out
}

// Group into "1. e4 e5" pairs for the right-side move list. `ply` indexes
// into `positions`: ply 1 = position after white's 1st move, etc.
const movePairs = computed(() => {
  const pairs = []
  for (let ply = 1; ply < positions.value.length; ply += 2) {
    pairs.push({
      number: Math.ceil(ply / 2),
      white: { ply, san: positions.value[ply].sanMove },
      black: positions.value[ply + 1]
        ? { ply: ply + 1, san: positions.value[ply + 1].sanMove }
        : null,
    })
  }
  return pairs
})

function goTo(ply) {
  if (ply < 0 || ply >= positions.value.length) return
  currentPly.value = ply
}

// Push the new FEN into the chessground board whenever the user navigates.
// Using watch (instead of doing it inside goTo) covers keyboard navigation
// and any other indirect sources.
watch(currentPly, (ply) => {
  const fen = positions.value[ply]?.fen
  if (fen && boardApi.value && typeof boardApi.value.setPosition === 'function') {
    boardApi.value.setPosition(fen)
  }
})

// Auto-scroll the active move into view when navigating via keyboard/buttons.
// Without this, long games scroll the active row off the visible area.
watch(currentPly, async () => {
  await nextTick()
  const active = moveListEl.value?.querySelector('.move-san.active')
  if (active) active.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
})

function onBoardCreated(api) {
  boardApi.value = api
  // The board mounts after our first goTo() may have already fired, so set
  // it to whatever the current ply is — usually 0 (starting position).
  const fen = positions.value[currentPly.value]?.fen
  if (fen && typeof api.setPosition === 'function') api.setPosition(fen)
}

// -- Eval bar math --------------------------------------------------------

const currentEval = computed(() => evals.value[currentPly.value] || null)

// Lichess-style sigmoid: smoothly maps centipawns to a 0..100 percent for
// White. ±150cp ≈ 65/35 split; ±500cp ≈ 85/15; ±1000cp ≈ 97/3.
function evalToWhitePercent(ev) {
  if (!ev) return 50
  if (ev.is_mate) {
    // Positive mate = white wins, negative = black wins. mate_in_moves of 0
    // shouldn't happen on a finished game, but guard anyway.
    if (ev.mate_in_moves === 0) return 50
    return ev.mate_in_moves > 0 ? 100 : 0
  }
  const cp = Math.max(-1500, Math.min(1500, ev.centipawns || 0))
  const winChance = 2 / (1 + Math.exp(-0.00368208 * cp)) - 1
  return 50 + 50 * winChance
}

const whitePercent = computed(() => evalToWhitePercent(currentEval.value))

const evalLabel = computed(() => {
  const ev = currentEval.value
  if (!ev) return ''
  if (ev.is_mate) {
    return ev.mate_in_moves > 0 ? `M${ev.mate_in_moves}` : `-M${Math.abs(ev.mate_in_moves)}`
  }
  const pawns = (ev.centipawns || 0) / 100
  const sign = pawns >= 0 ? '+' : ''
  return `${sign}${pawns.toFixed(1)}`
})

const evalTooltip = computed(() => {
  const ev = currentEval.value
  if (!ev) return 'Evaluation pending'
  return ev.best_move ? `Best move: ${ev.best_move}` : ''
})

// -- Result label ---------------------------------------------------------

const resultLabel = computed(() => {
  // game.result is the result_type string set by game_session_service —
  // values like "white_wins", "black_wins_by_resignation", "draw",
  // "white_wins_on_time", etc. Convert to a presentable label.
  const r = game.value?.result
  if (!r) return ''
  if (r === 'draw') return 'Draw'
  const parts = r.split('_')
  const winner = parts[0]   // "white" | "black"
  const reasonParts = parts.slice(2)  // after "_wins"
  const reason = reasonParts.length ? reasonParts.join(' ') : 'by checkmate'
  return `${winner[0].toUpperCase()}${winner.slice(1)} wins ${reason}`
})

const resultClass = computed(() => {
  const r = game.value?.result
  if (!r) return ''
  if (r === 'draw') return 'draw'
  return r.startsWith('white') ? 'white-wins' : 'black-wins'
})

// -- Keyboard navigation --------------------------------------------------

function onKey(e) {
  if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
  if (e.key === 'ArrowLeft') { e.preventDefault(); goTo(currentPly.value - 1) }
  else if (e.key === 'ArrowRight') { e.preventDefault(); goTo(currentPly.value + 1) }
  else if (e.key === 'Home') { e.preventDefault(); goTo(0) }
  else if (e.key === 'End') { e.preventDefault(); goTo(positions.value.length - 1) }
}

// -- Lifecycle ------------------------------------------------------------

async function runAnalysis(fens) {
  analyzing.value = true
  analysisError.value = null
  try {
    const results = await analysisApi.game(fens)
    evals.value = results
  } catch (err) {
    if (err instanceof ApiError) {
      // 400 typically means "too many positions" (>200 cap). 503 means the
      // Stockfish binary isn't reachable. Either way, the replay still works.
      if (err.status === 400 && err.message.includes('Too many')) {
        analysisError.value = 'Game too long to analyze.'
      } else if (err.status === 503) {
        analysisError.value = 'Analysis engine unavailable.'
      } else {
        analysisError.value = err.message
      }
    } else {
      analysisError.value = 'Could not load analysis.'
    }
  } finally {
    analyzing.value = false
  }
}

onMounted(async () => {
  const gameId = route.params.id
  if (!gameId) {
    bootError.value = 'Missing game id.'
    loading.value = false
    return
  }

  try {
    game.value = await gameApi.get(gameId)

    // Allow review of any game the user is part of. If it's still ongoing
    // (status !== 'finished'), the user probably wanted /game/:id instead —
    // gently redirect rather than show an empty replay.
    if (game.value.status !== 'finished') {
      router.replace(`/game/${gameId}`)
      return
    }

    positions.value = buildPositions(game.value.moves_pgn)
    currentPly.value = positions.value.length - 1  // jump to final position
  } catch (err) {
    if (err instanceof ApiError) {
      if (err.status === 401) { authStore.logout(); router.push('/login'); return }
      bootError.value = err.message
    } else {
      bootError.value = 'Could not load game.'
    }
    return
  } finally {
    loading.value = false
  }

  window.addEventListener('keydown', onKey)

  // Kick off background analysis. Don't await — the user can navigate the
  // game immediately, and the eval bar populates as results arrive.
  const fens = positions.value.map(p => p.fen)
  if (fens.length > 0) runAnalysis(fens)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@400;500;600&display=swap');

.review-page { min-height: 100vh; background: #1a1a1a; font-family: 'DM Sans', sans-serif; color: #e8e0d5; }
.topbar { display: flex; align-items: center; justify-content: space-between; padding: 0 2rem; height: 60px; background: #111; border-bottom: 1px solid #2e2e2e; }
.topbar-logo { display: flex; align-items: center; gap: 0.5rem; }
.logo-icon { font-size: 1.5rem; }
.logo-text { font-family: 'Playfair Display', serif; font-size: 1.2rem; }
.back-btn { color: #7cb662; text-decoration: none; font-size: 0.9rem; }

.centered { display: flex; align-items: center; justify-content: center; min-height: calc(100vh - 60px); color: #aaa; }
.boot-card { background: #252525; border-radius: 14px; padding: 2rem 2.5rem; display: flex; flex-direction: column; align-items: center; gap: 1rem; }

.review-layout { max-width: 880px; margin: 0 auto; padding: 1.5rem 1rem; display: flex; flex-direction: column; gap: 1rem; }

.game-header { background: #252525; border-radius: 12px; padding: 0.8rem 1rem; display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 1rem; }
.header-side { display: flex; }
.header-side-right { justify-content: flex-end; }
.header-player { display: flex; align-items: center; gap: 0.5rem; font-size: 0.95rem; }
.hp-color { width: 12px; height: 12px; border-radius: 50%; border: 1px solid #555; }
.hp-color.white-dot { background: #f0ebe0; }
.hp-color.black-dot { background: #1a1a1a; }
.hp-rating { color: #777; font-size: 0.8rem; font-variant-numeric: tabular-nums; }
.header-mid { text-align: center; }
.hm-tc { font-size: 0.78rem; color: #777; font-variant-numeric: tabular-nums; margin-bottom: 0.2rem; }
.hm-result { font-size: 0.9rem; font-weight: 600; padding: 0.15rem 0.6rem; border-radius: 5px; display: inline-block; }
.hm-result.white-wins { color: #f0ebe0; background: rgba(240,235,224,0.1); border: 1px solid rgba(240,235,224,0.25); }
.hm-result.black-wins { color: #888; background: rgba(120,120,120,0.15); border: 1px solid rgba(120,120,120,0.3); }
.hm-result.draw { color: #c9a227; background: rgba(201,162,39,0.15); }

.board-row { display: grid; grid-template-columns: 32px minmax(0, 1fr) 220px; gap: 0.8rem; align-items: start; }

.eval-bar { position: relative; height: min(480px, 80vw); background: #1a1a1a; border: 1px solid #2e2e2e; border-radius: 4px; overflow: hidden; }
.eval-fill-white { position: absolute; bottom: 0; left: 0; right: 0; background: #f0ebe0; transition: height 0.25s ease; }
.eval-label { position: absolute; top: 0.3rem; left: 50%; transform: translateX(-50%); font-size: 0.7rem; font-variant-numeric: tabular-nums; color: #1a1a1a; font-weight: 700; padding: 1px 4px; border-radius: 3px; background: rgba(0,0,0,0.0); }
.eval-label.on-white { color: #1a1a1a; }
.eval-label:not(.on-white) { color: #e8e0d5; }
.eval-overlay { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: #777; font-size: 1.2rem; letter-spacing: 0.2em; }

.board-wrap { width: 100%; aspect-ratio: 1; max-width: 480px; }
.board-wrap :deep(.cg-wrap) { width: 100%; height: 100%; }

.side-panel { background: #252525; border-radius: 12px; padding: 1rem; display: flex; flex-direction: column; gap: 0.8rem; min-height: 0; max-height: min(480px, 80vw); }
.panel-title { font-family: 'Playfair Display', serif; font-size: 1rem; color: #e8e0d5; }
.moves-grid { display: grid; grid-template-columns: 1.8rem 1fr 1fr; gap: 0.15rem 0.4rem; overflow-y: auto; flex: 1; min-height: 0; padding-right: 4px; }
.move-num { color: #555; font-size: 0.78rem; align-self: center; }
.move-san { font-size: 0.85rem; padding: 0.15rem 0.4rem; border-radius: 4px; cursor: pointer; user-select: none; font-variant-numeric: tabular-nums; }
.move-san:hover { background: #2e2e2e; }
.move-san.active { background: #5a9e42; color: #fff; }
.move-san.placeholder { cursor: default; }
.move-san.placeholder:hover { background: transparent; }
.empty-moves { grid-column: 1 / -1; color: #555; font-size: 0.85rem; text-align: center; padding: 1rem; }

.nav-controls { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.3rem; }
.nav-controls button { background: #1a1a1a; border: 1px solid #3a3a3a; color: #e8e0d5; padding: 0.45rem 0; border-radius: 6px; cursor: pointer; font-size: 0.95rem; }
.nav-controls button:hover:not(:disabled) { border-color: #5a9e42; }
.nav-controls button:disabled { opacity: 0.3; cursor: not-allowed; }
.ply-counter { font-size: 0.78rem; color: #777; text-align: center; font-variant-numeric: tabular-nums; }

.analysis-status { font-size: 0.78rem; color: #7cb662; text-align: center; margin-top: 0.2rem; }
.analysis-error { font-size: 0.78rem; color: #e05252; text-align: center; margin-top: 0.2rem; }

.btn-primary { padding: 0.6rem 1.2rem; background: #5a9e42; border: none; border-radius: 8px; color: #fff; font-family: inherit; font-size: 0.9rem; font-weight: 600; cursor: pointer; }
.btn-primary:hover { background: #7cb662; }

/* Mobile: stack everything */
@media (max-width: 720px) {
  .board-row { grid-template-columns: 24px 1fr; }
  .side-panel { grid-column: 1 / -1; max-height: 320px; }
  .eval-bar { height: min(380px, 80vw); }
}
</style>  