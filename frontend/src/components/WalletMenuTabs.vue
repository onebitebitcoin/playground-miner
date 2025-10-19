<template>
  <div class="mb-6">
    <div class="inline-flex rounded-lg bg-gray-100 p-1 text-sm">
      <RouterLink
        to="/wallet/kingstone"
        class="px-4 py-2 rounded-md font-medium transition"
        :class="kingstoneClasses"
        title="킹스톤 지갑"
      >
        킹스톤 지갑
      </RouterLink>
      <button
        disabled
        class="px-4 py-2 rounded-md font-medium text-gray-400 cursor-not-allowed opacity-60"
        title="준비 중"
      >
        크롱스 지갑
      </button>
      <button
        disabled
        class="px-4 py-2 rounded-md font-medium text-gray-400 cursor-not-allowed opacity-60"
        title="준비 중"
      >
        시드사이넝 지갑
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  active: {
    type: String,
    default: ''
  }
})

const route = useRoute()
const activeTab = computed(() => {
  if (props.active) return props.active
  const name = route.name || ''
  if (name === 'wallet-kingstone' || name === 'wallet-kingstone-detail') {
    return 'kingstone'
  }
  return 'kingstone'
})

const kingstoneClasses = computed(() => {
  const base = 'text-gray-600 hover:text-gray-900 hover:bg-white'
  const active = 'bg-white text-gray-900 shadow-sm cursor-default'
  return activeTab.value === 'kingstone' ? active : base
})
</script>
