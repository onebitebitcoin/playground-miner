<template>
  <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-8 space-y-6">
    <div class="flex flex-col items-center gap-4 text-center max-w-2xl mx-auto">
      <div class="space-y-2">
        <div class="flex items-center justify-center gap-2">
          <svg class="w-5 h-5 animate-spin text-indigo-600" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p class="text-lg font-bold text-slate-900">{{ currentStageLabel }}</p>
        </div>
        <p class="text-sm text-slate-500">{{ currentStageDescription }}</p>
      </div>

      <div class="w-full space-y-2">
        <div class="w-full bg-slate-100 rounded-full h-3 overflow-hidden shadow-inner">
          <div
            class="bg-gradient-to-r from-indigo-500 to-purple-600 h-full rounded-full transition-all duration-500 ease-out"
            :style="{ width: `${progress}%` }"
          ></div>
        </div>
        <p class="text-xs font-semibold text-slate-400 uppercase tracking-widest">
          Progress {{ progress }}%
        </p>
      </div>

      <div class="w-full grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2">
        <div
          v-for="(stage, index) in stages"
          :key="stage.key"
          class="flex flex-col items-center gap-1.5 p-2 rounded-xl transition-all"
          :class="index <= activeStageIndex ? 'bg-indigo-50 opacity-100' : 'bg-slate-50 opacity-40'"
        >
          <div 
            class="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold"
            :class="index < activeStageIndex ? 'bg-indigo-600 text-white' : index === activeStageIndex ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-200 text-slate-400'"
          >
            <svg v-if="index < activeStageIndex" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
            </svg>
            <span v-else>{{ index + 1 }}</span>
          </div>
          <span class="text-[10px] font-bold text-slate-600">{{ stage.label }}</span>
        </div>
      </div>

      <button
        type="button"
        class="flex items-center gap-2 px-5 py-2.5 bg-white border border-rose-200 text-rose-600 text-sm font-semibold rounded-full hover:bg-rose-50 transition-all shadow-sm active:scale-95"
        @click="$emit('cancel')"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
        분석 중단하기
      </button>
    </div>

    <!-- Live Logs -->
    <div class="max-w-3xl mx-auto space-y-3">
      <div class="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider px-1">
        <span class="relative flex h-2 w-2">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
        </span>
        Live Analysis Logs
      </div>
      <div class="bg-slate-900 rounded-2xl p-4 overflow-hidden shadow-2xl border border-slate-800">
        <div class="text-xs text-slate-300 font-mono whitespace-pre-wrap leading-relaxed max-h-40 overflow-y-auto pr-2 scroll-container">
          <div v-if="!logs.length" class="text-slate-600 italic">Waiting for agents...</div>
          <div v-for="(log, idx) in logs" :key="idx" class="border-b border-white/5 py-1 last:border-0">
            <span class="text-indigo-400 opacity-50 mr-2">[{{ (idx + 1).toString().padStart(2, '0') }}]</span>
            {{ log }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  stages: Array,
  activeStageIndex: Number,
  progress: Number,
  logs: Array
})

const activeStage = computed(() => props.stages[props.activeStageIndex] || props.stages[0])
const currentStageLabel = computed(() => activeStage.value?.label || '데이터 분석 중...')
const currentStageDescription = computed(() => activeStage.value?.description || '잠시만 기다려주세요.')

defineEmits(['cancel'])
</script>

<style scoped>
.scroll-container::-webkit-scrollbar {
  width: 4px;
}
.scroll-container::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.1);
  border-radius: 4px;
}
</style>
