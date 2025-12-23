<template>
  <div class="preset-card-container bg-white rounded-2xl shadow-sm p-4 sm:p-6 space-y-5 relative">
    <div
      v-if="disabled"
      class="absolute inset-0 bg-slate-900/30 backdrop-blur-md rounded-2xl flex items-center justify-center z-10 cursor-pointer"
      @click="$emit('enable')"
    >
      <div class="flex flex-col items-center gap-3">
        <button
          class="w-16 h-16 rounded-full bg-slate-900 text-white flex items-center justify-center hover:bg-slate-800 transition-colors shadow-lg"
          @click.stop="$emit('enable')"
        >
          <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 4v16m8-8H4" />
          </svg>
        </button>
        <p class="text-sm font-semibold text-slate-900">비교 대상 추가하기</p>
      </div>
    </div>

    <div>
      <h3 class="text-base font-semibold text-slate-900">{{ title }}</h3>
      <div class="mt-3 space-y-3 text-xs">
        <div class="flex flex-wrap items-center gap-2">
          <span class="text-slate-500 font-semibold uppercase tracking-wide">빠른 설정</span>
          <span v-if="loadingPresets" class="text-slate-400">불러오는 중...</span>
          <span v-else-if="!presets.length" class="text-slate-400">등록된 빠른 설정이 없습니다.</span>
          <span v-else class="text-slate-500">사용자를 선택하여 직접 입력을 하거나 다른 사람을 선택하세요</span>
        </div>
        <div v-if="!loadingPresets && presets.length" class="relative">
          <div class="flex gap-3 overflow-x-auto pb-6 pt-3 -mx-1 px-1 -mt-3 scroll-container" style="overflow-y: visible; scroll-behavior: smooth;">
            <CompatibilityCard
              v-for="preset in presets"
              :key="preset.id"
              :label="preset.label"
              :image-url="preset.imageUrl"
              :birthdate="preset.birthdate"
              :placeholder-icon="placeholderIcon"
              :selected="selectedPresetId === preset.id"
              @click="$emit('applyPreset', preset)"
            />
          </div>
          <div class="scroll-hint">
            <svg class="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
            </svg>
          </div>
        </div>
      </div>
      
      <div class="grid gap-4 sm:grid-cols-2 mt-3">
        <label class="space-y-1 text-sm text-slate-600">
          <span class="font-medium text-slate-900">이름</span>
          <input
            :value="userName"
            @input="$emit('update:userName', $event.target.value)"
            type="text"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0"
            placeholder="이름을 입력하세요"
          />
        </label>
        <label class="space-y-1">
          <span class="text-xs font-semibold text-slate-500">성별 (선택)</span>
          <select
            :value="gender"
            @change="$emit('update:gender', $event.target.value)"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0 bg-white"
          >
            <option value="">선택 안 함</option>
            <option value="male">남성</option>
            <option value="female">여성</option>
          </select>
        </label>
      </div>
    </div>
    
    <div class="grid gap-4 sm:grid-cols-2">
      <label class="space-y-1">
        <span class="text-xs font-semibold text-slate-500">생년월일 *</span>
        <input
          :value="birthdate"
          @input="$emit('update:birthdate', $event.target.value)"
          type="date"
          class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0"
          required
        />
      </label>
      <div class="space-y-2">
        <label class="space-y-1">
          <span class="text-xs font-semibold text-slate-500">태어난 시간 (선택)</span>
          <input
            :value="birthtime"
            @input="$emit('update:birthtime', $event.target.value)"
            type="time"
            :disabled="timeUnknown"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0 disabled:bg-slate-50"
          />
        </label>
        <label class="inline-flex items-center gap-2 text-xs text-slate-500">
          <input 
            type="checkbox" 
            :checked="timeUnknown"
            @change="$emit('update:timeUnknown', $event.target.checked)"
            class="rounded border-slate-300 text-slate-900" 
          />
          시간을 모르겠어요
        </label>
      </div>
    </div>
  </div>
</template>

<script setup>
import CompatibilityCard from './CompatibilityCard.vue'

const props = defineProps({
  title: String,
  presets: Array,
  loadingPresets: Boolean,
  selectedPresetId: [String, Number],
  userName: String,
  gender: String,
  birthdate: String,
  birthtime: String,
  timeUnknown: Boolean,
  placeholderIcon: String,
  disabled: Boolean
})

defineEmits([
  'applyPreset', 
  'update:userName', 
  'update:gender', 
  'update:birthdate', 
  'update:birthtime', 
  'update:timeUnknown',
  'enable'
])
</script>

<style scoped>
.scroll-container::-webkit-scrollbar {
  height: 4px;
}
.scroll-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}
.scroll-hint {
  position: absolute;
  right: -10px;
  top: 50%;
  transform: translateY(-50%);
  width: 30px;
  height: 30px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  pointer-events: none;
  opacity: 0.8;
  z-index: 5;
}
</style>
