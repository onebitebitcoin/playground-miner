import { ref, reactive, computed } from 'vue'
import { apiService } from '@/services/ApiService'
import { useWebSocket } from './useWebSocket'
import { usePolling } from './usePolling'
import { useNotifications } from './useNotifications'
import type { BlockchainStatus, Block, WebSocketMessage } from '@/types'

export function useBlockchain(nickname?: string) {
  // State
  const status = reactive<BlockchainStatus>({ 
    height: 0, 
    difficulty: 10000, 
    reward: 100 
  })
  
  const blocks = ref<Block[]>([])
  const peers = ref<string[]>([])
  const broadcastMsg = ref('')
  const highlighted = new Set<number>()
  const previousPeerCount = ref(0)

  // Composables
  const { connect, disconnect, isConnected } = useWebSocket()
  const { startPolling, stopPolling } = usePolling()
  const { notifications, showUserJoinNotification } = useNotifications()

  // Computed
  const totalPeerCount = computed(() => {
    const peerCount = peers.value.length
    const includesSelf = nickname && peers.value.includes(nickname)
    return includesSelf ? peerCount : peerCount + 1
  })

  // Block management
  function setBlocksSortedUnique(blockList: Block[]) {
    const map = new Map()
    for (const block of blockList) {
      if (!map.has(block.height)) {
        map.set(block.height, block)
      }
    }
    // Sort by height descending (latest first)
    blocks.value = Array.from(map.values()).sort((a, b) => b.height - a.height)
  }

  function addOrUpdateBlock(block: Block) {
    setBlocksSortedUnique([block, ...blocks.value])
    
    // Highlight animation
    try {
      highlighted.add(block.height)
      setTimeout(() => highlighted.delete(block.height), 1200)
    } catch (error) {
      console.warn('Failed to add highlight:', error)
    }
  }

  // Status management
  function applyStatus(newStatus: Partial<BlockchainStatus>) {
    // Ensure block height is monotonically increasing
    if (newStatus.height !== undefined) {
      status.height = Math.max(status.height, newStatus.height)
    }
    if (newStatus.difficulty !== undefined) {
      status.difficulty = newStatus.difficulty
    }
    if (newStatus.reward !== undefined) {
      status.reward = newStatus.reward
    }
  }

  // WebSocket message handler
  function handleMessage(payload: WebSocketMessage) {
    console.log('WebSocket message received:', payload)
    
    switch (payload.type) {
      case 'snapshot':
        if (payload.blocks) setBlocksSortedUnique(payload.blocks)
        if (payload.status) applyStatus(payload.status)
        if (payload.peers) peers.value = payload.peers
        stopPolling() // Stop polling when real-time connection works
        break
        
      case 'block':
        if (payload.block) {
          addOrUpdateBlock(payload.block)
          status.height = Math.max(status.height, payload.block.height)
        }
        if (payload.status) applyStatus(payload.status)
        
        // Show broadcast message
        if (payload.notice) {
          broadcastMsg.value = payload.notice
          setTimeout(() => { broadcastMsg.value = '' }, 3500)
        }
        break
        
      case 'status':
        if (payload.status) applyStatus(payload.status)
        break
        
      case 'peers':
        if (Array.isArray(payload.peers)) {
          const newPeerCount = payload.peers.length
          const oldPeerCount = previousPeerCount.value
          
          // Show notification for new users
          if (newPeerCount > oldPeerCount && oldPeerCount > 0) {
            const newUsers = payload.peers.filter(p => !peers.value.includes(p))
            if (newUsers.length > 0) {
              showUserJoinNotification(newUsers[0])
            }
          }
          
          peers.value = payload.peers
          previousPeerCount.value = newPeerCount
        }
        break
    }
  }

  // Polling fallback
  async function pollForUpdates() {
    try {
      const [statusResponse, blocksResponse] = await Promise.all([
        apiService.getStatus(),
        apiService.getBlocks()
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

  // Initialize connection
  async function initialize() {
    try {
      // Load initial data
      const [statusResponse, blocksResponse] = await Promise.all([
        apiService.getStatus(),
        apiService.getBlocks()
      ])
      
      applyStatus(statusResponse)
      setBlocksSortedUnique(blocksResponse.blocks)

      // Try to establish real-time connection
      try {
        connect(handleMessage, nickname)
      } catch (error) {
        console.warn('WebSocket connection failed, using polling:', error)
        startPolling(pollForUpdates, 2000)
      }
    } catch (error) {
      console.error('Failed to initialize blockchain data:', error)
      // Still try polling as fallback
      startPolling(pollForUpdates, 2000)
    }
  }

  // Cleanup
  function cleanup() {
    disconnect()
    stopPolling()
    highlighted.clear()
  }

  return {
    // State
    status: readonly(status),
    blocks: readonly(blocks),
    peers: readonly(peers),
    broadcastMsg: readonly(broadcastMsg),
    notifications,
    
    // Computed
    totalPeerCount,
    isConnected,
    
    // Methods  
    initialize,
    cleanup,
    addOrUpdateBlock,
    applyStatus
  }
}