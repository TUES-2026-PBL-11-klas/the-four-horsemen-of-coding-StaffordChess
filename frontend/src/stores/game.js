import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useAuthStore } from './auth'


export const useGameStore = defineStore('game', () => {
  const gameId = ref(null)
  const whitePlayer = ref(null)
  const blackPlayer = ref(null)
  const timeControl = ref(null)
  const winnerId = ref(null)

  const fen = ref(null)
  const turn = ref('white')
  const whiteTime = ref(null)
  const blackTime = ref(null)
  const isCheck = ref(false)
  const isGameOver = ref(false)
  const result = ref(null)
  const drawOfferedBy = ref(null)

  const error = ref(null)

  const auth = useAuthStore()

  const myColor = computed(() => {
    const myId = auth.user?.id
    if (myId == null) return null
    if (whitePlayer.value?.id === myId) return 'white'
    if (blackPlayer.value?.id === myId) return 'black'
    return null
  })

  const me = computed(() => myColor.value === 'white' ? whitePlayer.value : blackPlayer.value)
  const opponent = computed(() => myColor.value === 'white' ? blackPlayer.value : whitePlayer.value)
  const myTime = computed(() => myColor.value === 'white' ? whiteTime.value : blackTime.value)
  const opponentTime = computed(() => myColor.value === 'white' ? blackTime.value : whiteTime.value)
  const isMyTurn = computed(() => !isGameOver.value && turn.value === myColor.value)

  const incomingDrawOffer = computed(() =>
    drawOfferedBy.value != null && drawOfferedBy.value !== auth.user?.id
  )
  const outgoingDrawOffer = computed(() =>
    drawOfferedBy.value != null && drawOfferedBy.value === auth.user?.id
  )

  function setMeta(data) {
    gameId.value = data.id
    whitePlayer.value = data.white_player
    blackPlayer.value = data.black_player
    timeControl.value = data.time_control
    winnerId.value = data.winner_id ?? null
    if (data.status === 'finished') {
      isGameOver.value = true
      result.value = data.result
    }
  }

  function setState(s) {
    if (s.game_id !== undefined) gameId.value = s.game_id
    if (s.fen !== undefined) fen.value = s.fen
    if (s.turn !== undefined) turn.value = s.turn
    if (s.white_time !== undefined) whiteTime.value = s.white_time
    if (s.black_time !== undefined) blackTime.value = s.black_time
    if (s.is_check !== undefined) isCheck.value = s.is_check
    if (s.is_game_over !== undefined) isGameOver.value = s.is_game_over
    if (s.result !== undefined) result.value = s.result
    if (s.winner_id !== undefined) winnerId.value = s.winner_id
    if (s.draw_offered_by !== undefined) drawOfferedBy.value = s.draw_offered_by
  }

  function setError(msg) { error.value = msg }
  function clearError() { error.value = null }

  function reset() {
    gameId.value = null
    whitePlayer.value = null
    blackPlayer.value = null
    timeControl.value = null
    winnerId.value = null
    fen.value = null
    turn.value = 'white'
    whiteTime.value = null
    blackTime.value = null
    isCheck.value = false
    isGameOver.value = false
    result.value = null
    drawOfferedBy.value = null
    error.value = null
  }

  return {
    gameId, whitePlayer, blackPlayer, timeControl, winnerId,
    fen, turn, whiteTime, blackTime, isCheck, isGameOver, result, drawOfferedBy, error,
    myColor, me, opponent, myTime, opponentTime, isMyTurn,
    incomingDrawOffer, outgoingDrawOffer,
    setMeta, setState, setError, clearError, reset,
  }
})