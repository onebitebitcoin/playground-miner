import { ref, onUnmounted } from 'vue'
import type { WebSocketMessage } from '@/types'

export function useWebSocket() {
  const isConnected = ref(false)
  const connectionType = ref<'ws' | 'sse' | null>(null)
  
  let socket: WebSocket | EventSource | null = null

  function connect(
    onMessage: (message: WebSocketMessage) => void,
    nickname?: string
  ) {
    const query = nickname ? `?nick=${encodeURIComponent(nickname)}` : ''
    
    // Try WebSocket first
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
      const wsUrl = `${protocol}://${window.location.host}/ws/stream${query}`
      
      const ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        isConnected.value = true
        connectionType.value = 'ws'
      }
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          onMessage(data)
        } catch (error) {
          console.warn('Failed to parse WebSocket message:', error)
        }
      }
      
      ws.onclose = () => {
        isConnected.value = false
        connectionType.value = null
      }
      
      ws.onerror = () => {
        isConnected.value = false
        connectionType.value = null
        // Fallback to SSE
        connectSSE(onMessage, nickname)
      }
      
      socket = ws
      return { kind: 'ws' as const, socket: ws }
    } catch (error) {
      // Fallback to SSE
      return connectSSE(onMessage, nickname)
    }
  }

  function connectSSE(
    onMessage: (message: WebSocketMessage) => void,
    nickname?: string
  ) {
    const query = nickname ? `?nick=${encodeURIComponent(nickname)}` : ''
    const baseUrl = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')
    const url = `${baseUrl}/api/stream${query}`
    
    const eventSource = new EventSource(url)
    
    eventSource.onopen = () => {
      isConnected.value = true
      connectionType.value = 'sse'
    }
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessage(data)
      } catch (error) {
        console.warn('Failed to parse SSE message:', error)
      }
    }
    
    eventSource.onerror = () => {
      isConnected.value = false
      connectionType.value = null
    }
    
    socket = eventSource
    return { kind: 'sse' as const, socket: eventSource }
  }

  function disconnect() {
    if (socket) {
      if (socket instanceof WebSocket) {
        socket.close()
      } else if (socket instanceof EventSource) {
        socket.close()
      }
      socket = null
      isConnected.value = false
      connectionType.value = null
    }
  }

  // Auto cleanup on unmount
  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected: readonly(isConnected),
    connectionType: readonly(connectionType),
    connect,
    disconnect
  }
}

// Legacy compatibility exports
export function connectEvents(
  onMessage: (message: WebSocketMessage) => void,
  nickname?: string
) {
  const { connect } = useWebSocket()
  return connect(onMessage, nickname)
}

export function connectBlockStream(
  onMessage: (message: WebSocketMessage) => void,
  nickname?: string
) {
  const query = nickname ? `?nick=${encodeURIComponent(nickname)}` : ''
  const baseUrl = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')
  const url = `${baseUrl}/api/stream${query}`
  
  const es = new EventSource(url)
  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      onMessage(data)
    } catch (_) {}
  }
  return es
}