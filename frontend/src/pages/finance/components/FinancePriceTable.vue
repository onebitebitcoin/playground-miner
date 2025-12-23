<template>
  <div
    v-if="tableYears.length && sortedLegend.length"
    class="bg-white border border-slate-200 rounded-2xl shadow-sm p-3 sm:p-4 md:p-6 space-y-2 sm:space-y-3"
  >
    <div class="text-sm font-semibold text-slate-900 px-1">
      {{ analysisResultType === 'price' ? '연도별 가격 비교' : analysisResultType === 'cumulative' ? '연도별 누적 수익률 비교' : analysisResultType === 'yearly_growth' ? '연도별 전년 대비 증감률 비교' : '연도별 연평균 상승률 비교' }}
    </div>
    <div class="overflow-x-auto px-2 sm:-mx-4 sm:px-4 md:-mx-6 md:px-6">
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
              :class="['py-1.5 sm:py-2 px-1.5 sm:px-2 text-right font-mono', getCellClass(series, year)]"
            >
              {{ formatValue(series, year) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  tableYears: Array,
  sortedLegend: Array,
  analysisResultType: String,
  getAssetUrl: Function,
  getLegendLabel: Function,
  formatValue: Function,
  getCellClass: Function
})
</script>
