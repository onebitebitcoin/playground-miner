<template>
  <div class="bg-white rounded-2xl shadow-lg border border-slate-200 p-4 sm:p-6">
    <div class="flex items-center justify-between mb-4 gap-3">
      <h3 class="text-lg sm:text-xl font-bold text-slate-800">채굴 시작</h3>
      <span id="miner-label" class="text-sm font-medium text-slate-600">
        {{ miner || 'guest' }}
      </span>
    </div>

    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-3 mb-4">
      <div class="rounded-xl border border-slate-200 bg-slate-50/70 p-3">
        <p class="text-xs text-slate-500">블록 높이</p>
        <p class="mt-1 text-lg font-semibold text-slate-900">{{ status.height }}</p>
      </div>
      <div class="rounded-xl border border-slate-200 bg-slate-50/70 p-3">
        <p class="text-xs text-slate-500">난이도</p>
        <p class="mt-1 text-lg font-semibold text-slate-900">&le; {{ status.difficulty }}</p>
      </div>
      <div class="rounded-xl border border-slate-200 bg-slate-50/70 p-3">
        <p class="text-xs text-slate-500">블록 보상</p>
        <p class="mt-1 text-lg font-semibold text-slate-900">{{ status.reward }} sats</p>
      </div>
      <div class="rounded-xl border border-slate-200 bg-slate-50/70 p-3">
        <p class="text-xs text-slate-500">내 보상</p>
        <p class="mt-1 text-lg font-semibold text-slate-900">{{ myReward }} sats</p>
      </div>
      <button
        type="button"
        class="rounded-xl border border-slate-200 bg-slate-50/70 p-3 text-left hover:border-slate-300 transition"
        @click="$emit('show-peers')"
      >
        <p class="text-xs text-slate-500 flex items-center gap-1">
          접속자
          <svg class="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </p>
        <p class="mt-1 text-lg font-semibold text-slate-900">{{ totalPeerCount }}</p>
      </button>
    </div>

    <div class="bg-slate-50 border border-slate-200 rounded-xl p-4 sm:p-6 mb-4 flex items-center justify-center">
      <MiningAnim :state="miningState" />
    </div>

    <div v-if="lastAttempt" class="text-center mb-4">
      <span class="text-sm text-slate-600">마지막 시도값:</span>
      <span class="font-mono text-lg font-bold text-slate-800 ml-2">{{ lastAttempt }}</span>
    </div>

    <div class="mb-4">
      <label for="mining-note" class="sr-only">채굴 메시지</label>
      <input
        id="mining-note"
        type="text"
        :value="messageDraft"
        maxlength="120"
        class="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-800 focus:border-slate-900 focus:ring-2 focus:ring-slate-900/20 outline-none transition"
        placeholder="채굴되었을 때 저장할 메시지를 입력하세요"
        @input="$emit('update:messageDraft', ($event.target as HTMLInputElement).value)"
      />
      <p class="mt-1 text-right text-[11px] text-slate-400">최대 120자</p>
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

    <div
      v-if="message"
      :class="[
        'p-4 rounded-xl border transition-all duration-300 mt-3',
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

    <p class="mt-2 text-right text-xs text-slate-500">
      1~100,000 범위 난수 중 현재 난이도 이하가 나오면 채굴에 성공하며, 10블록마다 난이도는 절반으로 낮아집니다.
    </p>
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
  status: {
    height: number
    difficulty: number
    reward: number
  }
  myReward: number
  totalPeerCount: number
  messageDraft: string
}>()

defineEmits<{
  (e: 'update:miner', value: string): void
  (e: 'mine'): void
  (e: 'show-peers'): void
  (e: 'update:messageDraft', value: string): void
}>()
</script>
