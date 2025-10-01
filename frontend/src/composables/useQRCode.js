import { nextTick } from 'vue'
import QRCode from 'qrcode'

export async function generateQRCode(container, text, options = {}) {
  if (!container || !text) return false

  await nextTick()
  container.innerHTML = ''

  const defaultOptions = {
    width: 200,
    margin: 2,
    color: {
      dark: '#000000',
      light: '#FFFFFF'
    },
    ...options
  }

  try {
    const canvas = await QRCode.toCanvas(text, defaultOptions)
    container.appendChild(canvas)
    return true
  } catch (error) {
    const placeholder = document.createElement('div')
    placeholder.textContent = 'QR 코드 생성 실패'
    placeholder.className = 'text-red-500 text-center p-4'
    container.appendChild(placeholder)
    return false
  }
}
