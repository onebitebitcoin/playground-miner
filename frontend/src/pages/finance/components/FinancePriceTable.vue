<template>
  <div
    v-if="tableYears.length && sortedLegend.length"
    class="bg-white border border-slate-200 rounded-2xl shadow-sm p-3 sm:p-4 md:p-6 space-y-2 sm:space-y-3"
  >
    <div class="flex items-center justify-between gap-3 flex-wrap px-1">
      <div class="flex flex-col">
        <div class="text-sm font-semibold text-slate-900">
          {{ tableTitle }}
        </div>
        <p
          v-if="tableDescription"
          class="text-[11px] text-slate-400"
        >
          {{ tableDescription }}
        </p>
      </div>
      <div class="flex items-center text-xs text-slate-500">
        <div class="inline-flex items-center bg-slate-100 rounded-full p-0.5">
          <button
            v-for="mode in PRICE_TABLE_OPTIONS"
            :key="mode.key"
            type="button"
            class="px-2 py-1 rounded-full transition text-[11px]"
            :class="priceTableMode === mode.key ? 'bg-white text-slate-900 shadow-sm font-semibold' : 'text-slate-500'"
            @click="$emit('update:priceTableMode', mode.key)"
          >
            {{ mode.label }}
          </button>
        </div>
      </div>
    </div>
    <div
      ref="tableWrapper"
      class="overflow-x-auto px-2 sm:-mx-4 sm:px-4 md:-mx-6 md:px-6"
    >
      <table class="min-w-full table-fixed text-[11px] sm:text-xs text-slate-600 border-collapse">
        <thead>
          <tr class="bg-slate-50 text-slate-500">
            <th class="py-1.5 sm:py-2 px-1.5 sm:px-2 text-left font-medium w-32 sm:w-40 sticky left-0 bg-slate-50 z-10">자산</th>
            <th
              v-for="year in tableYears"
              :key="`ret-year-${year}`"
              class="py-1.5 sm:py-2 px-1.5 sm:px-2 text-right font-medium whitespace-nowrap"
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
            <td class="py-1.5 sm:py-2 px-1.5 sm:px-2 text-left font-semibold text-slate-700 sticky left-0 bg-white z-10">
              <a
                v-if="getAssetUrl(series)"
                :href="getAssetUrl(series)"
                target="_blank"
                rel="noopener noreferrer"
                class="hover:underline hover:text-blue-600 inline-flex items-center gap-1"
                title="실제 가격 확인"
              >
                {{ getLegendLabel(series) }}
                <svg class="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                </svg>
              </a>
              <span v-else>{{ getLegendLabel(series) }}</span>
            </td>
            <td
              v-for="year in tableYears"
              :key="`ret-cell-${series.id}-${year}`"
              :class="['py-1.5 sm:py-2 px-1.5 sm:px-2 text-right font-mono whitespace-pre-line', getCellClass(series, year)]"
            >
              {{ formatValue(series, year, { priceMode: priceTableMode }) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch, nextTick, computed } from 'vue'

const props = defineProps({
  tableYears: Array,
  sortedLegend: Array,
  analysisResultType: String,
  getAssetUrl: Function,
  getLegendLabel: Function,
  formatValue: Function,
  getCellClass: Function,
  priceTableMode: {
    type: String,
    default: 'price'
  }
})

defineEmits(['update:priceTableMode'])

const PRICE_TABLE_OPTIONS = [
  { key: 'price', label: '가격' },
  { key: 'return', label: '상승률' },
  { key: 'dividend', label: '배당률' }
]

const tableWrapper = ref(null)
const tableTitle = computed(() => {
  if (props.priceTableMode === 'price') {
    return '연도별 종가 비교 (연말 기준)'
  }
  if (props.priceTableMode === 'return') {
    return '연도별 상승률 비교'
  }
  if (props.priceTableMode === 'dividend') {
    return '연도별 배당률 비교'
  }
  return '연도별 비교'
})

const tableDescription = computed(() => {
  if (props.priceTableMode === 'price') {
    return '연말 종가 기준 (12월 31일, 현재 연도는 최신 가격)'
  }
  if (props.priceTableMode === 'return') {
    return '기준 연도를 1로 두고 누적 상승률(%)을 표시합니다'
  }
  if (props.priceTableMode === 'dividend') {
    return '해당 연도 배당금 ÷ 연말 가격 기준 배당 수익률'
  }
  return ''
})

function scrollToLatestColumns(behavior = 'auto') {
  if (!props.tableYears?.length) return
  nextTick(() => {
    const el = tableWrapper.value
    if (el) {
      el.scrollTo({
        left: el.scrollWidth,
        behavior
      })
    }
  })
}

onMounted(() => {
  scrollToLatestColumns('auto')
})

watch(
  () => [props.tableYears, props.sortedLegend, props.analysisResultType],
  () => {
    scrollToLatestColumns('smooth')
  }
)
</script>
