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
        <div class="flex rounded-xl bg-slate-100 p-full md:w-auto">
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
          <h3 class="text-base font-semibold text-slate-900">
            {{ analysisResultType === 'cumulative' ? '자산의 누적 수익률 분석' : '비트코인의 연평균 상승률은?' }}
          </h3>
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
            <div class="flex items-center justify-between">
              <label class="text-sm font-medium text-slate-700">질문 프롬프트</label>
              <div v-if="isAdmin" class="flex items-center gap-2">
                <button
                  v-if="showDebug && progressLogs.length > 0"
                  @click="progressLogs = []"
                  class="text-xs text-rose-500 hover:text-rose-700 underline decoration-dotted transition-colors"
                  title="로그 초기화"
                >
                  로그 초기화
                </button>
                <button
                  @click="showDebug = !showDebug"
                  class="text-xs text-slate-400 hover:text-slate-600 underline decoration-dotted transition-colors"
                >
                  {{ showDebug ? '로그 숨기기' : '진행상황 자세히 보기' }}
                </button>
              </div>
            </div>
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
                class="shrink-0 w-11 h-11 rounded-2xl bg-slate-900 text-white flex items-center justify-center hover:bg-slate-800 transition-colors shadow-sm"
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
                class="shrink-0 w-11 h-11 rounded-2xl bg-rose-500 text-white flex items-center justify-center shadow-sm hover:bg-rose-600 transition-colors"
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

            <div v-if="isAdmin && showDebug" ref="logContainer" class="mt-3 bg-slate-900 text-slate-300 p-4 rounded-xl text-xs font-mono overflow-x-auto whitespace-pre-wrap max-h-60 overflow-y-auto border border-slate-700 shadow-inner leading-relaxed">
              <div v-if="!displayLogs.length" class="text-slate-500 italic">대기 중...</div>
              <div v-for="(log, i) in displayLogs" :key="i" class="mb-0.5 last:mb-0 border-b border-slate-800/50 pb-0.5 last:border-0 last:pb-0">
                <span class="text-slate-500 mr-2 select-none">[{{ String(i + 1).padStart(3, '0') }}]</span><span :class="log.includes('Error') || log.includes('오류') || log.includes('실패') || log.includes('Failed') ? 'text-rose-400' : log.includes('✓') || log.includes('완료') || log.includes('성공') ? 'text-green-400' : ''">{{ log }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="analysis || loading" class="space-y-5">

        <p class="text-xs text-slate-500">
          <span v-if="loading">환율 정보 로딩 중...</span>
          <span v-else-if="!analysis">환율 정보를 불러오려면 분석을 실행하세요.</span>
          <span v-else>1 USD ≈ ₩{{ formatFxRate(fxRate) }} (실시간 환율)</span>
        </p>

        <FinanceLineChart
          :series="chartSeries"
          :colors="colorMap"
          :currency-mode="'usd'"
          :fx-rate="fxRate"
          :price-data="yearlyPriceMap"
          :loading="loading"
          :loading-progress="loadingProgress"
          :logs="progressLogs"
          :start-year="displayStartYear"
          :end-year="analysis?.end_year"
          :original-start-year="analysis?.start_year"
          :show-year-slider="!loading && !!analysis"
          :show-tax-toggle="showTaxToggle"
          :tax-included="includeTax"
          :calculation-method="analysisResultType"
          @update:start-year="displayStartYear = $event"
          @toggle-tax="includeTax = $event"
        />

        <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 space-y-4" v-if="!loading">
          <div class="flex items-center justify-between">
            <h4 class="text-sm font-semibold text-slate-900">범례</h4>
            <span class="text-[11px] text-slate-500">
              {{ analysisResultType === 'cumulative' ? '누적 수익률' : '연평균 수익률' }} 순서로 정렬
            </span>
          </div>
          <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
            <button
              v-for="series in sortedLegend"
              :key="series.id"
              class="flex items-center justify-between rounded-2xl border px-4 py-3 text-left transition"
              :class="[
                hiddenSeries.has(series.id)
                  ? 'border-slate-200 text-slate-400 bg-slate-50'
                  : 'border-slate-200 text-slate-800 hover:border-slate-400',
                isBitcoinLegend(series) ? 'border-amber-400 shadow-[0_0_12px_rgba(255,215,0,0.6)]' : ''
              ]"
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
                <p>{{ formatMultiple(series.multiple_from_start) }}배</p>
              </div>
            </button>
          </div>
          <p class="text-[11px] text-slate-500">
            데이터 출처: <span v-html="dataSourcesText"></span>
          </p>
        </div>

        <div
          v-if="!loading && tableYears.length && sortedLegend.length"
          class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 space-y-3"
        >
          <div class="text-sm font-semibold text-slate-900">
            {{ analysisResultType === 'cumulative' ? '연도별 누적 수익률 비교' : '연도별 연평균 수익률 비교' }}
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full table-fixed text-xs text-slate-600 border-collapse">
              <thead>
                <tr class="bg-slate-50 text-slate-500">
                  <th class="py-2 px-2 text-left font-medium w-40">자산</th>
                  <th
                    v-for="year in tableYears"
                    :key="`ret-year-${year}`"
                    class="py-2 px-2 text-right font-medium"
                  >
                    {{ year }}년
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="series in sortedLegend"
                  :key="`ret-table-${series.id}`"
                  class="border-t border-slate-100"
                >
                  <td class="py-2 px-2 text-left font-semibold text-slate-700">
                    {{ series.label }}
                  </td>
                  <td
                    v-for="year in tableYears"
                    :key="`ret-cell-${series.id}-${year}`"
                    class="py-2 px-2 text-right font-mono text-slate-600"
                  >
                    {{ getReturnForYear(series, year) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div
          v-if="!loading && tableYears.length && sortedLegend.length"
          class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 space-y-3"
        >
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div class="text-sm font-semibold text-slate-900">연도별 종가 비교</div>
            <div class="flex items-center gap-2">
              <span class="text-[11px] text-slate-500">표시 통화</span>
              <div class="inline-flex bg-slate-100 rounded-2xl p-1">
                <button
                  class="px-3 py-1 rounded-xl text-[11px] font-semibold transition"
                  :class="priceDisplayMode === 'usd' ? 'bg-white text-slate-900 shadow' : 'text-slate-500'"
                  @click="priceDisplayMode = 'usd'"
                >
                  USD
                </button>
                <button
                  class="px-3 py-1 rounded-xl text-[11px] font-semibold transition"
                  :class="priceDisplayMode === 'krw' ? 'bg-white text-slate-900 shadow' : 'text-slate-500'"
                  @click="priceDisplayMode = 'krw'"
                >
                  KRW
                </button>
              </div>
            </div>
          </div>
          <p v-if="priceTableLoading" class="text-[11px] text-slate-500">연도별 종가 데이터를 불러오는 중입니다...</p>
          <p v-else-if="priceTableError" class="text-[11px] text-rose-600">{{ priceTableError }}</p>
          <div class="overflow-x-auto">
            <table class="min-w-full table-fixed text-xs text-slate-600 border-collapse">
              <thead>
                <tr class="bg-slate-50 text-slate-500">
                  <th class="py-2 px-2 text-left font-medium w-40">자산</th>
                  <th
                    v-for="year in tableYears"
                    :key="`year-${year}`"
                    class="py-2 px-2 text-right font-medium"
                  >
                    {{ year }}년
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="series in sortedLegend"
                  :key="`table-${series.id}`"
                  class="border-t border-slate-100"
                >
                  <td class="py-2 px-2 text-left font-semibold text-slate-700">
                    {{ series.label }}
                  </td>
                  <td
                    v-for="year in tableYears"
                    :key="`cell-${series.id}-${year}`"
                    class="py-2 px-2 text-right font-mono text-slate-600"
                  >
                    <a
                      v-if="formatPriceCell(series, year).url"
                      :href="formatPriceCell(series, year).url"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="text-blue-600 hover:text-blue-800 underline decoration-dotted underline-offset-2"
                    >
                      {{ formatPriceCell(series, year).text }}
                    </a>
                    <span v-else>
                      {{ formatPriceCell(series, year).text }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="text-[11px] text-slate-500">
            종가 데이터 출처: <span v-html="dataSourcesText"></span>
          </p>
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
import { computed, ref, watch, nextTick } from 'vue'
import FinanceLineChart from '@/components/FinanceLineChart.vue'
import { fetchHistoricalReturns, fetchHistoricalReturnsStream, fetchYearlyClosingPrices } from '@/services/financeService'
const TAX_RATE = 0.22

const tabs = [
  { key: 'historical', label: '과거 수익률' },
  { key: 'future', label: '미래 시나리오' }
]

const quickRequestOptions = [
  {
    key: 'safe',
    label: '대표 투자 상품과 비교',
    example: '비트코인, 금, 미국 10년물 국채, 은, S&P 500, 다우지수, 나스닥 100, 달러지수, 원유, 구리의 10년 연 평균 수익률을 비교해줘',
    quickRequest: '비트코인, 금, 미국 10년물 국채, 은, S&P 500, 다우지수, 나스닥 100, 달러지수, 원유, 구리의 10 년 연평균 수익률을 비교해줘',
    context: 'safe_assets'
  },
  {
    key: 'm2Compare',
    label: '미국/한국 M2와 비교',
    example: '지난 10년간 미국의 M2 통화량 연평균 상승률과 한국의 M2 연평균 상승률, 비트코인을 비교해줘',
    quickRequest: '지난 10년간 미국의 M2 통화량 연평균 상승률과 한국의 M2 연평균 상승률, 비트코인을 비교해줘',
    context: 'm2_compare'
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
    example: '비트코인과 삼성전자, SK하이닉스, NAVER, 카카오, LG에너지솔루션, 현대차, 기아, 삼성바이오로직스, 삼성SDI, 포스코홀딩스의 10년 연평균 수익률을 비교해줘',
    quickRequest: '비트코인과 삼성전자, SK하이닉스, NAVER, 카카오, LG에너지솔루션, 현대차, 기아, 삼성바이오로직 스, 삼성SDI, 포스코홀딩스의 10년 연평균 수익률을 비교해줘',
    context: 'kr_equity'
  }
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
const hiddenSeries = ref(new Set())
const includeTax = ref(false)
const currentYear = new Date().getFullYear()
const priceDisplayMode = ref('usd')
const yearlyPriceMap = ref({})
const priceTableLoading = ref(false)
const priceTableError = ref('')
let priceRequestId = 0
const showWonMode = computed(() => selectedContextKey.value === 'kr_equity')
const showTaxToggle = computed(() => selectedContextKey.value === 'us_bigtech' && !loading.value && !!analysis.value)
const loading = ref(false)
const errorMessage = ref('')
const analysis = ref(null)
const analysisResultType = ref('cagr') // 'cagr' or 'cumulative'
const displayStartYear = ref(null)
let abortController = null
const progressLogs = ref([])
const progressTimers = []
const logContainer = ref(null)
const loadingProgress = ref(0)

// Admin 사용자 확인 (localStorage에서 nickname 확인)
const isAdmin = computed(() => {
  const nickname = localStorage.getItem('nickname')
  return nickname === 'admin'
})

// Admin이면 항상 로그 표시, 아니면 숨김
const showDebug = ref(false)

// Admin이면 로그 자동으로 펼침
watch(isAdmin, (admin) => {
  if (admin) {
    showDebug.value = true
  }
}, { immediate: true })

const comparisonYears = computed(() => {
  if (!analysis.value) return 0
  const startYear = displayStartYear.value || analysis.value?.start_year
  return Math.max(1, analysis.value.end_year - startYear)
})

const defaultSummary = computed(() => {
  if (!analysis.value) return ''
  const period = `${analysis.value.start_year}년부터 ${analysis.value.end_year}년까지의`
  if (analysisResultType.value === 'cumulative') {
    return `${period} 누적 수익률입니다.`
  }
  return `${period} 연평균 수익률입니다.`
})

const promptIncludesBitcoin = computed(() => {
  const texts = []
  if (prompt.value) texts.push(prompt.value)
  if (Array.isArray(selectedQuickRequests.value)) {
    texts.push(selectedQuickRequests.value.join(' '))
  }
  const combined = texts.join(' ').toLowerCase()
  return combined.includes('비트코인') || combined.includes('bitcoin') || combined.includes('btc')
})

const filteredSeries = computed(() => {
  if (!analysis.value?.series?.length) return []
  const startYear = displayStartYear.value || analysis.value?.start_year
  const baseSeries = analysis.value.series.filter((series) => promptIncludesBitcoin.value || !isBitcoinLabel(series?.label))
  if (!startYear) return baseSeries

  return baseSeries.map((series) => {
    const filteredPoints = series.points.filter((point) => point.year >= startYear)
    if (filteredPoints.length < 2) return null

    // 재계산: multiple 기준으로 CAGR 계산
    const sortedPoints = [...filteredPoints].sort((a, b) => a.year - b.year)
    const startMultiple = Number(sortedPoints[0].multiple)
    const endMultiple = Number(sortedPoints[sortedPoints.length - 1].multiple)
    const years = sortedPoints[sortedPoints.length - 1].year - sortedPoints[0].year

    let annualizedReturnPct = 0
    let multipleFromStart = 1
    const appliesTax = includeTax.value && shouldApplyTax(series)
    const taxMultiplier = appliesTax ? 1 - TAX_RATE : 1

    if (startMultiple && endMultiple && years > 0) {
      const cagr = Math.pow(endMultiple / startMultiple, 1 / years) - 1
      const adjustedCagr = cagr * taxMultiplier
      annualizedReturnPct = adjustedCagr * 100
      if (years > 0 && 1 + adjustedCagr > 0) {
        multipleFromStart = Math.pow(1 + adjustedCagr, years)
      } else {
        multipleFromStart = endMultiple / startMultiple
      }
    }

    const rebasedPoints = sortedPoints.map((point) => {
      const pointMultiple = Number(point.multiple)
      let normalizedMultiple = pointMultiple
      if (Number.isFinite(pointMultiple) && Number.isFinite(startMultiple) && startMultiple > 0) {
        normalizedMultiple = pointMultiple / startMultiple
      }
      if (!Number.isFinite(normalizedMultiple) || normalizedMultiple <= 0) {
        normalizedMultiple = 1
      }
      const yearsElapsed = point.year - sortedPoints[0].year
      let recalculatedValue = 0
      if (yearsElapsed > 0) {
        const growthRate = Math.pow(normalizedMultiple, 1 / yearsElapsed) - 1
        if (Number.isFinite(growthRate)) {
          const adjustedGrowth = appliesTax ? growthRate * taxMultiplier : growthRate
          recalculatedValue = adjustedGrowth * 100
        }
      }
      return {
        ...point,
        multiple: normalizedMultiple,
        value: recalculatedValue
      }
    })

    return {
      ...series,
      points: rebasedPoints,
      annualized_return_pct: annualizedReturnPct,
      multiple_from_start: multipleFromStart
    }
  }).filter(Boolean)
})

const chartSeries = computed(() => {
  if (!filteredSeries.value.length) return []
  return filteredSeries.value.filter((series) => !hiddenSeries.value.has(series.id))
})

const sortedLegend = computed(() => {
  if (!filteredSeries.value?.length) return []
  return [...filteredSeries.value].sort((a, b) => {
    const aVal = typeof a.annualized_return_pct === 'number' ? a.annualized_return_pct : -Infinity
    const bVal = typeof b.annualized_return_pct === 'number' ? b.annualized_return_pct : -Infinity
    return bVal - aVal
  })
})

const tableYears = computed(() => {
  const yearSet = new Set()
  filteredSeries.value.forEach((series) => {
    series.points?.forEach((point) => {
      if (typeof point.year === 'number') {
        yearSet.add(point.year)
      }
    })
  })
  return Array.from(yearSet).sort((a, b) => a - b)
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
    // 비트코인은 금색, 나머지는 기존 색상
    const isBitcoin = series.label?.toLowerCase().includes('비트코인') ||
                      series.label?.toLowerCase().includes('bitcoin') ||
                      series.label?.toLowerCase().includes('btc')
    map[series.id] = isBitcoin ? '#FFD700' : legendColors[index % legendColors.length]
  })
  return map
})

const fxRate = computed(() => analysis.value?.fx_rate || 1300)
const analysisLogs = computed(() => analysis.value?.logs || [])
const displayLogs = computed(() => {
  // 로딩 중이거나 완료 후에도 progressLogs를 그대로 표시
  return progressLogs.value
})

const dataSourcesText = computed(() => {
  if (!analysis.value?.yearly_prices) return ''

  const sourceMap = {
    'Yahoo Finance': { url: 'https://finance.yahoo.com', label: 'Yahoo Finance' },
    'Stooq': { url: 'https://stooq.com', label: 'Stooq' },
    'pykrx': { url: 'https://github.com/sharebook-kr/pykrx', label: 'pykrx' },
    'Upbit': { url: 'https://upbit.com', label: 'Upbit' },
    'ECOS': { url: 'https://ecos.bok.or.kr', label: 'ECOS' },
    'FRED': { url: 'https://fred.stlouisfed.org', label: 'FRED' }
  }

  const sources = new Set()

  // Collect all unique sources from yearly_prices
  analysis.value.yearly_prices.forEach(entry => {
    if (entry.source) {
      sources.add(entry.source)
    }
    // Also collect alt sources
    if (entry.alt_sources) {
      Object.values(entry.alt_sources).forEach(altSource => {
        sources.add(altSource)
      })
    }
  })

  // Generate HTML links
  const links = Array.from(sources)
    .filter(source => sourceMap[source])
    .map(source => {
      const info = sourceMap[source]
      return `<a href="${info.url}" target="_blank" rel="noopener noreferrer" class="text-slate-700 underline decoration-dotted underline-offset-2 hover:text-slate-900">${info.label}</a>`
    })

  return links.join(' / ') || '데이터 출처 정보 없음'
})

// 로그가 업데이트되면 자동으로 스크롤
watch(() => progressLogs.value.length, async () => {
  if (logContainer.value && showDebug.value) {
    await nextTick()
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
})

// 로그 내용을 기반으로 진행률 계산
watch(() => progressLogs.value, (logs) => {


  const lastLog = logs[logs.length - 1] || ''

  // 로그 패턴에 따라 진행률 할당
  if (lastLog.includes('Starting Multi-Agent') || lastLog.includes('분석 요청')) {
    loadingProgress.value = 5
  } else if (lastLog.includes('[IntentClassifier]') && lastLog.includes('Analyzing')) {
    loadingProgress.value = 10
  } else if (lastLog.includes('[IntentClassifier]') && lastLog.includes('Calling LLM')) {
    loadingProgress.value = 15
  } else if (lastLog.includes('[IntentClassifier]') && lastLog.includes('Extracted')) {
    loadingProgress.value = 25
  } else if (lastLog.includes('[PriceRetriever]') && lastLog.includes('Fetching')) {
    loadingProgress.value = 30
  } else if (lastLog.includes('[PriceRetriever]') && lastLog.includes('Processing')) {
    // 자산 수에 따라 진행률 증가 (30-70%)
    const assetMatches = logs.filter(l => l.includes('[PriceRetriever]') && l.includes('Fetched'))
    const progress = 30 + Math.min(assetMatches.length * 5, 40)
    loadingProgress.value = progress
  } else if (lastLog.includes('[Calculator]')) {
    loadingProgress.value = 75
  } else if (lastLog.includes('[Calculator]') && lastLog.includes('Generated')) {
    loadingProgress.value = 90
  } else if (lastLog.includes('✓') || lastLog.includes('완료')) {
    loadingProgress.value = 100
  }
}, { deep: true })

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

function getReturnForYear(series, year) {
  const point = series.points?.find(p => p.year === year)
  if (!point || typeof point.value !== 'number') return '-'
  return formatPercent(point.value)
}

function formatMultiple(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '0.0'
  return value.toFixed(1)
}

function formatFxRate(rate) {
  if (!Number.isFinite(rate)) return '1,300'
  return Math.round(rate).toLocaleString()
}

const priceFormatter = new Intl.NumberFormat('en-US', {
  notation: 'compact',
  maximumFractionDigits: 2
})

function formatPriceCell(series, year) {
  const priceEntry = findPriceEntry(series)
  if (!priceEntry) {
    return { text: priceTableLoading.value ? '...' : '-', url: null }
  }

  // If the asset fetch failed, display "조회되지 않음"
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
  // 레이블에서 종목 코드 추출 (예: "삼성전자(005930)" -> "005930")
  const match = series.label.match(/\((\d{6})\)/)
  return match ? match[1] : null
}

function generateNaverFinanceUrl(series, year) {
  if (selectedContextKey.value !== 'kr_equity') return null
  const stockCode = extractStockCode(series)
  if (!stockCode) return null
  // 네이버 금융 차트 페이지로 이동 (해당 연도 데이터 표시)
  return `https://finance.naver.com/item/sise_day.naver?code=${stockCode}`
}

function convertValue(value, unit) {
  const sourceUnit = (unit || '').toLowerCase()
  if (priceDisplayMode.value === 'krw' && sourceUnit !== 'krw') {
    return value * (fxRate.value || 1300)
  }
  if (priceDisplayMode.value === 'usd' && sourceUnit === 'krw') {
    return value / (fxRate.value || 1300)
  }
  return value
}

function getUnitSymbol(unit) {
  if (!unit) return ''
  const lowered = unit.toLowerCase()
  if (lowered === 'usd' || lowered === '$') return '$'
  if (lowered === 'krw' || lowered === '₩') return '₩'
  return ''
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

function isBitcoinLegend(series) {
  return isBitcoinLabel(series?.label)
}

function isBitcoinLabel(label) {
  if (!label) return false
  const lower = label.toLowerCase()
  return lower.includes('비트코인') || lower.includes('bitcoin') || lower.includes('btc')
}

function shouldApplyTax(series) {
  if (!series) return false
  if (isBitcoinLabel(series.label)) return false
  const category = (series.category || '').toLowerCase()
  const unit = (series.unit || '').toLowerCase()
  const label = (series.label || '').toLowerCase()
  const id = (series.id || '').toLowerCase()
  const isUsEquity =
    category.includes('미국') ||
    label.includes('미국') ||
    id.endsWith('.us')
  return isUsEquity && unit === 'usd'
}

function resetPrompt() {
  prompt.value = ''
  selectedQuickKey.value = ''
  selectedQuickRequests.value = []
  selectedContextKey.value = ''
  hiddenSeries.value = new Set()
  yearlyPriceMap.value = {}
  priceTableError.value = ''
  priceTableLoading.value = false
  priceRequestId += 1
  if (abortController) {
    abortController.abort()
    abortController = null
  }
  loading.value = false
  // 로그는 유지 - 사용자가 수동으로 초기화 가능
}

function cancelRequest() {
  if (abortController) {
    abortController.abort()
    abortController = null
    loading.value = false
    progressLogs.value.push('요청이 취소되었습니다.')
  }
  priceRequestId += 1
  yearlyPriceMap.value = {}
  priceTableError.value = ''
  priceTableLoading.value = false
}

async function runAnalysis() {
  if (abortController) {
    abortController.abort()
  }

  // 프롬프트가 바뀌면 기존 데이터 삭제
  analysis.value = null
  hiddenSeries.value = new Set()
  priceDisplayMode.value = showWonMode.value ? 'krw' : 'usd'
  yearlyPriceMap.value = {}
  priceTableError.value = ''
  priceTableLoading.value = false
  priceRequestId += 1

  abortController = new AbortController()
  loading.value = true
  errorMessage.value = ''
  loadingProgress.value = 0  // 진행상황 초기화

  // 로그 누적: 구분선 추가
  if (progressLogs.value.length > 0) {
    progressLogs.value.push('')
    progressLogs.value.push('='.repeat(50))
    progressLogs.value.push('')
  }
  progressLogs.value.push('분석 요청 중...')

  try {
    const payload = {
      prompt: prompt.value,
      quickRequests: selectedQuickRequests.value,
      contextKey: selectedContextKey.value,
      signal: abortController.signal,
      onLog: (message) => {
        // Real-time log streaming
        progressLogs.value.push(message)
      }
    }

    // Use streaming version to get real-time logs
    const result = await fetchHistoricalReturnsStream(payload)

    analysis.value = result
    analysisResultType.value = result.calculation_method || 'cagr'
    displayStartYear.value = result.start_year
    hiddenSeries.value = new Set()

    // Use the yearly prices returned directly by the agent system
    if (result.yearly_prices) {
      processYearlyPrices(result.yearly_prices)
    } else {
      yearlyPriceMap.value = {}
      priceTableError.value = ''
      priceTableLoading.value = false
    }

    // 완료 메시지 추가
    progressLogs.value.push('')
    progressLogs.value.push('✓ 분석 완료')

  } catch (error) {
    if (error.name === 'AbortError') {
      errorMessage.value = '요청이 취소되었습니다.'
      progressLogs.value.push('요청이 취소되었습니다.')
    } else {
      errorMessage.value = error.message || '분석 중 오류가 발생했습니다.'
      progressLogs.value.push(`오류: ${error.message}`)
    }
  } finally {
    loading.value = false
    abortController = null
  }
}

function processYearlyPrices(pricesData) {
  const map = {}
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

      const record = {
        unit: (entry.unit || '').toLowerCase(),
        label: entry.label || '',
        category: entry.category || '',
        source: entry.source || '',
        prices: priceMap,
        altPrices,
        altSources: entry.alt_sources || {},
        status: entry.status || 'unknown',
        errorMessage: entry.error_message || null,
      }

      const aliases = new Set()
      ;[entry.id, entry.requested_id].forEach((alias) => {
        if (alias) aliases.add(alias)
      })
      if (Array.isArray(entry.aliases)) {
        entry.aliases.forEach((alias) => {
          if (alias) aliases.add(alias)
        })
      }

      aliases.forEach((alias) => {
        if (!alias) return
        map[alias] = record
        map[String(alias).toLowerCase()] = record
      })
    })
  }
  yearlyPriceMap.value = map
  priceTableLoading.value = false
}
</script>
