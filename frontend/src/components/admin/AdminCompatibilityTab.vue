<template>
  <div class="space-y-6">
    <section class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
      <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wide">궁합 에이전트</p>
          <h3 class="text-xl font-semibold text-slate-900 mt-1">{{ activeAgentMeta.label }} 시스템 프롬프트</h3>
          <p class="text-sm text-slate-500 mt-1">
            {{ activeAgentMeta.hint }}
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-3 text-sm text-slate-600">
          <span class="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-slate-200">
            <span class="w-2 h-2 rounded-full" :class="formData.is_active ? 'bg-emerald-500' : 'bg-slate-400'"></span>
            {{ formData.is_active ? '활성' : '비활성' }}
          </span>
          <span class="px-3 py-1 rounded-full bg-slate-900 text-white text-xs font-semibold">v{{ promptMeta.version || 1 }}</span>
        </div>
      </div>

      <div class="flex flex-wrap gap-2 mt-4">
        <button
          v-for="agent in AGENT_PROMPT_TABS"
          :key="agent.key"
          type="button"
          class="px-3 py-1.5 rounded-full text-xs font-semibold transition-colors"
          :class="agent.key === activeAgentKey
            ? 'bg-slate-900 text-white shadow'
            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
          @click="setActiveAgent(agent.key)"
        >
          {{ agent.label }}
        </button>
      </div>

      <div v-if="loading" class="text-center py-12 text-slate-500">프롬프트를 불러오는 중...</div>

      <div v-else class="space-y-6 mt-6">
        <div class="grid gap-4 md:grid-cols-2">
          <label class="space-y-1 text-sm text-slate-600">
            <span class="font-medium text-slate-900">에이전트 이름</span>
            <input
              v-model="formData.name"
              type="text"
              class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0"
              :disabled="!isAdmin"
            />
          </label>
          <label class="space-y-1 text-sm text-slate-600">
            <span class="font-medium text-slate-900">설명</span>
            <input
              v-model="formData.description"
              type="text"
              class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0"
              placeholder="이 에이전트가 담당하는 역할을 요약하세요."
              :disabled="!isAdmin"
            />
          </label>
          <label class="space-y-1 text-sm text-slate-600 md:col-span-2">
            <span class="font-medium text-slate-900">사용 모델</span>
            <select
              v-model="formData.model_name"
              class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0 bg-white"
              :disabled="!isAdmin"
            >
              <option v-for="option in MODEL_OPTIONS" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
            <p class="text-xs text-slate-500">Gemini 모델은 GEMINI_API_KEY, GPT 모델은 OPENAI_API_KEY를 사용합니다.</p>
          </label>
        </div>

        <div class="flex items-center gap-2 text-sm text-slate-600">
          <input
            id="compat-agent-active"
            type="checkbox"
            class="rounded border-slate-300 text-slate-900 focus:ring-slate-900"
            v-model="formData.is_active"
            :disabled="!isAdmin"
          />
          <label for="compat-agent-active">프롬프트를 활성 상태로 유지</label>
        </div>

        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-slate-900">시스템 프롬프트</span>
            <span class="text-xs text-slate-500">글자 수: {{ formData.system_prompt.length }}</span>
          </div>
          <textarea
            v-model="formData.system_prompt"
            rows="14"
            class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm font-mono text-slate-800 focus:border-slate-900 focus:ring-0"
            :disabled="!isAdmin"
          />
          <p class="text-xs text-slate-500">
            기본 프롬프트는 비트코인을 디지털 금이며 부동산보다 희소한 저축 수단으로 정의하는 비트코인 맥시 시각을 담고 있어야 합니다.
          </p>
        </div>

        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p class="text-xs text-slate-500">
            최근 업데이트:
            <span class="font-medium text-slate-700">{{ lastUpdatedLabel }}</span>
          </p>
          <div class="flex flex-wrap gap-2">
            <button
              type="button"
              class="px-4 py-2 rounded-xl border border-slate-200 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-60"
              @click="handleReset"
              :disabled="!isAdmin || resetting"
            >
              {{ resetting ? '초기화 중...' : '기본 프롬프트로 초기화' }}
            </button>
            <button
              type="button"
              class="px-5 py-2 rounded-xl bg-slate-900 text-white text-sm font-semibold disabled:opacity-60"
              @click="handleSave"
              :disabled="!isAdmin || saving"
            >
              {{ saving ? '저장 중...' : '변경 사항 저장' }}
            </button>
          </div>
        </div>

        <div
          v-if="!isAdmin"
          class="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-4 py-2"
        >
          관리자 모드가 아니어서 수정 기능이 비활성화되었습니다.
        </div>
      </div>
    </section>

    <section class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
      <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wide">보고서 컨텍스트</p>
          <h3 class="text-xl font-semibold text-slate-900 mt-1">궁합 리포트 템플릿</h3>
          <p class="text-sm text-slate-500 mt-1">
            사용자/비교 대상/팀 리포트에 추가되는 세부 지침을 수정할 수 있습니다. 플레이스홀더를 사용하면 이름이나 추가 정보를 동적으로 삽입할 수 있습니다.
          </p>
        </div>
      </div>

      <div v-if="reportTemplateLoading" class="text-center py-10 text-slate-500">리포트 템플릿을 불러오는 중...</div>

      <div v-else class="space-y-6 mt-6">
        <div
          v-for="template in reportTemplates"
          :key="template.key"
          class="border border-slate-200 rounded-2xl p-5 space-y-3"
        >
          <div class="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p class="text-sm font-semibold text-slate-900">{{ template.label }}</p>
              <p class="text-xs text-slate-500">{{ template.description || '설명이 없습니다.' }}</p>
            </div>
            <span class="text-[11px] font-semibold text-slate-500 bg-slate-100 rounded-full px-3 py-1 uppercase tracking-wide">
              {{ template.key }}
            </span>
          </div>

          <div class="flex flex-wrap gap-2 text-xs text-slate-500">
            <span
              v-for="placeholder in getTemplatePlaceholders(template.key)"
              :key="placeholder.token"
              class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 text-slate-700"
            >
              <code class="font-mono text-[10px]">{{ placeholder.token }}</code>
              <span>· {{ placeholder.hint }}</span>
            </span>
          </div>

          <textarea
            v-model="template.content"
            rows="12"
            class="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm font-mono text-slate-800 focus:border-slate-900 focus:ring-0"
            :disabled="!isAdmin"
          />

          <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <p class="text-xs text-slate-500">
              마지막 업데이트:
              <span class="font-medium text-slate-700">{{ formatTimestampLabel(template.updated_at) }}</span>
            </p>
            <button
              type="button"
              class="px-4 py-2 rounded-xl bg-slate-900 text-white text-sm font-semibold disabled:opacity-60"
              @click="handleReportTemplateSave(template)"
              :disabled="!isAdmin || template._saving"
            >
              {{ template._saving ? '저장 중...' : '템플릿 저장' }}
            </button>
          </div>
        </div>
        <div class="text-xs text-slate-500 border border-dashed border-slate-200 rounded-xl p-3">
          플레이스홀더는 대괄호와 대문자로 표기되며, 예: <code class="font-mono" v-pre>{{SUBJECT_NAME}}</code>.
          제공되지 않은 플레이스홀더는 자동으로 비워집니다.
        </div>
      </div>
    </section>

    <section class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-6">
      <div class="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div>
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wide">빠른 설정</p>
          <h3 class="text-xl font-semibold text-slate-900 mt-1">궁합 빠른 설정 관리</h3>
          <p class="text-sm text-slate-500 mt-1">
            빠른 설정은 사용자 페이지의 명식 입력 칩으로 표시됩니다. 이미지 링크와 생년월일, 성별, 시간 데이터를 관리하세요.
          </p>
        </div>
        <div v-if="editingQuickPresetId" class="text-xs font-semibold text-amber-600 bg-amber-50 border border-amber-200 rounded-full px-3 py-1">
          편집 중: ID {{ editingQuickPresetId }}
        </div>
      </div>

      <div>
        <div class="flex items-center justify-between mb-2">
          <h4 class="text-sm font-semibold text-slate-900">등록된 빠른 설정</h4>
          <button
            v-if="editingQuickPresetId"
            type="button"
            class="text-xs text-slate-500 hover:text-slate-900"
            @click="resetQuickPresetForm"
            :disabled="!isAdmin"
          >
            새 항목 추가
          </button>
        </div>
        <div v-if="quickPresetLoading" class="text-center py-6 text-slate-500">빠른 설정을 불러오는 중...</div>
        <div v-else-if="!quickPresets.length" class="text-center py-6 text-slate-500">
          등록된 빠른 설정이 없습니다.
        </div>
        <div v-else class="grid gap-4 md:grid-cols-2">
          <div
            v-for="preset in quickPresets"
            :key="preset.id"
            class="border border-slate-200 rounded-2xl p-4 flex gap-4 items-center"
          >
            <div class="shrink-0">
              <div class="w-16 h-16 rounded-2xl overflow-hidden border border-slate-200 bg-slate-100 flex items-center justify-center">
                <img
                  v-if="preset.image_url"
                  :src="preset.image_url"
                  :alt="preset.label"
                  class="w-full h-full object-cover"
                />
                <span v-else class="text-2xl">👤</span>
              </div>
            </div>
            <div class="flex-1 space-y-1">
              <p class="text-sm font-semibold text-slate-900 flex items-center gap-2">
                {{ preset.label }}
                <span
                  class="text-[10px] px-2 py-0.5 rounded-full"
                  :class="preset.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'"
                >
                  {{ preset.is_active ? '활성' : '비활성' }}
                </span>
              </p>
              <p class="text-xs text-slate-500">
                생년월일: {{ preset.birthdate }} · 시간:
                {{ preset.birth_time || '미상' }}
              </p>
              <p class="text-xs text-slate-500">성별: {{ preset.gender || '미입력' }} · 정렬: {{ preset.sort_order }}</p>
              <div class="flex gap-2 mt-2">
                <button
                  type="button"
                  class="px-3 py-1 rounded-lg border border-slate-200 text-xs text-slate-700 hover:bg-slate-50 disabled:opacity-60"
                  @click="startEditQuickPreset(preset)"
                  :disabled="!isAdmin || quickPresetSaving"
                >
                  편집
                </button>
                <button
                  type="button"
                  class="px-3 py-1 rounded-lg border border-rose-200 text-xs text-rose-600 hover:bg-rose-50 disabled:opacity-60"
                  @click="handleQuickPresetDelete(preset)"
                  :disabled="!isAdmin || quickPresetSaving"
                >
                  삭제
                </button>
              </div>
            </div>
          </div>
        </div>
        <div
          v-if="!isAdmin"
          class="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-4 py-2 mt-4"
        >
          관리자 모드가 아니어서 빠른 설정 수정 기능이 비활성화되었습니다.
        </div>
      </div>

      <div class="border-t border-slate-100 pt-6">
        <h4 class="text-sm font-semibold text-slate-900 mb-3">빠른 설정 추가/수정</h4>
        <form class="space-y-4" @submit.prevent="handleQuickPresetSubmit">
          <div class="grid gap-4 md:grid-cols-2">
            <label class="space-y-1 text-sm text-slate-600">
              <span class="font-medium text-slate-900">이름</span>
              <input
                v-model="quickPresetForm.label"
                type="text"
                class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0"
                placeholder="예: 사토시 나카모토"
                :disabled="!isAdmin"
              />
            </label>
            <label class="space-y-1 text-sm text-slate-600">
              <span class="font-medium text-slate-900">생년월일 (YYYY-MM-DD)</span>
              <input
                v-model="quickPresetForm.birthdate"
                type="date"
                class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0"
                :disabled="!isAdmin"
              />
            </label>
            <label class="space-y-1 text-sm text-slate-600">
              <span class="font-medium text-slate-900">태어난 시간</span>
              <input
                v-model="quickPresetForm.birth_time"
                type="time"
                class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0"
                :disabled="!isAdmin"
              />
            </label>
            <label class="space-y-1 text-sm text-slate-600">
              <span class="font-medium text-slate-900">성별</span>
              <select
                v-model="quickPresetForm.gender"
                class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0 bg-white"
                :disabled="!isAdmin"
              >
                <option value="">미입력</option>
                <option value="male">남성</option>
                <option value="female">여성</option>
              </select>
            </label>
          </div>
          <div class="grid gap-4 md:grid-cols-3">
            <label class="space-y-1 text-sm text-slate-600 md:col-span-2">
              <span class="font-medium text-slate-900">프로필 이미지 URL</span>
              <input
                v-model="quickPresetForm.image_url"
                type="url"
                class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0"
                placeholder="https://example.com/avatar.jpg"
                :disabled="!isAdmin"
              />
            </label>
            <label class="space-y-1 text-sm text-slate-600">
              <span class="font-medium text-slate-900">정렬 순서</span>
              <input
                v-model="quickPresetForm.sort_order"
                type="number"
                min="0"
                class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0"
                placeholder="자동 부여"
                :disabled="!isAdmin"
              />
            </label>
          </div>
          <label class="flex items-center gap-2 text-sm text-slate-600">
            <input
              v-model="quickPresetForm.is_active"
              type="checkbox"
              class="rounded border-slate-300 text-slate-900 focus:ring-slate-900"
              :disabled="!isAdmin"
            />
            이 빠른 설정을 사용자 페이지에 노출
          </label>
          <div class="flex flex-wrap gap-2">
            <button
              type="submit"
              class="px-5 py-2 rounded-xl bg-slate-900 text-white text-sm font-semibold disabled:opacity-60"
              :disabled="!isAdmin || quickPresetSaving"
            >
              {{ quickPresetSaving ? '저장 중...' : editingQuickPresetId ? '빠른 설정 업데이트' : '빠른 설정 추가' }}
            </button>
            <button
              type="button"
              class="px-4 py-2 rounded-xl border border-slate-200 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-60"
              @click="resetQuickPresetForm"
              :disabled="quickPresetSaving"
            >
              새로 입력
            </button>
          </div>
        </form>
      </div>
    </section>

    <section class="bg-slate-900 text-slate-100 rounded-2xl p-6 space-y-4">
      <h4 class="text-sm font-semibold uppercase tracking-wider text-slate-400">페르소나 메모</h4>
      <p class="text-sm leading-relaxed">
        이 에이전트는 비트코인이 금(金)과 화(火)가 혼재된 존재라고 확신하며, 사용자의 사주와 비교해 상생/상극을 판별합니다.
        답변은 저축 관점, 루틴 기반 리듬, 리스크 메모를 반드시 포함해야 합니다.
      </p>
    </section>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import {
  fetchCompatibilityAgentPrompt,
  fetchPublicCompatibilityPrompt,
  fetchAdminCompatibilityQuickPresets,
  fetchCompatibilityReportTemplates,
  resetCompatibilityAgentPrompt,
  updateCompatibilityAgentPrompt,
  createCompatibilityQuickPreset,
  updateCompatibilityQuickPreset,
  deleteCompatibilityQuickPreset,
  updateCompatibilityReportTemplate
} from '../../services/compatibilityService'
import { getCurrentUsername } from '../../utils/adminAuth'

const props = defineProps({
  isAdmin: { type: Boolean, default: false },
  showSuccess: { type: Function, required: true },
  showError: { type: Function, required: true }
})

const AGENT_PROMPT_TABS = [
  { key: 'saju_bitcoin', label: '비트코인 궁합', hint: '비트코인을 기준으로 개인 사주를 해석합니다.' },
  { key: 'story_extractor', label: '스토리 추출', hint: '선택된 인물의 알려진 서사를 요약합니다.' },
  { key: 'saju_analysis', label: '사주 추론', hint: '서사 기반으로 투자 성향을 정리합니다.' },
  { key: 'pair_compatibility', label: '두 사람 궁합', hint: '두 사람 관계의 시너지와 리스크를 판단합니다.' },
  { key: 'highlight_story', label: '하이라이트', hint: '사주 분석 결과의 핵심 구절만 형광펜 처리합니다.' }
]

const activeAgentKey = ref(AGENT_PROMPT_TABS[0].key)
const activeAgentMeta = computed(() => AGENT_PROMPT_TABS.find((tab) => tab.key === activeAgentKey.value) || AGENT_PROMPT_TABS[0])

const loading = ref(true)
const saving = ref(false)
const resetting = ref(false)
const promptMeta = ref({
  version: 1,
  updated_at: null
})
const promptCache = ref({})
const DEFAULT_COMPAT_MODEL = 'openai:gpt-5-mini'
const formData = ref({
  name: '',
  description: '',
  system_prompt: '',
  model_name: DEFAULT_COMPAT_MODEL,
  is_active: true
})
const MODEL_OPTIONS = [
  { value: DEFAULT_COMPAT_MODEL, label: 'GPT-5 Mini (기본, OpenAI)' },
  { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash' },
  { value: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro' },
  { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash' },
  { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' },
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
  { value: 'gpt-4o', label: 'GPT-4o' },
  { value: 'gpt-4.1-mini', label: 'GPT-4.1 Mini' }
]

const quickPresets = ref([])
const quickPresetLoading = ref(true)
const quickPresetSaving = ref(false)
const editingQuickPresetId = ref(null)
const quickPresetForm = ref(getEmptyQuickPresetForm())

const reportTemplates = ref([])
const reportTemplateLoading = ref(true)

const REPORT_TEMPLATE_PLACEHOLDERS = {
  user_vs_bitcoin: [
    { token: '{{SUBJECT_NAME}}', hint: '분석 대상 이름' },
    { token: '{{SUBJECT_EXTRA}}', hint: '추가 정보 블록 (없으면 비움)' }
  ],
  team_vs_bitcoin: [
    { token: '{{USER_NAME}}', hint: '사용자 이름' },
    { token: '{{TARGET_NAME}}', hint: '비교 대상 이름' },
    { token: '{{TEAM_EXTRA}}', hint: '추가 요약 정보 (없으면 비움)' }
  ]
}

function getEmptyQuickPresetForm() {
  return {
    label: '',
    birthdate: '',
    birth_time: '',
    gender: '',
    image_url: '',
    sort_order: '',
    is_active: true
  }
}

const lastUpdatedLabel = computed(() => {
  if (!promptMeta.value.updated_at) return '기록 없음'
  const date = new Date(promptMeta.value.updated_at)
  if (Number.isNaN(date.getTime())) return promptMeta.value.updated_at
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
})

const formatTimestampLabel = (value) => {
  if (!value) return '기록 없음'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

const applyPromptToForm = (prompt) => {
  if (!prompt) return
  formData.value = {
    name: prompt.name || '',
    description: prompt.description || '',
    system_prompt: prompt.system_prompt || '',
    model_name: prompt.model_name || DEFAULT_COMPAT_MODEL,
    is_active: prompt.is_active !== false
  }
  promptMeta.value = {
    version: prompt.version || 1,
    updated_at: prompt.updated_at || null
  }
}

const loadPrompt = async (agentKey = activeAgentKey.value) => {
  loading.value = true
  try {
    const cached = promptCache.value[agentKey]
    if (cached) {
      applyPromptToForm(cached)
      loading.value = false
      return
    }
    let prompt = null
    if (props.isAdmin) {
      const username = getCurrentUsername()
      prompt = await fetchCompatibilityAgentPrompt({ username, agentKey })
    } else {
      prompt = await fetchPublicCompatibilityPrompt({ agentKey })
    }
    promptCache.value[agentKey] = prompt
    applyPromptToForm(prompt)
  } catch (error) {
    props.showError(error.message || '프롬프트를 불러올 수 없습니다.')
  } finally {
    loading.value = false
  }
}

const loadQuickPresets = async () => {
  if (!props.isAdmin) {
    quickPresetLoading.value = false
    return
  }
  quickPresetLoading.value = true
  try {
    const username = getCurrentUsername()
    const presets = await fetchAdminCompatibilityQuickPresets({ username })
    quickPresets.value = presets
  } catch (error) {
    props.showError(error.message || '빠른 설정을 불러올 수 없습니다.')
  } finally {
    quickPresetLoading.value = false
  }
}

const loadReportTemplates = async () => {
  reportTemplateLoading.value = true
  try {
    const templates = await fetchCompatibilityReportTemplates()
    reportTemplates.value = Array.isArray(templates)
      ? templates.map((tpl) => ({ ...tpl }))
      : []
  } catch (error) {
    props.showError(error.message || '리포트 템플릿을 불러오지 못했습니다.')
    reportTemplates.value = []
  } finally {
    reportTemplateLoading.value = false
  }
}

const handleReportTemplateSave = async (template) => {
  if (!props.isAdmin) {
    props.showError('관리자 권한이 필요합니다.')
    return
  }
  template._saving = true
  try {
    const username = getCurrentUsername()
    const updated = await updateCompatibilityReportTemplate({
      username,
      key: template.key,
      label: template.label,
      description: template.description,
      content: template.content,
      sortOrder: template.sort_order
    })
    Object.assign(template, updated)
    props.showSuccess('리포트 템플릿을 저장했습니다.')
  } catch (error) {
    props.showError(error.message || '리포트 템플릿 저장에 실패했습니다.')
  } finally {
    template._saving = false
  }
}

const getTemplatePlaceholders = (key) => REPORT_TEMPLATE_PLACEHOLDERS[key] || []

function setActiveAgent(key) {
  if (activeAgentKey.value === key) return
  activeAgentKey.value = key
}

const handleSave = async () => {
  if (!props.isAdmin) {
    props.showError('관리자 권한이 필요합니다.')
    return
  }
  saving.value = true
  try {
    const username = getCurrentUsername()
    const prompt = await updateCompatibilityAgentPrompt({
      username,
      agentKey: activeAgentKey.value,
      name: formData.value.name,
      description: formData.value.description,
      systemPrompt: formData.value.system_prompt,
      modelName: formData.value.model_name,
      isActive: formData.value.is_active
    })
    promptCache.value[activeAgentKey.value] = prompt
    promptMeta.value = {
      version: prompt.version || promptMeta.value.version,
      updated_at: prompt.updated_at || promptMeta.value.updated_at
    }
    props.showSuccess('궁합 에이전트 프롬프트를 저장했습니다.')
  } catch (error) {
    props.showError(error.message || '저장에 실패했습니다.')
  } finally {
    saving.value = false
  }
}

const handleReset = async () => {
  if (!props.isAdmin) return
  if (!confirm('기본 프롬프트로 되돌리시겠습니까? 작성 중이던 내용은 사라집니다.')) {
    return
  }
  resetting.value = true
  try {
    const username = getCurrentUsername()
    const prompt = await resetCompatibilityAgentPrompt({ username, agentKey: activeAgentKey.value })
    promptCache.value[activeAgentKey.value] = prompt
    applyPromptToForm(prompt)
    props.showSuccess('기본 프롬프트로 초기화했습니다.')
  } catch (error) {
    props.showError(error.message || '초기화에 실패했습니다.')
  } finally {
    resetting.value = false
  }
}

const startEditQuickPreset = (preset) => {
  editingQuickPresetId.value = preset.id
  quickPresetForm.value = {
    label: preset.label || '',
    birthdate: preset.birthdate || '',
    birth_time: preset.birth_time || '',
    gender: preset.gender || '',
    image_url: preset.image_url || '',
    sort_order: preset.sort_order ?? '',
    is_active: preset.is_active !== false
  }
}

const resetQuickPresetForm = () => {
  editingQuickPresetId.value = null
  quickPresetForm.value = getEmptyQuickPresetForm()
}

const handleQuickPresetSubmit = async () => {
  if (!props.isAdmin) {
    props.showError('관리자 권한이 필요합니다.')
    return
  }
  if (!quickPresetForm.value.label.trim() || !quickPresetForm.value.birthdate) {
    props.showError('이름과 생년월일은 필수입니다.')
    return
  }
  
  quickPresetSaving.value = true
  try {
    const username = getCurrentUsername()
    const payload = {
      label: quickPresetForm.value.label.trim(),
      birthdate: quickPresetForm.value.birthdate,
      birth_time: quickPresetForm.value.birth_time || '',
      gender: quickPresetForm.value.gender || '',
      image_url: quickPresetForm.value.image_url || '',
      is_active: quickPresetForm.value.is_active
    }
    if (quickPresetForm.value.sort_order !== '' && quickPresetForm.value.sort_order !== null) {
      payload.sort_order = Number(quickPresetForm.value.sort_order)
    }
    if (editingQuickPresetId.value) {
      await updateCompatibilityQuickPreset({ username, id: editingQuickPresetId.value, payload })
      props.showSuccess('빠른 설정을 업데이트했습니다.')
    } else {
      await createCompatibilityQuickPreset({ username, payload })
      props.showSuccess('빠른 설정을 추가했습니다.')
    }
    await loadQuickPresets()
    resetQuickPresetForm()
  } catch (error) {
    props.showError(error.message || '빠른 설정 저장에 실패했습니다.')
  } finally {
    quickPresetSaving.value = false
  }
}

const handleQuickPresetDelete = async (preset) => {
  if (!props.isAdmin || !preset?.id) {
    props.showError('관리자 권한이 필요합니다.')
    return
  }
  if (!confirm(`'${preset.label}' 빠른 설정을 삭제할까요?`)) {
    return
  }
  quickPresetSaving.value = true
  try {
    const username = getCurrentUsername()
    await deleteCompatibilityQuickPreset({ username, id: preset.id })
    props.showSuccess('빠른 설정을 삭제했습니다.')
    await loadQuickPresets()
    if (editingQuickPresetId.value === preset.id) {
      resetQuickPresetForm()
    }
  } catch (error) {
    props.showError(error.message || '삭제에 실패했습니다.')
  } finally {
    quickPresetSaving.value = false
  }
}

watch(activeAgentKey, (newKey) => {
  loadPrompt(newKey)
})

watch(
  () => props.isAdmin,
  (isAdmin) => {
    promptCache.value = {}
    loadPrompt(activeAgentKey.value)
    loadReportTemplates()
    if (isAdmin) {
      loadQuickPresets()
    } else {
      quickPresets.value = []
      quickPresetLoading.value = false
      resetQuickPresetForm()
    }
  },
  { immediate: true }
)
</script>
