import { ref, nextTick } from 'vue'
import type { NotificationState } from '@/types'

export function useNotifications() {
  const notifications = ref<NotificationState[]>([])
  const notificationId = ref(0)

  function addNotification(user: string, duration = 5000) {
    const id = ++notificationId.value
    const notification: NotificationState = {
      id,
      user: user || '알 수 없는 사용자',
      timestamp: Date.now()
    }
    
    notifications.value.push(notification)
    
    // Auto remove after duration
    if (duration > 0) {
      setTimeout(() => {
        removeNotification(id)
      }, duration)
    }
    
    return id
  }

  function removeNotification(id: number) {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index > -1) {
      notifications.value.splice(index, 1)
    }
  }

  function clearAllNotifications() {
    notifications.value = []
  }

  // User join notification helper
  function showUserJoinNotification(username: string) {
    return addNotification(username, 5000)
  }

  return {
    notifications: readonly(notifications),
    addNotification,
    removeNotification,
    clearAllNotifications,
    showUserJoinNotification
  }
}