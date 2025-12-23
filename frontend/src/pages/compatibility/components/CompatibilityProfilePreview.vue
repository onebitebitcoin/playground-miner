<template>
  <div v-if="user.birthdate || target.birthdate" class="flex flex-col gap-4">
    <div class="flex items-center justify-center gap-4">
      <!-- User Card -->
      <CompatibilityCard
        v-if="user.birthdate"
        :label="user.name || '사용자'"
        :image-url="user.imageUrl"
        :birthdate="user.birthdate"
        :birthtime="user.birthtime"
        :gender="user.gender"
        :show-time="!user.timeUnknown"
        active
      />

      <!-- Plus Icon -->
      <div v-if="user.birthdate && target.birthdate && targetEnabled" class="plus-icon">
        <svg class="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 4v16m8-8H4" />
        </svg>
      </div>

      <!-- Target Card -->
      <div v-if="target.birthdate && targetEnabled" class="relative group">
        <CompatibilityCard
          :label="target.name || '비교 대상'"
          :image-url="target.imageUrl"
          :birthdate="target.birthdate"
          :birthtime="target.birthtime"
          :gender="target.gender"
          :show-time="!target.timeUnknown"
          placeholder-icon="👥"
          active
        />
        <button
          type="button"
          class="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-rose-500 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow-lg z-30"
          @click="$emit('removeTarget')"
          title="비교 대상 제거"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import CompatibilityCard from './CompatibilityCard.vue'

const props = defineProps({
  user: Object,
  target: Object,
  targetEnabled: Boolean
})

defineEmits(['removeTarget'])
</script>

<style scoped>
.plus-icon {
  display: flex;
  align-items: center;
  justify-center: center;
  animation: bounce 2s infinite ease-in-out;
}

@keyframes bounce {
  0%, 100% { transform: scale(1); opacity: 0.5; }
  50% { transform: scale(1.2); opacity: 1; }
}
</style>
