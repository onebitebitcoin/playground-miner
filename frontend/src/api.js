// Use same-origin by default in production, override with VITE_API_BASE for local dev
const BASE_URL = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')

export async function fetchStatus() {
  const res = await fetch(`${BASE_URL}/api/status`, { headers: { 'Accept': 'application/json' } })
  return res.json()
}

export async function fetchBlocks() {
  const res = await fetch(`${BASE_URL}/api/blocks`, { headers: { 'Accept': 'application/json' } })
  return res.json()
}

export async function postMine({ miner, nonce }) {
  try {
    const res = await fetch(`${BASE_URL}/api/mine`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ miner, nonce })
    })
    return await res.json()
  } catch (e) {
    return { ok: false, error: '요청 실패(네트워크)' }
  }
}

export function connectBlockStream(onMessage) {
  const url = `${BASE_URL}/api/stream`
  const es = new EventSource(url)
  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      onMessage(data)
    } catch (_) {}
  }
  return es
}

export function connectEvents(onMessage) {
  // Try WebSocket first
  try {
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const wsUrl = `${proto}://${window.location.host}/ws/stream`
    const ws = new WebSocket(wsUrl)
    ws.onmessage = (e) => {
      try { onMessage(JSON.parse(e.data)) } catch (_) {}
    }
    return { kind: 'ws', socket: ws }
  } catch (_) {}
  // Fallback to SSE
  const es = connectBlockStream(onMessage)
  return { kind: 'sse', socket: es }
}
