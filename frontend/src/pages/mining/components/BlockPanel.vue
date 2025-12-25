<template>
  <div class="bg-white rounded-2xl shadow-lg border border-slate-200 p-4 sm:p-6">
    <div class="flex flex-wrap items-center justify-between gap-2 mb-3">
      <h3 class="text-base sm:text-lg font-bold text-slate-800">타임 체인 (블록 체인)</h3>
      <div class="flex items-center gap-3 text-xs sm:text-sm text-slate-500 ml-auto">
        <span>최근 {{ BLOCK_LIMIT }}개</span>
        <button
          @click="$emit('show-blocks')"
          class="px-3 sm:px-4 py-1.5 sm:py-2 text-amber-600 hover:text-amber-700 font-medium transition-all duration-200 text-xs sm:text-sm underline decoration-2 underline-offset-4 hover:decoration-amber-700"
        >
          최신 블록 보기
        </button>
      </div>
    </div>
    <BlockGrid :blocks="blocks" :limit="BLOCK_LIMIT" />
  </div>
</template>

<script setup lang="ts">
import BlockGrid from '@/components/BlockGrid.vue'
import type { Block } from '@/types'

const BLOCK_LIMIT = 60

defineProps<{
  blocks: Array<Block & { note?: string }>
}>()

defineEmits<{
  (e: 'show-blocks'): void
}>()
</script>
