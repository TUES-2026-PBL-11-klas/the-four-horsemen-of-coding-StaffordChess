import { ref, onUnmounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { wsBaseUrl } from '../api/http'

export function useLobbySocket() {
  const ws = ref(null)
  const connected = ref(false)
  const handlers = []

  function onEvent(cb) 
  {
    handlers.push(cb)
  }

  function connect() 
  {
    const auth = useAuthStore()
    if(!auth.token) return

    const wsUrl = `${wsBaseUrl()}/lobby/ws?token=${auth.token}`
    const sock = new WebSocket(wsUrl)
    ws.value = sock

    sock.onopen = () => { connected.value = true }
    sock.onmessage = (e) => {
      let msg
      try 
      {
        msg = JSON.parse(e.data)
      }
      catch
      {
        return
      }
      for(const cb of handlers) 
        cb(msg)
    }
    sock.onclose = () => { connected.value = false }
    sock.onerror = () => { connected.value = false }
  }

  function disconnect() {
    ws.value?.close()
    ws.value = null
  }

  onUnmounted(disconnect)

  return { connected, connect, disconnect, onEvent }
}