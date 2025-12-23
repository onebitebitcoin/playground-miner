<template>
  <div class="space-y-4">
    <div
      v-if="quickCompareGroups.length || quickCompareGroupsLoading"
      class="flex flex-wrap gap-3 items-center pt-4 border-t border-slate-700/50"
    >
      <span class="text-slate-400 text-sm mr-2">빠른 비교:</span>
      <div class="flex flex-wrap gap-2">
        <template v-if="quickCompareGroups.length">
          <button
            v-for="group in quickCompareGroups"
            :key="group.key"
            class="px-3 py-1 rounded-full text-xs border transition flex items-center gap-1"
            :class="selectedQuickCompareGroup === group.key ? 'bg-transparent text-[#ffd400] border-[#ffd400]' : 'bg-slate-800 text-slate-200 border-slate-700 hover:border-slate-500'"
            :disabled="quickCompareLoadingKey === group.key"
            @click="$emit('applyQuickCompare', group.key)"
          >
            <span>{{ group.label }}</span>
            <svg
              v-if="quickCompareLoadingKey === group.key"
              class="w-3 h-3 animate-spin text-current"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke-width="4"></circle>
              <path class="opacity-75" stroke-width="4" d="M4 12a8 8 0 018-8"></path>
            </svg>
          </button>
        </template>
        <span
          v-else
          class="text-xs text-slate-400 flex items-center gap-1"
        >
          <svg class="w-3 h-3 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke-width="4"></circle>
            <path class="opacity-75" stroke-width="4" d="M4 12a8 8 0 018-8"></path>
          </svg>
          그룹을 불러오는 중...
        </span>
      </div>
      <button
        class="px-3 py-1 rounded-full text-xs border border-slate-700 text-slate-300 hover:border-slate-500 transition disabled:opacity-50"
        :disabled="customAssetResolving || loading || !customAssets.length"
        @click="$emit('clearAll')"
      >
        모두 제거
      </button>
    </div>
    <p v-else class="text-xs text-slate-500 pt-4 border-t border-slate-700/50">
      등록된 빠른 비교 그룹이 없습니다.
    </p>

    <!-- Custom Assets Input -->
    <div class="flex flex-wrap gap-2 items-center">
      <span class="text-slate-400 text-sm mr-2">비교 종목:</span>
      <div 
        v-for="(asset, index) in customAssets" 
        :key="`${asset.label}-${asset.ticker || index}`" 
        class="bg-slate-800 text-slate-200 px-3 py-1 rounded-full text-sm flex items-center gap-2 border border-slate-700 animate-fade-in"
      >
        {{ asset.display || asset.label }}
        <button @click="$emit('removeAsset', index)" class="text-slate-500 hover:text-slate-300">×</button>
      </div>
      
      <div class="relative group">
        <input 
          :value="newAssetInput"
          @input="$emit('update:newAssetInput', $event.target.value)"
          @keydown.enter.prevent="$emit('addAsset')"
          type="text" 
          placeholder="종목명 (Enter)"
          :disabled="customAssetResolving || loading"
          class="bg-slate-800/50 text-white placeholder-slate-500 border border-slate-700 rounded-full px-4 py-1 text-sm focus:outline-none focus:border-[#ffd400] w-32 focus:w-48 transition-all disabled:opacity-50"
        />
        <button 
          @click="$emit('addAsset')" 
          :disabled="customAssetResolving || loading"
          class="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-[#ffd400] transition-colors disabled:opacity-40"
        >
          <span v-if="!customAssetResolving">+</span>
          <svg v-else class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke-width="4"></circle>
            <path class="opacity-75" stroke-width="4" d="M4 12a8 8 0 018-8"></path>
          </svg>
        </button>
      </div>
    </div>
    <p v-if="customAssetError" class="text-xs text-rose-400">{{ customAssetError }}</p>
  </div>
</template>

<script setup>
const props = defineProps({
  quickCompareGroups: Array,
  quickCompareGroupsLoading: Boolean,
  selectedQuickCompareGroup: String,
  quickCompareLoadingKey: String,
  customAssets: Array,
  customAssetResolving: Boolean,
  loading: Boolean,
  newAssetInput: String,
  customAssetError: String
})

defineEmits(['applyQuickCompare', 'clearAll', 'removeAsset', 'addAsset', 'update:newAssetInput'])
</script>
