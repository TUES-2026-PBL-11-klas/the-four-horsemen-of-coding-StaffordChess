import { ref, onUnmounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useGameStore } from '../stores/game'
import { apiBaseUrl } from '../api/http'


export function useGameSocket() 
{
  const ws = ref(null)
  const connected = ref(false)
  let syncTimer = null

  function connect(gameId) {
    const auth = useAuthStore()
    const store = useGameStore()
    if (!auth.token) return

    const url = `${apiBaseUrl.replace(/^http/, 'ws')}/game/${gameId}?token=${auth.token}`
    const sock = new WebSocket(url)
    ws.value = sock

    sock.onopen = () => 
    {
      connected.value = true
      store.clearError()
      syncTimer = setInterval(() => 
      {
        if(!store.isGameOver) send({ type: 'sync' })
      }, 3000)
    }

    sock.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        if (msg.error) {
          store.setError(msg.error)
          return
        }
        store.setState(msg)
      } catch {
      }
    }

    sock.onclose = (e) => {
      connected.value = false
      clearInterval(syncTimer)
      syncTimer = null
      if (e.code === 4001) store.setError('Authentication failed.')
      else if (e.code === 4003) store.setError('You are not a player in this game.')
      else if (e.code === 4004) store.setError('Game not found.')
    }

    sock.onerror = () => {
      connected.value = false
    }
  }

  function send(payload) {
    if (ws.value?.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify(payload))
    }
  }

  function sendMove(from, to, promotion = null) {
    const msg = { type: 'move', from, to }
    if (promotion) msg.promotion = promotion
    send(msg)
  }

  function sendResign() { send({ type: 'resign' }) }

  function sendDrawOffer() { send({ type: 'draw_offer' }) }
  function sendDrawAccept() { send({ type: 'draw_accept' }) }
  function sendDrawDecline() { send({ type: 'draw_decline' }) }

  function disconnect() {
    clearInterval(syncTimer)
    syncTimer = null
    ws.value?.close()
    ws.value = null
  }

  onUnmounted(disconnect)

  return { connected, connect, disconnect, sendMove, sendResign, sendDrawOffer, sendDrawAccept, sendDrawDecline }
}