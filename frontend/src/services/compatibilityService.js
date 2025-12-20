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

export async function fetchCompatibilityAgentPrompt({ username, agentKey = 'saju_bitcoin', signal } = {}) {
  const params = new URLSearchParams()
  if (username) {
    params.append('username', username)
  }
  if (agentKey) {
    params.append('agent_key', agentKey)
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

export async function updateCompatibilityAgentPrompt({ username, agentKey = 'saju_bitcoin', name, description, systemPrompt, modelName, isActive, signal } = {}) {
  if (!username) {
    throw new Error('관리자 인증 정보가 필요합니다.')
  }

  const body = { username }
  if (agentKey) body.agent_key = agentKey
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

export async function resetCompatibilityAgentPrompt({ username, agentKey = 'saju_bitcoin', signal } = {}) {
  if (!username) {
    throw new Error('관리자 인증 정보가 필요합니다.')
  }
  const body = { username, action: 'reset' }
  if (agentKey) body.agent_key = agentKey
  const response = await fetch(`${BASE_URL}/api/compatibility/admin/prompt`, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify(body),
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '기본 프롬프트로 초기화하지 못했습니다.')
  }
  return data.prompt
}

export async function fetchPublicCompatibilityPrompt({ agentKey = 'saju_bitcoin', signal } = {}) {
  const params = new URLSearchParams()
  if (agentKey) {
    params.append('agent_key', agentKey)
  }
  const qs = params.toString() ? `?${params.toString()}` : ''
  const response = await fetch(`${BASE_URL}/api/compatibility/prompt${qs}`, {
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

export async function fetchCompatibilityReportTemplates({ signal } = {}) {
  const response = await fetch(`${BASE_URL}/api/compatibility/report-templates`, {
    method: 'GET',
    headers: defaultHeaders,
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '리포트 템플릿을 불러오지 못했습니다.')
  }
  return data.templates || []
}

export async function updateCompatibilityReportTemplate({ username, key, label, description, content, sortOrder, signal } = {}) {
  if (!username) {
    throw new Error('관리자 인증 정보가 필요합니다.')
  }
  if (!key) {
    throw new Error('템플릿 key가 필요합니다.')
  }
  const body = { username }
  if (label !== undefined) body.label = label
  if (description !== undefined) body.description = description
  if (content !== undefined) body.content = content
  if (sortOrder !== undefined) body.sort_order = sortOrder

  const response = await fetch(`${BASE_URL}/api/compatibility/admin/report-templates/${encodeURIComponent(key)}`, {
    method: 'PATCH',
    headers: defaultHeaders,
    body: JSON.stringify(body),
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '리포트 템플릿을 업데이트하지 못했습니다.')
  }
  return data.template
}

export async function fetchCompatibilityAgentCaches({ username, search, category, limit, signal } = {}) {
  if (!username) {
    throw new Error('관리자 인증 정보가 필요합니다.')
  }
  const params = new URLSearchParams({ username })
  if (search) params.append('search', search)
  if (category) params.append('category', category)
  if (limit) params.append('limit', limit)
  const qs = params.toString() ? `?${params.toString()}` : ''
  const response = await fetch(`${BASE_URL}/api/compatibility/admin/cache${qs}`, {
    method: 'GET',
    headers: defaultHeaders,
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '캐시된 궁합 답변을 불러오지 못했습니다.')
  }
  return data.caches || []
}

export async function updateCompatibilityAgentCache({ username, cacheId, responseText, category, subjectName, targetName, metadata, signal } = {}) {
  if (!username) throw new Error('관리자 인증 정보가 필요합니다.')
  if (!cacheId) throw new Error('cacheId가 필요합니다.')
  const body = { username }
  if (responseText !== undefined) body.response_text = responseText
  if (category !== undefined) body.category = category
  if (subjectName !== undefined) body.subject_name = subjectName
  if (targetName !== undefined) body.target_name = targetName
  if (metadata !== undefined) body.metadata = metadata

  const response = await fetch(`${BASE_URL}/api/compatibility/admin/cache/${cacheId}`, {
    method: 'PATCH',
    headers: defaultHeaders,
    body: JSON.stringify(body),
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '캐시 엔트리를 업데이트하지 못했습니다.')
  }
  return data.cache
}

export async function deleteCompatibilityAgentCache({ username, cacheId, signal } = {}) {
  if (!username) throw new Error('관리자 인증 정보가 필요합니다.')
  if (!cacheId) throw new Error('cacheId가 필요합니다.')
  const params = new URLSearchParams({ username })
  const response = await fetch(`${BASE_URL}/api/compatibility/admin/cache/${cacheId}?${params.toString()}`, {
    method: 'DELETE',
    headers: defaultHeaders,
    signal
  })
  const data = await handleResponse(response)
  if (!data.ok) {
    throw new Error(data.error || '캐시 엔트리를 삭제하지 못했습니다.')
  }
  return true
}

export async function runCompatibilityAgent({ agentKey = 'saju_bitcoin', context, data, temperature, cache, signal } = {}) {
  const body = {}
  if (agentKey) body.agent_key = agentKey
  if (context !== undefined) body.context = context
  if (data !== undefined) body.data = data
  if (temperature !== undefined) body.temperature = temperature
  if (cache !== undefined) {
    if (cache && typeof cache === 'object') {
      try {
        body.cache = JSON.parse(JSON.stringify(cache))
      } catch (error) {
        body.cache = cache
      }
    } else {
      body.cache = cache
    }
  }

  if (context !== undefined) {
    const contextLength = typeof context === 'string' ? context.length : 0
    console.log(
      `%c[Agent:${agentKey}] ▶️ context 준비됨 (길이: ${contextLength}자)`,
      'color:#2563eb;font-weight:bold;'
    )
    if (contextLength) {
      const previewLimit = 800
      const truncated = contextLength > previewLimit
      const preview = truncated ? context.slice(0, previewLimit) : context
      console.groupCollapsed(`[Agent:${agentKey}] ⤷ context 내용${truncated ? ` (앞 ${previewLimit}자)` : ''}`)
      console.log(preview)
      if (truncated) {
        console.log(`… (추가 ${contextLength - previewLimit}자 생략)`)
      }
      console.groupEnd()
    }
  } else {
    console.log(`[Agent:${agentKey}] ▶️ context 없음`)
  }
  if (data !== undefined) {
    const keyPreview = data && typeof data === 'object' ? Object.keys(data) : []
    console.log(
      `[Agent:${agentKey}] ▶️ 구조화 데이터 전달 (키: ${keyPreview.join(', ') || '없음'})`
    )
  }

  const startedAt = typeof performance !== 'undefined' && performance.now ? performance.now() : Date.now()

  const response = await fetch(`${BASE_URL}/api/compatibility/agent/generate`, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify(body),
    signal
  })
  try {
    const payload = await handleResponse(response)
    const duration = (typeof performance !== 'undefined' && performance.now ? performance.now() : Date.now()) - startedAt
    if (payload?.ok) {
      const narrative = payload?.narrative || ''
      const preview = narrative.replace(/\s+/g, ' ').trim().slice(0, 160)
      console.log(
        `%c[Agent:${agentKey}] ${payload?.cached ? '♻️ 캐시 응답' : '✅ 응답 수신'} (${Math.round(duration)}ms)`,
        payload?.cached ? 'color:#0ea5e9;font-weight:bold;' : 'color:#16a34a;font-weight:bold;',
        {
          provider: payload.provider || payload.model || 'unknown',
          length: narrative.length,
          preview
        }
      )
    } else {
      console.warn(
        `[Agent:${agentKey}] ⚠️ 응답 이상 (${Math.round(duration)}ms):`,
        payload?.error || '알 수 없는 오류'
      )
    }
    return payload
  } catch (error) {
    const duration = (typeof performance !== 'undefined' && performance.now ? performance.now() : Date.now()) - startedAt
    console.error(`[Agent:${agentKey}] ❌ 호출 실패 (${Math.round(duration)}ms):`, error?.message || error)
    throw error
  }
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
