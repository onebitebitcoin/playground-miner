<template>
  <div class="space-y-6">
    <header class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 mb-2">재무 관리</h1>
        <p class="text-gray-600">
          비트코인과 주요 자산군의 과거/미래 수익률을 한 화면에서 비교하세요.
        </p>
      </div>
      <div class="flex rounded-xl bg-slate-100 p-1 w-full md:w-auto md:min-w-[320px]">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="flex-1 px-4 py-2 text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
          :class="activeTab === tab.key
            ? 'bg-white text-slate-900 shadow-sm'
            : 'text-slate-500'"
          :disabled="tab.disabled"
          :aria-disabled="tab.disabled ? 'true' : 'false'"
          :title="tab.disabled ? tab.disabledLabel || '현재 비활성화된 탭입니다' : undefined"
          @click="handleTabClick(tab)"
        >
          {{ tab.label }}
        </button>
      </div>
    </header>

    <section v-if="activeTab === 'historical'" class="space-y-6">
      <div class="space-y-5">
        <div class="space-y-4">
          <FinanceHeroSection
            v-model:years="investmentYearsAgo"
            v-model:amount="investmentAmount"
            :investment-years-ago="investmentYearsAgo"
            :investment-amount="investmentAmount"
            :formatted-investment-amount-number="formattedInvestmentAmountNumber"
            :hero-animation-active="heroAnimationActive"
            :displayed-hero-text="displayedHeroText"
            :hero-animation-key="heroAnimationKey"
            :loading="loading"
            :custom-asset-resolving="customAssetResolving"
            :search-button-attention="searchButtonAttention"
            @search="handleSearchClick"
            @update:years="investmentYearsAgo = $event"
            @update:amount="investmentAmount = $event"
          >
            <template #extra>
              <FinanceAssetSelection
                :quick-compare-groups="quickCompareGroups"
                :quick-compare-groups-loading="quickCompareGroupsLoading"
                :selected-quick-compare-group="selectedQuickCompareGroup"
                :quick-compare-loading-key="quickCompareLoadingKey"
                :custom-assets="customAssets"
                :custom-asset-resolving="customAssetResolving"
                :loading="loading"
                v-model:new-asset-input="newAssetInput"
                :custom-asset-error="customAssetError"
                @apply-quick-compare="applyQuickCompare($event, { autoRun: false })"
                @clear-all="clearAllCustomAssets"
                @remove-asset="removeAsset"
                @add-asset="addAsset"
              />
            </template>
          </FinanceHeroSection>

          <p v-if="errorMessage" class="text-xs text-rose-600">{{ errorMessage }}</p>
        </div>
      </div>

      <!-- Chart and Details Section -->
      <div v-if="analysis && !loading" class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 space-y-5">
        <FinanceAnalysisSummary
          :bitcoin-hero-summary="bitcoinHeroSummary"
          :analysis-summary="analysisSummary"
        />

        <p class="text-xs text-slate-500">
          1 USD ≈ ₩{{ formatFxRate(fxRate) }} (실시간 환율)
        </p>

        <FinanceLineChart
          :key="chartRenderKey"
          :series="chartSeries"
          :colors="colorMap"
          :currency-mode="'usd'"
          :fx-rate="fxRate"
          :loading="loading"
          :logs="analysisLogs"
          :start-year="displayStartYear || sliderMinYear"
          :end-year="analysis?.end_year"
          :original-start-year="sliderMinYear"
          :show-year-slider="!!analysis"
          :tax-included="includeTax"
          :show-tax-toggle="true"
          :dividend-included="includeDividends"
          :show-dividend-toggle="true"
          :dividend-toggle-pending="dividendTogglePending"
          :price-data="priceTableData"
          :calculation-method="analysisResultType"
          :bitcoin-summary="bitcoinPerformanceText"
          @update:start-year="displayStartYear = $event"
          @toggle-tax="includeTax = !includeTax"
          @toggle-dividends="handleDividendToggle"
        />

        <FinanceLegend
          :sorted-legend="sortedLegend"
          :color-map="colorMap"
          :hidden-series="hiddenSeries"
          :analysis-result-type="analysisResultType"
          :data-sources-text="dataSourcesText"
          :get-legend-label="getLegendLabel"
          @toggle-series="toggleSeries"
        />

        <FinancePriceTable
          :table-years="tableYears"
          :sorted-legend="sortedLegend"
          :analysis-result-type="analysisResultType"
          :get-asset-url="getAssetUrl"
          :get-legend-label="getLegendLabel"
          :format-value="getReturnForYear"
          :get-cell-class="getReturnCellClass"
          v-model:price-table-mode="priceTableMode"
        />

        <div class="flex items-center gap-2 text-xs text-slate-400 pt-3 border-t border-slate-100">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <span>{{ analysis.start_year }}년부터 {{ analysis.end_year }}년까지의 과거 데이터를 기반으로 계산되었습니다</span>
        </div>
      </div>

      <FinanceLoadingPanel
        v-if="loading"
        :label="loadingStageLabel"
        :description="loadingStageDescription"
        :progress="loadingProgress"
        @cancel="handleCancelClick"
      />

      <div v-if="!analysis && !loading" class="bg-slate-50 border border-dashed border-slate-200 rounded-2xl p-6 text-sm text-slate-600">
        아직 분석된 데이터가 없습니다. 상단 텍스트를 조정하거나 빠른 비교 태그를 눌러 예시 요청을 실행해 보세요.
      </div>

      <AdminPromptPanel
        v-if="allowRealtimeLogs"
        class="mt-6"
        v-model:show-debug="showDebugLogs"
        :display-logs="analysisLogs"
      />
    </section>

    <FinanceFutureTab
      v-else
      :scenarios="futureScenarios"
    />
  </div>
</template>

<script setup>
import { computed, ref, watch, onBeforeUnmount, onMounted, reactive } from 'vue'
import FinanceLineChart from '@/components/FinanceLineChart.vue'
import AdminPromptPanel from '@/components/AdminPromptPanel.vue'
import FinanceHeroSection from './finance/components/FinanceHeroSection.vue'
import FinanceAssetSelection from './finance/components/FinanceAssetSelection.vue'
import FinanceAnalysisSummary from './finance/components/FinanceAnalysisSummary.vue'
import FinanceLegend from './finance/components/FinanceLegend.vue'
import FinancePriceTable from './finance/components/FinancePriceTable.vue'
import FinanceLoadingPanel from './finance/components/FinanceLoadingPanel.vue'
import FinanceFutureTab from './finance/components/FinanceFutureTab.vue'

import {
  fetchHistoricalReturnsStream,
  fetchHistoricalReturns,
  resolveCustomAsset,
  fetchFinanceQuickCompareGroups,
  addSingleAsset
} from '@/services/financeService'
import { defaultFinanceQuickCompareGroups } from '@/config/financeQuickCompareGroups'

const TAX_RATE = 0.22
const KR_INTEREST_TAX_RATE = 0.154
const KR_EQUITY_TAX_FREE_ALLOWANCE = 50000000
const HERO_ANIMATION_DURATION = 2800
const MIN_DIVIDEND_YIELD_DISPLAY = 0.1
const LOADING_STAGES = [
  {
    key: 'init',
    label: '요청 준비 중',
    description: '멀티 에이전트 구성을 시작하고 있어요.',
    minProgress: 5,
    maxProgress: 12,
    fallbackDelayMs: 0,
    autoIncrement: 1,
    matchers: ['시스템:', '분석 시작', '분석 요청']
  },
  {
    key: 'intent',
    label: '프롬프트 해석 중',
    description: '요청에서 비교할 자산을 해석하고 있어요.',
    minProgress: 15,
    maxProgress: 30,
    fallbackDelayMs: 1500,
    autoIncrement: 2,
    matchers: ['[의도 분석]', 'intent']
  },
  {
    key: 'data',
    label: '자산 데이터 수집 중',
    description: '각 자산의 연도별 가격 데이터를 불러오고 있어요.',
    minProgress: 30,
    maxProgress: 70,
    fallbackDelayMs: 3500,
    autoIncrement: 2,
    matchers: ['[데이터 수집]', 'price retriever', '데이터 가져오는 중']
  },
  {
    key: 'calc',
    label: '수익률 계산 중',
    description: '불러온 데이터를 바탕으로 수익률을 계산하고 있어요.',
    minProgress: 70,
    maxProgress: 90,
    fallbackDelayMs: 7000,
    autoIncrement: 1,
    matchers: ['[수익률 계산]', 'calculator']
  },
  {
    key: 'summary',
    label: '결과 정리 중',
    description: '분석 내용을 정리하고 보고서를 구성하고 있어요.',
    minProgress: 90,
    maxProgress: 99,
    fallbackDelayMs: 9500,
    autoIncrement: 1,
    matchers: ['[분석 생성]', 'analysis', '요약']
  }
]

const tabs = [
  { key: 'historical', label: '과거 수익률' },
  { key: 'future', label: '미래 시나리오', disabled: true, disabledLabel: '준비 중인 기능입니다' }
]

const QUICK_COMPARE_CONTEXT_MAP = {
  frequent: 'safe_assets',
  safe_assets: 'safe_assets',
  us_bigtech: 'us_bigtech',
  kr_bluechips: 'kr_equity',
  kr_equity: 'kr_equity',
  dividend_favorites: 'safe_assets'
}

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

// Historical Analysis State
const investmentYearsAgo = ref(10)
const investmentAmount = ref(100) // in 10k KRW
const baseInvestmentWon = computed(() => {
  const amount = Number(investmentAmount.value)
  if (!Number.isFinite(amount) || amount <= 0) return 10000
  return amount * 10000
})
const priceTableMode = ref('price')
const heroAnimationKey = ref(0)
const heroAnimationActive = ref(false)
const searchButtonAttention = ref(false)
const displayedHeroText = ref('')

let typingInterval = null
let heroAnimationTimer = null

const lineColors = [
  '#0f172a', '#2563eb', '#1d4ed8', '#059669', '#0d9488',
  '#0891b2', '#7c3aed', '#4338ca', '#4f46e5', '#8b5cf6'
]

const BITCOIN_COLOR = '#FFD700'
const KOREAN_M2_COLOR = '#dc2626'
const assignedSeriesColors = ref({})
let nextColorIndex = 0

const activeTab = ref('historical')
const handleTabClick = (tab) => {
  if (tab.disabled) return
  activeTab.value = tab.key
}

const prompt = ref('')
const selectedContextKey = ref('safe_assets')
const hiddenSeries = ref(new Set())
const customAssetError = ref('')
const includeTax = ref(true)
const includeDividends = ref(true)
const dividendCache = reactive({ true: null, false: null })
const dividendPrefetchStatus = reactive({ true: false, false: false })
const dividendTogglePending = ref(null)

let prefetchController = null
let dividendPrefetchPromise = null

const yearlyPriceMap = ref({})
const priceTableLoading = ref(false)
const currentYear = new Date().getFullYear()
const priceDisplayMode = ref('usd')
const priceTableData = ref({})
const customAssetResolving = ref(false)
const customAssets = ref([])
const customAssetsLoading = ref(false)
let Gt = 0
let vo = false
const newAssetInput = ref('')
const isAutoApplyEnabled = computed(() => selectedContextKey.value === 'kr_equity')

const loading = ref(false)
const errorMessage = ref('')
const analysis = ref(null)
const analysisResultType = ref('cagr')
const displayStartYear = ref(null)
const sliderMinYear = ref(null)

let abortController = null
const progressLogs = ref([])
const analysisLogs = computed(() => progressLogs.value)
const showDebugLogs = ref(false)

function appendProgressLogs(...messages) {
  if (!messages.length) return
  progressLogs.value = [...progressLogs.value, ...messages]
}

function resetColorAssignments() {
  assignedSeriesColors.value = {}
  nextColorIndex = 0
}

function updateColorAssignments(seriesList, { reset = false } = {}) {
  if (!Array.isArray(seriesList)) {
    if (reset) resetColorAssignments()
    return
  }
  const baseMap = reset ? {} : { ...assignedSeriesColors.value }
  if (reset) nextColorIndex = 0
  let changed = false
  seriesList.forEach((series) => {
    if (!series || !series.id) return
    if (isBitcoinLabel(series.label)) {
      if (baseMap[series.id] !== BITCOIN_COLOR) {
        baseMap[series.id] = BITCOIN_COLOR
        changed = true
      }
      return
    }
    if (isKoreanM2Label(series.label)) {
      if (baseMap[series.id] !== KOREAN_M2_COLOR) {
        baseMap[series.id] = KOREAN_M2_COLOR
        changed = true
      }
      return
    }
    if (baseMap[series.id]) return
    baseMap[series.id] = lineColors[nextColorIndex % lineColors.length]
    nextColorIndex += 1
    changed = true
  })
  if (changed || reset) {
    assignedSeriesColors.value = baseMap
  }
}

const loadingProgress = ref(0)
const currentStageIndex = ref(0)
const activeStage = computed(() => LOADING_STAGES[currentStageIndex.value] || LOADING_STAGES[0])
const loadingStageLabel = computed(() => activeStage.value?.label || '데이터를 준비하고 있어요.')

let priceDataProgressBumps = 0
let stageIncrementInterval = null

const quickCompareGroups = ref([])
const quickCompareGroupsLoading = ref(false)
const selectedQuickCompareGroup = ref('')
const feKey = ref('')
const allowRealtimeLogs = import.meta.env.DEV

watch(loading, (val) => {
  if (!val && searchButtonAttention.value) {
    searchButtonAttention.value = false
    requestAgentAnalysis()
  }
})

watch(loading, (val) => {
  if (!val) {
    startLoadingStageTracking()
  }
})

watch([loading, heroAnimationActive], ([loadingVal, animationVal]) => {
  if (!loadingVal && !animationVal) {
    searchButtonAttention.value = true
  }
}, { immediate: true })

function handleProgressLog(message) {
  if (!message) return
  const lower = message.toLowerCase()
  const stage = LOADING_STAGES.find((s) => 
    !Array.isArray(s.matchers) || !s.matchers.length ? false : s.matchers.some((m) => m && lower.includes(m.toLowerCase()))
  )
  if (stage) {
    advanceToStage(stage.key)
  }

  if (lower.includes('[데이터 수집]')) {
    advanceToStage('data')
    if (isCacheIndicator(message)) {
      bumpDataProgress()
    }
  }

  if (lower.includes('[수익률 계산]')) advanceToStage('calc')
  if (lower.includes('[분석 생성]')) advanceToStage('summary')

  if (message.includes('✓ 분석 완료')) {
    handleAnalysisCompletion()
  } else if (lower.includes('요청이 취소되었습니다') || lower.includes('오류')) {
    stopLoadingStageTracking()
  }
}

function isCacheIndicator(msg) {
  const low = msg.toLowerCase()
  return !!(msg.includes('✓') || low.includes('cache hit') || low.includes('캐시됨') || low.includes('수집 완료') || low.includes('데이터 포인트'))
}

function advanceToStage(key, { immediate = false } = {}) {
  const index = LOADING_STAGES.findIndex((s) => s.key === key)
  if (index === -1 || index < currentStageIndex.value) return

  currentStageIndex.value = index
  const stage = LOADING_STAGES[index]
  const targetProgress = immediate ? stage.maxProgress : stage.minProgress
  if (loadingProgress.value < targetProgress) {
    loadingProgress.value = targetProgress
  }

  if (stageIncrementInterval) {
    const timer = A.get(key)
    if (timer) {
      clearTimeout(timer)
      A.delete(key)
    }
  }
}

const A = new Map()
let M = null

function startLoadingStageTracking() {
  stopLoadingStageTracking()
  priceDataProgressBumps = 0
  if (!LOADING_STAGES.length) return

  currentStageIndex.value = 0
  loadingProgress.value = LOADING_STAGES[0].minProgress

  LOADING_STAGES.slice(1).forEach((stage) => {
    if (!Number.isFinite(stage.fallbackDelayMs)) return
    const timer = setTimeout(() => {
      advanceToStage(stage.key)
    }, stage.fallbackDelayMs)
    A.set(stage.key, timer)
  })

  M = setInterval(() => {
    const stage = activeStage.value
    if (!stage || loadingProgress.value >= stage.maxProgress) return
    const step = stage.autoIncrement ?? 1
    loadingProgress.value = Math.min(stage.maxProgress, loadingProgress.value + step)
  }, 1000)
}

function stopLoadingStageTracking() {
  A.forEach((timer) => clearTimeout(timer))
  A.clear()
  if (M) {
    clearInterval(M)
    M = null
  }
}

function bumpDataProgress() {
  const dataStage = LOADING_STAGES.find((s) => s.key === 'data')
  if (!dataStage) return
  priceDataProgressBumps += 1
  const range = Math.max(0, dataStage.maxProgress - dataStage.minProgress)
  const bumpValue = Math.min(range, priceDataProgressBumps * 4)
  const nextProgress = dataStage.minProgress + bumpValue
  if (nextProgress > loadingProgress.value) {
    loadingProgress.value = nextProgress
  }
}

function handleAnalysisCompletion() {
  const last = LOADING_STAGES[LOADING_STAGES.length - 1]
  if (last) advanceToStage(last.key, { immediate: true })
  loadingProgress.value = 100
  stopLoadingStageTracking()
}

const loadingStageDescription = computed(() => activeStage.value?.description || '데이터를 가져오는 중입니다.')

function handleCancelClick() {
  if (abortController) {
    abortController.abort()
    abortController = null
    loading.value = false
    stopLoadingStageTracking()
    appendProgressLogs('요청이 취소되었습니다.')
  }
  yearlyPriceMap.value = {}
  newAssetInput.value = ''
  customAssetResolving.value = false
}

function getSeriesMetaValue(series, key) {
  if (!series || !key) return undefined
  if (Object.prototype.hasOwnProperty.call(series, key)) return series[key]
  if (series.metadata && Object.prototype.hasOwnProperty.call(series.metadata, key)) {
    return series.metadata[key]
  }
  return undefined
}

function getSeriesDisplayCurrency(series) {
  return isKoreanEquitySeries(series) ? 'krw' : 'usd'
}

function getCurrencySymbolForMode(mode) {
  return mode === 'krw' ? '₩' : '$'
}

const analysisContainsKoreanEquities = computed(() => {
  return !!analysis.value?.series?.some((s) => isKoreanEquitySeries(s))
})

const filteredSeries = computed(() => {
  var _analysis$value, _analysis$value$serie
  if (!((_analysis$value = analysis.value) != null && (_analysis$value$serie = _analysis$value.series) != null && _analysis$value$serie.length)) return []
  const startY = displayStartYear.value || analysis.value.start_year
  const allowKoreanEquities = selectedContextKey.value === 'kr_equity' || analysisContainsKoreanEquities.value
  const series = analysis.value.series.filter((s) =>
    isBitcoinLabel(s.label) ||
    !isKoreanEquitySeries(s) ||
    allowKoreanEquities
  )

  if (!startY) return series

  const isPrice = analysisResultType.value === 'price'
  return series.map((s) => {
    const validPoints = s.points.filter((p) => p.year >= startY)
    if (validPoints.length < 2) return null
    const sortedPoints = [...validPoints].sort((a, b) => a.year - b.year)
    const taxTreatment = includeTax.value ? resolveTaxTreatment(s) : null
    const applyTax = Boolean(taxTreatment)

    if (isPrice) {
      const startV = resolvePointValue(sortedPoints[0])
      const lastV = resolvePointValue(sortedPoints[sortedPoints.length - 1])
      if (!Number.isFinite(startV) || !Number.isFinite(lastV) || startV <= 0 || lastV <= 0) return null

      const duration = sortedPoints[sortedPoints.length - 1].year - sortedPoints[0].year
      let annualizedReturn = 0
      let multipleFromStart = lastV / startV
      if (duration > 0 && Number.isFinite(multipleFromStart) && multipleFromStart > 0) {
        const adjustedMultiple = applyTax ? applyTaxToMultiple(multipleFromStart, duration, taxTreatment) : multipleFromStart
        multipleFromStart = adjustedMultiple
        const rate = Math.pow(adjustedMultiple, 1 / duration) - 1
        if (Number.isFinite(rate)) {
          annualizedReturn = rate * 100
        }
      } else if (applyTax && Number.isFinite(multipleFromStart) && multipleFromStart > 0) {
        multipleFromStart = applyTaxToMultiple(multipleFromStart, 0, taxTreatment)
      }
      const points = sortedPoints.map((p) => {
        const v = resolvePointValue(p)
        if (!Number.isFinite(v) || v <= 0) return null
        let multiple = v / startV

        if (applyTax) {
          const yearsElapsed = p.year - sortedPoints[0].year
          multiple = applyTaxToMultiple(multiple, yearsElapsed, taxTreatment)
        }

        return { ...p, unit: s.unit || p.unit, multiple, value: multiple }
      }).filter(Boolean)
      if (points.length < 2) return null
      return { ...s, points, annualized_return_pct: annualizedReturn, multiple_from_start: multipleFromStart }
    }

    const startMultiple = Number(sortedPoints[0].multiple)
    const endMultiple = Number(sortedPoints[sortedPoints.length - 1].multiple)
    const duration = sortedPoints[sortedPoints.length - 1].year - sortedPoints[0].year
    let annualizedReturn = 0
    let multipleFromStart = 1
    if (Number.isFinite(startMultiple) && startMultiple > 0 && Number.isFinite(endMultiple) && endMultiple > 0) {
      const baseMultiple = endMultiple / startMultiple
      if (duration > 0 && Number.isFinite(baseMultiple) && baseMultiple > 0) {
        const adjustedMultiple = applyTax ? applyTaxToMultiple(baseMultiple, duration, taxTreatment) : baseMultiple
        multipleFromStart = adjustedMultiple
        const rate = Math.pow(adjustedMultiple, 1 / duration) - 1
        if (Number.isFinite(rate)) {
          annualizedReturn = rate * 100
        }
      } else if (Number.isFinite(baseMultiple) && baseMultiple > 0) {
        multipleFromStart = applyTax ? applyTaxToMultiple(baseMultiple, 0, taxTreatment) : baseMultiple
      }
    }
    const points = sortedPoints.map((p) => {
      const m = Number(p.multiple)
      let relativeMultiple = m
      if (Number.isFinite(m) && Number.isFinite(startMultiple) && startMultiple > 0) {
        relativeMultiple = m / startMultiple
      }
      if (!Number.isFinite(relativeMultiple) || relativeMultiple <= 0) relativeMultiple = 1
      const yearsElapsed = p.year - sortedPoints[0].year
      if (applyTax) {
        relativeMultiple = applyTaxToMultiple(relativeMultiple, yearsElapsed, taxTreatment)
      }
      let cagr = 0
      if (yearsElapsed > 0 && relativeMultiple > 0) {
        const rate = Math.pow(relativeMultiple, 1 / yearsElapsed) - 1
        if (Number.isFinite(rate)) {
          cagr = rate * 100
        }
      }
      return { ...p, multiple: relativeMultiple, value: cagr }
    })
    return { ...s, points, annualized_return_pct: annualizedReturn, multiple_from_start: multipleFromStart }
  }).filter(Boolean)
})

function resolvePointValue(point) {
  if (!point) return null
  const raw = Number(point.raw_value ?? point.rawValue)
  if (Number.isFinite(raw)) return raw
  const val = Number(point.value)
  return Number.isFinite(val) ? val : null
}

const chartSeries = computed(() => {
  if (!filteredSeries.value.length) return []
  return filteredSeries.value.filter((s) => !hiddenSeries.value.has(s.id))
})

const requestedAssetsForLegend = computed(() => {
  const requestedList = analysis.value?.requested_assets
  if (Array.isArray(requestedList) && requestedList.length) {
    return requestedList
  }
  return customAssets.value
})

const missingLegendEntries = computed(() => {
  const requested = requestedAssetsForLegend.value
  if (!Array.isArray(requested) || !requested.length) return []
  const seriesList = analysis.value?.series || []

  return requested.map((asset) => {
    if (!asset) return null
    const tokens = buildTokenSetFromAsset(asset)
    if (!tokens.size) return null
    const hasMatch = seriesList.some((series) => tokenSetsIntersect(tokens, buildTokenSetFromSeries(series)))
    if (hasMatch) return null
    return buildFailedLegendSeries(asset)
  }).filter(Boolean)
})

const sortedLegend = computed(() => {
  const baseSeries = filteredSeries.value || []
  const sortedSeries = baseSeries.length ? [...baseSeries].sort((a, b) => {
    const valA = typeof a.annualized_return_pct === 'number' ? a.annualized_return_pct : -Infinity
    const valB = typeof b.annualized_return_pct === 'number' ? b.annualized_return_pct : -Infinity
    return valB - valA
  }) : []

  if (!missingLegendEntries.value.length) {
    return sortedSeries
  }
  return [...sortedSeries, ...missingLegendEntries.value]
})

const tableYears = computed(() => {
  const years = new Set()
  filteredSeries.value.forEach((s) => {
    s.points?.forEach((p) => {
      if (typeof p.year === 'number') years.add(p.year)
    })
  })
  return Array.from(years).sort((a, b) => a - b)
})

const colorMap = computed(() => ({ ...assignedSeriesColors.value }))

const fxRate = computed(() => (analysis.value?.fx_rate || 1300))

const chartRenderKey = computed(() => {
  return `chart-${includeTax.value}-${includeDividends.value}-${displayStartYear.value || ''}`
})

const dataSourcesText = computed(() => {
  const sources = new Set()

  const addSource = (sourceValue) => {
    if (!sourceValue) return
    const src = String(sourceValue).trim()
    if (src && src !== 'undefined' && src !== 'null') {
      sources.add(src)
    }
  }

  const processEntry = (entry) => {
    if (!entry || typeof entry !== 'object') return

    // Add main source
    addSource(entry.source || entry.data_source)

    // Add alternative sources
    const alt = entry.alt_sources || entry.altSources
    if (alt && typeof alt === 'object') {
      Object.values(alt).forEach(altSourceObj => {
        if (altSourceObj && typeof altSourceObj === 'object') {
          addSource(altSourceObj.source || altSourceObj.data_source)
        } else {
          addSource(altSourceObj)
        }
      })
    }
  }

  // Collect from series
  if (Array.isArray(analysis.value?.series)) {
    analysis.value.series.forEach(series => {
      addSource(series.source)
    })
  }

  // Collect from yearly_prices
  if (Array.isArray(analysis.value?.yearly_prices)) {
    analysis.value.yearly_prices.forEach(processEntry)
  }

  // Collect from chart_data_table
  if (Array.isArray(analysis.value?.chart_data_table)) {
    analysis.value.chart_data_table.forEach(processEntry)
  }

  // Collect from priceTableData
  Object.values(priceTableData.value || {}).forEach(processEntry)

  if (!sources.size) return '데이터 출처 정보 없음'

  const sourceList = Array.from(sources).filter(src => src && src !== 'Unknown')

  const sourceLinks = {
    'Yahoo Finance': { url: 'https://finance.yahoo.com', label: 'Yahoo Finance' },
    Stooq: { url: 'https://stooq.com', label: 'Stooq' },
    pykrx: { url: 'https://github.com/sharebook-kr/pykrx', label: 'pykrx' },
    Upbit: { url: 'https://upbit.com', label: 'Upbit' },
    ECOS: { url: 'https://ecos.bok.or.kr', label: 'ECOS' },
    FRED: { url: 'https://fred.stlouisfed.org', label: 'FRED' },
    'KB부동산': { url: 'https://kbland.kr/', label: 'KB부동산' },
    'KB부동산 (정적)': { url: 'https://kbland.kr/', label: 'KB부동산' },
    'KB부동산 (Agent)': { url: 'https://kbland.kr/', label: 'KB부동산' }
  }

  if (!sourceList.length) return '데이터 출처 정보 없음'

  return sourceList.map((src) => {
    const link = sourceLinks[src]
    if (link) {
      return `<a href="${link.url}" target="_blank" rel="noopener noreferrer" class="text-slate-700 underline decoration-dotted underline-offset-2 hover:text-slate-900">${link.label}</a>`
    }
    return `<span>${src}</span>`
  }).join(' / ')
})

function findMatchingCustomAsset(series) {
  if (!series) return null
  const tokens = new Set()
  const labelToken = normalizeAssetToken(series.label)
  const aliasToken = normalizeAssetToken(normalizeLabelAlias(series.label || ''))
  const tickerToken = normalizeAssetToken(series.ticker || series.id)
  ;[labelToken, aliasToken, tickerToken].forEach((token) => {
    if (token) tokens.add(token)
  })

  if (!tokens.size) return null

  return (
    customAssets.value.find((asset) => {
      const assetTokens = [
        normalizeAssetToken(asset.label),
        normalizeAssetToken(normalizeLabelAlias(asset.label || '')),
        normalizeAssetToken(asset.ticker)
      ].filter(Boolean)
      return assetTokens.some((token) => tokens.has(token))
    }) || null
  )
}

function normalizeAssetToken(val) {
  return (val || '').toString().trim().toLowerCase()
}

function resolvePreferredSeriesLabel(series, tickerCandidate) {
  const tryLabel = (value) => {
    if (!value) return ''
    const friendly = stripTickerSuffix(value, tickerCandidate)
    if (friendly && !isTickerLikeLabel(friendly)) {
      return friendly
    }
    return ''
  }

  const meta = series?.metadata || {}
  const candidateLabels = []
  const pushLabel = (value) => {
    if (value) candidateLabels.push(value)
  }

  pushLabel(series.display_label)
  pushLabel(meta.display_label)
  pushLabel(meta.localized_label)
  pushLabel(meta.kr_name)
  pushLabel(meta.korean_name)
  pushLabel(meta.name)
  pushLabel(meta.friendly_label)
  pushLabel(meta.original_label)

  const collectAliases = (aliases) => {
    if (!Array.isArray(aliases)) return
    aliases.forEach((alias) => pushLabel(alias))
  }

  collectAliases(series.aliases)
  collectAliases(meta.aliases)

  const priceEntry = findPriceEntry(series)
  if (priceEntry) {
    pushLabel(priceEntry.label)
    pushLabel(priceEntry.displayLabel)
    collectAliases(priceEntry.aliases)
  }

  for (const value of candidateLabels) {
    const resolved = tryLabel(value)
    if (resolved) return resolved
  }

  return ''
}

async function appendResolvedAsset(name, { silent = false, targetList = null } = {}) {
  const text = (name || '').trim()
  if (!text) return false
  const existingList = Array.isArray(targetList) ? targetList : customAssets.value
  if (assetExistsInList(text, null, existingList)) return false
  
  let result = null
  try {
    result = await resolveCustomAsset(text)
  } catch (error) {
    if (!silent) {
      customAssetError.value = error.message || '종목 정보를 가져오지 못했습니다.'
      setTimeout(() => {
        if (customAssetError.value === (error.message || '종목 정보를 가져오지 못했습니다.')) {
          customAssetError.value = ''
        }
      }, 5000)
    }
    throw error
  }

  const label = result?.label?.trim() || text
  const ticker = result?.ticker?.trim() || result?.id?.trim()
  if (assetExistsInList(label, ticker, existingList)) return false
  
  const isSyntheticAsset = Boolean(result?.synthetic_asset)
  const display = isSyntheticAsset ? label : Io(label, ticker)
  const entry = {
    id: result?.id || ticker || label,
    label,
    display,
    ticker,
    category: result?.category || '',
    unit: result?.unit || '',
    synthetic_asset: result?.synthetic_asset || '',
    target_rate_pct: result?.target_rate_pct
  }
  if (targetList) {
    targetList.push(entry)
  } else {
    customAssets.value = [...customAssets.value, entry]
  }
  if (!silent) customAssetError.value = ''
  return entry
}

function assetExistsInList(label, ticker, list = customAssets.value) {
  const lowLabel = normalizeAssetToken(label)
  const lowTicker = normalizeAssetToken(ticker)
  return list.some((a) => {
    const matchLabel = lowLabel && normalizeAssetToken(a.label) === lowLabel
    const matchTicker = lowTicker && normalizeAssetToken(a.ticker) === lowTicker
    return matchLabel || matchTicker
  })
}

function Io(label, ticker) {
  if (!label) return ''
  if (ticker) {
    const lowTicker = ticker.toLowerCase()
    const lowLabel = label.toLowerCase()
    if (lowTicker !== lowLabel && !lowLabel.includes(lowTicker)) {
      return `${label} (${ticker})`
    }
  }
  return label
}

async function loadResolvedAssets(assets = []) {
  const id = ++Gt
  customAssetResolving.value = true
  customAssetError.value = ''
  customAssets.value = []
  try {
    const entries = assets.map((a) => {
      const label = a.label || a.id || ''
      const ticker = a.ticker || a.id || ''
      const isSyntheticAsset = Boolean(a?.synthetic_asset)
      return {
        id: a.id || ticker || label,
        label,
        ticker,
        display: isSyntheticAsset ? label : Io(label, ticker),
        category: a.category || '',
        unit: a.unit || '',
        synthetic_asset: a?.synthetic_asset || '',
        target_rate_pct: a?.target_rate_pct
      }
    }).filter((a) => a.label)
    if (id === Gt) {
      customAssets.value = entries
    }
  } finally {
    if (id === Gt) customAssetResolving.value = false
  }
}

async function loadCustomAssetsFromList(assets = []) {
  const id = ++Gt
  customAssetResolving.value = true
  customAssetError.value = ''
  customAssets.value = []
  const pending = []
  try {
    for (const name of assets) {
      if (id !== Gt) return
      try {
        if (await appendResolvedAsset(name, { silent: true, targetList: pending }), id !== Gt) return
      } catch (error) {
        if (id !== Gt) return
        pending.push({ label: name, display: name })
      }
    }
    if (id === Gt) {
      customAssets.value = pending
    }
  } finally {
    if (id === Gt) customAssetResolving.value = false
  }
}

async function applyQuickCompare(key, options = {}) {
  ee.value = ''
  const { autoRun = true } = options
  const group = quickCompareGroups.value.find((g) => g.key === key)
  if (!group) {
    ee.value = '선택한 그룹 정보를 찾을 수 없습니다.'
    return
  }
  selectedQuickCompareGroup.value = key
  selectedContextKey.value = resolveGroupContextKey(group)
  feKey.value = key
  try {
    if (group.resolved_assets && group.resolved_assets.length > 0) {
      await loadResolvedAssets(group.resolved_assets)
    } else {
      await loadCustomAssetsFromList(group.assets || [])
    }
    if (autoRun) {
      prompt.value = buildPromptFromInputs()
      requestAgentAnalysis()
    }
  } catch (error) {
    ee.value = '빠른 비교를 실행하는 중 오류가 발생했습니다.'
  } finally {
    if (feKey.value === key) feKey.value = ''
  }
}

function normalizeGroups(raw = []) {
  return raw.map((g, i) => {
    const assets = (Array.isArray(g?.assets) ? g.assets : Array.isArray(g?.asset_list) ? g.asset_list : []).map((a) => typeof a === 'string' ? a.trim() : '').filter(Boolean)
    if (!assets.length) return null
    const key = (g?.key || '').trim() || `group-${g?.id ?? i}`
    const label = (g?.label || '').trim() || `그룹 ${i + 1}`
    const context = (g?.context_key || g?.contextKey || QUICK_COMPARE_CONTEXT_MAP[key] || '').trim()
    const resolved = Array.isArray(g?.resolved_assets) ? g.resolved_assets : []
    const inferredContext = inferGroupContextKey(context, { resolved, assets })
    return {
      id: g?.id ?? i,
      key,
      label,
      assets,
      resolved_assets: resolved,
      contextKey: inferredContext,
      sortOrder: Number.isFinite(g?.sort_order) ? Number(g.sort_order) : Number.isFinite(g?.sortOrder) ? Number(g.sortOrder) : i,
      isActive: g?.is_active !== false
    }
  }).filter(Boolean).sort((a, b) => a.sortOrder !== b.sortOrder ? a.sortOrder - b.sortOrder : (a.id ?? 0) - (b.id ?? 0))
}

function loadDefaultGroups() {
  quickCompareGroups.value = normalizeGroups(defaultFinanceQuickCompareGroups)
}

function resolveGroupContextKey(group) {
  if (!group) return 'safe_assets'
  const key = (group.contextKey || group.context_key || '').trim()
  const resolved = Array.isArray(group.resolved_assets) ? group.resolved_assets : []
  const assets = Array.isArray(group.assets) ? group.assets : []
  return inferGroupContextKey(key || QUICK_COMPARE_CONTEXT_MAP[group.key], { resolved, assets })
}

async function ensureDefaultSelection({ reapply = false } = {}) {
  if (!quickCompareGroups.value.length) {
    selectedQuickCompareGroup.value = ''
    selectedContextKey.value = 'safe_assets'
    return
  }
  if (selectedQuickCompareGroup.value && quickCompareGroups.value.some((g) => g.key === selectedQuickCompareGroup.value) && !reapply) return
  const def = quickCompareGroups.value.find((g) => g.key === 'frequent') || quickCompareGroups.value.find((g) => g.key === 'dividend_favorites') || quickCompareGroups.value[0]
  if (!def) {
    selectedQuickCompareGroup.value = ''
    selectedContextKey.value = 'safe_assets'
    return
  }
  if (reapply || !vo) {
    vo = true
    await applyQuickCompare(def.key, { autoRun: false })
  } else {
    selectedQuickCompareGroup.value = def.key
    selectedContextKey.value = resolveGroupContextKey(def)
  }
}

async function loadQuickCompareGroups() {
  quickCompareGroupsLoading.value = true
  const prev = selectedQuickCompareGroup.value
  try {
    const raw = await fetchFinanceQuickCompareGroups({})
    const normalized = normalizeGroups(Array.isArray(raw) ? raw : [])
    if (normalized.length) {
      quickCompareGroups.value = normalized
    } else {
      loadDefaultGroups()
    }
  } catch (error) {
    console.warn('Failed to load quick compare groups', error)
    loadDefaultGroups()
  } finally {
    quickCompareGroupsLoading.value = false
  }
  const exists = !!prev && quickCompareGroups.value.some((g) => g.key === prev)
  await ensureDefaultSelection({ reapply: !exists })
}

function clearAllCustomAssets() {
  Gt += 1
  customAssetResolving.value = false
  customAssets.value = []
  customAssetError.value = ''
  selectedQuickCompareGroup.value = ''
  selectedContextKey.value = 'safe_assets'
  feKey.value = ''
}

function determineContextKeyForAssets(list = customAssets.value) {
  if (!Array.isArray(list) || !list.length) return 'safe_assets'

  // 한국 주식이 있으면 kr_equity
  if (list.some((asset) => isLikelyKoreanEquityAsset(asset))) {
    return 'kr_equity'
  }

  // 미국 주식이 있으면 us_bigtech
  if (list.some((asset) => isLikelyUSEquityAsset(asset))) {
    return 'us_bigtech'
  }

  // 그 외는 safe_assets
  return 'safe_assets'
}

function isLikelyUSEquityAsset(asset) {
  if (!asset) return false

  // 카테고리 확인
  const category = (asset.category || '').toString().toLowerCase()

  // 명시적으로 미국 주식/빅테크인 경우
  if (category.includes('미국') || category.includes('빅테크') || category.includes('bigtech')) {
    return true
  }

  // US, NASDAQ, NYSE 키워드가 있고 한국이 아닌 경우
  if (category.includes('us') || category.includes('nasdaq') || category.includes('nyse')) {
    if (!category.includes('국내') && !category.includes('korea') && !category.includes('kospi') && !category.includes('kosdaq')) {
      return true
    }
  }

  // Stock/Equity가 있고 한국이 아닌 경우
  if (category.includes('stock') || category.includes('equity')) {
    if (!category.includes('국내') && !category.includes('korea') && !category.includes('kospi') && !category.includes('kosdaq')) {
      return true
    }
  }

  // 티커 확인 (일반적으로 심볼 형태: AAPL, MSFT, MSTR 등)
  const ticker = (asset.ticker || asset.id || '').toString().toUpperCase()
  if (ticker && /^[A-Z]{1,5}$/.test(ticker)) {
    // 한국이나 다른 특정 시장 suffix가 없는 경우
    if (!ticker.includes('.') && ticker.length <= 5) {
      return true
    }
  }

  // unit이 USD이고 주식 관련 카테고리인 경우
  const unit = (asset.unit || '').toString().toLowerCase()
  if (unit === 'usd' && (category.includes('주식') || category.includes('stock') || category.includes('equity'))) {
    return true
  }

  return false
}

function inferGroupContextKey(baseContext, meta = {}) {
  const normalized = (baseContext || '').trim()
  if (normalized && normalized !== 'safe_assets') return normalized

  const resolvedAssets = Array.isArray(meta?.resolved) ? meta.resolved : []

  // 한국 주식 우선 확인
  if (resolvedAssets.some((asset) => isLikelyKoreanEquityAsset(asset))) {
    return 'kr_equity'
  }

  const rawAssets = Array.isArray(meta?.assets) ? meta.assets : []
  if (rawAssets.some(isLikelyKoreanAssetName)) {
    return 'kr_equity'
  }

  // 미국 주식 확인
  if (resolvedAssets.some((asset) => isLikelyUSEquityAsset(asset))) {
    return 'us_bigtech'
  }

  if (rawAssets.some(isLikelyUSAssetName)) {
    return 'us_bigtech'
  }

  return normalized || 'safe_assets'
}

function isLikelyUSAssetName(name) {
  if (!name) return false
  const text = name.toString().trim().toUpperCase()
  if (!text) return false

  // 1~5자 알파벳만으로 구성된 경우 (AAPL, MSFT, MSTR 등)
  if (/^[A-Z]{1,5}$/.test(text)) {
    return true
  }

  // 미국 관련 키워드
  const lower = text.toLowerCase()
  if (lower.includes('nasdaq') || lower.includes('nyse') || lower.includes('s&p')) {
    return true
  }

  return false
}

function isLikelyKoreanAssetName(name) {
  if (!name) return false
  const text = name.toString().trim()
  if (!text) return false
  if (/[가-힣]/.test(text)) return true
  if (/^\d{6}$/.test(text)) return true
  if (/\.(KS|KQ|KR)$/i.test(text)) return true
  return false
}

function isLikelyKoreanEquityAsset(asset) {
  if (!asset) return false
  const category = (asset.category || '').toString().toLowerCase()
  if (category.includes('국내') || category.includes('korea') || category.includes('kospi') || category.includes('kosdaq')) {
    return true
  }
  const unit = (asset.unit || '').toString().toLowerCase()
  if (unit === 'krw') return true
  const ticker = (asset.ticker || asset.id || '').toString().toUpperCase()
  if (!ticker) return false
  if (/\.K[QSLR]$/.test(ticker)) return true
  const normalized = ticker.replace(/\.K[QSLR]$/, '')
  return /^\d{6}$/.test(normalized)
}

async function addAsset() {
  const raw = (newAssetInput.value || '').trim()
  if (!raw || customAssetResolving.value || loading.value) return

  customAssetResolving.value = true
  customAssetError.value = ''
  try {
    const added = await appendResolvedAsset(raw)
    if (added) {
      newAssetInput.value = ''
      selectedQuickCompareGroup.value = ''
      selectedContextKey.value = determineContextKeyForAssets()

      // Get the last added asset
      const lastAsset = customAssets.value[customAssets.value.length - 1]
      const assetId = lastAsset.ticker || lastAsset.id || lastAsset.label

      // If there's existing analysis data, append the new asset incrementally
      if (analysis.value && analysis.value.start_year && analysis.value.end_year) {
        await appendAssetToExistingAnalysis(assetId)
      }
    }
  } finally {
    customAssetResolving.value = false
  }
}

async function appendAssetToExistingAnalysis(assetId) {
  try {
    customAssetResolving.value = true
    appendProgressLogs(`새로운 자산 추가 중: ${assetId}`)

    const result = await addSingleAsset({
      assetId: assetId,
      startYear: analysis.value.start_year,
      endYear: analysis.value.end_year,
      calculationMethod: analysisResultType.value,
      includeDividends: includeDividends.value
    })

    if (result.series) {
      // Add series to existing analysis
      const currentAnalysis = analysis.value || {}
      const currentSeries = currentAnalysis.series || []
      const nextSeries = [...currentSeries, result.series]
      const snapshot = buildRequestedAssetSnapshotFromSeries(result.series)
      const nextRequestedAssets = upsertRequestedAssetsSnapshot(currentAnalysis.requested_assets, snapshot)
      analysis.value = {
        ...currentAnalysis,
        series: nextSeries,
        requested_assets: nextRequestedAssets
      }
      updateColorAssignments([result.series])

      // Add chart data table entry
      if (result.chartDataTableEntry) {
        const currentChartData = currentAnalysis.chart_data_table || []
        analysis.value.chart_data_table = [...currentChartData, result.chartDataTableEntry]

        // Process the new entry for price table (merge with existing data)
        processYearlyPrices([result.chartDataTableEntry], { merge: true })
      }

      ensureMissingPriceEntries(nextRequestedAssets.length ? nextRequestedAssets : customAssets.value)
      appendProgressLogs(`✓ ${assetId} 추가 완료`)
    }
  } catch (error) {
    customAssetError.value = error.message || '자산 추가 중 오류가 발생했습니다.'
    appendProgressLogs(`오류: ${error.message}`)
    setTimeout(() => {
      customAssetError.value = ''
    }, 5000)
  } finally {
    customAssetResolving.value = false
  }
}

function removeAsset(index) {
  const targetAsset = customAssets.value[index]
  customAssets.value = customAssets.value.filter((_, i) => i !== index)
  customAssetError.value = ''
  selectedQuickCompareGroup.value = ''
  selectedContextKey.value = determineContextKeyForAssets()
  if (targetAsset) {
    removeAssetDataFromAnalysis(targetAsset)
  }
}

watch(
  () => progressLogs.value.length,
  () => {
    const lastLog = progressLogs.value[progressLogs.value.length - 1]
    if (lastLog) {
      handleProgressLog(lastLog)
    }
  }
)

function formatMultiple(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '0.0'
  const absValue = Math.abs(value)
  let decimals = 1
  if (absValue < 1) decimals = 2
  if (absValue < 0.1) decimals = 3
  if (absValue < 0.01) decimals = 4
  return value.toFixed(decimals)
}

function formatFxRate(rate) {
  if (!Number.isFinite(rate)) return '1,300'
  return Math.round(rate).toLocaleString()
}

function getLegendLabel(series) {
  if (!series) return ''
  const customAsset = findMatchingCustomAsset(series)
  if (customAsset) {
    const friendly = stripTickerSuffix(
      customAsset.label || customAsset.display || '',
      customAsset.ticker || series.ticker || series.id
    )
    if (friendly) return friendly
  }
  const tickerCandidate = series.ticker || series.id
  const resolved = resolvePreferredSeriesLabel(series, tickerCandidate)
  if (resolved) return resolved
  return stripTickerSuffix(series.label || '', tickerCandidate)
}

function stripTickerSuffix(label, tickerCandidate) {
  const text = (label || '').trim()
  if (!text) return ''

  const ticker = (tickerCandidate || '').trim()
  if (ticker) {
    const escapedTicker = ticker.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const tickerPattern = new RegExp(`\\s*\\(${escapedTicker}\\)\\s*$`, 'i')
    if (tickerPattern.test(text)) {
      const cleaned = text.replace(tickerPattern, '').trim()
      if (cleaned) return cleaned
    }
  }

  const trailingParenMatch = text.match(/\(([^)]*)\)\s*$/)
  if (trailingParenMatch) {
    const candidate = trailingParenMatch[1].trim()
    if (/^[A-Z0-9.\-]+$/.test(candidate) || /^\d{4,6}$/.test(candidate)) {
      const cleaned = text.replace(/\s*\([^)]*\)\s*$/, '').trim()
      if (cleaned) return cleaned
    }
  }

  return text
}

const priceFormatter = new Intl.NumberFormat('en-US', {
  notation: 'compact',
  maximumFractionDigits: 2
})

function getAssetUrl(series) {
  if (!series) return null
  const ticker = series.ticker || series.id
  if (!ticker) return null
  if (series?.metadata?.synthetic_asset || series?.synthetic_asset || /^SYNTH-(DEPOSIT|SAVINGS)-/i.test(ticker)) {
    return null
  }
  
  const symbol = ticker.toUpperCase()
  const entry = findPriceEntry(series)
  if (entry?.status === 'failed') {
    return null
  }
  const source = String(entry?.source || series.source || '')
  const category = entry?.category || series.category || ''
  const labelLower = (series.label || '').toLowerCase()

  if (source.includes('KB부동산') || labelLower.includes('아파트')) {
    return 'https://kbland.kr/'
  }
  
  if (source === 'pykrx' || symbol.endsWith('.KS') || symbol.endsWith('.KQ') || category === '국내 주식') {
    const code = symbol.split('.')[0]
    return `https://finance.naver.com/item/main.naver?code=${code}`
  }
  
  if (source === 'Upbit') {
     return `https://upbit.com/exchange?code=CRIX.UPBIT.${symbol}`
  }
  
  if (source === 'FRED') {
    return `https://fred.stlouisfed.org/series/${symbol}`
  }
  
  return `https://finance.yahoo.com/quote/${symbol}`
}

function formatPriceCell(series, year) {
  const priceEntry = findPriceEntry(series)
  if (!priceEntry) {
    return { text: priceTableLoading.value ? '...' : '-', url: null }
  }

  if (priceEntry.status === 'failed') {
    return { text: '조회되지 않음', url: null }
  }

  const { rawValue, unit } = resolvePriceByMode(priceEntry, year)
  if (!Number.isFinite(rawValue)) {
    return { text: '-', url: null }
  }

  const displayValue = convertValue(rawValue, unit)
  const symbol = getUnitSymbol(priceDisplayMode.value)
  const formatted = priceFormatter.format(displayValue)
  const valueText = symbol ? `${symbol}${formatted}` : formatted
  const isLatestYear = year === currentYear || year === analysis.value?.end_year
  const text = isLatestYear ? `${valueText} (오늘)` : valueText
  const url = generateNaverFinanceUrl(series, year)
  return { text, url }
}

function getDividendYieldForYear(series, year) {
  if (!series || !year) return null
  const priceEntry = findPriceEntry(series)
  if (!priceEntry || !priceEntry.dividends) return null
  const dividendAmount = priceEntry.dividends[year]
  const priceValue = priceEntry.prices?.[year]
  if (!Number.isFinite(dividendAmount) || !Number.isFinite(priceValue) || priceValue <= 0) return null
  const yieldPct = (dividendAmount / priceValue) * 100
  if (!Number.isFinite(yieldPct) || yieldPct <= 0) return null
  return yieldPct
}

function findPriceEntry(series) {
  if (!series) return null
  const candidates = new Set()
  if (series.id) {
    candidates.add(series.id)
    candidates.add(series.id.toLowerCase())
  }
  if (series.label) {
    candidates.add(series.label)
    const normalized = normalizeLabelAlias(series.label)
    if (normalized) {
      candidates.add(normalized)
    }
  }
  for (const key of candidates) {
    if (key && yearlyPriceMap.value[key]) {
      return yearlyPriceMap.value[key]
    }
  }
  return null
}

function normalizeLabelAlias(label) {
  return label.replace(/\([^)]*\)/g, '').trim().toLowerCase()
}

function isTickerLikeLabel(label) {
  const text = (label || '').trim()
  if (!text) return false
  const compact = text.replace(/\s+/g, '')
  if (/^[A-Z0-9.\-]+$/.test(compact)) return true
  if (/^\d{4,6}$/.test(compact)) return true
  return false
}

function buildTokenSetFromAsset(asset) {
  const tokens = new Set()
  if (!asset) return tokens
  const addToken = (value) => {
    const token = normalizeAssetToken(value)
    if (token) tokens.add(token)
  }
  ;[asset.id, asset.label, asset.display, asset.ticker, asset.requested_id].forEach(addToken)
  if (Array.isArray(asset.aliases)) {
    asset.aliases.forEach(addToken)
  }
  if (asset.metadata && Array.isArray(asset.metadata.aliases)) {
    asset.metadata.aliases.forEach(addToken)
  }
  const aliasFromLabel = normalizeAssetToken(normalizeLabelAlias(asset.label || ''))
  if (aliasFromLabel) tokens.add(aliasFromLabel)
  return tokens
}

function buildTokenSetFromSeries(series) {
  const tokens = new Set()
  if (!series) return tokens
  const addToken = (value) => {
    const token = normalizeAssetToken(value)
    if (token) tokens.add(token)
  }
  ;[series.id, series.label, series.ticker].forEach(addToken)
  const aliasFromLabel = normalizeAssetToken(normalizeLabelAlias(series.label || ''))
  if (aliasFromLabel) tokens.add(aliasFromLabel)
  if (Array.isArray(series.aliases)) {
    series.aliases.forEach(addToken)
  }
  if (series.metadata) {
    if (Array.isArray(series.metadata.aliases)) {
      series.metadata.aliases.forEach(addToken)
    }
    addToken(series.metadata.id)
  }
  return tokens
}

function buildTokenSetFromEntry(entry) {
  const tokens = new Set()
  if (!entry) return tokens
  const addToken = (value) => {
    const token = normalizeAssetToken(value)
    if (token) tokens.add(token)
  }
  ;[entry.id, entry.label, entry.requested_id].forEach(addToken)
  if (Array.isArray(entry.aliases)) {
    entry.aliases.forEach(addToken)
  }
  const aliasFromLabel = normalizeAssetToken(normalizeLabelAlias(entry.label || ''))
  if (aliasFromLabel) tokens.add(aliasFromLabel)
  return tokens
}

function tokenSetsIntersect(primary, secondary) {
  if (!primary.size || !secondary.size) return false
  for (const token of secondary) {
    if (primary.has(token)) return true
  }
  return false
}

function buildFailedLegendSeries(asset) {
  const label = asset?.display ?? asset?.label ?? asset?.requested_id ?? asset?.id ?? asset?.ticker ?? '알 수 없는 자산'
  const entryId = asset?.id || asset?.requested_id || asset?.ticker || label
  const ticker = asset?.ticker || entryId || label
  const failureReason = asset?.failure_reason || asset?.error_message || '데이터 불러오기 실패'
  return {
    id: entryId || `missing-${Date.now()}-${Math.random()}`,
    label,
    display_label: label,
    ticker,
    category: asset?.category || asset?.type || '',
    status: 'failed',
    failure_reason: failureReason,
    metadata: {
      ...(asset?.metadata || {}),
      failure_reason: failureReason,
      requested_id: asset?.requested_id || asset?.id || ticker
    },
    requested_id: asset?.requested_id || asset?.id || ticker,
    points: [],
    annualized_return_pct: null,
    multiple_from_start: null
  }
}

function buildRequestedAssetSnapshotFromSeries(series) {
  if (!series) return null
  return {
    id: series.id,
    requested_id: series.requested_id || series.id,
    label: series.label,
    display: series.display_label || series.label,
    ticker: series.ticker || series.id,
    category: series.category || series.metadata?.category || '',
    unit: series.unit || series.metadata?.unit || '',
    aliases: series.aliases || series.metadata?.aliases || []
  }
}

function upsertRequestedAssetsSnapshot(existingList, assetSnapshot) {
  if (!assetSnapshot) return Array.isArray(existingList) ? existingList : []
  const base = Array.isArray(existingList) ? [...existingList] : []
  const tokens = buildTokenSetFromAsset(assetSnapshot)
  const filtered = base.filter((entry) => !tokenSetsIntersect(tokens, buildTokenSetFromAsset(entry)))
  filtered.push(assetSnapshot)
  return filtered
}

function removeRequestedAssetsByTokens(tokens, existingList) {
  if (!Array.isArray(existingList) || !existingList.length) return []
  return existingList.filter((entry) => !tokenSetsIntersect(tokens, buildTokenSetFromAsset(entry)))
}

function removeAssetDataFromAnalysis(asset) {
  if (!analysis.value) return
  const assetTokens = buildTokenSetFromAsset(asset)
  if (!assetTokens.size) return

  const current = analysis.value
  let changed = false

  const nextSeries = Array.isArray(current.series)
    ? current.series.filter((series) => !tokenSetsIntersect(assetTokens, buildTokenSetFromSeries(series)))
    : []
  if (Array.isArray(current.series) && nextSeries.length !== current.series.length) {
    changed = true
  }

  const nextChartData = Array.isArray(current.chart_data_table)
    ? current.chart_data_table.filter((entry) => !tokenSetsIntersect(assetTokens, buildTokenSetFromEntry(entry)))
    : current.chart_data_table
  if (Array.isArray(current.chart_data_table) && nextChartData.length !== current.chart_data_table.length) {
    changed = true
  }

  const nextYearlyPrices = Array.isArray(current.yearly_prices)
    ? current.yearly_prices.filter((entry) => !tokenSetsIntersect(assetTokens, buildTokenSetFromEntry(entry)))
    : current.yearly_prices
  if (Array.isArray(current.yearly_prices) && nextYearlyPrices.length !== current.yearly_prices.length) {
    changed = true
  }

  if (!changed) return

  const nextRequested = removeRequestedAssetsByTokens(assetTokens, current.requested_assets)
  const nextAnalysis = {
    ...current,
    series: nextSeries,
    requested_assets: nextRequested
  }
  if (Array.isArray(current.chart_data_table)) {
    nextAnalysis.chart_data_table = nextChartData
  }
  if (Array.isArray(current.yearly_prices)) {
    nextAnalysis.yearly_prices = nextYearlyPrices
  }

  analysis.value = nextAnalysis
  updateColorAssignments(nextSeries, { reset: true })

  const validIds = new Set(nextSeries.map((series) => series.id))
  hiddenSeries.value = new Set([...hiddenSeries.value].filter((id) => validIds.has(id)))

  if (Array.isArray(nextChartData) && nextChartData.length) {
    processYearlyPrices(nextChartData)
  } else if (Array.isArray(nextYearlyPrices) && nextYearlyPrices.length) {
    processYearlyPrices(nextYearlyPrices)
  } else {
    yearlyPriceMap.value = {}
  }
  ensureMissingPriceEntries(nextRequested.length ? nextRequested : customAssets.value)
}

function resolvePriceByMode(priceEntry, year) {
  const mode = priceDisplayMode.value === 'krw' ? 'krw' : 'usd'
  const altMap = priceEntry.altPrices?.[mode]
  if (altMap) {
    const altValue = Number(altMap[year])
    if (Number.isFinite(altValue)) {
      return { rawValue: altValue, unit: mode }
    }
  }
  const baseValue = Number(priceEntry.prices?.[year])
  if (Number.isFinite(baseValue)) {
    return { rawValue: baseValue, unit: priceEntry.unit || '' }
  }
  return { rawValue: null, unit: priceEntry.unit || '' }
}

function extractStockCode(series) {
  if (!series?.label) return null
  const match = series.label.match(/\\((\\d{6})\\)/)
  return match ? match[1] : null
}

function generateNaverFinanceUrl(series, year) {
  if (selectedContextKey.value !== 'kr_equity') return null
  const stockCode = extractStockCode(series)
  if (!stockCode) return null
  return `https://finance.naver.com/item/sise_day.naver?code=${stockCode}`
}

function convertValue(value, unit, targetMode = priceDisplayMode.value) {
  const sourceUnit = (unit || '').toLowerCase()
  const normalizedTarget = targetMode === 'krw' ? 'krw' : 'usd'
  if (!Number.isFinite(value)) return value
  if (normalizedTarget === 'krw' && sourceUnit !== 'krw') {
    return value * (fxRate.value || 1300)
  }
  if (normalizedTarget === 'usd' && sourceUnit === 'krw') {
    return value / (fxRate.value || 1300)
  }
  return value
}

function isKoreanEquitySeries(series) {
  if (!series) return false
  const entry = findPriceEntry(series)
  const ticker = (series.ticker || series.id || '').toUpperCase()
  const source = (entry?.source || entry?.data_source || series.source || '').toString().toLowerCase()
  if (source.includes('pykrx')) return true
  if (/\\.K[QS]$/.test(ticker)) return true

  const categoryCandidates = [
    series.category,
    entry?.category,
    getSeriesMetaValue(series, 'category'),
    getSeriesMetaValue(series, 'asset_class'),
    getSeriesMetaValue(series, 'asset_category')
  ]

  if (categoryCandidates.some((value) => {
    if (!value) return false
    const lower = value.toString().toLowerCase()
    return lower.includes('국내') || lower.includes('korea') || lower.includes('kospi') || lower.includes('kosdaq')
  })) {
    return true
  }

  const regionCandidates = [
    getSeriesMetaValue(series, 'region'),
    getSeriesMetaValue(series, 'country'),
    entry?.region
  ]

  return regionCandidates.some((value) => {
    if (!value) return false
    return value.toString().toLowerCase().includes('korea')
  })
}

function resolvePriceValueForCurrency(series, point, year, targetCurrency) {
  const normalizedTarget = targetCurrency === 'krw' ? 'krw' : 'usd'
  const entry = findPriceEntry(series)
  if (entry) {
    const altMap = entry.altPrices?.[normalizedTarget]
    if (altMap && Number.isFinite(Number(altMap[year]))) {
      return { value: Number(altMap[year]), unit: normalizedTarget }
    }
    const baseValue = Number(entry.prices?.[year])
    if (Number.isFinite(baseValue)) {
      const converted = convertValue(baseValue, entry.unit || series.unit || '', normalizedTarget)
      return { value: converted, unit: normalizedTarget }
    }
  }

  if (point) {
    const rawValue = Number(point.raw_value ?? point.rawValue)
    if (Number.isFinite(rawValue)) {
      const converted = convertValue(rawValue, series.unit || '', normalizedTarget)
      return { value: converted, unit: normalizedTarget }
    }
    const fallback = Number(point.multiple ?? point.value)
    if (Number.isFinite(fallback)) {
      return { value: fallback, unit: null }
    }
  }

  return { value: null, unit: normalizedTarget }
}

function getUnitSymbol(unit) {
  if (!unit) return ''
  const lowered = unit.toLowerCase()
  if (lowered === 'usd' || lowered === '$') return '$'
  if (lowered === 'krw' || lowered === '₩') return '₩'
  return ''
}

function formatKoreanWonVerbose(amount) {
  if (!Number.isFinite(amount) || amount <= 0) return '0원'
  let remainder = Math.floor(amount)
  const units = [
    { value: 1000000000000, label: '조' },
    { value: 100000000, label: '억' },
    { value: 10000, label: '만' }
  ]
  const parts = []
  units.forEach(({ value, label }) => {
    if (remainder >= value) {
      const unitValue = Math.floor(remainder / value)
      parts.push(`${unitValue.toLocaleString()}${label}`)
      remainder %= value
    }
  })
  if (remainder > 0 || !parts.length) {
    parts.push(remainder.toLocaleString())
  }
  return `${parts.join(' ')} 원`
}

const bitcoinPerformanceStats = computed(() => {
  if (!analysis.value || !filteredSeries.value.length) return null
  const bitcoinSeries = filteredSeries.value.find((series) => isBitcoinLabel(series.label))
  if (!bitcoinSeries || !bitcoinSeries.points?.length) return null

  const points = bitcoinSeries.points
  const preferredStartYear = displayStartYear.value || analysis.value.start_year
  const startPoint = preferredStartYear
    ? points.find((point) => point.year === preferredStartYear) || points[0]
    : points[0]
  const latestPoint = points[points.length - 1]
  if (!startPoint || !latestPoint) return null

  const dStartYear = preferredStartYear || startPoint.year
  const entry = findPriceEntry(bitcoinSeries)
  let priceText = ''
  if (entry) {
    const { rawValue, unit } = resolvePriceByMode(entry, latestPoint.year)
    if (Number.isFinite(rawValue)) {
      const converted = convertValue(rawValue, unit)
      const symbol = priceDisplayMode.value === 'krw' ? '₩' : '$'
      priceText = `${symbol}${priceFormatter.format(converted)}`
    }
  }

  const baseMultiple = Number(startPoint.multiple)
  const endMultiple = Number(latestPoint.multiple)
  let multipleFromStart = bitcoinSeries.multiple_from_start
  if (Number.isFinite(baseMultiple) && baseMultiple > 0 && Number.isFinite(endMultiple)) {
    multipleFromStart = endMultiple / baseMultiple
  }

  let annualizedReturnPct = bitcoinSeries.annualized_return_pct
  const spanYears = Number.isFinite(dStartYear)
    ? Math.max(1, latestPoint.year - dStartYear)
    : null
  if (spanYears && Number.isFinite(multipleFromStart) && multipleFromStart > 0) {
    annualizedReturnPct = (Math.pow(multipleFromStart, 1 / spanYears) - 1) * 100
  }

  return {
    startYear: dStartYear,
    endYear: latestPoint.year,
    annualizedReturnPct,
    multipleFromStart,
    priceText
  }
})

function formatPercent(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '0.0%'
  return `${value.toFixed(1)}%`
}

const bitcoinPerformanceText = computed(() => {
  const stats = bitcoinPerformanceStats.value
  if (!stats) return ''
  const segments = []
  if (Number.isFinite(stats.annualizedReturnPct)) {
    segments.push(`연평균 ${formatPercent(stats.annualizedReturnPct)}`)
  }
  if (Number.isFinite(stats.multipleFromStart)) {
    segments.push(`${formatMultiple(stats.multipleFromStart)}배`)
  }
  if (stats.priceText) {
    segments.push(`현재 ${stats.priceText}`)
  }
  if (!segments.length) return ''
  return `비트코인 (${stats.startYear}년 → ${stats.endYear}년) · ${segments.join(' · ')}`
})

const bitcoinHeroSummary = computed(() => {
  const stats = bitcoinPerformanceStats.value
  if (!stats || !analysis.value) return null
  const startYear = stats.startYear
  const endYear = stats.endYear || analysis.value.end_year
  if (!startYear || !endYear) return null

  const multiple = Number(stats.multipleFromStart)
  const cagr = Number(stats.annualizedReturnPct ?? stats.annualized_return_pct)
  const investmentWon = Number(investmentAmount.value) * 10000
  const finalWon = Number.isFinite(multiple) ? investmentWon * multiple : null

  return {
    startYear,
    endYear,
    duration: Math.max(1, endYear - startYear),
    multipleText: Number.isFinite(multiple) ? `${formatMultiple(multiple)}배` : '',
    cagrText: Number.isFinite(cagr) ? formatPercent(cagr) : '',
    investmentText: `${formattedInvestmentAmountNumber.value}만원`,
    finalText: Number.isFinite(finalWon) ? formatKoreanWonVerbose(finalWon) : ''
  }
})

const analysisSummary = computed(() => Te.value)

function getReturnForYear(series, year, options = {}) {
  if (!series?.points) return '-'
  const point = series.points.find((p) => p.year === year)
  if (!point) return '-'
  if (analysisResultType.value === 'price') {
    const mode = options.priceMode || priceTableMode.value
    if (mode === 'dividend') {
      const yieldPct = getDividendYieldForYear(series, year)
      if (!Number.isFinite(yieldPct) || yieldPct < MIN_DIVIDEND_YIELD_DISPLAY) return '-'
      return `${yieldPct.toFixed(1)}%`
    }
    if (mode === 'multiple') {
      const multiple = Number(point.multiple)
      if (!Number.isFinite(multiple) || multiple <= 0) return '-'
      return `${formatMultiple(multiple)}배`
    }
    const displayCurrency = getSeriesDisplayCurrency(series)
    const { value } = resolvePriceValueForCurrency(series, point, year, displayCurrency)
    if (!Number.isFinite(value)) return '-'
    const symbol = getCurrencySymbolForMode(displayCurrency)
    return `${symbol}${priceFormatter.format(value)}`
  }

  const value = Number(point.value)
  if (!Number.isFinite(value)) return '-'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(1)}%`
}

function determineYearlySign(series, year) {
  if (!series) return 0
  if (analysisResultType.value === 'price') {
    if (priceTableMode.value === 'dividend') return 0
    return getPriceYearlySign(series, year)
  }
  const point = series.points?.find((p) => p.year === year)
  if (!point) return 0
  const value = Number(point.value)
  if (!Number.isFinite(value)) return 0
  if (value > 0) return 1
  if (value < 0) return -1
  return 0
}

function getPriceYearlySign(series, year) {
  const years = tableYears.value
  const idx = years.indexOf(year)
  if (idx <= 0) return 0
  const prevYear = years[idx - 1]
  const current = getPriceValueForYear(series, year)
  const previous = getPriceValueForYear(series, prevYear)
  if (!Number.isFinite(current) || !Number.isFinite(previous)) return 0
  if (current > previous) return 1
  if (current < previous) return -1
  return 0
}

function getPriceValueForYear(series, year) {
  if (!series?.points) return null
  const point = series.points.find((p) => p.year === year)
  if (!point) return null
  const displayCurrency = getSeriesDisplayCurrency(series)
  const { value } = resolvePriceValueForCurrency(series, point, year, displayCurrency)
  return Number.isFinite(value) ? value : null
}

function getReturnCellClass(series, year) {
  const sign = determineYearlySign(series, year)
  if (sign > 0) return 'text-rose-600 font-semibold'
  if (sign < 0) return 'text-blue-600 font-semibold'
  return 'text-slate-600'
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

function isBitcoinLabel(label) {
  if (!label) return false
  const lower = label.toLowerCase()
  return lower.includes('비트코인') || lower.includes('bitcoin') || lower.includes('btc')
}

function isKoreanM2Label(label) {
  if (!label) return false
  const lower = label.toLowerCase()
  const hasKorea = lower.includes('한국') || lower.includes('korea')
  return hasKorea && lower.includes('m2')
}

function resolveTaxTreatment(series) {
  if (!series || isBitcoinLabel(series.label)) return null
  const syntheticType = (series?.metadata?.synthetic_asset || series?.synthetic_asset || '').toLowerCase()
  if (syntheticType === 'deposit') {
    const targetRate = Number(series?.metadata?.target_rate_pct ?? series?.target_rate_pct)
    return {
      type: 'kr_deposit',
      rate: KR_INTEREST_TAX_RATE,
      targetRatePct: Number.isFinite(targetRate) ? targetRate : null
    }
  }
  if (isKoreanEquitySeries(series)) {
    return {
      type: 'kr',
      rate: TAX_RATE,
      allowance: KR_EQUITY_TAX_FREE_ALLOWANCE
    }
  }
  const category = (series.category || '').toLowerCase()
  const unit = (series.unit || '').toLowerCase()
  const label = (series.label || '').toLowerCase()
  const id = (series.id || '').toLowerCase()
  const isUsEquity =
    category.includes('미국') ||
    label.includes('미국') ||
    id.endsWith('.us')
  if (isUsEquity && unit === 'usd') {
    return {
      type: 'us',
      rate: TAX_RATE
    }
  }
  return null
}

function applyTaxToMultiple(multiple, yearsElapsed, taxTreatment) {
  if (!taxTreatment) return multiple
  if (!Number.isFinite(multiple) || multiple <= 0) return multiple
  if (taxTreatment.type === 'us' || taxTreatment.type === 'kr_deposit') {
    if (!Number.isFinite(yearsElapsed) || yearsElapsed <= 0) return multiple
    const cagr = Math.pow(multiple, 1 / yearsElapsed) - 1
    if (!Number.isFinite(cagr)) return multiple
    const rate = taxTreatment.rate ?? (taxTreatment.type === 'us' ? TAX_RATE : KR_INTEREST_TAX_RATE)
    const adjusted = cagr * (1 - rate)
    return Math.pow(1 + adjusted, yearsElapsed)
  }
  if (taxTreatment.type === 'kr') {
    const principal = baseInvestmentWon.value
    if (!Number.isFinite(principal) || principal <= 0) return multiple
    const gain = (multiple - 1) * principal
    if (gain <= 0) return multiple
    const allowance = Number.isFinite(taxTreatment.allowance) ? taxTreatment.allowance : KR_EQUITY_TAX_FREE_ALLOWANCE
    const taxableGain = Math.max(0, gain - allowance)
    const afterTaxGain = (gain - taxableGain) + taxableGain * (1 - (taxTreatment.rate ?? TAX_RATE))
    const afterTaxMultiple = (principal + afterTaxGain) / principal
    return Math.max(afterTaxMultiple, 0)
  }
  return multiple
}

function startHeroTypewriterAnimation() {
  const fullText = heroTypewriterText.value
  displayedHeroText.value = ''
  heroAnimationActive.value = true
  let index = 0
  if (typingInterval) clearInterval(typingInterval)
  typingInterval = setInterval(() => {
    if (index < fullText.length) {
      displayedHeroText.value += fullText[index]
      index++
    } else {
      clearInterval(typingInterval)
      heroAnimationTimer = setTimeout(() => {
        heroAnimationActive.value = false
      }, 1000)
    }
  }, 45)
}

function buildPromptFromInputs() {
  const years = Math.max(1, Math.min(30, Number(investmentYearsAgo.value) || 1))
  const amount = Math.max(1, Math.min(100000, Number(investmentAmount.value) || 1))
  const amountText = `${amount.toLocaleString('ko-KR')}만원`

  if (!customAssets.value.length) {
    return `${years}년 전에 비트코인에 ${amountText}을 투자했다면 지금 얼마인지 알려줘.`
  }

  const assetText = customAssets.value.map((asset) => asset.display || asset.label).join(', ')
  return `${years}년 전에 비트코인에 ${amountText}을 투자했다면 지금 얼마인지 알려주고, 비트코인과 비교 종목(${assetText})을 비교해줘.`
}

const formattedInvestmentAmountNumber = computed(() => {
  return investmentAmount.value.toLocaleString('ko-KR')
})

const heroTypewriterText = computed(() => {
  return `${investmentYearsAgo.value}년 전에 비트코인 ${formattedInvestmentAmountNumber.value}만원을 샀다면 지금 얼마일까?`
})

watch(investmentYearsAgo, (val) => {
  let num = Number(val)
  if (!Number.isFinite(num)) num = 1
  num = Math.min(30, Math.max(1, Math.round(num)))
  if (num !== val) investmentYearsAgo.value = num
})

watch(investmentAmount, (val) => {
  let num = Number(val)
  if (!Number.isFinite(num)) num = 1
  num = Math.min(100000, Math.max(1, Math.round(num)))
  if (num !== val) investmentAmount.value = num
})

onBeforeUnmount(() => {
  if (heroAnimationTimer) clearTimeout(heroAnimationTimer)
  if (typingInterval) clearInterval(typingInterval)
  cancelDividendPrefetch()
  stopLoadingStageTracking()
})

onMounted(() => {
  startHeroTypewriterAnimation()
  loadQuickCompareGroups()
})

function handleSearchClick() {
  if (loading.value || customAssetResolving.value) return
  searchButtonAttention.value = false
  prompt.value = buildPromptFromInputs()
  heroAnimationKey.value += 1
  displayStartYear.value = null
  requestAgentAnalysis()
}

async function requestAgentAnalysis(options = {}) {
  const { preserveCache = false } = options
  if (abortController) abortController.abort()
  if (preserveCache) cancelDividendPrefetch()
  else resetDividendCache()

  analysis.value = null
  displayStartYear.value = null
  sliderMinYear.value = null
  hiddenSeries.value = new Set()
  resetColorAssignments()
  priceDisplayMode.value = isAutoApplyEnabled.value ? 'krw' : 'usd'
  yearlyPriceMap.value = {}
  errorMessage.value = ''
  feKey.value = ''

  const requestContext = {
    prompt: prompt.value,
    contextKey: selectedContextKey.value,
    customAssets: customAssets.value.map((a) => a.ticker || a.label)
  }

  lastAnalysisRequest.value = requestContext
  prefetchDividendVariant(!includeDividends.value)

  abortController = new AbortController()
  loading.value = true
  ee.value = ''
  loadingProgress.value = 0
  showDebugLogs.value = true
  startLoadingStageTracking()

  if (analysisLogs.value.length > 0) {
    appendProgressLogs('', '='.repeat(50), '')
  }
  appendProgressLogs('분석 요청 중...')

  try {
    const streamOptions = {
      ...requestContext,
      includeDividends: includeDividends.value,
      signal: abortController.signal,
      onLog: (msg) => {
        appendProgressLogs(msg)
      }
    }

    const result = await fetchHistoricalReturnsStream(streamOptions)
    applyAnalysisResult(result, { shouldCache: true, resetColors: true })
    prefetchDividendVariant(!includeDividends.value)
    completeLoadingStageTracking()

    appendProgressLogs('', '✓ 분석 완료')
  } catch (error) {
    stopLoadingStageTracking()
    if (error.name === 'AbortError') {
      errorMessage.value = '요청이 취소되었습니다.'
      appendProgressLogs('요청이 취소되었습니다.')
    } else {
      errorMessage.value = error.message || '분석 중 오류가 발생했습니다.'
      appendProgressLogs(`오류: ${error.message}`)
      cancelDividendPrefetch()
    }
  } finally {
    loading.value = false
    abortController = null
  }
}

const lastAnalysisRequest = ref(null)
const analysisSummaryContent = ref('')
const Te = ref('')
const ee = ref('')

function resetDividendCache() {
  cancelDividendPrefetch()
  dividendCache.true = null
  dividendCache.false = null
  dividendPrefetchStatus.true = false
  dividendPrefetchStatus.false = false
  dividendTogglePending.value = null
}

function cancelDividendPrefetch() {
  if (prefetchController) {
    prefetchController.abort()
    prefetchController = null
    dividendPrefetchPromise = null
  }
}

function applyAnalysisResult(result, { shouldCache = true, preserveHidden = true, resetColors = false } = {}) {
  if (!result) return
  dividendTogglePending.value = null
  const prevHidden = preserveHidden ? new Set(hiddenSeries.value) : null
  const currentSeriesIds = new Set((result?.series || []).map((s) => s.id))
  updateColorAssignments(result?.series || [], { reset: resetColors })

  analysis.value = result
  analysisResultType.value = result.calculation_method || 'cagr'
  Te.value = result.analysis_summary || ''

  const inc = Object.prototype.hasOwnProperty.call(result, 'include_dividends') ? !!result.include_dividends : includeDividends.value
  includeDividends.value = inc
  dividendPrefetchStatus[orKey(inc)] = true

  displayStartYear.value = result.start_year
  sliderMinYear.value = result.start_year
  hiddenSeries.value = prevHidden ? new Set([...prevHidden].filter((id) => currentSeriesIds.has(id))) : new Set()

  if (result.chart_data_table) {
    processYearlyPrices(result.chart_data_table)
  } else if (result.yearly_prices) {
    processYearlyPrices(result.yearly_prices)
  } else {
    yearlyPriceMap.value = {}
  }

  const placeholderTargets = (Array.isArray(result.requested_assets) && result.requested_assets.length)
    ? result.requested_assets
    : customAssets.value
  ensureMissingPriceEntries(placeholderTargets)

  if (shouldCache) {
    const key = orKey(inc)
    dividendCache[key] = result
  }
}

function orKey(val) {
  return val ? 'true' : 'false'
}

function handleDividendToggle() {
  if (loading.value || !analysis.value) return
  const nextVal = !includeDividends.value
  const key = orKey(nextVal)
  const cached = dividendCache[key]

  if (!cached) {
    dividendTogglePending.value = nextVal
    prefetchDividendVariant(nextVal)
    return
  }

  dividendTogglePending.value = null
  includeDividends.value = nextVal
  applyAnalysisResult(cached, { preserveHidden: true })
  prefetchDividendVariant(!nextVal)
}

async function prefetchDividendVariant(val) {
  const request = lastAnalysisRequest.value
  if (!request) return
  const key = orKey(val)
  if (dividendCache[key]) {
    dividendPrefetchStatus[key] = true
    return
  }
  if (prefetchController && dividendPrefetchPromise && val === prefetchController.val) return

  cancelDividendPrefetch()
  prefetchController = new AbortController()
  prefetchController.val = val
  dividendPrefetchStatus[key] = false

  let wasSuccess = false
  try {
    const result = await fetchHistoricalReturns({ ...request, includeDividends: val, signal: prefetchController.signal })
    if (result && result.ok) {
      dividendCache[key] = result
      dividendPrefetchStatus[key] = true
      if (dividendTogglePending.value === val) {
        includeDividends.value = val
        applyAnalysisResult(result, { preserveHidden: true })
        dividendTogglePending.value = null
        wasSuccess = true
      }
    }
  } catch (error) {
    if (error.name !== 'AbortError') {
      console.error('Dividend prefetch failed', error)
    }
    if (dividendTogglePending.value === val) {
      dividendTogglePending.value = null
    }
  } finally {
    prefetchController = null
    if (wasSuccess) {
      prefetchDividendVariant(!val)
    }
  }
}

function completeLoadingStageTracking() {
  const last = LOADING_STAGES[LOADING_STAGES.length - 1]
  if (last) advanceToStage(last.key, { immediate: true })
  loadingProgress.value = 100
  stopLoadingStageTracking()
}

function processYearlyPrices(pricesData, { merge = false } = {}) {
  const map = merge ? { ...yearlyPriceMap.value } : {}
  if (Array.isArray(pricesData)) {
    pricesData.forEach((entry) => {
      const priceMap = {}
      if (Array.isArray(entry.prices)) {
        entry.prices.forEach((pricePoint) => {
          const year = Number(pricePoint.year)
          const value = Number(pricePoint.value)
          if (Number.isFinite(year) && Number.isFinite(value)) {
            priceMap[year] = value
          }
        })
      }
      if (Array.isArray(entry.values)) {
        entry.values.forEach((point) => {
          const year = Number(point.year)
          const value = Number(point.value)
          if (Number.isFinite(year) && Number.isFinite(value)) {
            priceMap[year] = value
          }
        })
      }

      const altPrices = {}
      if (entry.alt_prices && typeof entry.alt_prices === 'object') {
        Object.entries(entry.alt_prices).forEach(([unitKey, priceList]) => {
          const normalizedUnit = String(unitKey || '').toLowerCase()
          if (!normalizedUnit) return
          const altMap = {}
          if (Array.isArray(priceList)) {
            priceList.forEach((pricePoint) => {
              const year = Number(pricePoint.year)
              const value = Number(pricePoint.value)
              if (Number.isFinite(year) && Number.isFinite(value)) {
                altMap[year] = value
              }
            })
          }
          if (Object.keys(altMap).length) {
            altPrices[normalizedUnit] = altMap
          }
        })
      }

      const dividendsMap = {}
      if (Array.isArray(entry.dividends)) {
        entry.dividends.forEach((divPoint) => {
          const year = Number(divPoint.year)
          const amount = Number(divPoint.amount)
          if (Number.isFinite(year) && Number.isFinite(amount)) {
            dividendsMap[year] = amount
          }
        })
      } else if (entry.dividends && typeof entry.dividends === 'object') {
        Object.entries(entry.dividends).forEach(([yearKey, amount]) => {
          const year = Number(yearKey)
          const val = Number(amount)
          if (Number.isFinite(year) && Number.isFinite(val)) {
            dividendsMap[year] = val
          }
        })
      }

      const aliasSet = new Set()
      ;[entry.id, entry.requested_id].forEach((alias) => {
        if (alias) aliasSet.add(alias)
      })
      if (Array.isArray(entry.aliases)) {
        entry.aliases.forEach((alias) => {
          if (alias) aliasSet.add(alias)
        })
      }

      const record = {
        unit: (entry.unit || '').toLowerCase(),
        label: entry.label || '',
        category: entry.category || '',
        source: entry.source || '',
        prices: priceMap,
        altPrices,
        dividends: dividendsMap,
        dividendUnit: (entry.dividend_unit || entry.unit || '').toLowerCase(),
        altSources: entry.alt_sources || {},
        status: entry.status || 'unknown',
        errorMessage: entry.error_message || null,
        aliases: Array.from(aliasSet)
      }

      aliasSet.forEach((alias) => {
        if (!alias) return
        map[alias] = record
        map[String(alias).toLowerCase()] = record
      })
    })
  }
  yearlyPriceMap.value = map
}

function ensureMissingPriceEntries(requestedAssets = []) {
  if (!Array.isArray(requestedAssets) || !requestedAssets.length) return
  const map = { ...yearlyPriceMap.value }
  let changed = false
  requestedAssets.forEach((asset) => {
    if (!asset) return
    const tokens = buildTokenSetFromAsset(asset)
    if (!tokens.size) return
    const hasEntry = Array.from(tokens).some((token) => token && map[token])
    if (hasEntry) return
    const placeholder = buildYearlyPricePlaceholder(asset)
    placeholder.aliases.forEach((alias) => {
      if (!alias) return
      map[alias] = placeholder
      map[String(alias).toLowerCase()] = placeholder
    })
    changed = true
  })
  if (changed) {
    yearlyPriceMap.value = map
  }
}

function buildYearlyPricePlaceholder(asset) {
  const label = asset?.display ?? asset?.label ?? asset?.requested_id ?? asset?.id ?? asset?.ticker ?? '알 수 없는 자산'
  const entryId = asset?.id || asset?.requested_id || asset?.ticker || label
  const aliasSet = new Set()
  ;[entryId, asset?.label, asset?.display, asset?.ticker, asset?.requested_id].forEach((alias) => {
    if (alias) {
      aliasSet.add(alias)
      const normalized = normalizeLabelAlias(alias)
      if (normalized) aliasSet.add(normalized)
    }
  })
  const normalizedLabel = normalizeLabelAlias(label || '')
  if (normalizedLabel) aliasSet.add(normalizedLabel)
  return {
    unit: (asset?.unit || '').toLowerCase(),
    label,
    category: asset?.category || asset?.type || '',
    source: '',
    prices: {},
    altPrices: {},
    dividends: {},
    dividendUnit: '',
    altSources: {},
    status: 'failed',
    errorMessage: '데이터 불러오기 실패',
    aliases: Array.from(aliasSet).filter(Boolean)
  }
}

</script>
