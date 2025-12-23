<template>
  <div class="space-y-6">
    <StatusBar
      :status="blockchain.status"
      :my-reward="myReward"
      :total-peer-count="blockchain.totalPeerCount"
      @show-peers="showPeersModal = true"
    />

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6">
      <MiningPanel
        v-model:miner="miner"
        :mining-state="mining.miningState"
        :last-attempt="mining.lastAttempt"
        :message="mining.message"
        :message-type="mining.messageType"
        @mine="handleMine"
      />

      <BlockPanel
        :blocks="blockchain.blocks.value"
        @show-blocks="showBlocksModal = true"
      />
    </div>

    <BlocksModal
      v-if="showBlocksModal"
      :blocks="latestBlocks"
      :broadcast-msg="blockchain.broadcastMsg"
      @close="showBlocksModal = false"
    />

    <PeersModal
      v-if="showPeersModal"
      :peers="blockchain.peers"
      :current-miner="miner"
      @close="showPeersModal = false"
    />

    <NotificationOverlay
      :notifications="blockchain.notifications"
      @dismiss="blockchain.dismissNotification"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useMining } from '@/composables/useMining'
import { useBlockchain } from '@/composables/useBlockchain'
import StatusBar from './components/StatusBar.vue'
import MiningPanel from './components/MiningPanel.vue'
import BlockPanel from './components/BlockPanel.vue'
import BlocksModal from './components/BlocksModal.vue'
import PeersModal from './components/PeersModal.vue'
import NotificationOverlay from './components/NotificationOverlay.vue'
import type { Block } from '@/types'

const miner = ref(localStorage.getItem('nickname') || 'guest')
const showBlocksModal = ref(false)
const showPeersModal = ref(false)

const mining = useMining()
const blockchain = useBlockchain(miner)

const latestBlocks = computed<Block[]>(() => blockchain.blocks.value.slice(0, 20))

const myReward = computed(() => {
  const rewards = new Map<string, number>()
  for (const block of blockchain.blocks.value) {
    const key = block.miner || 'guest'
    rewards.set(key, (rewards.get(key) || 0) + (block.reward || 0))
  }
  return rewards.get(miner.value) || 0
})

async function handleMine() {
  const result = await mining.tryMine(miner.value, blockchain.status.difficulty)
  if (result?.block) {
    blockchain.addOrUpdateBlock(result.block)
    blockchain.applyStatus(result.status)
    try {
      window.dispatchEvent(new CustomEvent('lesson:mined', { detail: { block: result.block, status: result.status } }))
    } catch (error) {
      console.warn('Failed to dispatch lesson:mined event', error)
    }
  }
}

onMounted(() => {
  blockchain.initialize()
})

onUnmounted(() => {
  blockchain.cleanup()
  mining.resetMiningState()
})

watch(miner, (value) => {
  if (value) {
    localStorage.setItem('nickname', value)
  }
})
</script>
