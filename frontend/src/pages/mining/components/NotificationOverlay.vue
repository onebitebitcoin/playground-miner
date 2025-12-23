<template>
  <div class="fixed top-4 right-4 z-50 space-y-2 pointer-events-none">
    <TransitionGroup name="notification" tag="div">
      <div
        v-for="notification in notifications"
        :key="notification.id"
        class="bg-white border border-emerald-200 rounded-lg shadow-lg p-4 max-w-sm pointer-events-auto"
      >
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <svg class="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <div class="font-medium text-slate-800">새 사용자 입장</div>
            <div class="text-sm text-slate-500 truncate">{{ notification.user }}님이 입장했습니다</div>
          </div>
          <button
            class="text-slate-400 hover:text-slate-600 p-1"
            @click="$emit('dismiss', notification.id)"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import type { NotificationState } from '@/types'

defineProps<{
  notifications: NotificationState[]
}>()

defineEmits<{
  (e: 'dismiss', id: number): void
}>()
</script>

<style scoped>
.notification-enter-active,
.notification-leave-active {
  transition: all 0.2s ease;
}
.notification-enter-from,
.notification-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
