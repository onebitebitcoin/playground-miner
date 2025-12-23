<template>
  <div>
    <div class="mb-2 flex items-center justify-between">
      <h4 class="font-semibold text-sm sm:text-base">블록 스택 <span class="text-xs text-slate-500 hidden sm:inline">(최신 → 과거)</span></h4>
      <div class="text-[10px] sm:text-xs text-slate-500">최근 {{ limit }}개</div>
    </div>
    <div class="overflow-x-auto -mx-2 px-2">
      <div class="flex items-center gap-1 sm:gap-2 pr-2 min-w-max">
        <template v-for="(b, idx) in displayed" :key="b.height">
          <div
            class="relative w-7 h-7 sm:w-8 sm:h-8 md:w-9 md:h-9 lg:w-10 lg:h-10 rounded shadow-sm bg-gradient-to-br from-amber-200 to-amber-400 border border-amber-500/40 animate-pop-in flex-shrink-0"
            :title="`#${b.height} — 난이도 ${b.difficulty}\n${new Date(b.timestamp).toLocaleString()}`"
          >
            <div class="absolute inset-0 grid place-items-center text-[9px] sm:text-[10px] md:text-[11px] lg:text-[12px] text-amber-900/80 font-semibold">
              {{ b.height }}
            </div>
          </div>
          <div v-if="idx < displayed.length - 1" class="flex-none text-slate-400">
            <svg class="w-3 h-2 sm:w-4 sm:h-3" viewBox="0 0 18 10" fill="none" xmlns="http://www.w3.org/2000/svg">
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
