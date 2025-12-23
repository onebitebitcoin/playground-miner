import { ref, computed, readonly } from 'vue'
import { apiService } from '@/services/ApiService'
import type { MiningState } from '@/types'

export function useMining() {
  // State
  const miningState = ref<MiningState>('idle')
  const lastAttempt = ref<number | null>(null)
  const message = ref('')
  const messageType = ref<'ok' | 'info'>('info')
  
  let stopMining = false

  // Computed
  const isMining = computed(() => miningState.value === 'mining')
  const canMine = computed(() => !isMining.value)

  // Mining logic
  async function tryMine(miner: string, difficulty: number) {
    if (!miner) miner = 'guest'
    
    message.value = '성공할 때까지 자동 재시도 중입니다…'
    messageType.value = 'info'
    miningState.value = 'mining'
    stopMining = false

    const attempt = async (): Promise<{ success: boolean; data?: any }> => {
      const nonce = Math.floor(Math.random() * 100000) + 1
      lastAttempt.value = nonce
      
      if (nonce <= difficulty) {
        try {
          const response = await apiService.submitMining({ miner, nonce })
          
          if (response.ok && response.block) {
            return { success: true, data: response }
          }
        } catch (error) {
          console.warn('Mining attempt failed:', error)
        }
      }
      
      return { success: false }
    }

    try {
      let success = false
      
      while (!success && !stopMining) {
        const result = await attempt()
        
        if (result.success) {
          success = true
          message.value = `축하합니다! 블록 #${result.data.block.height} 채굴에 성공했습니다.`
          messageType.value = 'ok'
          miningState.value = 'success'
          
          return result.data
        }
        
        // Small delay between attempts
        if (!stopMining) {
          await new Promise(resolve => setTimeout(resolve, 60))
        }
      }
    } catch (error) {
      message.value = '네트워크 오류 또는 서버 오류가 발생했습니다.'
      messageType.value = 'info'
      miningState.value = 'fail'
    } finally {
      // Reset state after animation
      setTimeout(() => {
        if (miningState.value !== 'mining') {
          miningState.value = 'idle'
        }
      }, 1200)
    }

    return null
  }

  function stopMiningProcess() {
    stopMining = true
    if (miningState.value === 'mining') {
      miningState.value = 'idle'
    }
  }

  function resetMiningState() {
    stopMining = false
    miningState.value = 'idle'
    message.value = ''
    lastAttempt.value = null
  }

  return {
    // State
    miningState: readonly(miningState),
    lastAttempt: readonly(lastAttempt),
    message: readonly(message),
    messageType: readonly(messageType),
    
    // Computed
    isMining,
    canMine,
    
    // Methods
    tryMine,
    stopMiningProcess,
    resetMiningState
  }
}
