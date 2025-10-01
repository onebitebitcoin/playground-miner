import { ref } from 'vue'

export function useNotification() {
  const successMessage = ref('')
  const errorMessage = ref('')

  const showSuccess = (message) => {
    successMessage.value = message
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  }

  const showError = (message) => {
    errorMessage.value = message
    setTimeout(() => {
      errorMessage.value = ''
    }, 3000)
  }

  const clearMessages = () => {
    successMessage.value = ''
    errorMessage.value = ''
  }

  return {
    successMessage,
    errorMessage,
    showSuccess,
    showError,
    clearMessages
  }
}
