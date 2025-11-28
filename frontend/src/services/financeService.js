const BASE_URL = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')

const defaultHeaders = {
  'Accept': 'application/json',
  'Content-Type': 'application/json'
}

function handleResponse(response) {
  if (!response.ok) {
    throw new Error(`요청 실패(${response.status})`)
  }
  const contentType = response.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) {
    throw new Error('JSON 응답이 필요합니다.')
  }
  return response.json()
}

export async function fetchHistoricalReturns({ prompt, quickRequests, contextKey, signal }) {
  const body = {
    prompt: prompt || '',
    quick_requests: Array.isArray(quickRequests) ? quickRequests : [],
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

export async function fetchHistoricalReturnsStream({ prompt, quickRequests, contextKey, signal, onLog }) {
  /**
   * Streaming version of fetchHistoricalReturns
   * @param {Function} onLog - Callback for each log message: onLog(message)
   * @returns {Promise<Object>} - Final result data
   */
  const body = {
    prompt: prompt || '',
    quick_requests: Array.isArray(quickRequests) ? quickRequests : [],
  }
  if (contextKey) {
    body.context_key = contextKey
  }

  const response = await fetch(`${BASE_URL}/api/finance/historical-returns?stream=1`, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify(body),
    signal
  })

  if (!response.ok) {
    throw new Error(`요청 실패(${response.status})`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let finalResult = null

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.trim() || !line.startsWith('data: ')) continue

        try {
          const jsonData = JSON.parse(line.slice(6))

          if (jsonData.type === 'log') {
            if (onLog) onLog(jsonData.message)
          } else if (jsonData.type === 'error') {
            throw new Error(jsonData.message)
          } else if (jsonData.type === 'result') {
            finalResult = jsonData.data
          }
        } catch (e) {
          if (e.message && e.message.includes('분석') || e.message.includes('자산')) {
            throw e
          }
          console.warn('Failed to parse SSE message:', line, e)
        }
      }
    }
  } finally {
    reader.releaseLock()
  }

  if (!finalResult) {
    throw new Error('서버로부터 결과를 받지 못했습니다.')
  }

  return finalResult
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
