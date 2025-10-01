export async function copyToClipboard(text, successCallback, errorCallback) {
  if (!text) {
    errorCallback?.('복사할 내용이 없습니다')
    return false
  }

  try {
    await navigator.clipboard.writeText(text)
    successCallback?.('클립보드에 복사되었습니다')
    return true
  } catch (error) {
    // Fallback for older browsers
    try {
      const textarea = document.createElement('textarea')
      textarea.value = text
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      const success = document.execCommand('copy')
      document.body.removeChild(textarea)

      if (success) {
        successCallback?.('클립보드에 복사되었습니다')
        return true
      } else {
        errorCallback?.('클립보드 복사에 실패했습니다')
        return false
      }
    } catch (fallbackError) {
      errorCallback?.('클립보드 복사에 실패했습니다')
      return false
    }
  }
}
