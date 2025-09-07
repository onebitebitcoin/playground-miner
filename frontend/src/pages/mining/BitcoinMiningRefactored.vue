<template>
  <div class="space-y-6">
    <!-- Status Bar -->
    <StatusBar
      :status="blockchain.status"
      :my-reward="myReward"
      :total-peer-count="blockchain.totalPeerCount"
      @show-peers="showPeersModal = true"
    />

    <!-- Main Content Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6">
      <!-- Mining Interface -->
      <MiningPanel
        v-model:miner="miner"
        :mining-state="mining.miningState"
        :last-attempt="mining.lastAttempt"
        :message="mining.message"
        :message-type="mining.messageType"
        @mine="handleMine"
      />

      <!-- Block Chain Display -->
      <BlockPanel
        :blocks="blockchain.blocks"
        @show-blocks="showBlocksModal = true"
      />
    </div>

    <!-- Modals -->
    <BlocksModal
      v-if="showBlocksModal"
      :blocks="blockchain.blocks.slice(0, 20)"
      :broadcast-msg="blockchain.broadcastMsg"
      @close="showBlocksModal = false"
    />

    <PeersModal
      v-if="showPeersModal"
      :peers="blockchain.peers"
      :current-miner="miner"
      @close="showPeersModal = false"
    />

    <!-- Notifications -->
    <NotificationOverlay :notifications="blockchain.notifications" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useMining } from '@/composables/useMining'
import { useBlockchain } from '@/composables/useBlockchain'

// Components
import StatusBar from './components/StatusBar.vue'
import MiningPanel from './components/MiningPanel.vue'
import BlockPanel from './components/BlockPanel.vue'
import BlocksModal from './components/BlocksModal.vue'
import PeersModal from './components/PeersModal.vue'
import NotificationOverlay from './components/NotificationOverlay.vue'

// State
const miner = ref('guest')
const showBlocksModal = ref(false)
const showPeersModal = ref(false)

// Composables
const mining = useMining()
const blockchain = useBlockchain()

// Load saved nickname
const savedNick = localStorage.getItem('nickname') || ''
if (savedNick) {
  miner.value = savedNick
}

// Computed
const myReward = computed(() => {
  const rewardByMiner = new Map()
  
  for (const block of blockchain.blocks.value) {
    const key = block.miner || 'guest'
    rewardByMiner.set(key, (rewardByMiner.get(key) || 0) + (block.reward || 0))
  }
  
  return rewardByMiner.get(miner.value) || 0
})

// Methods
async function handleMine() {
  const result = await mining.tryMine(miner.value, blockchain.status.difficulty)
  
  if (result?.block) {
    // Optimistic update - add block immediately
    blockchain.addOrUpdateBlock(result.block)
    blockchain.applyStatus(result.status)
  }
}

// Lifecycle
onMounted(async () => {
  await blockchain.initialize()
})

onUnmounted(() => {
  blockchain.cleanup()
  mining.resetMiningState()
})
</script>

<style scoped>
/* Component-specific styles if needed */
</style>