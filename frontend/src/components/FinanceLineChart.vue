<template>
  <div class="w-full bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
    <div class="p-4 border-b border-slate-100 flex items-center justify-between gap-4">
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

      <!-- 시작 연도 조절 -->
      <div v-if="showYearSlider" class="flex items-center gap-3 flex-wrap">
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
          class="w-24 h-1 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-slate-900"
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
          v-if="showTaxToggle"
          class="flex items-center gap-2 pl-3 border-l border-slate-200"
        >
          <span class="text-xs font-medium text-slate-600 whitespace-nowrap">세금 포함</span>
          <button
            type="button"
            class="relative inline-flex h-5 w-9 items-center rounded-full transition-colors"
            :class="taxIncluded ? 'bg-slate-900' : 'bg-slate-200'"
            @click="toggleTax"
          >
            <span
              class="inline-block h-4 w-4 transform rounded-full bg-white transition"
              :class="taxIncluded ? 'translate-x-4' : 'translate-x-1'"
            ></span>
          </button>
        </div>
      </div>
    </div>

    <div class="p-4">
      <div v-if="chart.lines.length || loading" class="relative w-full h-[400px]">
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
          모든 자산의 {{ calculationMethod === 'cumulative' ? '누적 수익률' : '연평균 수익률' }}을 서로 비교하기 위해, 각 연도별 {{ calculationMethod === 'cumulative' ? '누적 수익률' : '연평균 수익률' }}(%)을 0에서 100 사이 값으로 스케일링한 뒤 차트에 표시합니다.
        </p>
        <p class="text-xs text-slate-500">
          즉, 시작 연도에 투자했다고 가정하고 해당 연도부터 올해까지의 {{ calculationMethod === 'cumulative' ? '누적' : '연평균(복리)' }} 수익률을 계산해 비교하는 방식입니다.
        </p>
        <div class="bg-slate-50 rounded-xl border border-slate-200 p-4 text-sm text-slate-700 space-y-2">
          <p class="font-semibold text-slate-900">계산식</p>
          <p class="font-mono">
            정규화 값 = clamp({{ calculationMethod === 'cumulative' ? '누적 수익률' : '연평균 수익률' }} %, 0, 100)
          </p>
          <p class="text-xs text-slate-500">
            clamp는 값이 0보다 작으면 0, 100보다 크면 100으로 제한합니다.
          </p>
        </div>
        <p class="text-xs text-slate-500">
          툴팁에서는 정규화된 값(0~100)과 함께 실제 {{ calculationMethod === 'cumulative' ? '누적 수익률' : '연평균 수익률' }}(%)도 함께 표시해 비교에 도움이 되도록 했습니다.
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
  priceData: {
    type: Object,
    default: () => ({})
  },
  calculationMethod: {
    type: String,
    default: 'cagr' // 'cagr' or 'cumulative'
  }
})

const emit = defineEmits(['update:start-year', 'toggle-tax'])

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

const chartTitle = computed(() => {
  if (!props.startYear || !props.endYear) {
    return '차트'
  }
  const yearDiff = props.endYear - props.startYear + 1
  const methodText = props.calculationMethod === 'cumulative' ? '누적 수익률' : '연평균 상승률'
  return `${yearDiff}년 ${methodText} 비교 (${props.startYear} ~ ${props.endYear})`
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

    const rawPoints = orderedPoints
      .map((point) => {
        const annualizedRate = extractAnnualizedRate(point)
        if (!Number.isFinite(annualizedRate)) {
          return null
        }

        const normalizedValue = clampNormalizedValue(annualizedRate)
        if (normalizedValue === null) {
          return null
        }

        values.push(normalizedValue)
        return {
          year: point.year,
          value: normalizedValue,
          originalValue: annualizedRate,
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

  // Y축을 0~100 범위로 제한하되 데이터 크기에 맞춰 상단을 조정
  const minValue = 0
  const rawMax = Math.max(...values, 0)
  let maxValue = 100
  if (Number.isFinite(rawMax) && rawMax > 0) {
    maxValue = Math.min(100, rawMax * 1.1)
    if (maxValue < rawMax + 5) {
      maxValue = Math.min(100, rawMax + 5)
    }
    if (maxValue < 20) {
      maxValue = Math.min(100, 20)
    }
  }

  const scaleValue = (value) => {
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
    const ratio = idx / 4
    const value = minValue + (maxValue - minValue) * ratio
    return {
      y: scaleValue(value),
      label: value.toFixed(0) // 정규화된 값은 정수로 표시
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
