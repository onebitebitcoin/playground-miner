<template>
  <div class="bg-white rounded-2xl shadow-lg border border-slate-200 p-4 sm:p-6">
    <div class="flex items-center justify-between mb-4 gap-3">
      <h3 class="text-lg sm:text-xl font-bold text-slate-800">채굴 시작</h3>
      <span id="miner-label" class="text-sm font-medium text-slate-600">
        {{ miner || 'guest' }}
      </span>
    </div>

    <div class="bg-slate-800/5 rounded-xl p-3 sm:p-4 mb-4 border border-slate-200 text-xs sm:text-sm text-slate-800 leading-relaxed">
      1~100,000 범위의 난수 중 현재 난이도 이하가 나오면 블록을 채굴할 수 있습니다. 10블록마다 난이도는 절반으로 낮아집니다.
    </div>

    <div class="bg-slate-50 border border-slate-200 rounded-xl p-4 sm:p-6 mb-4 flex items-center justify-center">
      <MiningAnim :state="miningState" />
    </div>

    <button
      class="w-full bg-slate-800 hover:bg-slate-700 disabled:bg-slate-400 text-white rounded-xl px-4 sm:px-6 py-3 sm:py-4 font-semibold text-base sm:text-lg transition-all duration-200 disabled:cursor-not-allowed"
      :disabled="miningState === 'mining'"
      @click="$emit('mine')"
    >
      <span v-if="miningState === 'mining'" class="flex items-center justify-center gap-2">
        <svg class="animate-spin w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <circle
            cx="12"
            cy="12"
            r="10"
            stroke-width="3"
            stroke-dasharray="31.416"
            stroke-dashoffset="31.416"
            class="animate-spin"
            style="animation: spin 1s linear infinite;"
          />
        </svg>
        채굴 중...
      </span>
      <span v-else>채굴 시도하기</span>
    </button>

    <div v-if="lastAttempt" class="text-center my-4">
      <span class="text-sm text-slate-600">마지막 시도값:</span>
      <span class="font-mono text-lg font-bold text-slate-800 ml-2">{{ lastAttempt }}</span>
    </div>

    <div
      v-if="message"
      :class="[
        'p-4 rounded-xl border transition-all duration-300',
        messageType === 'ok'
          ? 'bg-gradient-to-br from-amber-50 via-yellow-50 to-amber-100 border-amber-300 text-amber-900 font-semibold shadow-lg shadow-amber-200/50'
          : 'border-slate-200 bg-slate-800/5 text-slate-800'
      ]"
    >
      <div v-if="messageType === 'ok'" class="flex items-center gap-2">
        <svg class="w-5 h-5 text-amber-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
        </svg>
        <span>{{ message }}</span>
      </div>
      <div v-else>{{ message }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import MiningAnim from '@/components/MiningAnim.vue'

defineProps<{
  miner: string
  miningState: string
  lastAttempt: number | null
  message: string
  messageType: 'ok' | 'info'
}>()

defineEmits<{
  (e: 'update:miner', value: string): void
  (e: 'mine'): void
}>()
</script>
