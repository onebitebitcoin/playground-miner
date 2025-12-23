<template>
  <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-8">
    <div class="flex flex-col items-center gap-4 text-center">
      <div class="space-y-1">
        <p class="text-sm font-semibold text-slate-900">{{ label }}</p>
        <p class="text-xs text-slate-500">{{ description }}</p>
      </div>
      <div class="w-full max-w-md">
        <div class="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
          <div
            class="bg-gradient-to-r from-blue-500 to-blue-600 h-full rounded-full transition-all duration-300 ease-out"
            :style="{ width: `${progress}%` }"
          ></div>
        </div>
      </div>
      <p class="text-xs text-slate-500">진행률 {{ progress }}%</p>
      <button
        class="flex items-center gap-2 px-3 py-1.5 border border-rose-200 text-rose-500 text-xs rounded-full hover:bg-rose-50 transition-colors"
        @click="$emit('cancel')"
      >
        <svg class="w-3.5 h-3.5 animate-spin" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
        취소
      </button>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  label: String,
  description: String,
  progress: Number
})

defineEmits(['cancel'])
</script>
