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
