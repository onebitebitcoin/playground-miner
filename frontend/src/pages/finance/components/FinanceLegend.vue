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
          isFailedSeries(series)
            ? 'border-rose-200 text-slate-400 bg-rose-50/60 cursor-not-allowed'
            : hiddenSeries.has(series.id)
              ? 'border-slate-200 text-slate-400 bg-slate-50'
              : 'border-slate-200 text-slate-800 hover:border-slate-400 active:bg-slate-50',
          isBitcoinLegend(series)
            ? 'border-amber-400 shadow-[0_0_12px_rgba(255,215,0,0.6)]'
            : isKoreanM2Legend(series)
              ? 'border-rose-400 shadow-[0_0_12px_rgba(248,113,113,0.55)]'
              : ''
        ]"
        :disabled="isFailedSeries(series)"
        :aria-disabled="isFailedSeries(series)"
        @click="handleToggle(series)"
      >
        <div class="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
          <span
            class="w-7 sm:w-9 h-2 rounded-full flex-shrink-0"
            :style="{
              backgroundColor: isFailedSeries(series) ? '#cbd5f5' : (colorMap[series.id] || '#0f172a'),
              opacity: isFailedSeries(series) ? 0.3 : (hiddenSeries.has(series.id) ? 0.3 : 1)
            }"
          ></span>
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2 flex-wrap">
              <p class="text-xs sm:text-sm font-semibold truncate">{{ legendLabel(series) }}</p>
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
          <template v-if="isFailedSeries(series)">
            <p class="whitespace-nowrap text-rose-500 font-semibold">데이터 불러오기 실패</p>
            <p class="whitespace-nowrap text-slate-400 mb-1">{{ getFailureReason(series) }}</p>
            <button
              @click.stop="handleRefresh(series)"
              class="inline-flex items-center gap-1 px-2 py-1 text-[10px] sm:text-[11px] font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded transition disabled:opacity-60 disabled:cursor-not-allowed"
              :disabled="isRefreshingSeries(series)"
              title="다시 시도"
            >
              <svg
                class="w-3 h-3"
                :class="isRefreshingSeries(series) ? 'animate-spin text-blue-600' : ''"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
              <span>{{ isRefreshingSeries(series) ? '불러오는 중...' : '새로고침' }}</span>
            </button>
          </template>
          <template v-else>
            <p class="whitespace-nowrap">{{ analysisResultType === 'price' ? '연평균 상승률' : analysisResultType === 'yearly_growth' ? '평균 증감률' : '연평균' }} {{ formatPercent(series.annualized_return_pct) }}</p>
            <p class="whitespace-nowrap">{{ formatMultiple(series.multiple_from_start) }}배</p>
          </template>
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
  isKoreanM2Legend,
  getLegendLabel as getDefaultLegendLabel,
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
  dataSourcesText: String,
  getLegendLabel: Function,
  refreshingAssetToken: String
})

const legendLabel = (series) => {
  if (typeof props.getLegendLabel === 'function') {
    return props.getLegendLabel(series)
  }
  return getDefaultLegendLabel(series)
}

const emit = defineEmits(['toggleSeries', 'refreshAsset'])

const isFailedSeries = (series) => {
  if (!series) return false
  return series.status === 'failed'
}

const normalizeToken = (value) => (value || '').toString().trim().toLowerCase()

const isRefreshingSeries = (series) => {
  if (!series || !props.refreshingAssetToken) return false
  const candidates = [
    series?.metadata?.requested_id,
    series?.requested_id,
    series?.ticker,
    series?.id,
    series?.label
  ]
  return candidates.some((candidate) => candidate && normalizeToken(candidate) === props.refreshingAssetToken)
}

const getFailureReason = (series) => {
  if (!series) return ''
  return series.failure_reason || series.error_message || series.metadata?.failure_reason || '데이터 불러오기 실패'
}

function handleToggle(series) {
  if (!series || isFailedSeries(series)) return
  emit('toggleSeries', series.id)
}

function handleRefresh(series) {
  if (!series) return
  emit('refreshAsset', series)
}
</script>
