<template>
  <div class="bg-white rounded-2xl shadow-lg border border-slate-200 p-4 sm:p-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-base sm:text-lg font-bold text-slate-800">블록 체인</h3>
      <button
        @click="$emit('show-blocks')"
        class="px-3 sm:px-4 py-2 text-amber-600 hover:text-amber-700 font-medium transition-all duration-200 text-sm sm:text-base underline decoration-2 underline-offset-4 hover:decoration-amber-700"
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
