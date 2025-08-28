const BASE_URL = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8002'

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
