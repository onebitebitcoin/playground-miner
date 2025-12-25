const BASE_URL = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')

const defaultHeaders = {
  'Accept': 'application/json',
  'Content-Type': 'application/json'
}

async function handleResponse(response) {
  const contentType = response.headers.get('content-type') || ''
  const isJson = contentType.includes('application/json')
  const payload = isJson ? await response.json() : null

  if (!response.ok) {
    const message = (payload && payload.error) || `요청 실패(${response.status})`
    throw new Error(message)
  }

  if (!isJson) {
    throw new Error('JSON 응답이 필요합니다.')
  }

  return payload
}

export async function fetchHistoricalReturns({ prompt, quickRequests, contextKey, customAssets, includeDividends, signal }) {
  const body = {
    prompt: prompt || '',
    quick_requests: Array.isArray(quickRequests) ? quickRequests : [],
    custom_assets: Array.isArray(customAssets) ? customAssets : [],
    include_dividends: Boolean(includeDividends)
  }
  if (contextKey) {
    body.context_key = contextKey
  }

  const response = await fetch(`${BASE_URL}/api/finance/historical-returns`, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify(body),
    signal
  })

  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || 'AI 데이터 요청에 실패했습니다.')
  }
  return data
}

function createStreamChannelId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return `finance-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function createAbortError(message) {
  if (typeof DOMException !== 'undefined') {
    return new DOMException(message, 'AbortError')
  }
  const error = new Error(message)
  error.name = 'AbortError'
  return error
}

function buildFinanceWebSocketUrl(channelId) {
  const baseEnv = (import.meta.env.VITE_API_BASE || '').trim()
  if (baseEnv) {
    try {
      const base = new URL(baseEnv)
      base.protocol = base.protocol === 'https:' ? 'wss:' : 'ws:'
      const normalizedPath = base.pathname.replace(/\/$/, '')
      base.pathname = `${normalizedPath}/ws/finance`
      base.search = `channel=${encodeURIComponent(channelId)}`
      return base.toString()
    } catch (error) {
      console.warn('Invalid VITE_API_BASE for WebSocket:', error)
    }
  }

  if (typeof window === 'undefined') {
    throw new Error('WebSocket URL를 결정할 수 없습니다.')
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws/finance?channel=${encodeURIComponent(channelId)}`
}

export async function fetchHistoricalReturnsStream({ prompt, quickRequests, contextKey, customAssets, includeDividends, signal, onLog }) {
  /**
   * WebSocket-assisted streaming version of fetchHistoricalReturns.
   * Uses a dedicated per-request channel so each browser session receives only its own logs.
   */
  if (signal?.aborted) {
    throw createAbortError('요청이 취소되었습니다.')
  }

  const channelId = createStreamChannelId()
  const wsUrl = buildFinanceWebSocketUrl(channelId)

  const body = {
    prompt: prompt || '',
    quick_requests: Array.isArray(quickRequests) ? quickRequests : [],
    custom_assets: Array.isArray(customAssets) ? customAssets : [],
    include_dividends: Boolean(includeDividends),
    stream_channel: channelId,
    stream_transport: 'websocket'
  }
  if (contextKey) {
    body.context_key = contextKey
  }

  const fetchController = new AbortController()

  return await new Promise((resolve, reject) => {
    let finished = false
    let ws = null
    const abortHandlers = []

    const cleanup = () => {
      abortHandlers.forEach(({ target, handler }) => {
        target.removeEventListener('abort', handler)
      })
      abortHandlers.length = 0
      if (ws) {
        try {
          ws.close()
        } catch (_) {}
        ws = null
      }
    }

    const fail = (error) => {
      if (finished) return
      finished = true
      if (!fetchController.signal.aborted) {
        fetchController.abort()
      }
      cleanup()
      reject(error)
    }

    const succeed = (result) => {
      if (finished) return
      finished = true
      cleanup()
      resolve(result)
    }

    if (signal) {
      const abortHandler = () => {
        fail(createAbortError('요청이 취소되었습니다.'))
      }
      signal.addEventListener('abort', abortHandler, { once: true })
      abortHandlers.push({ target: signal, handler: abortHandler })
    }

    try {
      ws = new WebSocket(wsUrl)
    } catch (error) {
      fail(new Error('실시간 로그 채널을 열 수 없습니다.'))
      return
    }

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        if (payload.type === 'log') {
          if (onLog) onLog(payload.message)
        } else if (payload.type === 'error') {
          fail(new Error(payload.message || '분석 중 오류가 발생했습니다.'))
        }
      } catch (error) {
        console.warn('Failed to parse finance WebSocket message:', error)
      }
    }

    ws.onerror = () => {
      fail(new Error('실시간 로그 연결에 실패했습니다.'))
    }

    ws.onclose = () => {
      ws = null
    }

    ws.onopen = async () => {
      try {
        const response = await fetch(`${BASE_URL}/api/finance/historical-returns`, {
          method: 'POST',
          headers: defaultHeaders,
          body: JSON.stringify(body),
          signal: fetchController.signal
        })
        const data = await handleResponse(response)
        if (!data.ok) {
          throw new Error(data.error || 'AI 데이터 요청에 실패했습니다.')
        }
        succeed(data)
      } catch (error) {
        if (error.name === 'AbortError') {
          fail(error)
        } else {
          fail(new Error(error.message || 'AI 데이터 요청에 실패했습니다.'))
        }
      }
    }
  })
}

export async function fetchYearlyClosingPrices({ assets, startYear, endYear, signal }) {
  if (!Array.isArray(assets) || !assets.length) {
    throw new Error('자산 목록이 필요합니다.')
  }

  const body = {
    assets,
    start_year: startYear,
    end_year: endYear
  }

  const response = await fetch(`${BASE_URL}/api/finance/yearly-closing-prices`, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify(body),
    signal
  })

  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '연도별 종가 데이터를 불러오지 못했습니다.')
  }
  return data
}

export async function fetchAgentPrompts({ signal }) {
  const response = await fetch(`${BASE_URL}/api/finance/admin/agent-prompts`, {
    method: 'GET',
    headers: defaultHeaders,
    signal
  })

  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || 'Agent 프롬프트를 불러오지 못했습니다.')
  }
  return data
}

export async function resolveCustomAsset(name, { signal } = {}) {
  const body = { name: name || '' }
  const response = await fetch(`${BASE_URL}/api/finance/custom-asset/resolve`, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify(body),
    signal
  })

  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '종목 정보를 가져오지 못했습니다.')
  }
  return data.asset
}

export async function updateAgentPrompt({ agentType, name, description, systemPrompt, isActive, signal }) {
  const body = {}
  if (name !== undefined) body.name = name
  if (description !== undefined) body.description = description
  if (systemPrompt !== undefined) body.system_prompt = systemPrompt
  if (isActive !== undefined) body.is_active = isActive

  const response = await fetch(`${BASE_URL}/api/finance/admin/agent-prompts/${agentType}`, {
    method: 'PATCH',
    headers: defaultHeaders,
    body: JSON.stringify(body),
    signal
  })

  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || 'Agent 프롬프트 업데이트에 실패했습니다.')
  }
  return data
}

export async function deleteAgentPrompt({ agentType, signal }) {
  if (!agentType) {
    throw new Error('Agent 타입이 필요합니다.')
  }
  const response = await fetch(`${BASE_URL}/api/finance/admin/agent-prompts/${agentType}`, {
    method: 'DELETE',
    headers: defaultHeaders,
    signal
  })

  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || 'Agent 프롬프트 삭제에 실패했습니다.')
  }
  return data
}

export async function initializeAgentPrompts({ signal }) {
  const response = await fetch(`${BASE_URL}/api/finance/admin/agent-prompts`, {
    method: 'POST',
    headers: defaultHeaders,
    signal
  })

  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || 'Agent 프롬프트 초기화에 실패했습니다.')
  }
  return data
}

export async function fetchFinanceQuickCompareGroups({ signal } = {}) {
  const response = await fetch(`${BASE_URL}/api/finance/quick-compare-groups`, {
    method: 'GET',
    headers: defaultHeaders,
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '비교 종목 그룹을 불러오지 못했습니다.')
  }
  return data.groups || []
}

export async function fetchAdminFinanceQuickCompareGroups({ signal } = {}) {
  const response = await fetch(`${BASE_URL}/api/finance/admin/quick-compare-groups`, {
    method: 'GET',
    headers: defaultHeaders,
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '비교 종목 그룹을 불러오지 못했습니다.')
  }
  return data.groups || []
}

export async function createAdminFinanceQuickCompareGroup(payload, { signal } = {}) {
  const response = await fetch(`${BASE_URL}/api/finance/admin/quick-compare-groups`, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify(payload || {}),
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '비교 종목 그룹을 추가하지 못했습니다.')
  }
  return data.group
}

export async function updateAdminFinanceQuickCompareGroup(id, payload, { signal } = {}) {
  if (!id) throw new Error('그룹 ID가 필요합니다.')
  const response = await fetch(`${BASE_URL}/api/finance/admin/quick-compare-groups/${id}`, {
    method: 'PATCH',
    headers: defaultHeaders,
    body: JSON.stringify(payload || {}),
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '비교 종목 그룹을 업데이트하지 못했습니다.')
  }
  return data.group
}

export async function deleteAdminFinanceQuickCompareGroup(id, { signal } = {}) {
  if (!id) throw new Error('그룹 ID가 필요합니다.')
  const response = await fetch(`${BASE_URL}/api/finance/admin/quick-compare-groups/${id}`, {
    method: 'DELETE',
    headers: defaultHeaders,
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '비교 종목 그룹을 삭제하지 못했습니다.')
  }
  return true
}

export async function fetchAdminPriceCache({ offset = 0, limit = 10, search = '', signal } = {}) {
  const params = new URLSearchParams({
    offset: offset.toString(),
    limit: limit.toString()
  })
  if (search) {
    params.append('search', search)
  }
  const response = await fetch(`${BASE_URL}/api/finance/admin/price-cache?${params.toString()}`, {
    method: 'GET',
    headers: defaultHeaders,
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '캐시된 종목 목록을 불러오지 못했습니다.')
  }
  return data
}

export async function deleteAdminPriceCache(id, { signal } = {}) {
  if (!id) throw new Error('캐시 ID가 필요합니다.')
  const response = await fetch(`${BASE_URL}/api/finance/admin/price-cache/${id}`, {
    method: 'DELETE',
    headers: defaultHeaders,
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '캐시를 삭제하지 못했습니다.')
  }
  return true
}

export async function addSingleAsset({ assetId, startYear, endYear, calculationMethod, includeDividends, signal }) {
  if (!assetId) {
    throw new Error('자산 ID가 필요합니다.')
  }

  const body = {
    asset_id: assetId,
    start_year: startYear,
    end_year: endYear,
    calculation_method: calculationMethod || 'cagr',
    include_dividends: Boolean(includeDividends)
  }

  const response = await fetch(`${BASE_URL}/api/finance/add-single-asset`, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify(body),
    signal
  })

  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '자산 데이터를 불러오지 못했습니다.')
  }

  return {
    series: data.series,
    chartDataTableEntry: data.chart_data_table_entry
  }
}
