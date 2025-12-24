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
            class="block-item relative w-7 h-7 sm:w-8 sm:h-8 md:w-9 md:h-9 lg:w-10 lg:h-10 rounded shadow-sm bg-gradient-to-br from-amber-500 via-yellow-500 to-amber-600 border border-amber-600/60 animate-pop-in flex-shrink-0"
            :title="`#${b.height} — 난이도 ${b.difficulty}\n${new Date(b.timestamp).toLocaleString()}`"
          >
            <div class="absolute inset-0 bg-gradient-to-br from-transparent via-white/20 to-transparent opacity-50"></div>
            <div class="absolute inset-0 grid place-items-center text-[9px] sm:text-[10px] md:text-[11px] lg:text-[12px] text-amber-950 font-bold drop-shadow-sm">
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
  0% {
    transform: scale(0.6) rotate(-10deg);
    opacity: 0.1;
  }
  70% {
    transform: scale(1.12) rotate(5deg);
    opacity: 1;
  }
  100% {
    transform: scale(1) rotate(0deg);
  }
}

.animate-pop-in {
  animation: popIn 400ms cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.block-item {
  box-shadow:
    0 4px 6px rgba(251, 191, 36, 0.3),
    0 1px 3px rgba(0, 0, 0, 0.1),
    inset 0 1px 2px rgba(255, 255, 255, 0.3);
  transition: all 0.2s ease;
}

.block-item:hover {
  transform: translateY(-2px) scale(1.05);
  box-shadow:
    0 8px 12px rgba(251, 191, 36, 0.5),
    0 2px 6px rgba(0, 0, 0, 0.15),
    inset 0 1px 2px rgba(255, 255, 255, 0.4),
    0 0 20px rgba(251, 191, 36, 0.4);
}
</style>
