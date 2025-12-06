<template>
  <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 relative">
    <button
      type="button"
      class="w-full flex items-center justify-between text-left hover:bg-slate-50 -m-4 sm:-m-6 p-4 sm:p-6 rounded-2xl transition-colors"
      @click="toggleDebug"
    >
      <div class="flex items-center gap-2">
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
          <p class="text-base font-semibold text-slate-900">로그</p>
          <p class="text-xs text-slate-500">관리자 전용 질문 프롬프트 & 실시간 로그</p>
        </div>
      </div>
      <span class="text-xs text-slate-500">
        {{ showDebug ? '닫기' : '펼치기' }}
      </span>
    </button>

    <div v-if="showDebug && hasLogs" class="absolute top-5 right-6 flex gap-3 z-10">
      <button
        type="button"
        class="text-xs text-blue-600 hover:text-blue-800 underline decoration-dotted transition-colors"
        @click.stop="handleCopy"
      >
        {{ copyText }}
      </button>
      <button
        type="button"
        class="text-xs text-rose-500 hover:text-rose-700 underline decoration-dotted transition-colors"
        @click.stop="clearLogs"
      >
        로그 초기화
      </button>
    </div>

    <div v-if="showDebug" class="space-y-3 mt-6">
      <div class="flex gap-2 items-center">
        <input
          :value="prompt"
          type="text"
          class="flex-1 rounded-2xl border border-slate-200 px-4 py-2.5 text-sm focus:ring-2 focus:ring-slate-900 focus:border-slate-900 disabled:bg-slate-50 disabled:text-slate-400"
          placeholder="예) 100만원을 넣었으면 비트코인과 대표 자산의 10년 후에는 얼마일까?"
          :disabled="loading"
          @keyup.enter.prevent="submit"
          @input="handleInput"
        />
      </div>

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
import { copyToClipboard } from '@/composables/useClipboard'

const props = defineProps({
  showDebug: { type: Boolean, default: false },
  prompt: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  displayLogs: { type: Array, default: () => [] },
  hasLogs: { type: Boolean, default: false }
})

const emit = defineEmits(['update:show-debug', 'update:prompt', 'clear-logs', 'submit', 'input-change'])
const logContainer = ref(null)
const copyText = ref('로그 복사')

function toggleDebug() {
  emit('update:show-debug', !props.showDebug)
}

function clearLogs() {
  emit('clear-logs')
}

function handleInput(event) {
  emit('update:prompt', event.target.value)
  emit('input-change')
}

function submit() {
  emit('submit')
}

async function handleCopy() {
  if (!props.displayLogs.length) return
  const text = props.displayLogs.join('\n')
  await copyToClipboard(
    text,
    () => {
      copyText.value = '복사 완료!'
      setTimeout(() => {
        copyText.value = '로그 복사'
      }, 2000)
    },
    () => {
      copyText.value = '복사 실패'
      setTimeout(() => {
        copyText.value = '로그 복사'
      }, 2000)
    }
  )
}

watch(() => props.displayLogs.length, async () => {
  if (logContainer.value && props.showDebug) {
    await nextTick()
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
})
</script>
