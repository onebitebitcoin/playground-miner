<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-2 sm:p-4">
    <div class="bg-white rounded-xl sm:rounded-2xl shadow-2xl max-w-4xl w-full max-h-[95vh] sm:max-h-[90vh] flex flex-col">
      <div class="flex items-center justify-between p-4 sm:p-6 border-b border-slate-200">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 sm:w-10 sm:h-10 rounded-lg flex items-center justify-center border border-amber-600/60 bg-gradient-to-br from-amber-500 via-yellow-500 to-amber-600 shadow-sm">
            <svg class="w-4 h-4 sm:w-5 sm:h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h3 class="text-lg sm:text-xl font-bold text-slate-800">최신 블록</h3>
        </div>
        <button @click="$emit('close')" class="p-2 hover:bg-slate-100 rounded-full transition-colors">
          <svg class="w-6 h-6 text-slate-800" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="flex-1 overflow-y-auto p-3 sm:p-6">
        <div v-if="broadcastMsg" class="mb-4 p-3 sm:p-4 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 text-sm">
          {{ broadcastMsg }}
        </div>

        <TransitionGroup name="list" tag="div" class="space-y-3">
          <div
            v-for="block in blocks"
            :key="block.height"
            class="p-4 rounded-xl border border-slate-100 bg-gradient-to-r from-slate-50 to-white hover:shadow-md transition-all duration-200"
          >
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-lg flex items-center justify-center border border-amber-600/60 bg-gradient-to-br from-amber-500 via-yellow-500 to-amber-600 shadow-sm">
                  <span class="text-white text-sm font-bold">#</span>
                </div>
                <span class="font-bold text-lg text-slate-800">{{ block.height }}</span>
              </div>
              <div class="text-xs text-slate-500">{{ formatTimestamp(block.timestamp) }}</div>
            </div>

            <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div class="bg-white rounded-lg p-3">
                <div class="text-xs text-slate-500 mb-1">채굴자</div>
                <div class="font-semibold text-slate-800">{{ block.miner || 'guest' }}</div>
              </div>
              <div class="bg-white rounded-lg p-3">
                <div class="text-xs text-slate-500 mb-1">난수</div>
                <div class="font-mono text-slate-800">{{ block.nonce }}</div>
              </div>
              <div class="bg-white rounded-lg p-3">
                <div class="text-xs text-slate-500 mb-1">난이도</div>
                <div class="font-mono text-slate-800">≤ {{ block.difficulty }}</div>
              </div>
              <div class="bg-white rounded-lg p-3">
                <div class="text-xs text-slate-500 mb-1">보상</div>
                <div class="font-semibold text-slate-800">{{ block.reward || 0 }} sats</div>
              </div>
              <div
                v-if="block.note"
                class="bg-white rounded-lg p-3 col-span-2 md:col-span-4"
              >
                <div class="text-xs text-slate-500 mb-1">메시지</div>
                <div class="text-sm text-slate-800 whitespace-pre-line">
                  {{ block.note }}
                </div>
              </div>
            </div>
          </div>
        </TransitionGroup>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Block } from '@/types'

type BlockWithNote = Block & { note?: string }

const props = defineProps<{
  blocks: BlockWithNote[]
  broadcastMsg?: string
}>()

defineEmits<{
  (e: 'close'): void
}>()

const formatTimestamp = (value?: string | number | Date) => {
  if (!value) return ''
  try {
    return new Date(value).toLocaleString()
  } catch {
    return ''
  }
}
</script>
