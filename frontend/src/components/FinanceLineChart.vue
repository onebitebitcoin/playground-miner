<template>
  <div class="w-full bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
    <div class="p-4 border-b border-slate-100 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div class="flex flex-col gap-1 flex-1 min-w-0">
        <div class="flex items-center gap-2">
          <h3 class="text-base font-semibold text-slate-900">{{ chartTitle }}</h3>
          <button
            type="button"
            class="text-slate-500 hover:text-slate-900 transition"
            aria-label="정규화 계산식 설명"
            @click="showNormalizationInfo = true"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 12v4m0-8h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
        </div>
        <p v-if="bitcoinSummary" class="text-xs text-slate-500 truncate">{{ bitcoinSummary }}</p>
      </div>

      <!-- 시작 연도 조절 -->
      <div v-if="showYearSlider" class="flex flex-wrap items-center gap-3 sm:gap-4 w-full md:w-auto md:justify-end">
        <button
          @click="decrementYear"
          :disabled="!canDecrement"
          class="w-6 h-6 rounded flex items-center justify-center text-slate-700 hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed transition"
          title="연도 감소"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M20 12H4" />
          </svg>
        </button>

        <input
          :value="startYear"
          @input="updateYear($event.target.value)"
          type="range"
          :min="originalStartYear"
          :max="endYear - 1"
          step="1"
          class="flex-1 min-w-[140px] w-full max-w-xs h-1 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-slate-900"
        />

        <button
          @click="incrementYear"
          :disabled="!canIncrement"
          class="w-6 h-6 rounded flex items-center justify-center text-slate-700 hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed transition"
          title="연도 증가"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
          </svg>
        </button>

        <span class="text-xs font-mono text-slate-700 min-w-[3rem]">{{ startYear }}년</span>

        <div
          v-if="showTaxToggle || showDividendToggle"
          class="flex flex-row gap-2 w-full sm:gap-3 sm:w-auto sm:flex-wrap sm:items-center md:pl-3 md:border-l md:border-slate-200"
        >
          <div class="flex items-center gap-1.5 flex-shrink-0" v-if="showTaxToggle">
            <span class="text-xs font-medium text-slate-600 whitespace-nowrap">세금</span>
            <button
              type="button"
              class="text-slate-400 hover:text-slate-700 transition flex-shrink-0"
              aria-label="해외 주식 양도소득세 계산식 안내"
              @click.stop="showTaxInfo = true"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 12v4m0-8h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </button>
            <button
              type="button"
              class="relative inline-flex h-4 w-7 flex-shrink-0 items-center rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-1"
              :class="taxIncluded ? 'bg-slate-900' : 'bg-slate-200'"
              @click="toggleTax"
            >
              <span
                class="inline-block h-3 w-3 transform rounded-full bg-white shadow-sm transition-transform duration-200"
                :class="taxIncluded ? 'translate-x-3.5' : 'translate-x-0.5'"
              ></span>
            </button>
          </div>
          <div class="flex items-center gap-1.5 flex-shrink-0" v-if="showDividendToggle">
            <span class="text-xs font-medium text-slate-600 whitespace-nowrap">배당</span>
            <button
              type="button"
              class="text-slate-400 hover:text-slate-700 transition flex-shrink-0"
              aria-label="배당 재투자 계산식 안내"
              @click.stop="showDividendInfo = true"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 12v4m0-8h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </button>
            <button
              type="button"
              class="relative inline-flex h-4 w-7 flex-shrink-0 items-center rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-1"
              :class="[
                dividendIncluded ? 'bg-slate-900' : 'bg-slate-200',
                dividendTogglePending ? 'cursor-wait opacity-60' : ''
              ]"
              @click="toggleDividends"
              :aria-disabled="dividendTogglePending"
            >
              <span
                class="inline-block h-3 w-3 transform rounded-full bg-white shadow-sm transition-transform duration-200"
                :class="dividendIncluded ? 'translate-x-3.5' : 'translate-x-0.5'"
              ></span>
            </button>
            <div v-if="dividendTogglePending" class="flex items-center gap-1 text-[10px] text-slate-400 flex-shrink-0">
              <svg class="w-3 h-3 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke-width="3"></circle>
                <path class="opacity-75" stroke-width="3" d="M4 12a8 8 0 018-8"></path>
              </svg>
              <span class="hidden sm:inline">데이터 준비 중</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="p-4">
      <div v-if="chart.lines.length || loading" class="-mx-2 sm:mx-0">
        <div class="overflow-x-auto px-2 sm:px-0">
          <div class="relative w-full min-w-[640px] h-[320px] sm:h-[360px] md:h-[420px]">
            <!-- 로딩 오버레이 -->
            <div
              v-if="loading"
              class="absolute inset-0 bg-white/95 backdrop-blur-sm flex flex-col items-center justify-center z-10 rounded-xl"
            >
              <div class="w-full max-w-md px-6 space-y-4">
                <p class="text-sm font-semibold text-slate-700 text-center">
                  {{ loading && loadingProgress >= 80 ? '계산 중...' : '데이터 로딩 중...' }}
                </p>
                <p class="text-xs text-slate-500 text-center">
                  1~2분 정도 소요됩니다
                </p>

                <!-- Progress bar -->
                <div class="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden">
                  <div
                    class="bg-blue-500 h-full rounded-full transition-all duration-300 ease-out"
                    :class="{ 'animate-pulse': loadingProgress >= 100 }"
                    :style="{ width: `${loadingProgress}%` }"
                  ></div>
                </div>

                <!-- Progress percentage -->
                <p class="text-xs font-mono text-slate-600 text-center">{{ loadingProgress }}%</p>
              </div>
            </div>

            <svg
              :viewBox="`0 0 ${dimensions.width} ${dimensions.height}`"
              role="img"
              class="w-full h-full"
              preserveAspectRatio="xMidYMid meet"
              @mouseleave="hideTooltip"
            >
          <defs>
            <filter id="bitcoin-glow">
              <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>

          <g class="text-slate-200">
            <line
              v-for="tick in chart.yTicks"
              :key="`grid-${tick.y}`"
              :x1="dimensions.padding"
              :x2="dimensions.width - dimensions.padding"
              :y1="tick.y"
              :y2="tick.y"
              stroke="currentColor"
              stroke-width="1"
              stroke-dasharray="4 4"
            />
          </g>

          <g fill="none">
            <path
              v-for="line in chart.lines"
              :key="line.id"
              :d="line.path"
              :stroke="isBitcoinLine(line.label) ? '#FFD700' : line.color"
              :stroke-width="isBitcoinLine(line.label) ? 4 : 3"
              stroke-linecap="round"
              stroke-linejoin="round"
              fill="none"
              class="line-path"
              :filter="isBitcoinLine(line.label) ? 'url(#bitcoin-glow)' : undefined"
            />
          </g>

          <g>
            <g v-for="line in chart.lines" :key="`${line.id}-points`">
              <circle
                v-for="point in line.points"
                :key="`${line.id}-${point.year}`"
                :cx="point.x"
                :cy="point.y"
                :fill="isBitcoinLine(line.label) ? '#FFD700' : line.color"
                :r="isBitcoinLine(line.label) ? 5 : 4"
                fill-opacity="0.9"
                tabindex="0"
                @mouseenter="showTooltip(line.label, point)"
                @focus="showTooltip(line.label, point)"
                @mouseleave="hideTooltip"
                @blur="hideTooltip"
                class="line-point"
                :filter="isBitcoinLine(line.label) ? 'url(#bitcoin-glow)' : undefined"
              />
            </g>
          </g>

          <g class="text-slate-500 text-xs">
            <text
              v-for="tick in chart.yTicks"
              :key="`label-${tick.label}`"
              :x="dimensions.padding - 8"
              :y="tick.y + 4"
              text-anchor="end"
            >
              {{ tick.label }}
            </text>
            <text
              v-for="label in chart.xLabels"
              :key="`x-${label.year}`"
              :x="label.x"
              :y="dimensions.height - 15"
              text-anchor="middle"
            >
              {{ label.year }}
            </text>

          </g>
            </svg>
            <div
              v-if="tooltip.show"
              class="absolute pointer-events-none bg-slate-900 text-white text-xs rounded-lg px-3 py-2 shadow-lg"
              :style="{
                left: tooltip.left + '%',
                top: tooltip.top + '%',
                transform: 'translate(-50%, -120%)'
              }"
            >
              <div class="font-semibold">{{ tooltip.label }}</div>
              <div class="font-mono">{{ tooltip.valueText }}</div>
              <div class="text-[10px] text-slate-300">{{ tooltip.year }}년</div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="text-center text-sm text-slate-500 py-10">
        <span v-if="loading">데이터를 계산중입니다...</span>
        <span v-else>렌더링할 데이터가 없습니다. 프롬프트를 실행해 주세요.</span>
      </div>
    </div>
  </div>

  <teleport to="body">
    <div
      v-if="showNormalizationInfo"
      class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 px-4 py-6 sm:py-10"
      @click.self="showNormalizationInfo = false"
    >
      <div class="bg-white rounded-2xl shadow-xl max-w-lg w-full max-h-[calc(100vh-3rem)] overflow-y-auto p-6 space-y-4">
        <div class="flex items-center justify-between">
          <h4 class="text-base font-semibold text-slate-900">정규화 계산식</h4>
          <button
            type="button"
            class="text-slate-400 hover:text-slate-700 transition"
            aria-label="정규화 계산식 닫기"
            @click="showNormalizationInfo = false"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <p class="text-sm text-slate-600">
          <template v-if="calculationMethod === 'price'">
            각 자산의 시작 연도 가격을 1배로 정규화한 뒤, 시간이 지날수록 몇 배 상승 혹은 하락했는지를 로그 스케일로 표시합니다.
          </template>
          <template v-else>
            모든 자산의 {{ calculationMethod === 'cumulative' ? '누적 수익률' : calculationMethod === 'yearly_growth' ? '전년 대비 증감률' : '연평균 상승률' }}을 서로 비교하기 위해, 각 연도별 값(%)을 0에서 100 사이로 스케일링한 뒤 차트에 표시합니다.
          </template>
        </p>
        <p class="text-xs text-slate-500">
          <template v-if="calculationMethod === 'price'">
            서로 다른 가격 단위의 자산도 동일한 배수(Performance Multiple) 기준으로 비교할 수 있어 상대적인 성과를 직관적으로 파악할 수 있습니다.
          </template>
          <template v-else>
            즉, 시작 연도에 투자했다고 가정하고 해당 연도부터 올해까지의 {{ calculationMethod === 'cumulative' ? '누적' : calculationMethod === 'yearly_growth' ? '전년 대비' : '연평균(복리)' }} 상승률을 계산해 비교하는 방식입니다.
          </template>
        </p>
        <div class="bg-slate-50 rounded-xl border border-slate-200 p-4 text-sm text-slate-700 space-y-2">
          <p class="font-semibold text-slate-900">계산식</p>
          <p class="font-mono text-xs">
            <template v-if="calculationMethod === 'price'">
              Y축: Log10(배수) (시작 연도 = 1배)
            </template>
            <template v-else>
              정규화 값 = clamp({{ calculationMethod === 'cumulative' ? '누적 수익률' : calculationMethod === 'yearly_growth' ? '증감률' : '연평균 상승률' }} %, 0, 100)
            </template>
          </p>
          <p class="text-xs text-slate-500">
            <template v-if="calculationMethod === 'price'">
              로그 스케일은 동일한 비율(%) 변동을 동일한 간격으로 보여 주어, 어느 자산이 더 많은 배수로 성장했는지 쉽게 확인할 수 있습니다.
            </template>
            <template v-else>
              clamp는 값이 0보다 작으면 0, 100보다 크면 100으로 제한합니다.
            </template>
          </p>
        </div>
        <p class="text-xs text-slate-500">
          <template v-if="calculationMethod === 'price'">
            툴팁에서 실제 가격과 배수를 함께 보여주어, 절대가격과 상대 성과를 동시에 확인할 수 있습니다.
          </template>
          <template v-else>
            툴팁에서는 정규화된 값(0~100)과 함께 실제 {{ calculationMethod === 'cumulative' ? '누적 수익률' : calculationMethod === 'yearly_growth' ? '증감률' : '연평균 상승률' }}(%)도 함께 표시해 비교에 도움이 되도록 했습니다.
          </template>
        </p>
        <div class="text-right">
          <button
            type="button"
            class="px-4 py-2 rounded-xl bg-slate-900 text-white text-sm font-semibold"
            @click="showNormalizationInfo = false"
          >
            확인
          </button>
        </div>
      </div>
    </div>
  </teleport>

  <teleport to="body">
    <div
      v-if="showTaxInfo"
      class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 px-4 py-6 sm:py-10"
      @click.self="showTaxInfo = false"
    >
      <div class="bg-white rounded-2xl shadow-xl max-w-lg w-full max-h-[calc(100vh-3rem)] overflow-y-auto p-6 space-y-4">
        <div class="flex items-center justify-between">
          <h4 class="text-base font-semibold text-slate-900">해외 주식 양도소득세 계산식</h4>
          <button
            type="button"
            class="text-slate-400 hover:text-slate-700 transition"
            aria-label="세금 안내 닫기"
            @click="showTaxInfo = false"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="space-y-2 text-sm text-slate-700">
          <p>한국 거주자의 해외 주식 양도소득세는 다음과 같이 계산됩니다.</p>
          <div class="bg-slate-50 rounded-xl border border-slate-200 p-4 space-y-2 text-xs font-mono text-slate-800">
            <p>과세표준 = max(0, 양도차익 - 2,500,000원)</p>
            <p>세액 = 과세표준 × (20% + 지방소득세 2%) = 과세표준 × 22%</p>
            <p>세후 연평균 수익률 = 세전 연평균 수익률 × (1 - 0.22)</p>
            <p>세후 배수 = (1 + 세후 연평균 수익률) ^ 투자기간</p>
          </div>
          <p class="text-xs text-slate-500">
            차트에서는 미국 주식(USD 표기) 자산에만 위 세율을 적용하며, 비트코인과 디지털 자산·국내 자산에는 적용하지 않습니다. 기본공제액을 별도로 계산하지 않는 단순화 모델로, 동일 세율(22%)을 즉시 적용해 세후 성과를 추정합니다.
          </p>
        </div>
        <div class="text-right">
          <button
            type="button"
            class="px-4 py-2 rounded-xl bg-slate-900 text-white text-sm font-semibold"
            @click="showTaxInfo = false"
          >
            확인
          </button>
        </div>
      </div>
    </div>
  </teleport>

  <teleport to="body">
    <div
      v-if="showDividendInfo"
      class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 px-4 py-6 sm:py-10"
      @click.self="showDividendInfo = false"
    >
      <div class="bg-white rounded-2xl shadow-xl max-w-lg w-full max-h-[calc(100vh-3rem)] overflow-y-auto p-6 space-y-4">
        <div class="flex items-center justify-between">
          <h4 class="text-base font-semibold text-slate-900">배당 재투자 계산 방식</h4>
          <button
            type="button"
            class="text-slate-400 hover:text-slate-700 transition"
            aria-label="배당 안내 닫기"
            @click="showDividendInfo = false"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="space-y-2 text-sm text-slate-700">
          <p>배당 포함을 켜면 Yahoo Finance 종목의 배당 재투자(Adjusted Close) 데이터를 다시 불러와 연도별 가격을 재계산합니다.</p>
          <div class="bg-slate-50 rounded-xl border border-slate-200 p-4 space-y-2 text-xs font-mono text-slate-800">
            <p>조정 종가<sub>t</sub> = (종가<sub>t</sub> + 배당금<sub>t</sub>) × 분할·배당 조정계수</p>
            <p>재투자 가정: 배당금은 지급 즉시 동일 종목에 재투자 → Adjusted Close 사용</p>
            <p>연도별 수익률 = 조정 종가 기반 CAGR / 누적 수익률</p>
          </div>
          <p class="text-xs text-slate-500">
            즉, 배당 포함 시에는 배당금을 현금으로 받지 않고 같은 종목을 추가 매수했다고 가정해 배당 효과가 복리로 반영됩니다. 배당 정보가 없는 자산은 원래 가격 데이터를 그대로 사용합니다.
          </p>
        </div>
        <div class="text-right">
          <button
            type="button"
            class="px-4 py-2 rounded-xl bg-slate-900 text-white text-sm font-semibold"
            @click="showDividendInfo = false"
          >
            확인
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  series: {
    type: Array,
    default: () => []
  },
  colors: {
    type: Object,
    default: () => ({})
  },
  currencyMode: {
    type: String,
    default: 'usd'
  },
  fxRate: {
    type: Number,
    default: 1300
  },
  loading: {
    type: Boolean,
    default: false
  },
  logs: {
    type: Array,
    default: () => []
  },
  startYear: {
    type: Number,
    default: null
  },
  endYear: {
    type: Number,
    default: null
  },
  originalStartYear: {
    type: Number,
    default: null
  },
  showYearSlider: {
    type: Boolean,
    default: false
  },
  taxIncluded: {
    type: Boolean,
    default: false
  },
  showTaxToggle: {
    type: Boolean,
    default: false
  },
  dividendIncluded: {
    type: Boolean,
    default: false
  },
  showDividendToggle: {
    type: Boolean,
    default: false
  },
  dividendTogglePending: {
    type: Boolean,
    default: false
  },
  priceData: {
    type: Object,
    default: () => ({})
  },
  calculationMethod: {
    type: String,
    default: 'cagr' // 'cagr' or 'cumulative'
  },
  bitcoinSummary: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:start-year', 'toggle-tax', 'toggle-dividends'])

const palette = ['#0f172a', '#2563eb', '#f97316', '#dc2626', '#059669', '#7c3aed', '#ea580c', '#0891b2', '#be185d', '#4338ca']
const currencySymbols = {
  usd: '$',
  krw: '₩'
}
const dimensions = {
  width: 1200,
  height: 400,
  padding: 60,
  paddingBottom: 40
}

const formatCurrencyValue = (value, mode) => {
  const symbol = currencySymbols[mode] || ''
  const formatter = new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: 2
  })
  return `${symbol}${formatter.format(value)}`
}

const formatMultipleValue = (value) => {
  if (!Number.isFinite(value)) return '-'
  if (value >= 10) return `${value.toFixed(0)}배`
  if (value >= 2) return `${value.toFixed(1)}배`
  return `${value.toFixed(2)}배`
}

const convertPriceForMode = (price, unit, mode, fxRate) => {
  if (!Number.isFinite(price)) return null
  const normalizedUnit = (unit || '').toLowerCase()
  if (mode === 'usd') {
    if (normalizedUnit === 'krw' || normalizedUnit === '₩' || normalizedUnit === 'krw₩') {
      return price / (fxRate || 1300)
    }
    return price
  }
  if (mode === 'krw') {
    if (normalizedUnit === 'krw' || normalizedUnit === '₩' || normalizedUnit === 'krw₩') {
      return price
    }
    return price * (fxRate || 1300)
  }
  return price
}

const resolveRawValue = (point, series, mode, fxRate) => {
  const getEntry = () => {
    if (!props.priceData) return null
    if (props.priceData[series.id]) return props.priceData[series.id]
    const lower = series.id?.toLowerCase()
    if (lower && props.priceData[lower]) return props.priceData[lower]
    return null
  }

  const entry = getEntry()
  let unit = (series.unit || '').toLowerCase()
  let rawValue = null

  if (entry) {
    const normalizedMode = mode === 'krw' ? 'krw' : 'usd'
    const altMap = entry.altPrices?.[normalizedMode]
    if (altMap && Number.isFinite(Number(altMap[point.year]))) {
      rawValue = Number(altMap[point.year])
      unit = normalizedMode
    } else if (entry.prices && Number.isFinite(Number(entry.prices[point.year]))) {
      rawValue = Number(entry.prices[point.year])
      unit = (entry.unit || unit || '').toLowerCase()
    }
  }

  if (!Number.isFinite(rawValue)) {
    rawValue = Number(point.raw_value ?? point.rawValue)
  }

  if (!Number.isFinite(rawValue)) {
    const fallback = Number(point.multiple)
    return { value: Number.isFinite(fallback) ? fallback : null, isRaw: false }
  }

  if (mode === 'usd') {
    if (unit === 'krw') {
      return { value: rawValue / (fxRate || 1300), isRaw: true }
    }
    return { value: rawValue, isRaw: true }
  }
  if (mode === 'krw') {
    if (unit === 'krw') {
      return { value: rawValue, isRaw: true }
    }
    return { value: rawValue * (fxRate || 1300), isRaw: true }
  }
  return { value: rawValue, isRaw: true }
}

const formatAxisLabel = (value, mode, usesRaw) => {
  if (!usesRaw) {
    return `${value.toFixed(1)}배`
  }
  return formatCurrencyValue(value, mode)
}

const currencyLabel = computed(() => (props.currencyMode === 'krw' ? 'KRW' : 'USD'))

const canDecrement = computed(() => {
  return props.startYear > props.originalStartYear
})

const canIncrement = computed(() => {
  return props.startYear < props.endYear - 1
})

function updateYear(value) {
  const year = parseInt(value)
  if (!isNaN(year)) {
    emit('update:start-year', year)
  }
}

function decrementYear() {
  if (canDecrement.value) {
    emit('update:start-year', props.startYear - 1)
  }
}

function incrementYear() {
  if (canIncrement.value) {
    emit('update:start-year', props.startYear + 1)
  }
}

function toggleTax() {
  emit('toggle-tax', !props.taxIncluded)
}

function toggleDividends() {
  emit('toggle-dividends', !props.dividendIncluded)
}

const chartTitle = computed(() => {
  if (!props.startYear || !props.endYear) {
    return '차트'
  }
  const yearDiff = props.endYear - props.startYear + 1
  const displayYears = Math.max(1, yearDiff - 1)
  let methodText
  if (props.calculationMethod === 'price') {
    return `${displayYears}년 가격 성과 비교 (${props.startYear} ~ ${props.endYear}, 배수 기준)`
  } else if (props.calculationMethod === 'cumulative') {
    methodText = '누적 수익률'
  } else if (props.calculationMethod === 'yearly_growth') {
    methodText = '전년 대비 증감률'
  } else {
    methodText = '연평균 상승률'
  }
  return `${displayYears}년 ${methodText} 비교 (${props.startYear} ~ ${props.endYear})`
})

const loadingProgress = computed(() => {
  if (!props.loading) return 100

  // progressTick을 종속성에 포함하여 자동 재계산 트리거
  progressTick.value

  const baseProgress = 5
  const maxFetchProgress = 80
  if (!props.logs.length) return baseProgress

  const maxLogs = 10
  const ratio = Math.min(1, props.logs.length / maxLogs)
  let progress = baseProgress + ratio * (maxFetchProgress - baseProgress)

  // 80% 이후에는 시간 기반으로 진행률을 천천히 증가
  if (progress >= maxFetchProgress) {
    // 80%부터 95%까지 천천히 증가 (최대 15초 동안)
    const elapsedTime = Date.now() - loadingStartTime.value
    const additionalProgress = Math.min(15, (elapsedTime / 1000) * 1.5) // 초당 1.5%씩 증가
    progress = maxFetchProgress + additionalProgress
  }

  return Math.round(Math.min(99, progress)) // 99%까지만 표시 (완료는 100%)
})

const tooltip = ref({
  show: false,
  label: '',
  valueText: '',
  year: '',
  left: 50,
  top: 50
})
const showNormalizationInfo = ref(false)
const showTaxInfo = ref(false)
const showDividendInfo = ref(false)
const loadingStartTime = ref(Date.now())
const progressTick = ref(0) // 진행률 강제 업데이트용
const progressUpdateInterval = ref(null)

// loading 상태 변경 감지
watch(() => props.loading, (newLoading) => {
  if (newLoading) {
    // 로딩 시작 시 타이머 시작
    loadingStartTime.value = Date.now()
    progressTick.value = 0

    // 80% 이후 진행률을 자동으로 업데이트하기 위한 인터벌
    if (progressUpdateInterval.value) {
      clearInterval(progressUpdateInterval.value)
    }
    progressUpdateInterval.value = setInterval(() => {
      // progressTick을 증가시켜 computed 재계산 트리거
      progressTick.value++
    }, 500) // 0.5초마다 업데이트
  } else {
    // 로딩 완료 시 인터벌 정리
    if (progressUpdateInterval.value) {
      clearInterval(progressUpdateInterval.value)
      progressUpdateInterval.value = null
    }
  }
})

const clampNormalizedValue = (value) => {
  if (!Number.isFinite(value)) return null
  // Price 모드, YoY Growth, CAGR 등은 음수 및 100 초과가 가능하므로 클램핑 하지 않음
  if (props.calculationMethod === 'price' || props.calculationMethod === 'yearly_growth' || props.calculationMethod === 'cagr') {
    return value
  }
  // 누적 수익률(Cumulative)만 0-100 범위로 클램핑
  return Math.max(0, Math.min(100, value))
}

const extractAnnualizedRate = (point) => {
  if (!point || typeof point !== 'object') return null
  const candidates = [point.value, point.annualized_return_pct, point.annualizedReturnPct]
  for (const candidate of candidates) {
    const rate = Number(candidate)
    if (Number.isFinite(rate)) {
      return rate
    }
  }
  return null
}

const chart = computed(() => {
  const visibleSeries = (props.series || []).filter(
    (s) => Array.isArray(s.points) && s.points.length
  )

  if (!visibleSeries.length) {
    return { lines: [], xLabels: [], yTicks: [], usesRawValues: false, fallbackOnly: false }
  }

  const yearSet = new Set()
  const values = []

  visibleSeries.forEach((series) => {
    series.points.forEach((point) => {
      if (typeof point.year === 'number') {
        yearSet.add(point.year)
      }
    })
  })

  const years = Array.from(yearSet).sort((a, b) => a - b)
  const chartWidth = dimensions.width - dimensions.padding * 2
  const chartHeight = dimensions.height - dimensions.padding - dimensions.paddingBottom
  const step = years.length > 1 ? chartWidth / (years.length - 1) : 0
  const scaleYear = (year, index) => dimensions.padding + index * step

  const lineData = visibleSeries.map((series, idx) => {
    const orderedPoints = [...series.points].sort((a, b) => a.year - b.year)
    const color = props.colors[series.id] || palette[idx % palette.length]

    // Price 모드: 로그 스케일 적용을 위해 원본 가격(Raw Price) 사용
    let firstValue = null
    if (props.calculationMethod === 'price' && orderedPoints.length > 0) {
      firstValue = extractAnnualizedRate(orderedPoints[0])
    }

    const rawPoints = orderedPoints
      .map((point) => {
        const annualizedRate = extractAnnualizedRate(point)
        if (!Number.isFinite(annualizedRate)) {
          return null
        }

        let normalizedValue
        let originalValue = annualizedRate

        // Price 모드: 배수 값 그대로 사용
        if (props.calculationMethod === 'price') {
          normalizedValue = annualizedRate
        } else {
          normalizedValue = clampNormalizedValue(annualizedRate)
        }

        if (normalizedValue === null) {
          return null
        }

        values.push(normalizedValue)
        return {
          year: point.year,
          value: normalizedValue,
          originalValue: originalValue,
          isRaw: false,
          isRate: true
        }
      })
      .filter(Boolean)

    return {
      id: series.id,
      color,
      rawPoints,
      label: series.label
    }
  })

  if (!values.length) {
    return { lines: [], xLabels: [], yTicks: [], usesRawValues: false, fallbackOnly: false }
  }

  // Y축 스케일링 계산
  let minValue = 0
  let maxValue = 100

  const allValues = values
  if (allValues.length > 0) {
    const realMin = Math.min(...allValues)
    const realMax = Math.max(...allValues)

    // Price 모드: 로그 스케일용 범위 (0 이하 제외)
    if (props.calculationMethod === 'price') {
      minValue = realMin > 0 ? realMin * 0.9 : 1
      maxValue = realMax * 1.1
    }
    // 데이터가 음수를 포함하거나 100을 크게 초과하는 경우 동적 스케일링 적용
    else if (realMin < 0 || realMax > 120) {
      const range = realMax - realMin
      minValue = Math.floor(realMin - range * 0.1)
      maxValue = Math.ceil(realMax + range * 0.1)
    } else {
      // 기존 정규화 로직 유지
      const rawMax = Math.max(...values, 0)
      if (Number.isFinite(rawMax) && rawMax > 0) {
        maxValue = Math.min(100, rawMax * 1.1)
        if (maxValue < rawMax + 5) {
          maxValue = Math.min(100, rawMax + 5)
        }
        if (maxValue < 20) {
          maxValue = Math.min(100, 20)
        }
      }
    }
  }

  const scaleValue = (value) => {
    // Price 모드: 로그 스케일
    if (props.calculationMethod === 'price') {
        if (value <= 0) return dimensions.padding + chartHeight
        const minLog = Math.log10(minValue)
        const maxLog = Math.log10(maxValue)
        const valLog = Math.log10(value)
        const ratio = (valLog - minLog) / (maxLog - minLog || 1)
        return dimensions.padding + chartHeight - ratio * chartHeight
    }
    
    // Linear Scale
    const ratio = (value - minValue) / (maxValue - minValue || 1)
    return dimensions.padding + chartHeight - ratio * chartHeight
  }

  const lines = lineData.map((line) => {
    const svgPoints = line.rawPoints.map((point) => {
      const yearIndex = years.indexOf(point.year)
      return {
        x: scaleYear(point.year, yearIndex === -1 ? 0 : yearIndex),
        y: scaleValue(point.value),
        ...point
      }
    })
    const path = svgPoints
      .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`)
      .join(' ')
    return {
      id: line.id,
      label: line.label,
      color: line.color,
      path,
      points: svgPoints
    }
  })

  const yTicks = Array.from({ length: 5 }).map((_, idx) => {
    let value
    let label

    if (props.calculationMethod === 'price') {
        // Log Scale Ticks (multiples)
        const minLog = Math.log10(minValue)
        const maxLog = Math.log10(maxValue)
        const logVal = minLog + (maxLog - minLog) * (idx / 4)
        value = Math.pow(10, logVal)
        label = formatMultipleValue(value)
    } else {
        // Linear Scale Ticks
        const ratio = idx / 4
        value = minValue + (maxValue - minValue) * ratio
        label = value.toFixed(0)
    }

    return {
      y: scaleValue(value),
      label
    }
  })

  // X축 라벨 - 모든 연도 표시
  const xLabels = years.map((year, index) => ({
    year,
    x: scaleYear(year, index)
  }))

  return {
    lines,
    yTicks,
    xLabels,
    usesRawValues: false,
    fallbackOnly: false,
    mode: 'normalized'
  }
})

defineExpose({ chart, dimensions })

function isBitcoinLine(label) {
  if (!label) return false
  const lowerLabel = label.toLowerCase()
  return lowerLabel.includes('비트코인') || lowerLabel.includes('bitcoin') || lowerLabel.includes('btc')
}

function tooltipValueFormatter(point) {
  if (!point) return '-'

  // Price 모드: 실제 가격 표시
  if (props.calculationMethod === 'price') {
    const multiple = Number(point.value)
    const rawPrice = Number(point.raw_value ?? point.rawValue)
    const convertedPrice = convertPriceForMode(rawPrice, point.unit, props.currencyMode, props.fxRate)
    const parts = []
    if (Number.isFinite(multiple)) {
      parts.push(formatMultipleValue(multiple))
    }
    if (Number.isFinite(convertedPrice)) {
      parts.push(formatCurrencyValue(convertedPrice, props.currencyMode))
    }
    return parts.length ? parts.join(' · ') : '-'
  }

  // 다른 모드일 때는 % 표시
  if (Number.isFinite(point.originalValue)) {
    return `${point.originalValue.toFixed(1)}%`
  }
  if (Number.isFinite(point.value)) {
    return `${point.value.toFixed(1)}%`
  }
  return '-'
}

function showTooltip(seriesLabel, point) {
  const left = Math.max(5, Math.min(95, (point.x / dimensions.width) * 100))
  const top = Math.max(10, Math.min(90, (point.y / dimensions.height) * 100))
  tooltip.value = {
    show: true,
    label: seriesLabel,
    valueText: tooltipValueFormatter(point),
    year: point.year,
    left,
    top
  }
}

function hideTooltip() {
  tooltip.value = { ...tooltip.value, show: false }
}
</script>

<style scoped>
.line-path {
  stroke-dasharray: 2000;
  stroke-dashoffset: 2000;
  animation: line-draw 1s ease forwards;
}
.line-point {
  animation: point-pop 0.6s ease forwards;
  opacity: 0;
}
@keyframes line-draw {
  to {
    stroke-dashoffset: 0;
  }
}
@keyframes point-pop {
  to {
    opacity: 1;
    transform: scale(1);
  }
  from {
    opacity: 0;
    transform: scale(0.6);
  }
}
.animate-fade-in {
  animation: fade-in 0.3s ease-in forwards;
  opacity: 0;
}
@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
