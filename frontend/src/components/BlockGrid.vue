<template>
  <div>
    <div class="mb-2 flex items-center justify-between">
      <h4 class="font-semibold">블록 스택 <span class="text-xs text-slate-500">(최신 → 과거)</span></h4>
      <div class="text-xs text-slate-500">최근 {{ limit }}개 표시</div>
    </div>
    <div class="overflow-x-auto">
      <div class="flex items-center gap-2 pr-2 min-w-max">
        <template v-for="(b, idx) in displayed" :key="b.height">
          <div
            class="relative w-8 h-8 sm:w-9 sm:h-9 md:w-10 md:h-10 rounded shadow-sm bg-gradient-to-br from-indigo-200 to-indigo-400 border border-indigo-500/40 animate-pop-in"
            :title="`#${b.height} — 난이도 ${b.difficulty}\n${new Date(b.timestamp).toLocaleString()}`"
          >
            <div class="absolute inset-0 grid place-items-center text-[10px] sm:text-[11px] md:text-[12px] text-indigo-900/80 font-semibold">
              {{ b.height }}
            </div>
          </div>
          <div v-if="idx < displayed.length - 1" class="flex-none text-slate-400">
            <svg width="18" height="10" viewBox="0 0 18 10" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M0 5 H14" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" />
              <path d="M14 1 L18 5 L14 9" fill="#94a3b8" />
            </svg>
          </div>
        </template>
      </div>
    </div>
  </div>
<!-- 최신(왼쪽) → 과거(오른쪽) 순서로 가로 흐름. 래핑 없이 스크롤. -->
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  blocks: { type: Array, default: () => [] },
  limit: { type: Number, default: 60 },
})

// 화면에는 최신이 왼쪽에 오도록, 전달받은 순서(내림차순)를 유지
const displayed = computed(() => (props.blocks || []).slice(0, props.limit))
</script>

<style scoped>
@keyframes popIn {
  0% { transform: scale(0.6); opacity: 0.1; }
  70% { transform: scale(1.08); opacity: 1; }
  100% { transform: scale(1); }
}
.animate-pop-in { animation: popIn 300ms ease-out; }
</style>
