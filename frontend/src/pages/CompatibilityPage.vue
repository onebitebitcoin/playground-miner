<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-3xl font-bold text-gray-900 mb-2">궁합 분석</h1>
      <p class="text-gray-600">비트코인을 매개로 다양한 궁합 시나리오를 확인해 보세요.</p>
    </div>

    <!-- Bitcoin Saju Overview Section -->
    <BitcoinSajuSection
      :selectedHighlight="selectedBitcoinHighlight"
      :selectedKey="selectedBitcoinHighlightKey"
      :highlights="bitcoinHighlights"
      :radarChart="bitcoinRadarChart"
      @selectHighlight="handleBitcoinHighlightSelect"
    />

    <!-- Profile Input Section -->
    <section class="space-y-6">
      <div class="grid gap-6 lg:grid-cols-2">
        <!-- User Profile Input -->
        <CompatibilityProfileInput
          title="나의 사주 입력"
          :presets="quickPresetOptions"
          :loadingPresets="quickPresetLoading"
          :selectedPresetId="selectedPresetId"
          v-model:userName="userName"
          v-model:gender="gender"
          v-model:birthdate="birthdate"
          v-model:birthtime="birthtime"
          v-model:timeUnknown="timeUnknown"
          placeholderIcon="👤"
          @applyPreset="applyQuickPreset"
        />

        <!-- Target Profile Input -->
        <CompatibilityProfileInput
          title="비교 대상 사주"
          :presets="quickPresetOptions"
          :loadingPresets="quickPresetLoading"
          :selectedPresetId="selectedTargetPresetId"
          v-model:userName="targetName"
          v-model:gender="targetGender"
          v-model:birthdate="targetBirthdate"
          v-model:birthtime="targetBirthtime"
          v-model:timeUnknown="targetTimeUnknown"
          :disabled="!targetProfileEnabled"
          placeholderIcon="👥"
          @applyPreset="applyTargetQuickPreset"
          @enable="targetProfileEnabled = true"
        />
      </div>

      <!-- Card Preview Section -->
      <CompatibilityProfilePreview
        :user="{
          name: userName || DEFAULT_USER_NAME,
          imageUrl: userImageUrl,
          birthdate: birthdate,
          birthtime: birthtime,
          gender: gender,
          timeUnknown: timeUnknown
        }"
        :target="{
          name: targetName || '비교 대상',
          imageUrl: targetImageUrl,
          birthdate: targetBirthdate,
          birthtime: targetBirthtime,
          gender: targetGender,
          timeUnknown: targetTimeUnknown
        }"
        :targetEnabled="targetProfileEnabled"
        @removeTarget="handleRemoveTarget"
      />

      <!-- Action Button -->
      <div class="flex flex-col gap-2">
        <button
          class="w-full py-4 bg-slate-900 text-white font-bold rounded-2xl shadow-xl hover:bg-slate-800 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3 overflow-hidden relative"
          :disabled="!canStartAnalysis || loading"
          @click="handleCompatibility"
        >
          <div v-if="loading" class="flex items-center gap-3">
            <svg class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke-width="4"></circle>
              <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>분석 에이전트 가동 중...</span>
          </div>
          <div v-else class="flex items-center gap-3">
            <svg class="w-5 h-5 group-hover:rotate-12 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span>비트코인 궁합 분석 시작</span>
          </div>
          <div class="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:animate-shine pointer-events-none"></div>
        </button>
        <p v-if="!canStartAnalysis && !loading" class="text-center text-xs text-slate-400 font-medium">
          분석을 시작하려면 최소한 한 명의 생년월일이 필요합니다.
        </p>
      </div>
    </section>

    <!-- Loading Panel -->
    <CompatibilityLoadingPanel
      v-if="loading"
      :stages="AGENT_STAGES"
      :activeStageIndex="currentStageIndex"
      :progress="loadingProgress"
      :logs="analysisLogs"
      @cancel="handleCancelAnalysis"
    />

    <!-- Results Section -->
    <div v-if="hasAnyResult && !loading" class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 space-y-6">
      <div class="flex items-center justify-between border-b border-slate-100 pb-4">
        <h3 class="text-xl font-black text-slate-900">궁합 분석 리포트</h3>
        <span class="text-xs text-slate-500 font-medium">에이전트 실시간 분석 결과</span>
      </div>

      <!-- Individual Results -->
      <div class="grid gap-6">
        <!-- User vs Bitcoin -->
        <CompatibilityReportCard
          v-if="userVsBitcoinResult"
          title="사용자 × 비트코인 궁합"
          :imageUrl="userImageUrl"
          :facts="userVsBitcoinResult.profileFacts"
          :story="userVsBitcoinResult.personStory"
          :narrative="userVsBitcoinResult.narrative"
          :highlightedNarrative="userVsBitcoinResult.highlightedNarrative"
          :highlightLoading="userVsBitcoinResult.highlightLoading"
          :agentProvider="userVsBitcoinResult.agentProvider"
          :radarChart="userVsBitcoinResult.profileRadarData"
        />

        <!-- Target vs Bitcoin -->
        <CompatibilityReportCard
          v-if="targetVsBitcoinResult"
          title="비교 대상 × 비트코인 궁합"
          icon="👥"
          :imageUrl="targetImageUrl"
          :facts="targetVsBitcoinResult.profileFacts"
          :story="targetVsBitcoinResult.personStory"
          :narrative="targetVsBitcoinResult.narrative"
          :highlightedNarrative="targetVsBitcoinResult.highlightedNarrative"
          :highlightLoading="targetVsBitcoinResult.highlightLoading"
          :agentProvider="targetVsBitcoinResult.agentProvider"
          :radarChart="targetVsBitcoinResult.profileRadarData"
        />

        <!-- Team Result -->
        <div v-if="userVsTargetResult" class="border-t border-slate-200 pt-6">
          <h4 class="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
            <span class="w-2 h-6 bg-indigo-600 rounded-full"></span>
            두 사람 × 비트코인 시너지
          </h4>
          <CompatibilityReportCard
            title="팀 비트코인 투자 궁합"
            icon="🤝"
            :facts="[`${userName} & ${targetName} 팀` ]"
            :narrative="userVsTargetResult.narrative"
            :highlightedNarrative="userVsTargetResult.highlightedNarrative"
            :highlightLoading="userVsTargetResult.highlightLoading"
            :agentProvider="userVsTargetResult.agentProvider"
          />
        </div>

        <!-- Direct Pair Compatibility Result -->
        <div v-if="pairCompatibilityResult" class="border-t border-slate-200 pt-6">
          <h4 class="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
            <span class="w-2 h-6 bg-purple-600 rounded-full"></span>
            두 사람의 직접 궁합
          </h4>
          <CompatibilityReportCard
            title="상호 보완성 및 협업 지수"
            icon="💎"
            :facts="[`${userName} ↔ ${targetName}`]"
            :narrative="pairCompatibilityResult.narrative"
            :highlightedNarrative="pairCompatibilityResult.highlightedNarrative"
            :highlightLoading="pairCompatibilityResult.highlightLoading"
            :agentProvider="pairCompatibilityResult.agentProvider"
          />
        </div>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="errorMessage" class="bg-rose-50 border border-rose-200 rounded-2xl p-6 text-rose-600 font-medium text-center">
      {{ errorMessage }}
    </div>

    <!-- Debug Panel -->
    <AdminPromptPanel
      v-if="isAdmin"
      class="mt-6"
      v-model:show-debug="showDebugLogs"
      :display-logs="stageDebugLogs"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, reactive } from 'vue'
import {
  fetchCompatibilityAgentPrompt,
  fetchPublicCompatibilityPrompt,
  fetchCompatibilityQuickPresets,
  runCompatibilityAgent,
  fetchCompatibilityReportTemplates
} from '@/services/compatibilityService'
import { getCurrentUsername } from '@/utils/adminAuth'
import AdminPromptPanel from '@/components/AdminPromptPanel.vue'

// Decomposed components
import BitcoinSajuSection from './compatibility/components/BitcoinSajuSection.vue'
import CompatibilityProfileInput from './compatibility/components/CompatibilityProfileInput.vue'
import CompatibilityProfilePreview from './compatibility/components/CompatibilityProfilePreview.vue'
import CompatibilityLoadingPanel from './compatibility/components/CompatibilityLoadingPanel.vue'
import CompatibilityReportCard from './compatibility/components/CompatibilityReportCard.vue'

// Utils
import { 
  ELEMENTS, 
  calculateSajuElement, 
  calculateZodiacSign, 
  calculateYinYang, 
  buildRadarChartData 
} from './compatibility/utils'

const DEFAULT_USER_NAME = '사용자'
const AGENT_STAGES = [
  { key: 'story_stage', label: '인물 서사 추출', description: '인물의 공개된 정보를 바탕으로 삶의 궤적을 정리합니다.' },
  { key: 'saju_stage', label: '사주·오행 분석', description: '비트코인의 기운과 사용자의 오행을 대조합니다.' },
  { key: 'report_stage', label: '궁합 리포트 생성', description: '투자 성향과 협업 전략을 포함한 보고서를 작성합니다.' },
  { key: 'highlight_stage', label: '핵심 요약 정리', description: '리포트에서 반드시 기억해야 할 포인트를 하이라이트합니다.' }
]

// State: Bitcoin Saju
const selectedBitcoinHighlightKey = ref('metal')
const bitcoinHighlights = [
  { label: '목(木)', elementKey: 'wood', value: '성장과 개발 생태계', description: '새로운 확장 제안과 구축자 생태계를 키우는 힘. 라이트닝·탭루트 같은 실험을 밀어 올리고, 지속적인 코드 리뷰·테스트 문화가 뿌리처럼 비트코인을 지탱한다.', icon: '🌱', ratio: 10, colorClass: 'bg-green-500' },
  { label: '화(火)', elementKey: 'fire', value: '관심, 서사, 과열 모멘텀', description: '가격 급등락과 서사가 촉발하는 열기. 밈과 미디어, 정치 발언이 불꽃처럼 튀며, 한 번 붙은 불길이 글로벌 유동성을 빨아들여 단기간 폭증을 만든다.', icon: '🔥', ratio: 20, colorClass: 'bg-red-500' },
  { label: '토(土)', elementKey: 'earth', value: '완충, 신뢰 인프라, 거버넌스', description: '채굴자·노드·풀 운영자가 만든 방호벽. 전 세계에 흩어진 노드가 규칙을 검증하고, 채굴 난이도·반감기 구조가 충격을 흡수하는 버팀목이 된다.', icon: '🏔️', ratio: 10, colorClass: 'bg-yellow-600' },
  { label: '금(金)', elementKey: 'metal', value: '규칙, 고정 공급, 불변성', description: '비트코인의 핵심 본체. 2,100만 개 고정 공급과 검증 가능한 합의 규칙이 디지털 금의 품격을 부여하고, 누구도 임의 발행·검열을 할 수 없도록 만든다.', icon: '🥇', ratio: 35, colorClass: 'bg-amber-500' },
  { label: '수(水)', elementKey: 'water', value: '유동성, 글로벌 자본 흐름', description: '거대한 자본·거래소·파생상품 시장이 만들어내는 파도. 상승장에서는 폭발적 흡인력을, 조정기에는 급랭을 유발하며 온체인 자금 이동이 실시간으로 흐른다.', icon: '💧', ratio: 25, colorClass: 'bg-blue-500' }
]
const selectedBitcoinHighlight = computed(() => 
  bitcoinHighlights.find(h => h.elementKey === selectedBitcoinHighlightKey.value) || bitcoinHighlights[3]
)
const bitcoinRadarChart = computed(() => {
  const ratios = {}
  bitcoinHighlights.forEach(h => ratios[h.elementKey] = h.ratio)
  return buildRadarChartData(ratios, { size: 300, maxRadius: 100, activeKey: selectedBitcoinHighlightKey.value })
})

function handleBitcoinHighlightSelect(key) {
  selectedBitcoinHighlightKey.value = key
}

// State: Profiles
const userName = ref('')
const gender = ref('')
const birthdate = ref('')
const birthtime = ref('')
const timeUnknown = ref(false)
const userImageUrl = ref('')
const selectedPresetId = ref(null)

const targetName = ref('')
const targetGender = ref('')
const targetBirthdate = ref('')
const targetBirthtime = ref('')
const targetTimeUnknown = ref(false)
const targetImageUrl = ref('')
const selectedTargetPresetId = ref(null)
const targetProfileEnabled = ref(false)

const quickPresetOptions = ref([])
const quickPresetLoading = ref(false)

// State: Analysis
const loading = ref(false)
const currentStageIndex = ref(0)
const loadingProgress = ref(0)
const analysisLogs = ref([])
const stageDebugLogs = ref([])
const errorMessage = ref('')
const showDebugLogs = ref(false)
const isAdmin = ref(localStorage.getItem('isAdmin') === 'true')

// State: Results
const userVsBitcoinResult = ref(null)
const targetVsBitcoinResult = ref(null)
const userVsTargetResult = ref(null)
const pairCompatibilityResult = ref(null)
const hasAnyResult = computed(() => !!(userVsBitcoinResult.value || targetVsBitcoinResult.value || userVsTargetResult.value || pairCompatibilityResult.value))

const canStartAnalysis = computed(() => !!(birthdate.value || targetBirthdate.value))

// Constants for caching categories
const CACHE_CATEGORY = {
  STORY: 'story',
  SAJU_SUMMARY: 'saju_summary',
  USER_REPORT: 'user_report',
  TARGET_REPORT: 'target_report',
  TEAM_REPORT: 'duo_report',
  PAIR_REPORT: 'pair_report',
  HIGHLIGHT_USER: 'highlight_user',
  HIGHLIGHT_TARGET: 'highlight_target',
  HIGHLIGHT_DUO: 'highlight_duo',
  HIGHLIGHT_PAIR: 'highlight_pair'
}

let analysisRunId = 0
let abortController = null

onMounted(() => {
  loadQuickPresets()
})

onBeforeUnmount(() => {
  if (abortController) abortController.abort()
})

async function loadQuickPresets() {
  quickPresetLoading.value = true
  try {
    const presets = await fetchCompatibilityQuickPresets()
    quickPresetOptions.value = presets
  } catch (error) {
    console.error('Failed to load presets', error)
  } finally {
    quickPresetLoading.value = false
  }
}

function applyQuickPreset(preset) {
  selectedPresetId.value = preset.id
  userName.value = preset.label
  gender.value = preset.gender || ''
  birthdate.value = preset.birthdate || ''
  birthtime.value = preset.birth_time || preset.birthtime || ''
  timeUnknown.value = !birthtime.value
  userImageUrl.value = preset.imageUrl || ''
}

function applyTargetQuickPreset(preset) {
  selectedTargetPresetId.value = preset.id
  targetName.value = preset.label
  targetGender.value = preset.gender || ''
  targetBirthdate.value = preset.birthdate || ''
  targetBirthtime.value = preset.birth_time || preset.birthtime || ''
  targetTimeUnknown.value = !targetBirthtime.value
  targetImageUrl.value = preset.imageUrl || ''
  targetProfileEnabled.value = true
}

function handleRemoveTarget() {
  targetProfileEnabled.value = false
  targetName.value = ''
  targetBirthdate.value = ''
  targetBirthtime.value = ''
  targetTimeUnknown.value = false
  targetImageUrl.value = ''
  selectedTargetPresetId.value = null
  targetVsBitcoinResult.value = null
  userVsTargetResult.value = null
  pairCompatibilityResult.value = null
}

function addAnalysisLog(msg) {
  analysisLogs.value.push(msg)
}

function addDebugLog(msg) {
  stageDebugLogs.value.push(msg)
}

function handleCancelAnalysis() {
  if (abortController) abortController.abort()
  loading.value = false
  currentStageIndex.value = 0
  loadingProgress.value = 0
}

// Utility: Build Cache Payload
function serializeProfile(p) {
  if (!p) return null
  return {
    name: p.name,
    birthdate: p.birthdate,
    birth_time: p.birthtime,
    gender: p.gender,
    zodiac: p.zodiac,
    yin_yang: p.yinYang,
    element: p.elementLabel
  }
}

function buildCachePayload(category, profile, targetProfile = null, extra = null) {
  const payload = { category }
  if (profile) payload.profile = serializeProfile(profile)
  if (targetProfile) payload.target_profile = serializeProfile(targetProfile)
  if (extra) payload.extra = extra
  return payload
}

// Main Analysis Logic
async function handleCompatibility() {
  if (!canStartAnalysis.value || loading.value) return

  const runId = ++analysisRunId
  loading.value = true
  errorMessage.value = ''
  analysisLogs.value = []
  stageDebugLogs.value = []
  currentStageIndex.value = 0
  loadingProgress.value = 10
  
  userVsBitcoinResult.value = null
  targetVsBitcoinResult.value = null
  userVsTargetResult.value = null
  pairCompatibilityResult.value = null

  abortController = new AbortController()
  const signal = abortController.signal

  try {
    // 1. Resolve Profiles
    const userProfile = birthdate.value ? buildProfileData('user') : null
    const targetProfile = (targetProfileEnabled.value && targetBirthdate.value) ? buildProfileData('target') : null
    const bitcoinProfile = buildBitcoinProfile()

    // 2. Story Stage
    currentStageIndex.value = 0
    loadingProgress.value = 20
    const stories = await runStoryStage(userProfile, targetProfile, signal)
    if (runId !== analysisRunId) return

    // 3. Analysis Stage (Saju + Reports)
    currentStageIndex.value = 1
    loadingProgress.value = 40
    await runAnalysisStage(userProfile, targetProfile, bitcoinProfile, stories, signal)
    if (runId !== analysisRunId) return

    // 4. Team / Pair Stage
    currentStageIndex.value = 2
    loadingProgress.value = 70
    await runTeamStage(userProfile, targetProfile, bitcoinProfile, signal)
    if (runId !== analysisRunId) return

    // 5. Finalize
    currentStageIndex.value = 3
    loadingProgress.value = 100
    loading.value = false
    addAnalysisLog('분석이 모두 완료되었습니다.')

  } catch (error) {
    if (error.name === 'AbortError') return
    console.error('Analysis failed', error)
    errorMessage.value = error.message || '분석 중 오류가 발생했습니다.'
    loading.value = false
  }
}

function buildProfileData(type) {
  const name = type === 'user' ? userName.value || DEFAULT_USER_NAME : targetName.value || '비교 대상'
  const date = type === 'user' ? birthdate.value : targetBirthdate.value
  const time = type === 'user' ? birthtime.value : targetBirthtime.value
  const unknown = type === 'user' ? timeUnknown.value : targetTimeUnknown.value
  const g = type === 'user' ? gender.value : targetGender.value
  
  const [y, m, d] = date.split('-').map(Number)
  const saju = calculateSajuElement(y, m, d)
  const zodiac = calculateZodiacSign(y)
  const yinYang = calculateYinYang(y, m, d)
  
  const genderLabel = g === 'male' ? '남성' : g === 'female' ? '여성' : '미입력'
  const facts = [
    `생년월일: ${date}`,
    `성별: ${genderLabel}`,
    `시간: ${unknown ? '시간 미상' : time || '미입력'}`,
    `일간/오행: ${saju.element.label} (${saju.element.summary})`,
    `띠: ${zodiac}띠`,
    `음양: ${yinYang}`
  ]

  return {
    name,
    birthdate: date,
    birthtime: time,
    timeUnknown: unknown,
    gender: g,
    elementLabel: saju.element.label,
    elementKey: saju.element.key,
    zodiac,
    yinYang,
    facts,
    radarData: buildRadarChartData({ [saju.element.key]: 60 }, { size: 120, maxRadius: 40 })
  }
}

function buildBitcoinProfile() {
  const date = '2009-01-03'
  const [y, m, d] = [2009, 1, 3]
  const saju = calculateSajuElement(y, m, d)
  return {
    name: '비트코인',
    birthdate: date,
    elementLabel: saju.element.label,
    elementKey: saju.element.key,
    zodiac: calculateZodiacSign(y),
    yinYang: calculateYinYang(y, m, d)
  }
}

async function runStoryStage(user, target, signal) {
  const results = { user: null, target: null }
  const tasks = []

  if (user) {
    tasks.push((async () => {
      addAnalysisLog('사용자의 인물 서사를 분석 중입니다...')
      const story = await callStoryAgent(user, '사용자', signal)
      results.user = story
      addAnalysisLog('사용자 서사 분석 완료.')
    })())
  }

  if (target) {
    tasks.push((async () => {
      addAnalysisLog('비교 대상의 인물 서사를 분석 중입니다...')
      const story = await callStoryAgent(target, '비교 대상', signal)
      results.target = story
      addAnalysisLog('비교 대상 서사 분석 완료.')
    })())
  }

  await Promise.all(tasks)
  return results
}

async function callStoryAgent(profile, role, signal) {
  const context = [
    `인물: ${profile.name} (${role})`,
    ...profile.facts
  ].join('\n')

  const resp = await runCompatibilityAgent({
    agentKey: 'story_extractor',
    context,
    cache: buildCachePayload(CACHE_CATEGORY.STORY, profile),
    signal
  })
  return resp.ok ? resp.narrative : ''
}

async function runAnalysisStage(user, target, bitcoin, stories, signal) {
  const tasks = []

  if (user) {
    tasks.push((async () => {
      addAnalysisLog('사용자와 비트코인의 궁합을 분석 중입니다...')
      const res = await callReportAgent(user, bitcoin, stories.user, 'user_report', signal)
      userVsBitcoinResult.value = {
        ...res,
        profileFacts: user.facts,
        personStory: stories.user,
        profileRadarData: user.radarData
      }
      addAnalysisLog('사용자 궁합 리포트 생성 완료.')
      await runHighlight(userVsBitcoinResult.value, CACHE_CATEGORY.HIGHLIGHT_USER, user, bitcoin, signal)
    })())
  }

  if (target) {
    tasks.push((async () => {
      addAnalysisLog('비교 대상과 비트코인의 궁합을 분석 중입니다...')
      const res = await callReportAgent(target, bitcoin, stories.target, 'target_report', signal)
      targetVsBitcoinResult.value = {
        ...res,
        profileFacts: target.facts,
        personStory: stories.target,
        profileRadarData: target.radarData
      }
      addAnalysisLog('비교 대상 궁합 리포트 생성 완료.')
      await runHighlight(targetVsBitcoinResult.value, CACHE_CATEGORY.HIGHLIGHT_TARGET, target, bitcoin, signal)
    })())
  }

  await Promise.all(tasks)
}

async function callReportAgent(profile, target, story, type, signal) {
  const context = [
    `대상: ${profile.name}`,
    `스토리: ${story}`,
    `사주 정보: ${profile.facts.join(', ')}`,
    `비교 대상: ${target.name} (사주: ${target.elementLabel})`
  ].join('\n')

  const cacheCat = type === 'user_report' ? CACHE_CATEGORY.USER_REPORT : CACHE_CATEGORY.TARGET_REPORT
  const resp = await runCompatibilityAgent({
    agentKey: 'saju_bitcoin',
    context,
    cache: buildCachePayload(cacheCat, profile, target, { scope: type }),
    signal
  })
  
  return {
    narrative: resp.ok ? resp.narrative : '',
    agentProvider: resp.model || resp.provider,
    highlightedNarrative: '',
    highlightLoading: false
  }
}

async function runTeamStage(user, target, bitcoin, signal) {
  if (!user || !target) return

  addAnalysisLog('두 사람의 팀 시너지 및 상호 궁합을 분석 중입니다...')
  
  const teamTask = (async () => {
    const context = `사용자: ${user.name} (${user.elementLabel})\n비교 대상: ${target.name} (${target.elementLabel})\n비트코인과의 팀 궁합을 분석하라.`
    const resp = await runCompatibilityAgent({
      agentKey: 'saju_bitcoin',
      context,
      cache: buildCachePayload(CACHE_CATEGORY.TEAM_REPORT, user, target, { scope: 'duo_vs_bitcoin' }),
      signal
    })
    userVsTargetResult.value = {
      narrative: resp.ok ? resp.narrative : '',
      agentProvider: resp.model || resp.provider,
      highlightedNarrative: '',
      highlightLoading: false
    }
    await runHighlight(userVsTargetResult.value, CACHE_CATEGORY.HIGHLIGHT_DUO, user, target, signal)
  })()

  const pairTask = (async () => {
    const context = `두 사람(${user.name}, ${target.name})의 직접적인 사주 상생을 분석하라.`
    const resp = await runCompatibilityAgent({
      agentKey: 'pair_compatibility',
      context,
      cache: buildCachePayload(CACHE_CATEGORY.PAIR_REPORT, user, target, { scope: 'direct_pair' }),
      signal
    })
    pairCompatibilityResult.value = {
      narrative: resp.ok ? resp.narrative : '',
      agentProvider: resp.model || resp.provider,
      highlightedNarrative: '',
      highlightLoading: false
    }
    await runHighlight(pairCompatibilityResult.value, CACHE_CATEGORY.HIGHLIGHT_PAIR, user, target, signal)
  })()

  await Promise.all([teamTask, pairTask])
  addAnalysisLog('시너지 및 상호 궁합 분석 완료.')
}

async function runHighlight(result, category, profile, target, signal) {
  if (!result || !result.narrative) return
  result.highlightLoading = true
  try {
    const context = `다음 텍스트에서 핵심 구절을 하이라이트하라:\n\n${result.narrative}`
    const resp = await runCompatibilityAgent({
      agentKey: 'highlight_story',
      context,
      cache: buildCachePayload(category, profile, target),
      signal
    })
    if (resp.ok) {
      result.highlightedNarrative = resp.narrative
    }
  } catch (e) {
    console.warn('Highlight failed', e)
  } finally {
    result.highlightLoading = false
  }
}

</script>

<style scoped>
.scroll-container::-webkit-scrollbar {
  height: 4px;
}
.scroll-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

@keyframes shine {
  from { transform: translateX(-100%); }
  to { transform: translateX(100%); }
}
.group-hover\:animate-shine {
  animation: shine 1.5s infinite;
}
</style>
