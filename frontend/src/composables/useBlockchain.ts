import { ref, reactive, computed, readonly, isRef, watch } from 'vue'
import type { Ref } from 'vue'
import { apiService } from '@/services/ApiService'
import { useWebSocket } from './useWebSocket'
import { usePolling } from './usePolling'
import type { BlockchainStatus, Block, WebSocketMessage } from '@/types'

export function useBlockchain(nickname?: Ref<string> | string) {
  const status = reactive<BlockchainStatus>({
    height: 0,
    difficulty: 10000,
    reward: 100,
  })
  const blocks = ref<Block[]>([])
  const peers = ref<string[]>([])
  const broadcastMsg = ref('')
  const isActive = ref(false)
  const nicknameRef = isRef(nickname) ? nickname : ref(nickname || '')

  const { connect, disconnect, isConnected } = useWebSocket()
  const { startPolling, stopPolling } = usePolling()
  const totalPeerCount = computed(() => {
    const peerCount = peers.value.length
    const currentNickname = nicknameRef.value || ''
    const includesSelf = currentNickname && peers.value.includes(currentNickname)
    return includesSelf ? peerCount : peerCount + 1
  })

  function setBlocksSortedUnique(blockList: Block[]) {
    const map = new Map<number, Block>()
    for (const block of blockList) {
      if (!map.has(block.height)) {
        map.set(block.height, block)
      }
    }
    blocks.value = Array.from(map.values()).sort((a, b) => b.height - a.height)
  }

  function addOrUpdateBlock(block: Block) {
    setBlocksSortedUnique([block, ...blocks.value])
  }

  function applyStatus(newStatus: Partial<BlockchainStatus>) {
    if (typeof newStatus.height === 'number') {
      status.height = Math.max(status.height, newStatus.height)
    }
    if (typeof newStatus.difficulty === 'number') {
      status.difficulty = newStatus.difficulty
    }
    if (typeof newStatus.reward === 'number') {
      status.reward = newStatus.reward
    }
  }

  function handleMessage(payload: WebSocketMessage) {
    switch (payload.type) {
      case 'snapshot': {
        if (payload.blocks) setBlocksSortedUnique(payload.blocks)
        if (payload.status) applyStatus(payload.status)
        if (payload.peers) peers.value = payload.peers
        if (payload.me?.nickname) {
          nicknameRef.value = payload.me.nickname
          localStorage.setItem('nickname', payload.me.nickname)
        }
        stopPolling()
        break
      }

      case 'block': {
        if (payload.block) {
          addOrUpdateBlock(payload.block)
          status.height = Math.max(status.height, payload.block.height)
        }
        if (payload.status) applyStatus(payload.status)
        if (payload.notice) {
          broadcastMsg.value = payload.notice
          setTimeout(() => {
            broadcastMsg.value = ''
          }, 3500)
        }
        break
      }

      case 'status': {
        if (payload.status) applyStatus(payload.status)
        break
      }

      case 'peers': {
        if (Array.isArray(payload.peers)) {
          peers.value = payload.peers
        }
        break
      }
    }
  }

  async function pollForUpdates() {
    try {
      const [statusResponse, blocksResponse] = await Promise.all([
        apiService.getStatus(),
        apiService.getBlocks(),
      ])
      const prevHeight = status.height
      applyStatus(statusResponse)
      if (status.height !== prevHeight) {
        setBlocksSortedUnique(blocksResponse.blocks)
      }
    } catch (error) {
      console.warn('Polling failed:', error)
    }
  }

  watch(isConnected, (connected) => {
    if (!isActive.value) return
    if (connected) {
      stopPolling()
    } else {
      startPolling(pollForUpdates, 2000)
    }
  })

  async function initialize() {
    if (isActive.value) return
    isActive.value = true
    startPolling(pollForUpdates, 2000)

    try {
      const [statusResponse, blocksResponse] = await Promise.all([
        apiService.getStatus(),
        apiService.getBlocks(),
      ])
      applyStatus(statusResponse)
      setBlocksSortedUnique(blocksResponse.blocks)
    } catch (error) {
      console.error('Failed to initialize blockchain data:', error)
    }

    try {
      const nicknameValue = nicknameRef.value || undefined
      connect(handleMessage, nicknameValue)
    } catch (error) {
      console.warn('WebSocket connection failed, continuing with polling:', error)
    }
  }

  function cleanup() {
    isActive.value = false
    disconnect()
    stopPolling()
    peers.value = []
    broadcastMsg.value = ''
  }

  return {
    status: readonly(status),
    blocks: readonly(blocks),
    peers: readonly(peers),
    broadcastMsg: readonly(broadcastMsg),
    totalPeerCount,
    isConnected,
    initialize,
    cleanup,
    addOrUpdateBlock,
    applyStatus,
  }
}
