<template>
  <div class="space-y-5">
    <div
      v-if="bitcoinHeroSummary"
      class="space-y-2 sm:space-y-3 text-slate-900 mb-4 sm:mb-6"
    >
      <p class="text-lg sm:text-2xl md:text-3xl font-black leading-snug">
        {{ bitcoinHeroSummary.startYear }}년부터 {{ bitcoinHeroSummary.endYear }}년까지 비트코인은
        {{ bitcoinHeroSummary.duration }}년 동안 원금의
        <span class="px-3 py-1 rounded-xl bg-yellow-200 text-yellow-900 font-black">
          {{ bitcoinHeroSummary.multipleText }}
        </span>
        가 되었습니다.
      </p>
      <p class="text-lg sm:text-2xl md:text-3xl font-black text-slate-900">
        같은 기간 연평균 상승률은
        <span class="px-3 py-1 rounded-xl bg-yellow-200 text-yellow-900 font-black">
          {{ bitcoinHeroSummary.cagrText }}
        </span>
        였습니다.
      </p>
      <p class="text-lg sm:text-2xl md:text-3xl font-black text-slate-900">
        {{ bitcoinHeroSummary.investmentText }}을 비트코인에 투자했다면 지금은
        <span class="px-3 py-1 rounded-xl bg-emerald-200 text-emerald-900 font-black">
          {{ bitcoinHeroSummary.finalText }}
        </span>
        정도입니다.
      </p>
    </div>
    <div v-else-if="analysisSummary" class="mb-2">
      <div v-html="analysisSummary" class="analysis-summary-content"></div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  bitcoinHeroSummary: Object,
  analysisSummary: String
})
</script>

<style scoped>
.analysis-summary-content :deep(h2),
.analysis-summary-content :deep(h3) {
  font-weight: 800;
  color: #0f172a;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}

.analysis-summary-content :deep(p) {
  line-height: 1.6;
  margin-bottom: 1rem;
}

.analysis-summary-content :deep(ul),
.analysis-summary-content :deep(ol) {
  margin-bottom: 1rem;
  padding-left: 1.5rem;
}

.analysis-summary-content :deep(li) {
  margin-bottom: 0.5rem;
}

.analysis-summary-content :deep(strong) {
  color: #1e293b;
  font-weight: 700;
}
</style>
