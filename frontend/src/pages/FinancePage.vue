<template>
  <div class="space-y-6">
    <section class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6">
      <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 class="text-lg font-semibold text-slate-900">재무 관리</h2>
          <p class="text-sm text-slate-500 mt-1">
            비트코인과 주요 자산군의 과거/미래 수익률을 한 화면에서 비교하세요.
          </p>
        </div>
        <div class="flex rounded-xl bg-slate-100 p-1 w-full md:w-auto">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            class="flex-1 px-4 py-2 text-sm font-medium rounded-lg transition-colors"
            :class="activeTab === tab.key
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-500'"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>
      </div>
    </section>

    <section v-if="activeTab === 'historical'" class="space-y-6">
      <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 space-y-5">
        <div class="flex flex-col gap-1">
          <h3 class="text-base font-semibold text-slate-900">과거 비트코인 수익률</h3>
          <p class="text-sm text-slate-500">
            AI 분석 엔진에 한국어로 질문하면 최대 10개의 비교 자산 데이터를 받아 라인 차트로 비교합니다.
          </p>
        </div>

        <div class="space-y-4">
          <div>
            <p class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">자주 사용하는 요청</p>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="option in quickRequestOptions"
                :key="option.key"
                @click="handleQuickRequest(option)"
                class="px-3 py-1.5 rounded-full border text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                :disabled="loading"
                :class="selectedQuickKey === option.key
                  ? 'bg-slate-900 text-white border-slate-900'
                  : 'border-slate-200 text-slate-600 hover:border-slate-400'"
              >
                {{ option.label }}
              </button>
            </div>
          </div>

          <div class="space-y-2">
            <label class="text-sm font-medium text-slate-700">질문 프롬프트</label>
            <div class="flex gap-2 items-center">
              <input
                v-model="prompt"
                type="text"
                class="flex-1 rounded-2xl border border-slate-200 px-4 py-2.5 text-sm focus:ring-2 focus:ring-slate-900 focus:border-slate-900 disabled:bg-slate-50 disabled:text-slate-400"
                placeholder="예) 비트코인과 금/미국 국채의 지난 10년 연평균 수익률을 비교해줘"
                :disabled="loading"
                @keyup.enter.prevent="runAnalysis"
              />
              <button
                v-if="!loading"
                class="shrink-0 w-11 h-11 rounded-2xl bg-slate-900 text-white flex items-center justify-center"
                @click="runAnalysis"
                title="분석 실행"
                aria-label="분석 실행"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </button>
              <button
                v-else
                class="shrink-0 w-11 h-11 rounded-2xl bg-rose-500 text-white flex items-center justify-center"
                @click="cancelRequest"
                title="요청 취소"
                aria-label="요청 취소"
              >
                <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <p v-if="errorMessage" class="text-xs text-rose-600">{{ errorMessage }}</p>
          </div>


        </div>
      </div>

      <div v-if="analysis || loading" class="space-y-5">

        <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div class="text-sm font-semibold text-slate-800">자산 표시 통화</div>
          <div class="inline-flex bg-slate-100 rounded-2xl p-1">
            <button
              v-for="option in currencyOptions"
              :key="option.key"
              class="px-3 py-1.5 rounded-xl text-xs font-semibold transition"
              :class="currencyMode === option.key ? 'bg-white text-slate-900 shadow' : 'text-slate-500'"
              @click="currencyMode = option.key"
            >
              {{ option.label }}
            </button>
          </div>
        </div>
        <p class="text-xs text-slate-500">
          <span v-if="loading">환율 정보 로딩 중...</span>
          <span v-else-if="!analysis">환율 정보를 불러오려면 분석을 실행하세요.</span>
          <span v-else>1 USD ≈ ₩{{ formatFxRate(fxRate) }} (실시간 환율)</span>
        </p>

        <FinanceLineChart
          :series="visibleSeries"
          :colors="colorMap"
          :currency-mode="currencyMode"
          :fx-rate="fxRate"
          :loading="loading"
          :logs="progressLogs"
          :start-year="analysis?.start_year"
          :end-year="analysis?.end_year"
        />

        <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 space-y-4">
          <div class="flex items-center justify-between">
            <h4 class="text-sm font-semibold text-slate-900">범례</h4>
          </div>
          <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            <button
              v-for="series in sortedLegend"
              :key="series.id"
              class="flex items-center justify-between rounded-2xl border px-4 py-3 text-left transition"
              :class="hiddenSeries.has(series.id)
                ? 'border-slate-200 text-slate-400 bg-slate-50'
                : 'border-slate-200 text-slate-800 hover:border-slate-400'"
              @click="toggleSeries(series.id)"
            >
              <div class="flex items-center gap-3">
                <span
                  class="w-9 h-2 rounded-full"
                  :style="{ backgroundColor: legendColorMap[series.id] || legendColors[0], opacity: hiddenSeries.has(series.id) ? 0.3 : 1 }"
                />
                <div>
                  <p class="text-sm font-semibold">{{ series.label }}</p>
                  <p class="text-xs text-slate-500">
                    {{ series.category || '자산군 정보 없음' }}
                  </p>
                </div>
              </div>
              <div class="text-xs text-slate-500 text-right">
                <p>연평균 {{ formatPercent(series.annualized_return_pct) }}</p>
                <p>{{ comparisonYears }}년 전 대비 {{ formatMultiple(series.multiple_from_start) }}배</p>
              </div>
            </button>
          </div>
        </div>
      </div>

      <div
        v-else
        class="bg-slate-50 border border-dashed border-slate-200 rounded-2xl p-6 text-sm text-slate-600"
      >
        아직 분석된 데이터가 없습니다. 프롬프트를 작성하거나 상단 태그를 눌러 예시 요청을 실행해 보세요.
      </div>
    </section>

    <section v-else class="space-y-4">
      <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 space-y-4">
        <h3 class="text-base font-semibold text-slate-900">미래 비트코인 수익률 시나리오</h3>
        <p class="text-sm text-slate-600">
          온체인 사이클, 거시 환경, 채택률을 기준으로 3가지 시나리오를 구성했습니다.
          실사용 데이터가 업데이트되면 자동으로 보정하도록 설계되어 있습니다.
        </p>
        <div class="grid gap-4 md:grid-cols-3">
          <div
            v-for="scenario in futureScenarios"
            :key="scenario.title"
            class="rounded-2xl border border-slate-200 p-4 bg-slate-50"
          >
            <p class="text-xs font-semibold text-slate-500 uppercase mb-1">{{ scenario.title }}</p>
            <p class="text-sm font-semibold text-slate-900 mb-2">{{ scenario.headline }}</p>
            <ul class="space-y-1 text-xs text-slate-500">
              <li>1년 기대 수익률: {{ scenario.oneYear }}</li>
              <li>3년 연평균: {{ scenario.threeYear }}</li>
              <li>핵심 변수: {{ scenario.trigger }}</li>
            </ul>
          </div>
        </div>
        <p class="text-xs text-slate-500">
          실제 투자 판단은 별도의 리서치를 병행하세요. 본 시나리오는 참고용입니다.
        </p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import FinanceLineChart from '@/components/FinanceLineChart.vue'
import { fetchHistoricalReturns } from '@/services/financeService'

const tabs = [
  { key: 'historical', label: '과거 수익률' },
  { key: 'future', label: '미래 시나리오' }
]

const quickRequestOptions = [
  {
    key: 'safe',
    label: '안전 자산과 비교',
    example: '비트코인과 금, 미국 10년물 국채, 은, S&P 500, 다우지수, 나스닥 100 등을 포함한 10개 안전 자산의 2016년 이후 연평균 수익률을 알려줘',
    quickRequest: '비트코인, 금, 미국 10년물 국채, 은, S&P 500, 다우지수, 나스닥 100, 달러지수, 채권 ETF, 금광주',
    context: null
  },
  {
    key: 'usTech',
    label: '미국 빅테크와 비교',
    example: '비트코인과 미국 빅테크 10개 종목(애플, 마이크로소프트, 알파벳, 아마존, 메타, 테슬라, 엔비디아, 넷플릭스, 어도비, AMD)의 지난 10년 연평균 수익률을 비교해줘',
    quickRequest: '미국 빅테크 10개 종목의 지난 10년 연평균 수익률을 알려줘',
    context: 'us_bigtech'
  },
  {
    key: 'krEquity',
    label: '국내 주식과 비교',
    example: '비트코인과 코스피 지수의 10년 연평균 수익률을 비교해줘',
    quickRequest: '비트코인과 코스피 지수의 10년 연평균 수익률을 비교해줘',
    context: 'kr_kospi'
  }
]

const currencyOptions = [
  { key: 'usd', label: '$ USD' },
  { key: 'krw', label: '₩ KRW' }
]

const futureScenarios = [
  {
    title: 'Defensive',
    headline: '보수적인 미래 수익률',
    oneYear: '연 +5% ~ +8%',
    threeYear: '연평균 +10%',
    trigger: '고금리·규제 강화'
  },
  {
    title: 'Base',
    headline: '기본 시나리오 수익률',
    oneYear: '연 +12% ~ +20%',
    threeYear: '연평균 +22%',
    trigger: 'ETF 유입·기관 수요'
  },
  {
    title: 'Growth',
    headline: '고성장 수익률 전망',
    oneYear: '연 +25% ~ +40%',
    threeYear: '연평균 +35%',
    trigger: '온체인 확장·네트워크 효과'
  }
]

// 라인 차트 색상 (진한 색상)
const lineColors = ['#0f172a', '#2563eb', '#f97316', '#dc2626', '#059669', '#7c3aed', '#ea580c', '#0891b2', '#be185d', '#4338ca']

// 범례 박스 색상 (밝은 색상 - 라인과 구분)
const legendColors = ['#94a3b8', '#93c5fd', '#fdba74', '#fca5a5', '#6ee7b7', '#c4b5fd', '#fed7aa', '#67e8f9', '#f9a8d4', '#a5b4fc']

const activeTab = ref('historical')
const prompt = ref('')
const selectedQuickKey = ref('')
const selectedQuickRequests = ref([])
const selectedContextKey = ref('')
const currencyMode = ref('usd')
const hiddenSeries = ref(new Set())
const loading = ref(false)
const errorMessage = ref('')
const analysis = ref(null)
let abortController = null
const progressLogs = ref([])
const progressTimers = []

const comparisonYears = computed(() => {
  if (!analysis.value) return 0
  return Math.max(1, analysis.value.end_year - analysis.value.start_year)
})

const defaultSummary = computed(() => {
  if (!analysis.value) return ''
  return `${analysis.value.start_year}년부터 ${analysis.value.end_year}년까지의 누적 수익률입니다.`
})

const visibleSeries = computed(() => {
  if (!analysis.value) return []
  return analysis.value.series.filter((series) => !hiddenSeries.value.has(series.id))
})

const sortedLegend = computed(() => {
  if (!analysis.value?.series) return []
  return [...analysis.value.series].sort((a, b) => {
    const aVal = typeof a.annualized_return_pct === 'number' ? a.annualized_return_pct : -Infinity
    const bVal = typeof b.annualized_return_pct === 'number' ? b.annualized_return_pct : -Infinity
    return bVal - aVal
  })
})

// 라인 차트용 색상 맵
const colorMap = computed(() => {
  if (!analysis.value?.series) return {}
  const map = {}
  analysis.value.series.forEach((series, index) => {
    map[series.id] = lineColors[index % lineColors.length]
  })
  return map
})

// 범례 박스용 색상 맵
const legendColorMap = computed(() => {
  if (!analysis.value?.series) return {}
  const map = {}
  analysis.value.series.forEach((series, index) => {
    map[series.id] = legendColors[index % legendColors.length]
  })
  return map
})

const fxRate = computed(() => analysis.value?.fx_rate || 1300)
const analysisLogs = computed(() => analysis.value?.logs || [])
const displayLogs = computed(() => {
  if (loading.value) return progressLogs.value
  return analysisLogs.value
})

function handleQuickRequest(option) {
  if (selectedQuickKey.value === option.key) {
    selectedQuickKey.value = ''
    selectedQuickRequests.value = []
    selectedContextKey.value = ''
    return
  }
  selectedQuickKey.value = option.key
  selectedQuickRequests.value = [option.quickRequest]
  selectedContextKey.value = option.context || ''
  prompt.value = option.example
  runAnalysis()
}

function formatPercent(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '0.0%'
  return `${value.toFixed(1)}%`
}

function formatMultiple(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '0.0'
  return value.toFixed(1)
}

function formatFxRate(rate) {
  if (!Number.isFinite(rate)) return '1,300'
  return Math.round(rate).toLocaleString()
}

function toggleSeries(id) {
  const next = new Set(hiddenSeries.value)
  if (next.has(id)) {
    next.delete(id)
  } else {
    next.add(id)
  }
  hiddenSeries.value = next
}

function resetPrompt() {
  prompt.value = ''
  selectedQuickKey.value = ''
  selectedQuickRequests.value = []
  selectedContextKey.value = ''
  hiddenSeries.value = new Set()
  if (abortController) {
    abortController.abort()
    abortController = null
  }
  loading.value = false
  progressLogs.value = []
  clearProgressTimers()
}

function cancelRequest() {
  if (abortController) {
    abortController.abort()
    abortController = null
    loading.value = false
    clearProgressTimers()
    progressLogs.value.push('요청이 취소되었습니다.')
  }
}

async function runAnalysis() {
  if (abortController) {
    abortController.abort()
  }

  // 프롬프트가 바뀌면 기존 데이터 삭제
  analysis.value = null
  hiddenSeries.value = new Set()

  abortController = new AbortController()
  loading.value = true
  errorMessage.value = ''
  progressLogs.value = ['프롬프트 전송 중...']
  startProgressLogs()
  try {
    const payload = {
      prompt: prompt.value,
      quickRequests: selectedQuickRequests.value,
      contextKey: selectedContextKey.value,
      signal: abortController.signal
    }
    const result = await fetchHistoricalReturns(payload)
    analysis.value = result
    hiddenSeries.value = new Set()
  } catch (error) {
    if (error.name === 'AbortError') {
      errorMessage.value = '요청이 취소되었습니다.'
    } else {
      errorMessage.value = error.message || '분석 중 오류가 발생했습니다.'
    }
  } finally {
    loading.value = false
    abortController = null
    clearProgressTimers()
  }
}

const SAFE_ASSET_LABELS = [
  { keyword: ['비트코인', 'bitcoin', 'btc'], label: '비트코인' },
  { keyword: ['금', 'gold'], label: '금' },
  { keyword: ['미국 10년물', '10년물', 'treasury'], label: '미국 10년물 국채' },
  { keyword: ['은', 'silver'], label: '은' },
  { keyword: ['s&p', 'sp500', 's&p500'], label: 'S&P 500' },
  { keyword: ['다우', 'dow'], label: '다우 지수' },
  { keyword: ['나스닥', 'nasdaq'], label: '나스닥 100' }
]

const PRESET_LOG_MAP = {
  us_bigtech: ['애플(AAPL)', '마이크로소프트(MSFT)', '알파벳(GOOGL)', '아마존(AMZN)', '메타(META)', '테슬라(TSLA)', '엔비디아(NVDA)', '넷플릭스(NFLX)', '어도비(ADBE)', 'AMD(AMD)'],
  kr_kospi: ['비트코인(BTC)', '코스피 지수(KOSPI)']
}

function collectExpectedAssets() {
  const targets = new Set()
  const haystack = `${prompt.value} ${selectedQuickRequests.value.join(' ')}`.toLowerCase()
  SAFE_ASSET_LABELS.forEach((entry) => {
    if (entry.keyword.some((word) => haystack.includes(word.toLowerCase()))) {
      targets.add(entry.label)
    }
  })
  if (selectedContextKey.value && PRESET_LOG_MAP[selectedContextKey.value]) {
    PRESET_LOG_MAP[selectedContextKey.value].forEach((label) => targets.add(label))
  }
  return Array.from(targets)
}

function startProgressLogs() {
  clearProgressTimers()
  const assets = collectExpectedAssets()
  let delay = 600
  assets.forEach((asset, index) => {
    const timer = setTimeout(() => {
      progressLogs.value = [...progressLogs.value, `${asset} 데이터 가져오는 중...`]
    }, delay * (index + 1))
    progressTimers.push(timer)
  })
}

function clearProgressTimers() {
  while (progressTimers.length) {
    const timer = progressTimers.pop()
    clearTimeout(timer)
  }
}
</script>
