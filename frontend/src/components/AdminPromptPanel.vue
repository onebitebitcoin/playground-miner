<template>
  <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 relative">
    <button
      type="button"
      class="w-full flex items-center justify-between text-left hover:bg-slate-50 -m-4 sm:-m-6 p-4 sm:p-6 rounded-2xl transition-colors"
      @click="toggleDebug"
    >
      <div class="flex items-center gap-3">
        <svg
          class="w-5 h-5 text-slate-600 transition-transform duration-200"
          :class="{ 'rotate-90': showDebug }"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
        </svg>
        <div>
          <p class="text-base font-semibold text-slate-900">실시간 로그</p>
          <p class="text-xs text-slate-500">분석 요청이 어떻게 진행되는지 확인하세요.</p>
        </div>
      </div>
    </button>

    <div v-if="showDebug" class="space-y-3 mt-6">
      <div ref="logContainer" class="bg-slate-900 text-slate-300 p-4 rounded-xl text-xs font-mono overflow-x-auto whitespace-pre-wrap max-h-60 overflow-y-auto border border-slate-700 shadow-inner leading-relaxed">
        <div v-if="!displayLogs.length" class="text-slate-500 italic">대기 중...</div>
        <div
          v-for="(log, i) in displayLogs"
          :key="i"
          class="mb-0.5 last:mb-0 border-b border-slate-800/50 pb-0.5 last:border-0 last:pb-0"
        >
          <span class="text-slate-500 mr-2 select-none">[{{ String(i + 1).padStart(3, '0') }}]</span>
          <span
            :class="log.includes('Error') || log.includes('오류') || log.includes('실패') || log.includes('Failed')
              ? 'text-rose-400'
              : log.includes('✓') || log.includes('완료') || log.includes('성공')
                ? 'text-green-400'
                : ''"
          >
            {{ log }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  showDebug: { type: Boolean, default: false },
  displayLogs: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:show-debug'])
const logContainer = ref(null)

function toggleDebug() {
  emit('update:show-debug', !props.showDebug)
}

watch(() => props.displayLogs.length, async () => {
  if (logContainer.value && props.showDebug) {
    await nextTick()
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
})
</script>
