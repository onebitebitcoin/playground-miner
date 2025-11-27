<template>
  <div class="w-full bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
    <div class="p-4 border-b border-slate-100 flex items-center justify-between">
      <div>
        <h3 class="text-base font-semibold text-slate-900">{{ chartTitle }}</h3>
      </div>
      <span v-if="chart.lines.length" class="text-xs text-slate-500">
        {{ chart.mode === 'percent' ? '연평균 %' : currencyLabel }}
      </span>
    </div>

    <div class="p-4">
      <div v-if="chart.lines.length || loading" class="relative w-full h-[320px]">
        <!-- 로딩 오버레이 -->
        <div
          v-if="loading"
          class="absolute inset-0 bg-white/95 backdrop-blur-sm flex flex-col items-center justify-center z-10 rounded-xl"
        >
          <div class="w-full max-w-md px-6 space-y-4">
            <p class="text-sm font-semibold text-slate-700 text-center">
              {{ loadingProgress >= 100 ? '계산 중...' : '데이터 로딩 중...' }}
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
              :stroke="line.color"
              stroke-width="3"
              stroke-linecap="round"
              stroke-linejoin="round"
              fill="none"
              class="line-path"
            />
          </g>

          <g>
            <g v-for="line in chart.lines" :key="`${line.id}-points`">
              <circle
                v-for="point in line.points"
                :key="`${line.id}-${point.year}`"
                :cx="point.x"
                :cy="point.y"
                :fill="line.color"
                r="4"
                fill-opacity="0.9"
                tabindex="0"
                @mouseenter="showTooltip(line.label, point)"
                @focus="showTooltip(line.label, point)"
                @mouseleave="hideTooltip"
                @blur="hideTooltip"
                class="line-point"
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
              :y="dimensions.height - 12"
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
</template>

<script setup>
import { computed, ref } from 'vue'

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
  }
})

const palette = ['#0f172a', '#2563eb', '#f97316', '#dc2626', '#059669', '#7c3aed', '#ea580c', '#0891b2', '#be185d', '#4338ca']
const currencySymbols = {
  usd: '$',
  krw: '₩'
}
const dimensions = {
  width: 800,
  height: 360,
  padding: 32
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
  const rawValue = Number(point.raw_value ?? point.rawValue)
  const unit = (series.unit || '').toLowerCase()
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

const chartTitle = computed(() => {
  if (!props.startYear || !props.endYear) {
    return '라인 차트'
  }
  const yearDiff = props.endYear - props.startYear + 1
  return `${yearDiff}년 연평균 수익률 비교`
})

const loadingProgress = computed(() => {
  if (!props.loading) return 0
  if (!props.logs.length) return 5 // 초기 로딩 시작

  // 로그 수에 따라 진행률 계산 (최대 10개 자산 기준)
  const maxLogs = 10
  const progress = Math.min(100, 5 + (props.logs.length / maxLogs) * 95)
  return Math.round(progress)
})

const tooltip = ref({
  show: false,
  label: '',
  valueText: '',
  year: '',
  left: 50,
  top: 50
})

const chart = computed(() => {
  const visibleSeries = (props.series || []).filter(
    (s) => Array.isArray(s.points) && s.points.length
  )

  if (!visibleSeries.length) {
    return { lines: [], xLabels: [], yTicks: [], usesRawValues: false, fallbackOnly: false }
  }

  const yearSet = new Set()
  let rawCount = 0
  let fallbackCount = 0
  const values = []
  const usePercent = visibleSeries.some((series) =>
    series.points.some((point) => Number.isFinite(Number(point.value)))
  )

  visibleSeries.forEach((series) => {
    series.points.forEach((point) => {
      if (typeof point.year === 'number') {
        yearSet.add(point.year)
      }
    })
  })

  const years = Array.from(yearSet).sort((a, b) => a - b)
  const chartWidth = dimensions.width - dimensions.padding * 2
  const chartHeight = dimensions.height - dimensions.padding * 1.5
  const step = years.length > 1 ? chartWidth / (years.length - 1) : 0
  const scaleYear = (year, index) => dimensions.padding + index * step

  const lineData = visibleSeries.map((series, idx) => {
    const orderedPoints = [...series.points].sort((a, b) => a.year - b.year)
    const color = props.colors[series.id] || palette[idx % palette.length]
    const rawPoints = orderedPoints
      .map((point) => {
        let value
        let isRaw = false
        let isRate = false
        if (usePercent && Number.isFinite(Number(point.value))) {
          value = Number(point.value)
          isRate = true
        } else {
          const resolved = resolveRawValue(point, series, props.currencyMode, props.fxRate)
          value = resolved.value
          isRaw = resolved.isRaw
        }
        if (!Number.isFinite(value)) return null
        values.push(value)
        if (!usePercent) {
          if (isRaw) rawCount += 1
          else fallbackCount += 1
        }
        return {
          year: point.year,
          value,
          isRaw,
          isRate
        }
      })
      .filter(Boolean)
    return {
      id: series.id,
      color,
      rawPoints
    }
  })

  if (!values.length) {
    return { lines: [], xLabels: [], yTicks: [], usesRawValues: false, fallbackOnly: false }
  }

  let minValue = Math.min(...values, 0)
  let maxValue = Math.max(...values, 0)
  if (!Number.isFinite(minValue) || !Number.isFinite(maxValue)) {
    minValue = 0
    maxValue = 1
  }
  if (minValue === maxValue) {
    const delta = Math.abs(maxValue) * 0.2 || 0.5
    minValue -= delta
    maxValue += delta
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
      color: line.color,
      path,
      points: svgPoints
    }
  })

  const yTicks = Array.from({ length: 4 }).map((_, idx) => {
    const ratio = idx / 3
    const value = minValue + (maxValue - minValue) * ratio
    return {
      y: scaleValue(value),
      label: usePercent ? `${value.toFixed(1)}%` : formatAxisLabel(value, props.currencyMode, rawCount > 0)
    }
  })

  const xLabels = years.map((year, index) => ({
    year,
    x: scaleYear(year, index)
  }))

  return {
    lines,
    yTicks,
    xLabels,
    usesRawValues: !usePercent && rawCount > 0,
    fallbackOnly: !usePercent && rawCount === 0 && fallbackCount > 0,
    mode: usePercent ? 'percent' : (rawCount > 0 ? 'currency' : 'multiple')
  }
})

defineExpose({ chart, dimensions })

function tooltipValueFormatter(value, isRaw) {
  if (!Number.isFinite(value)) return '-'
  if (isRaw === 'rate') {
    return `${value.toFixed(2)}%`
  }
  return isRaw ? formatCurrencyValue(value, props.currencyMode) : `${value.toFixed(2)}배`
}

function showTooltip(seriesLabel, point) {
  const left = Math.max(5, Math.min(95, (point.x / dimensions.width) * 100))
  const top = Math.max(10, Math.min(90, (point.y / dimensions.height) * 100))
  tooltip.value = {
    show: true,
    label: seriesLabel,
    valueText: tooltipValueFormatter(point.value, point.isRate ? 'rate' : point.isRaw),
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
