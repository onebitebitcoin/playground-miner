// Use same-origin by default in production, override with VITE_API_BASE for local dev
const BASE_URL = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')
export const API_BASE_URL = BASE_URL

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
export async function apiRequestMnemonic(username) {
  try {
    const res = await fetch(`${BASE_URL}/api/mnemonic/request`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ username })
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

// Admin: delete mnemonic
export async function apiDeleteMnemonic(username, id) {
  try {
    const res = await fetch(`${BASE_URL}/api/mnemonic/admin/delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ username, id })
    })
    let data = null
    try { data = await res.json() } catch (_) {}
    if (!res.ok) return { success: false, error: data?.error || `서버 오류(${res.status})` }
    return { success: data.ok, deleted: data.deleted, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

// Admin: unassign a mnemonic by id
export async function apiUnassignMnemonic(username, id) {
  try {
    const res = await fetch(`${BASE_URL}/api/mnemonic/admin/unassign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ username, id })
    })
    let data = null
    try { data = await res.json() } catch (_) {}
    if (!res.ok) return { success: false, error: data?.error || `서버 오류(${res.status})` }
    return { success: data.ok, mnemonic: data.mnemonic, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

// Admin: get BIP84 account zpub for a mnemonic id
export async function apiGetMnemonicZpub(username, id, account = 0) {
  try {
    const params = new URLSearchParams({ id: String(id), account: String(account), username })
    const res = await fetch(`${BASE_URL}/api/mnemonic/admin/xpub?${params.toString()}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    })
    let data = null
    try { data = await res.json() } catch (_) {}
    if (!res.ok) return { success: false, error: data?.error || `서버 오류(${res.status})` }
    return { success: data.ok, zpub: data.zpub, account: data.account, master_fingerprint: data.master_fingerprint, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

// Admin: get a bech32 BIP84 address for a mnemonic id (default index 0)
export async function apiGetMnemonicAddress(username, id, { index = 0, account = 0, change = 0 } = {}) {
  try {
    const params = new URLSearchParams({ id: String(id), index: String(index), account: String(account), change: String(change), username })
    const res = await fetch(`${BASE_URL}/api/mnemonic/admin/address?${params.toString()}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    })
    let data = null
    try { data = await res.json() } catch (_) {}
    if (!res.ok) return { success: false, error: data?.error || `서버 오류(${res.status})` }
    return { success: data.ok, address: data.address, index: data.index, account: data.account, change: data.change, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

// Validate a BIP39 mnemonic (server-side, normalized)
export async function apiValidateMnemonic(mnemonic) {
  try {
    const res = await fetch(`${BASE_URL}/api/mnemonic/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ mnemonic })
    })
    let data = null
    try { data = await res.json() } catch (_) {}
    if (!res.ok) return { success: false, error: data?.error || `서버 오류(${res.status})`, unknown_words: (data && data.unknown_words) || [] }
    return { success: data.ok, valid: data.valid, word_count: data.word_count, normalized: data.normalized, unknown_words: data.unknown_words || [], error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

// Mnemonic balance APIs
export async function apiGetMnemonicBalance(id) {
  try {
    const res = await fetch(`${BASE_URL}/api/mnemonic/balance?id=${encodeURIComponent(String(id))}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    })
    let data = null
    try { data = await res.json() } catch (_) {}
    if (!res.ok) return { success: false, error: data?.error || `서버 오류(${res.status})` }
    return { success: data.ok, id: data.id, balance_sats: data.balance_sats, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiSetMnemonicBalance(username, id, balanceSats) {
  try {
    const res = await fetch(`${BASE_URL}/api/mnemonic/admin/balance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ username, id, balance_sats: balanceSats })
    })
    let data = null
    try { data = await res.json() } catch (_) {}
    if (!res.ok) return { success: false, error: data?.error || `서버 오류(${res.status})` }
    return { success: data.ok, mnemonic: data.mnemonic, error: data.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

// On-chain balance via backend derivation + explorer
export async function apiGetOnchainBalanceById(id, { count = 20, account = 0, bothChains = true, includeMempool = true } = {}) {
  try {
    const params = new URLSearchParams({
      id: String(id),
      count: String(count),
      account: String(account),
      both_chains: bothChains ? '1' : '0',
      include_mempool: includeMempool ? '1' : '0',
    })
    const res = await fetch(`${BASE_URL}/api/mnemonic/balance/onchain?${params.toString()}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    })
    let data = null
    try { data = await res.json() } catch (_) {}

    // Handle specific HTTP status codes
    if (!res.ok) {
      const errorMsg = data?.error || `서버 오류(${res.status})`
      const errorType = data?.error_type || 'unknown'

      // Provide more context for specific errors
      if (res.status === 429 || errorType === 'rate_limit') {
        return { success: false, error: errorMsg, error_type: 'rate_limit', status: res.status }
      } else if (res.status === 504 || errorType === 'timeout') {
        return { success: false, error: errorMsg, error_type: 'timeout', status: res.status }
      } else if (res.status === 502 || res.status === 503 || errorType === 'service_unavailable') {
        return { success: false, error: errorMsg, error_type: 'service_unavailable', status: res.status }
      }

      return { success: false, error: errorMsg, error_type: errorType, status: res.status }
    }

    return { success: data.ok, total_sats: data.total_sats, by_address: data.by_address, count: data.count, error: data.error }
  } catch (e) {
    // Network or fetch errors
    if (e.name === 'TypeError' && e.message.includes('fetch')) {
      return { success: false, error: '네트워크 연결 실패', error_type: 'network' }
    }
    return { success: false, error: e.message || '네트워크 오류', error_type: 'network' }
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

// Wallet password APIs
export async function apiSetWalletPassword(password) {
  try {
    const res = await fetch(`${BASE_URL}/api/wallet/password/admin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ password })
    })
    let data = null
    try { data = await res.json() } catch (_) {}
    if (!res.ok) return { success: false, error: data?.error || `서버 오류(${res.status})` }
    return { success: data.ok, wallet_password_set: data.wallet_password_set }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiCheckWalletPassword(password) {
  try {
    const res = await fetch(`${BASE_URL}/api/wallet/password/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ password })
    })
    let data = null
    try { data = await res.json() } catch (_) {}
    if (!res.ok) return { success: false, error: data?.error || `서버 오류(${res.status})` }
    return { success: data.ok, error: data?.error }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiGetWalletPassword() {
  try {
    const res = await fetch(`${BASE_URL}/api/wallet/password/admin/get`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    })
    let data = null
    try { data = await res.json() } catch (_) {}
    if (!res.ok) return { success: false, error: data?.error || `서버 오류(${res.status})` }
    return { success: data.ok, password: data.password }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

// Kingstone wallet APIs
export async function apiGetKingstoneWallets(username) {
  try {
    const params = new URLSearchParams({ username })
    const res = await fetch(`${BASE_URL}/api/kingstone/wallets?${params.toString()}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    })
    let data = null
    try { data = await res.json() } catch (_) {}
    if (!res.ok) return { success: false, error: data?.error || `서버 오류(${res.status})` }
    return {
      success: data?.ok ?? false,
      wallets: data?.wallets || [],
      count: data?.count ?? 0,
      limit: data?.limit ?? 3,
      error: data?.error
    }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiVerifyKingstonePin(username, pin) {
  try {
    const res = await fetch(`${BASE_URL}/api/kingstone/pin/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ username, pin })
    })
    let data = null
    try { data = await res.json() } catch (_) {}
    if (!res.ok) return { success: false, error: data?.error || `서버 오류(${res.status})`, code: data?.code }
    return {
      success: data?.ok ?? false,
      wallet: data?.wallet || null,
      error: data?.error,
      code: data?.code
    }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiRegisterKingstonePin(username, pin, { walletName = '', mnemonic = '' } = {}) {
  try {
    const payload = { username, pin }
    if (walletName) payload.wallet_name = walletName
    if (mnemonic) payload.mnemonic = mnemonic
    const res = await fetch(`${BASE_URL}/api/kingstone/pin/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify(payload)
    })
    let data = null
    try { data = await res.json() } catch (_) {}
    if (!res.ok) return { success: false, error: data?.error || `서버 오류(${res.status})`, code: data?.code }
    return {
      success: data?.ok ?? false,
      wallet: data?.wallet || null,
      limit: data?.limit ?? 3,
      error: data?.error,
      code: data?.code
    }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiGetKingstoneWalletAddress(username, walletId, { index = 0, account = 0, change = 0 } = {}) {
  try {
    const params = new URLSearchParams({
      username,
      wallet_id: walletId,
      index: String(index),
      account: String(account),
      change: String(change)
    })
    const res = await fetch(`${BASE_URL}/api/kingstone/wallet/address?${params.toString()}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    })
    let data = null
    try { data = await res.json() } catch (_) {}
    if (!res.ok) return { success: false, error: data?.error || `서버 오류(${res.status})` }
    return {
      success: data?.ok ?? false,
      address: data?.address || '',
      index: data?.index ?? 0,
      account: data?.account ?? 0,
      change: data?.change ?? 0,
      error: data?.error
    }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiGetKingstoneAdminWallets(username) {
  try {
    const params = new URLSearchParams({ username })
    const res = await fetch(`${BASE_URL}/api/kingstone/admin/wallets?${params.toString()}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    })
    let data = null
    try { data = await res.json() } catch (_) {}
    if (!res.ok) return { success: false, error: data?.error || `서버 오류(${res.status})` }
    return {
      success: data?.ok ?? false,
      wallets: data?.wallets || [],
      error: data?.error
    }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiAdminDeleteKingstoneWallet(username, walletId) {
  try {
    const res = await fetch(`${BASE_URL}/api/kingstone/wallet/delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ username, wallet_id: walletId })
    })
    let data = null
    try { data = await res.json() } catch (_) {}
    if (!res.ok) return { success: false, error: data?.error || `서버 오류(${res.status})` }
    return { success: data?.ok ?? false, error: data?.error }
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

export async function apiUpdateServiceNode(username, service, displayName, nodeType, isKyc, isCustodial, isEnabled, description, websiteUrl) {
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
        node_type: nodeType,
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

export async function apiCreateRoute(id, username, sourceId, destinationId, routeType, feeRate, feeFixed, feeFixedCurrency, isEnabled, description, isEvent = false, eventTitle = '', eventDescription = '', eventUrl = '') {
  try {
    const payload = {
      username,
      source_id: sourceId,
      destination_id: destinationId,
      route_type: routeType,
      fee_rate: feeRate,
      fee_fixed: feeFixed,
      fee_fixed_currency: feeFixedCurrency,
      is_enabled: isEnabled,
      description,
      is_event: isEvent,
      event_title: eventTitle,
      event_description: eventDescription,
      event_url: eventUrl
    }
    if (id) {
      payload.id = id
    }

    const res = await fetch(`${BASE_URL}/api/routes/admin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(payload)
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

export async function apiGetSidebarConfig() {
  try {
    const res = await fetch(`${BASE_URL}/api/sidebar-config`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, config: data.config }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}

export async function apiUpdateSidebarConfig(username, config) {
  try {
    const res = await fetch(`${BASE_URL}/api/sidebar-config/admin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ username, ...config })
    })
    if (!res.ok) return { success: false, error: `서버 오류(${res.status})` }
    const data = await res.json()
    return { success: data.ok, config: data.config }
  } catch (e) {
    return { success: false, error: '네트워크 오류' }
  }
}
