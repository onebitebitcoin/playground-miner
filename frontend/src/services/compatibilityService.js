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
    const message = payload?.error || `요청 실패(${response.status})`
    throw new Error(message)
  }

  if (!isJson) {
    throw new Error('JSON 응답이 필요합니다.')
  }

  return payload
}

export async function fetchCompatibilityAgentPrompt({ username, signal } = {}) {
  const params = new URLSearchParams()
  if (username) {
    params.append('username', username)
  }
  const qs = params.toString() ? `?${params.toString()}` : ''

  const response = await fetch(`${BASE_URL}/api/compatibility/admin/prompt${qs}`, {
    method: 'GET',
    headers: defaultHeaders,
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '궁합 에이전트 프롬프트를 불러오지 못했습니다.')
  }
  return data.prompt
}

export async function updateCompatibilityAgentPrompt({ username, name, description, systemPrompt, modelName, isActive, signal } = {}) {
  if (!username) {
    throw new Error('관리자 인증 정보가 필요합니다.')
  }

  const body = { username }
  if (name !== undefined) body.name = name
  if (description !== undefined) body.description = description
  if (systemPrompt !== undefined) body.system_prompt = systemPrompt
  if (modelName !== undefined) body.model_name = modelName
  if (isActive !== undefined) body.is_active = isActive

  const response = await fetch(`${BASE_URL}/api/compatibility/admin/prompt`, {
    method: 'PATCH',
    headers: defaultHeaders,
    body: JSON.stringify(body),
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '궁합 에이전트 프롬프트를 업데이트하지 못했습니다.')
  }
  return data.prompt
}

export async function resetCompatibilityAgentPrompt({ username, signal } = {}) {
  if (!username) {
    throw new Error('관리자 인증 정보가 필요합니다.')
  }
  const response = await fetch(`${BASE_URL}/api/compatibility/admin/prompt`, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify({ username, action: 'reset' }),
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '기본 프롬프트로 초기화하지 못했습니다.')
  }
  return data.prompt
}

export async function fetchPublicCompatibilityPrompt({ signal } = {}) {
  const response = await fetch(`${BASE_URL}/api/compatibility/prompt`, {
    method: 'GET',
    headers: defaultHeaders,
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '궁합 에이전트 프롬프트를 불러오지 못했습니다.')
  }
  return data.prompt
}

export async function fetchCompatibilityQuickPresets({ signal } = {}) {
  const response = await fetch(`${BASE_URL}/api/compatibility/quick-presets`, {
    method: 'GET',
    headers: defaultHeaders,
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '빠른 설정을 불러오지 못했습니다.')
  }
  return data.presets || []
}

export async function generateCompatibilityNarrative({ context, data, temperature, signal } = {}) {
  const body = {}
  if (context !== undefined) body.context = context
  if (data !== undefined) body.data = data
  if (temperature !== undefined) body.temperature = temperature

  const response = await fetch(`${BASE_URL}/api/compatibility/agent/generate`, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify(body),
    signal
  })
  return handleResponse(response)
}

export async function saveCompatibilityAnalysis({ birthdate, birthTime, gender, element, zodiac, yinYang, score, rating, narrative, signal } = {}) {
  const body = {
    birthdate, // Format: 'YYYY-MM-DD'
    element,
    zodiac,
    yin_yang: yinYang,
    score,
    rating,
    narrative
  }

  if (birthTime) {
    body.birth_time = birthTime // Format: 'HH:MM'
  }

  if (gender) {
    body.gender = gender
  }

  const response = await fetch(`${BASE_URL}/api/compatibility/analysis/save`, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify(body),
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '궁합 분석 결과를 저장하지 못했습니다.')
  }
  return data
}

export async function fetchCompatibilityAnalysisList({ page = 1, perPage = 10, signal } = {}) {
  const params = new URLSearchParams({
    page: page.toString(),
    per_page: perPage.toString()
  })

  const response = await fetch(`${BASE_URL}/api/compatibility/analysis/list?${params.toString()}`, {
    method: 'GET',
    headers: defaultHeaders,
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '궁합 분석 내역을 불러오지 못했습니다.')
  }
  return data
}

export async function fetchAdminCompatibilityQuickPresets({ username, signal } = {}) {
  if (!username) {
    throw new Error('관리자 인증 정보가 필요합니다.')
  }
  const params = new URLSearchParams({ username })
  const response = await fetch(`${BASE_URL}/api/compatibility/admin/quick-presets?${params.toString()}`, {
    method: 'GET',
    headers: defaultHeaders,
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '빠른 설정 목록을 불러오지 못했습니다.')
  }
  return data.presets || []
}

export async function createCompatibilityQuickPreset({ username, payload, signal } = {}) {
  if (!username) {
    throw new Error('관리자 인증 정보가 필요합니다.')
  }
  const body = { ...(payload || {}), username }
  const response = await fetch(`${BASE_URL}/api/compatibility/admin/quick-presets`, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify(body),
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '빠른 설정을 추가하지 못했습니다.')
  }
  return data.preset
}

export async function updateCompatibilityQuickPreset({ username, id, payload, signal } = {}) {
  if (!username) {
    throw new Error('관리자 인증 정보가 필요합니다.')
  }
  if (!id) {
    throw new Error('preset id가 필요합니다.')
  }
  const body = { ...(payload || {}), username }
  const response = await fetch(`${BASE_URL}/api/compatibility/admin/quick-presets/${id}`, {
    method: 'PATCH',
    headers: defaultHeaders,
    body: JSON.stringify(body),
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '빠른 설정을 수정하지 못했습니다.')
  }
  return data.preset
}

export async function deleteCompatibilityQuickPreset({ username, id, signal } = {}) {
  if (!username) {
    throw new Error('관리자 인증 정보가 필요합니다.')
  }
  if (!id) {
    throw new Error('preset id가 필요합니다.')
  }
  const body = JSON.stringify({ username })
  const response = await fetch(`${BASE_URL}/api/compatibility/admin/quick-presets/${id}`, {
    method: 'DELETE',
    headers: defaultHeaders,
    body,
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '빠른 설정을 삭제하지 못했습니다.')
  }
  return true
}

export async function calculateSaju({ birthdate, birthTime, signal } = {}) {
  const body = { birthdate }
  if (birthTime) {
    body.birth_time = birthTime
  }

  const response = await fetch(`${BASE_URL}/api/compatibility/admin/calculate-saju`, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify(body),
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '사주 계산에 실패했습니다.')
  }
  return data.saju
}

export async function processSajuWithAgent({ storedSaju, name, birthdate, birthTime, signal } = {}) {
  const body = {}

  if (storedSaju) {
    body.stored_saju = storedSaju
  }

  if (name) {
    body.name = name
  }

  if (birthdate) {
    body.birthdate = birthdate
  }

  if (birthTime) {
    body.birth_time = birthTime
  }

  const response = await fetch(`${BASE_URL}/api/compatibility/agent/process-saju`, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify(body),
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '사주 처리에 실패했습니다.')
  }
  return data
}
