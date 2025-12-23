<template>
  <div class="bg-white rounded-2xl shadow-lg border border-slate-200 p-4 sm:p-6">
    <div class="flex items-center gap-3 mb-4">
      <div class="w-10 h-10 sm:w-12 sm:h-12 bg-slate-800 rounded-xl flex items-center justify-center">
        <svg class="w-5 h-5 sm:w-6 sm:h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      </div>
      <h3 class="text-lg sm:text-xl font-bold text-slate-800">채굴 시작</h3>
    </div>

    <label class="block mb-4">
      <span class="text-sm font-medium text-slate-700 mb-2 block">채굴자 닉네임</span>
      <input
        :value="miner"
        @input="$emit('update:miner', $event.target?.value || '')"
        class="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all"
        placeholder="예: satoshi"
        inputmode="text"
      />
    </label>

    <div class="bg-amber-50 rounded-xl p-3 sm:p-4 mb-4 border border-amber-100 text-xs sm:text-sm text-amber-800 leading-relaxed">
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
      class="p-4 rounded-xl"
      :class="messageType === 'ok' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'"
    >
      {{ message }}
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
