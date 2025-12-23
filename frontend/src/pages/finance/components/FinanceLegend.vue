<template>
  <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-3 sm:p-4 md:p-6 space-y-3 sm:space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-0">
      <h4 class="text-sm font-semibold text-slate-900">범례</h4>
      <span class="text-[10px] sm:text-[11px] text-slate-500">
        {{ analysisResultType === 'price' ? '연평균 상승률' : analysisResultType === 'cumulative' ? '누적 수익률' : analysisResultType === 'yearly_growth' ? '전년 대비 증감률' : '연평균 상승률' }} 순서로 정렬
      </span>
    </div>
    <div class="grid gap-2 sm:gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
      <button
        v-for="series in sortedLegend"
        :key="series.id"
        class="flex items-center justify-between rounded-xl sm:rounded-2xl border px-3 py-2.5 sm:px-4 sm:py-3 text-left transition"
        :class="[
          hiddenSeries.has(series.id)
            ? 'border-slate-200 text-slate-400 bg-slate-50'
            : 'border-slate-200 text-slate-800 hover:border-slate-400 active:bg-slate-50',
          isBitcoinLegend(series) ? 'border-amber-400 shadow-[0_0_12px_rgba(255,215,0,0.6)]' : ''
        ]"
        @click="$emit('toggleSeries', series.id)"
      >
        <div class="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
          <span
            class="w-7 sm:w-9 h-2 rounded-full flex-shrink-0"
            :style="{ backgroundColor: colorMap[series.id] || '#0f172a', opacity: hiddenSeries.has(series.id) ? 0.3 : 1 }"
          ></span>
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2 flex-wrap">
              <p class="text-xs sm:text-sm font-semibold truncate">{{ getLegendLabel(series) }}</p>
            </div>
            <p class="text-[11px] sm:text-xs text-slate-500 truncate">
              {{ formatAssetCategory(series) }}
            </p>
            <p
              v-if="getDividendYieldText(series)"
              class="text-[10px] sm:text-[11px] text-emerald-600 mt-0.5 sm:mt-1"
            >
              {{ getDividendYieldText(series) }}
            </p>
          </div>
        </div>
        <div class="text-[11px] sm:text-xs text-slate-500 text-right flex-shrink-0 ml-2">
          <p class="whitespace-nowrap">{{ analysisResultType === 'price' ? '연평균 상승률' : analysisResultType === 'yearly_growth' ? '평균 증감률' : '연평균' }} {{ formatPercent(series.annualized_return_pct) }}</p>
          <p class="whitespace-nowrap">{{ formatMultiple(series.multiple_from_start) }}배</p>
        </div>
      </button>
    </div>
    <p class="text-[11px] text-slate-500">
      데이터 출처: <span v-html="dataSourcesText"></span>
    </p>
  </div>
</template>

<script setup>
import { 
  isBitcoinLegend, 
  getLegendLabel, 
  formatAssetCategory, 
  formatPercent, 
  formatMultiple, 
  getDividendYieldText 
} from '../utils'

const props = defineProps({
  sortedLegend: Array,
  colorMap: Object,
  hiddenSeries: Object, // Set
  analysisResultType: String,
  dataSourcesText: String
})

defineEmits(['toggleSeries'])
</script>
