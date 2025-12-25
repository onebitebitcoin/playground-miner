const BASE_URL = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')

const defaultHeaders = {
  'Accept': 'application/json',
  'Content-Type': 'application/json'
}

function resolveApiUrl(path = '') {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  if (BASE_URL) {
    return `${BASE_URL}${normalizedPath}`
  }
  if (typeof window !== 'undefined' && window.location?.origin) {
    return `${window.location.origin}${normalizedPath}`
  }
  throw new Error('API base URL를 결정할 수 없습니다.')
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

  const response = await fetch(resolveApiUrl('/api/finance/historical-returns'), {
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

function createAbortError(message) {
  if (typeof DOMException !== 'undefined') {
    return new DOMException(message, 'AbortError')
  }
  const error = new Error(message)
  error.name = 'AbortError'
  return error
}

function parseSseChunk(chunk, onLog) {
  const lines = chunk.split('\n')
  const dataLine = lines.find((line) => line.startsWith('data:'))
  if (!dataLine) return null

  let payload = null
  try {
    payload = JSON.parse(dataLine.replace(/^data:\s*/, ''))
  } catch (error) {
    console.warn('Failed to parse SSE payload:', error, dataLine)
    return null
  }

  if (payload.type === 'log') {
    if (payload.message && onLog) {
      onLog(payload.message)
    }
    return null
  }
  if (payload.type === 'error') {
    throw new Error(payload.message || '분석 중 오류가 발생했습니다.')
  }
  if (payload.type === 'result') {
    return payload.data || null
  }
  return null
}

export async function fetchHistoricalReturnsStream({ prompt, quickRequests, contextKey, customAssets, includeDividends, signal, onLog }) {
  if (signal?.aborted) {
    throw createAbortError('요청이 취소되었습니다.')
  }

  const controller = new AbortController()
  const abortHandlers = []

  const cleanup = () => {
    abortHandlers.forEach(({ target, handler }) => {
      target.removeEventListener('abort', handler)
    })
    abortHandlers.length = 0
  }

  if (signal) {
    const abortHandler = () => {
      controller.abort()
    }
    signal.addEventListener('abort', abortHandler, { once: true })
    abortHandlers.push({ target: signal, handler: abortHandler })
  }

  const body = {
    prompt: prompt || '',
    quick_requests: Array.isArray(quickRequests) ? quickRequests : [],
    custom_assets: Array.isArray(customAssets) ? customAssets : [],
    include_dividends: Boolean(includeDividends)
  }
  if (contextKey) {
    body.context_key = contextKey
  }

  const url = new URL(resolveApiUrl('/api/finance/historical-returns'))
  url.searchParams.set('stream', '1')

  try {
    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: defaultHeaders,
      body: JSON.stringify(body),
      signal: controller.signal
    })

    if (!response.ok) {
      const errorPayload = await response.json().catch(() => ({}))
      throw new Error(errorPayload.error || `요청 실패(${response.status})`)
    }

    if (!response.body || typeof response.body.getReader !== 'function') {
      throw new Error('브라우저가 스트리밍 응답을 지원하지 않습니다.')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    let finalResult = null

    const processBuffer = () => {
      let boundary = buffer.indexOf('\n\n')
      while (boundary !== -1) {
        const chunk = buffer.slice(0, boundary).trim()
        buffer = buffer.slice(boundary + 2)
        if (chunk) {
          const parsed = parseSseChunk(chunk, onLog)
          if (parsed) {
            finalResult = parsed
          }
        }
        boundary = buffer.indexOf('\n\n')
      }
    }

    while (true) {
      const { value, done } = await reader.read()
      if (done) {
        buffer += decoder.decode()
        processBuffer()
        break
      }
      buffer += decoder.decode(value, { stream: true })
      processBuffer()
    }

    if (buffer.trim()) {
      const parsed = parseSseChunk(buffer.trim(), onLog)
      if (parsed) {
        finalResult = parsed
      }
    }

    if (!finalResult) {
      throw new Error('분석 결과를 받지 못했습니다.')
    }

    return finalResult
  } catch (error) {
    if (error.name === 'AbortError') {
      throw createAbortError('요청이 취소되었습니다.')
    }
    throw error
  } finally {
    cleanup()
  }
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

  const response = await fetch(resolveApiUrl('/api/finance/yearly-closing-prices'), {
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
  const response = await fetch(resolveApiUrl('/api/finance/admin/agent-prompts'), {
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
  const response = await fetch(resolveApiUrl('/api/finance/custom-asset/resolve'), {
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

  const response = await fetch(resolveApiUrl(`/api/finance/admin/agent-prompts/${agentType}`), {
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
  const response = await fetch(resolveApiUrl(`/api/finance/admin/agent-prompts/${agentType}`), {
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
  const response = await fetch(resolveApiUrl('/api/finance/admin/agent-prompts'), {
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
  const response = await fetch(resolveApiUrl('/api/finance/quick-compare-groups'), {
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
  const response = await fetch(resolveApiUrl('/api/finance/admin/quick-compare-groups'), {
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
  const response = await fetch(resolveApiUrl('/api/finance/admin/quick-compare-groups'), {
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
  const response = await fetch(resolveApiUrl(`/api/finance/admin/quick-compare-groups/${id}`), {
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
  const response = await fetch(resolveApiUrl(`/api/finance/admin/quick-compare-groups/${id}`), {
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
  const response = await fetch(`${resolveApiUrl('/api/finance/admin/price-cache')}?${params.toString()}`, {
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
  const response = await fetch(resolveApiUrl(`/api/finance/admin/price-cache/${id}`), {
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

  const response = await fetch(resolveApiUrl('/api/finance/add-single-asset'), {
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
