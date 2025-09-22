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

export async function apiCheckNickname(nickname) {
  const res = await fetch(`${BASE_URL}/api/check_nick?nickname=${encodeURIComponent(nickname)}`, {
    method: 'GET',
    headers: { 'Accept': 'application/json' }
  })
  if (!res.ok) throw new Error(`check ${res.status}`)
  return res.json()
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

// Mnemonic API functions
export async function apiRequestMnemonic() {
  try {
    const res = await fetch(`${BASE_URL}/api/mnemonic/request`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, mnemonic: data.mnemonic, id: data.id, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiGenerateMnemonic() {
  try {
    const res = await fetch(`${BASE_URL}/api/mnemonic/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, mnemonic: data.mnemonic, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiSaveMnemonic(mnemonic, username) {
  try {
    const res = await fetch(`${BASE_URL}/api/mnemonic/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ mnemonic, username })
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, id: data.id, message: data.message, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiGetAdminMnemonics(username) {
  try {
    const res = await fetch(`${BASE_URL}/api/mnemonic/admin?username=${encodeURIComponent(username)}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, mnemonics: data.mnemonics, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

// Exchange rates API functions
export async function apiGetExchangeRates() {
  try {
    const res = await fetch(`${BASE_URL}/api/exchange-rates`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, rates: data.rates, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiGetAdminExchangeRates(username) {
  try {
    const res = await fetch(`${BASE_URL}/api/exchange-rates/admin?username=${encodeURIComponent(username)}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, rates: data.rates, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiUpdateExchangeRate(username, exchange, feeRate, isEvent, description, eventDetails = '') {
  try {
    const res = await fetch(`${BASE_URL}/api/exchange-rates/admin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        username,
        exchange,
        fee_rate: feeRate,
        is_event: isEvent,
        description,
        event_details: eventDetails
      })
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, rate: data.rate, created: data.created, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

// Withdrawal Fees API
export async function apiGetWithdrawalFees() {
  try {
    const res = await fetch(`${BASE_URL}/api/withdrawal-fees`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, fees: data.fees, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiGetAdminWithdrawalFees(username) {
  try {
    const res = await fetch(`${BASE_URL}/api/withdrawal-fees/admin?username=${encodeURIComponent(username)}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, fees: data.fees, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiUpdateWithdrawalFee(username, exchange, withdrawalType, feeBtc, description) {
  try {
    const res = await fetch(`${BASE_URL}/api/withdrawal-fees/admin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        username,
        exchange,
        withdrawal_type: withdrawalType,
        fee_btc: feeBtc,
        description
      })
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, fee: data.fee, created: data.created, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

// Lightning Services API
export async function apiGetLightningServices() {
  try {
    const res = await fetch(`${BASE_URL}/api/lightning-services`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, services: data.services, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiGetAdminLightningServices(username) {
  try {
    const res = await fetch(`${BASE_URL}/api/lightning-services/admin?username=${encodeURIComponent(username)}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, services: data.services, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiUpdateLightningService(username, service, feeRate, isKyc, isCustodial, description) {
  try {
    const res = await fetch(`${BASE_URL}/api/lightning-services/admin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        username,
        service,
        fee_rate: feeRate,
        is_kyc: isKyc,
        is_custodial: isCustodial,
        description
      })
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, service: data.service, created: data.created, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

// New routing system API

export async function apiGetServiceNodes(username) {
  try {
    const res = await fetch(`${BASE_URL}/api/service-nodes/admin?username=${encodeURIComponent(username)}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, nodes: data.nodes, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiUpdateServiceNode(username, service, displayName, isKyc, isCustodial, isEnabled, description, websiteUrl) {
  try {
    const res = await fetch(`${BASE_URL}/api/service-nodes/admin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        username,
        service,
        display_name: displayName,
        is_kyc: isKyc,
        is_custodial: isCustodial,
        is_enabled: isEnabled,
        description,
        website_url: websiteUrl
      })
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, node: data.node, created: data.created, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiGetRoutes(username) {
  try {
    const res = await fetch(`${BASE_URL}/api/routes/admin?username=${encodeURIComponent(username)}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, routes: data.routes, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiCreateRoute(username, sourceId, destinationId, routeType, feeRate, feeFixed, isEnabled, description) {
  try {
    const res = await fetch(`${BASE_URL}/api/routes/admin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        username,
        source_id: sourceId,
        destination_id: destinationId,
        route_type: routeType,
        fee_rate: feeRate,
        fee_fixed: feeFixed,
        is_enabled: isEnabled,
        description
      })
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, route: data.route, created: data.created, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiDeleteRoute(username, routeId) {
  try {
    const res = await fetch(`${BASE_URL}/api/routes/admin`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        username,
        id: routeId
      })
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiGetOptimalPaths(maxPaths = 300) {
  try {
    const params = new URLSearchParams({ max_paths: String(maxPaths || 300) })
    const res = await fetch(`${BASE_URL}/api/optimal-paths?${params.toString()}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, paths: data.paths, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

// Routing snapshot API
export async function apiGetRoutingSnapshotInfo() {
  try {
    const res = await fetch(`${BASE_URL}/api/routing-snapshot`, { method: 'GET', headers: { 'Accept': 'application/json' } })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, info: data }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiSaveRoutingSnapshot(username) {
  try {
    const res = await fetch(`${BASE_URL}/api/routing-snapshot`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ username, action: 'save' })
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, data }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiResetRoutingFromSnapshot(username) {
  try {
    const res = await fetch(`${BASE_URL}/api/routing-snapshot`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ username, action: 'reset' })
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, data }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}
