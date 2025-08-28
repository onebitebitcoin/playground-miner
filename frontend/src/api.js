// Use same-origin by default in production, override with VITE_API_BASE for local dev
const BASE_URL = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')

export async function fetchStatus() {
  const res = await fetch(`${BASE_URL}/api/status`, { headers: { 'Accept': 'application/json' } })
  if (!res.ok) throw new Error(`status ${res.status}`)
  const ct = (res.headers.get('content-type') || '').toLowerCase()
  if (!ct.includes('application/json')) {
    const body = await res.text()
    throw new Error(`non-json response: ${res.status} ${ct} ${body.slice(0,120)}`)
  }
  return res.json()
}

export async function fetchBlocks() {
  const res = await fetch(`${BASE_URL}/api/blocks`, { headers: { 'Accept': 'application/json' } })
  if (!res.ok) throw new Error(`blocks ${res.status}`)
  const ct = (res.headers.get('content-type') || '').toLowerCase()
  if (!ct.includes('application/json')) {
    const body = await res.text()
    throw new Error(`non-json response: ${res.status} ${ct} ${body.slice(0,120)}`)
  }
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
    if (!res.ok) return { ok: false, error: `서버 오류(${res.status})` }
    const ct = (res.headers.get('content-type') || '').toLowerCase()
    if (!ct.includes('application/json')) return { ok: false, error: '서버 응답 형식 오류' }
    return await res.json()
  } catch (e) {
    return { ok: false, error: '요청 실패(네트워크)' }
  }
}

export function connectBlockStream(onMessage, nickname) {
  const q = nickname ? `?nick=${encodeURIComponent(nickname)}` : ''
  const url = `${BASE_URL}/api/stream${q}`
  const es = new EventSource(url)
  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      onMessage(data)
    } catch (_) {}
  }
  return es
}

export function connectEvents(onMessage, nickname) {
  // Try WebSocket first
  try {
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const qs = nickname ? `?nick=${encodeURIComponent(nickname)}` : ''
    const wsUrl = `${proto}://${window.location.host}/ws/stream${qs}`
    const ws = new WebSocket(wsUrl)
    ws.onmessage = (e) => {
      try { onMessage(JSON.parse(e.data)) } catch (_) {}
    }
    return { kind: 'ws', socket: ws }
  } catch (_) {}
  // Fallback to SSE
  const es = connectBlockStream(onMessage, nickname)
  return { kind: 'sse', socket: es }
}

export async function apiRegisterNickname(nickname) {
  const res = await fetch(`${BASE_URL}/api/register_nick`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify({ nickname })
  })
  if (!res.ok) throw new Error(`register ${res.status}`)
  return res.json()
}

export async function apiInitReset(token) {
  const res = await fetch(`${BASE_URL}/api/init_reset`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify({ token })
  })
  if (!res.ok) throw new Error(`init ${res.status}`)
  return res.json()
}
