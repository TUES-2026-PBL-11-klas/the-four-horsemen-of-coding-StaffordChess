import { ref, onUnmounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { apiBaseUrl } from '../api/http'


export function useLobbySocket() {
  const ws = ref(null)
  const connected = ref(false)
  const lastEvent = ref(null)

  function connect() {
    const auth = useAuthStore()
    if (!auth.token) return

    const wsUrl = `${apiBaseUrl.replace(/^http/, 'ws')}/lobby/ws?token=${auth.token}`

    const sock = new WebSocket(wsUrl)
    ws.value = sock

    sock.onopen = () => { connected.value = true }
    sock.onmessage = (e) => {
      try {
        lastEvent.value = JSON.parse(e.data)
      } catch {
      }
    }
    sock.onclose = () => { connected.value = false }
    sock.onerror = () => { connected.value = false }
  }

  function disconnect() {
    ws.value?.close()
    ws.value = null
  }

  onUnmounted(disconnect)

  return { connected, lastEvent, connect, disconnect }
}