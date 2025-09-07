<template>
  <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-3 sm:p-4">
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-4">
      <StatusCard
        title="블록 높이"
        :value="status.height"
        subtitle="블록 높이"
        icon="block"
        color="orange"
      />

      <StatusCard
        title="난이도"
        :value="status.difficulty"
        subtitle="난이도"
        icon="difficulty"
        color="blue"
        prefix="≤ "
      />

      <StatusCard
        title="블록 보상"
        :value="status.reward"
        subtitle="블록 보상"
        icon="reward"
        color="green"
      />

      <StatusCard
        title="내 보상"
        :value="myReward"
        subtitle="내 보상"
        icon="reward"
        color="orange"
      />

      <StatusCard
        title="접속자"
        :value="totalPeerCount"
        subtitle="접속자"
        icon="users"
        color="blue"
        :clickable="true"
        @click="$emit('showPeers')"
      />
    </div>
  </div>
</template>

<script setup>
import StatusCard from '@/components/ui/StatusCard.vue'

defineProps({
  status: {
    type: Object,
    required: true
  },
  myReward: {
    type: Number,
    default: 0
  },
  totalPeerCount: {
    type: Number,
    default: 0
  }
})

defineEmits(['showPeers'])
</script>