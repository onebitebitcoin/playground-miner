import { ref, onUnmounted } from 'vue'

export function usePolling() {
  const isPolling = ref(false)
  let pollTimer: number | null = null

  function startPolling(callback: () => void | Promise<void>, interval = 2000) {
    if (pollTimer) return false // Already polling
    
    isPolling.value = true
    pollTimer = setInterval(async () => {
      try {
        await callback()
      } catch (error) {
        console.warn('Polling callback failed:', error)
      }
    }, interval)
    
    return true
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
      isPolling.value = false
      return true
    }
    return false
  }

  function restartPolling(callback: () => void | Promise<void>, interval = 2000) {
    stopPolling()
    return startPolling(callback, interval)
  }

  // Auto cleanup on unmount
  onUnmounted(() => {
    stopPolling()
  })

  return {
    isPolling: readonly(isPolling),
    startPolling,
    stopPolling,
    restartPolling
  }
}