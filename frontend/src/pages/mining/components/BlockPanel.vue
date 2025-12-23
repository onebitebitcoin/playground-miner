<template>
  <div class="bg-white rounded-2xl shadow-lg border border-slate-200 p-4 sm:p-6">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 sm:w-10 sm:h-10 bg-orange-100 rounded-lg flex items-center justify-center">
          <svg class="w-4 h-4 sm:w-5 sm:h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.783 0-2.676-2.153-1.415-3.414l5-5A2 2 0 009 9.172V5L8 4z" />
          </svg>
        </div>
        <h3 class="text-base sm:text-lg font-bold text-slate-800">블록 체인</h3>
      </div>
      <button
        @click="$emit('show-blocks')"
        class="px-3 sm:px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-all duration-200 text-sm sm:text-base"
      >
        최신 블록 보기
      </button>
    </div>
    <BlockGrid :blocks="blocks" :limit="60" />
  </div>
</template>

<script setup lang="ts">
import BlockGrid from '@/components/BlockGrid.vue'
import type { Block } from '@/types'

defineProps<{
  blocks: Block[]
}>()

defineEmits<{
  (e: 'show-blocks'): void
}>()
</script>
