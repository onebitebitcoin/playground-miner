<template>
  <div class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-2 sm:p-4">
    <div class="bg-white rounded-xl shadow-2xl max-w-md w-full max-h-[90vh] flex flex-col">
      <div class="flex items-center justify-between p-4 border-b border-slate-200">
        <div class="flex items-center gap-2">
          <div class="w-9 h-9 bg-green-100 rounded-full flex items-center justify-center">
            <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
            </svg>
          </div>
          <div>
            <h3 class="text-lg font-semibold text-slate-900">현재 접속자</h3>
            <p class="text-xs text-slate-500">실시간으로 접속 중인 사용자 목록</p>
          </div>
        </div>
        <button @click="$emit('close')" class="p-2 rounded-full hover:bg-slate-100 transition-colors">
          <svg class="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="flex-1 overflow-y-auto p-4 space-y-3">
        <div v-if="!peers.length" class="text-center text-slate-500 text-sm py-10">
          현재 접속자가 없습니다.
        </div>
        <div
          v-for="(peer, index) in peers"
          :key="peer || index"
          class="flex items-center gap-3 p-3 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors"
        >
          <div class="w-3 h-3 rounded-full bg-green-500 animate-pulse flex-shrink-0"></div>
          <div class="flex-1 min-w-0">
            <div class="font-medium text-slate-800 truncate">
              {{ peer || 'Unknown User' }}
              <span v-if="peer && peer === currentMiner" class="text-xs text-green-600 ml-2 font-normal">(나)</span>
            </div>
            <div class="text-xs text-slate-500">온라인</div>
          </div>
          <div v-if="peer && peer === currentMiner" class="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
            <svg class="w-3 h-3 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  peers: string[]
  currentMiner: string
}>()

defineEmits<{
  (e: 'close'): void
}>()
</script>
