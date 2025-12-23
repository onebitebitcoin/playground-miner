<template>
  <section class="space-y-4">
    <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 space-y-4">
      <h3 class="text-base font-semibold text-slate-900">미래 비트코인 수익률 시나리오</h3>
      <p class="text-sm text-slate-600">
        온체인 사이클, 거시 환경, 채택률을 기준으로 3가지 시나리오를 구성했습니다. 실사용 데이터가 업데이트되면 자동으로 보정하도록 설계되어 있습니다.
      </p>
      <div class="grid gap-4 md:grid-cols-3">
        <div v-for="scenario in scenarios" :key="scenario.title" class="rounded-2xl border border-slate-200 p-4 bg-slate-50">
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
</template>

<script setup>
const props = defineProps({
  scenarios: Array
})
</script>
