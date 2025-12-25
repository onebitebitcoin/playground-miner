<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6">
      <MiningPanel
        v-model:miner="miner"
        v-model:message-draft="miningMessage"
        :mining-state="mining.miningState.value"
        :last-attempt="mining.lastAttempt.value"
        :message="mining.message.value"
        :message-type="mining.messageType.value"
        :status="blockchain.status"
        :my-reward="myReward"
        :total-peer-count="blockchain.totalPeerCount.value"
        @mine="handleMine"
        @show-peers="showPeersModal = true"
      />

      <BlockPanel
        :blocks="annotatedBlocks"
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

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useMining } from '@/composables/useMining'
import { useBlockchain } from '@/composables/useBlockchain'
import MiningPanel from './components/MiningPanel.vue'
import BlockPanel from './components/BlockPanel.vue'
import BlocksModal from './components/BlocksModal.vue'
import PeersModal from './components/PeersModal.vue'
import { useBlockMessageStore } from '@/utils/blockMessages'
import type { Block } from '@/types'

type AnnotatedBlock = Block & { note?: string }

const miner = ref(localStorage.getItem('nickname') || 'guest')
const showBlocksModal = ref(false)
const showPeersModal = ref(false)
const miningMessage = ref('')

const mining = useMining()
const blockchain = useBlockchain(miner)
const { saveMessage, getMessage } = useBlockMessageStore()

const annotatedBlocks = computed<AnnotatedBlock[]>(() =>
  blockchain.blocks.value.map((block) => ({
    ...block,
    note: getMessage(block)
  }))
)

const latestBlocks = computed<AnnotatedBlock[]>(() => annotatedBlocks.value.slice(0, 20))

const myReward = computed(() => {
  const rewards = new Map<string, number>()
  for (const block of blockchain.blocks.value) {
    const key = block.miner || 'guest'
    rewards.set(key, (rewards.get(key) || 0) + (block.reward || 0))
  }
  return rewards.get(miner.value) || 0
})

async function handleMine() {
  const plannedMessage = miningMessage.value
  const result = await mining.tryMine(miner.value, blockchain.status.difficulty)
  if (result?.block) {
    if (plannedMessage.trim()) {
      saveMessage(result.block, plannedMessage)
      miningMessage.value = ''
    }
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
