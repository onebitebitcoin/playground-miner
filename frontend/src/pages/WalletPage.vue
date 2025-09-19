<template>
  <div class="max-w-4xl mx-auto">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900 mb-2">비트코인 지갑</h1>
      <p class="text-gray-600">니모닉을 관리하고 새로운 지갑을 생성하세요</p>
    </div>

    <!-- Main Content -->
    <div class="grid md:grid-cols-2 gap-6">
      <!-- Step 1: Request Existing Mnemonic -->
      <div class="bg-white border border-gray-200 rounded-lg p-6">
        <h2 class="text-xl font-semibold text-gray-900 mb-4">1단계: 기존 니모닉 요청</h2>
        <p class="text-gray-600 mb-4">서버에 저장된 니모닉을 할당받습니다</p>

        <button @click="requestExistingMnemonic"
                :disabled="loading"
                class="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
          {{ loading ? '요청 중...' : '기존 니모닉 요청하기' }}
        </button>

        <div v-if="assignedMnemonic" class="mt-4 p-3 bg-green-50 border border-green-200 rounded">
          <p class="text-sm text-green-800 mb-2">니모닉이 할당되었습니다:</p>
          <div class="font-mono text-sm bg-white p-2 rounded border break-all">
            {{ assignedMnemonic }}
          </div>
          <div class="mt-2 flex gap-2">
            <button @click="showQRCode(assignedMnemonic)"
                    class="text-sm px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700">
              QR 코드 보기
            </button>
            <button @click="copyToClipboard(assignedMnemonic)"
                    class="text-sm px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700">
              복사
            </button>
          </div>
        </div>
      </div>

      <!-- Step 2: Generate New Mnemonic -->
      <div class="bg-white border border-gray-200 rounded-lg p-6">
        <h2 class="text-xl font-semibold text-gray-900 mb-4">2단계: 새 니모닉 생성</h2>
        <p class="text-gray-600 mb-4">새로운 니모닉을 자동 생성하거나 수동으로 입력합니다</p>

        <div class="space-y-4">
          <!-- Mode Selection -->
          <div class="flex gap-2">
            <button @click="switchGenerationMode('auto')"
                    :class="generationMode === 'auto' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'"
                    class="flex-1 px-3 py-2 rounded text-sm">
              자동 생성
            </button>
            <button @click="switchGenerationMode('manual')"
                    :class="generationMode === 'manual' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'"
                    class="flex-1 px-3 py-2 rounded text-sm">
              수동 입력
            </button>
          </div>

          <!-- Auto Generation -->
          <div v-if="generationMode === 'auto'">
            <button @click="generateNewMnemonic"
                    :disabled="loading"
                    class="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50">
              {{ loading ? '생성 중...' : '자동 생성하기' }}
            </button>
          </div>

          <!-- Manual Input -->
          <div v-if="generationMode === 'manual'">
            <div class="space-y-4">
              <!-- Individual word inputs -->
              <div class="grid grid-cols-3 gap-2">
                <div v-for="i in 12" :key="i" class="relative">
                  <label :for="`word-${i}`" class="block text-xs font-medium text-gray-500 mb-1">
                    {{ i }}
                  </label>
                  <input
                    :id="`word-${i}`"
                    v-model="mnemonicWords[i-1]"
                    @input="updateManualMnemonic"
                    @paste="handlePaste($event, i-1)"
                    type="text"
                    :placeholder="`단어 ${i}`"
                    class="w-full px-2 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    :class="{ 'border-red-300': mnemonicError }"
                  />
                </div>
              </div>

              <!-- Alternative textarea input -->
              <div class="border-t pt-4">
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  또는 한번에 입력:
                </label>
                <textarea v-model="manualMnemonicText"
                          @input="updateFromTextarea"
                          placeholder="12개의 영어 단어를 공백으로 구분하여 입력하세요"
                          class="w-full h-16 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                          :class="{ 'border-red-300': mnemonicError }"></textarea>
              </div>

              <div v-if="mnemonicError" class="text-sm text-red-600">{{ mnemonicError }}</div>

              <button @click="saveManualMnemonic"
                      :disabled="loading || !isValidMnemonicInput"
                      class="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50">
                {{ loading ? '저장 중...' : '니모닉 저장하기' }}
              </button>
            </div>
          </div>

          <!-- Generated/Saved Mnemonic Display -->
          <div v-if="newMnemonic" class="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
            <p class="text-sm text-blue-800 mb-2">새 니모닉이 생성되었습니다:</p>
            <div class="font-mono text-sm bg-white p-2 rounded border break-all">
              {{ newMnemonic }}
            </div>
            <div class="mt-2 flex gap-2">
              <button @click="showQRCode(newMnemonic)"
                      class="text-sm px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">
                QR 코드 보기
              </button>
              <button @click="copyToClipboard(newMnemonic)"
                      class="text-sm px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700">
                복사
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- QR Code Modal -->
    <div v-if="showQR" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl shadow-lg max-w-md w-full p-6">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-semibold">니모닉 QR 코드</h3>
          <button @click="showQR = false" class="text-gray-500 hover:text-gray-700">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="flex justify-center mb-4">
          <div ref="qrCodeContainer" class="p-4 bg-white border-2 border-gray-200 rounded-lg"></div>
        </div>
        <div class="text-center">
          <div class="font-mono text-xs bg-gray-50 p-2 rounded border break-all">
            {{ currentMnemonic }}
          </div>
        </div>
      </div>
    </div>

    <!-- Success Message -->
    <div v-if="successMessage" class="fixed bottom-4 right-4 bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg">
      {{ successMessage }}
    </div>

    <!-- Error Message -->
    <div v-if="errorMessage" class="fixed bottom-4 right-4 bg-red-600 text-white px-4 py-2 rounded-lg shadow-lg">
      {{ errorMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import QRCode from 'qrcode'
import {
  apiRequestMnemonic,
  apiGenerateMnemonic,
  apiSaveMnemonic
} from '../api'

// State
const loading = ref(false)
const assignedMnemonic = ref('')
const newMnemonic = ref('')
const generationMode = ref('auto')
const manualMnemonic = ref('')
const mnemonicWords = ref(Array(12).fill(''))
const manualMnemonicText = ref('')
const mnemonicError = ref('')
const showQR = ref(false)
const currentMnemonic = ref('')
const qrCodeContainer = ref(null)
const successMessage = ref('')
const errorMessage = ref('')

// Computed for valid mnemonic input
const isValidMnemonicInput = computed(() => {
  const words = mnemonicWords.value.filter(w => w.trim().length > 0)
  return words.length === 12 || (manualMnemonicText.value.trim().split(/\s+/).length === 12)
})

// Utility functions
const getCurrentUsername = () => {
  return localStorage.getItem('nickname') || 'anonymous'
}

// Mnemonic validation
const validateMnemonic = (mnemonic) => {
  const words = mnemonic.trim().split(/\s+/)
  if (words.length !== 12) {
    return '니모닉은 정확히 12개의 단어로 구성되어야 합니다'
  }

  for (const word of words) {
    if (!/^[a-z]+$/.test(word)) {
      return '모든 단어는 영어 소문자여야 합니다'
    }
  }

  return null
}

// Generation mode switching
const switchGenerationMode = (mode) => {
  generationMode.value = mode
  mnemonicError.value = ''
}

// Manual mnemonic input handling
const updateManualMnemonic = () => {
  const words = mnemonicWords.value.filter(w => w.trim().length > 0)
  manualMnemonic.value = words.join(' ')
  manualMnemonicText.value = mnemonicWords.value.join(' ').trim()
}

const updateFromTextarea = () => {
  const words = manualMnemonicText.value.trim().split(/\s+/).filter(w => w.length > 0)

  for (let i = 0; i < 12; i++) {
    mnemonicWords.value[i] = words[i] || ''
  }

  manualMnemonic.value = words.slice(0, 12).join(' ')
}

const handlePaste = (event, startIndex) => {
  event.preventDefault()
  const pastedText = (event.clipboardData || window.clipboardData).getData('text')
  const words = pastedText.trim().split(/\s+/).filter(w => w.length > 0)

  for (let i = 0; i < 12; i++) {
    mnemonicWords.value[i] = words[i] || ''
  }

  updateManualMnemonic()
}

// API functions
const requestExistingMnemonic = async () => {
  loading.value = true
  try {
    const username = getCurrentUsername()
    const response = await apiRequestMnemonic(username)

    if (response.ok && response.mnemonic) {
      assignedMnemonic.value = response.mnemonic
      showSuccessMessage('기존 니모닉이 할당되었습니다')
    } else {
      showErrorMessage(response.error || '사용 가능한 니모닉이 없습니다')
    }
  } catch (error) {
    showErrorMessage('네트워크 오류가 발생했습니다')
  } finally {
    loading.value = false
  }
}

const generateNewMnemonic = async () => {
  loading.value = true
  try {
    const response = await apiGenerateMnemonic()

    if (response.ok && response.mnemonic) {
      newMnemonic.value = response.mnemonic
      showSuccessMessage('새 니모닉이 생성되었습니다')
    } else {
      showErrorMessage('니모닉 생성에 실패했습니다')
    }
  } catch (error) {
    showErrorMessage('네트워크 오류가 발생했습니다')
  } finally {
    loading.value = false
  }
}

const saveManualMnemonic = async () => {
  mnemonicError.value = ''

  const finalMnemonic = manualMnemonicText.value.trim() || mnemonicWords.value.join(' ').trim()
  const error = validateMnemonic(finalMnemonic)
  if (error) {
    mnemonicError.value = error
    return
  }

  loading.value = true
  try {
    const username = getCurrentUsername()
    const response = await apiSaveMnemonic(username, finalMnemonic)

    if (response.ok) {
      newMnemonic.value = finalMnemonic
      showSuccessMessage('니모닉이 저장되었습니다')

      // Clear inputs
      mnemonicWords.value = Array(12).fill('')
      manualMnemonicText.value = ''
      manualMnemonic.value = ''
    } else {
      mnemonicError.value = response.error || '니모닉 저장에 실패했습니다'
    }
  } catch (error) {
    mnemonicError.value = '네트워크 오류가 발생했습니다'
  } finally {
    loading.value = false
  }
}

// QR Code functionality
const showQRCode = async (mnemonic) => {
  currentMnemonic.value = mnemonic
  showQR.value = true

  await nextTick()

  if (qrCodeContainer.value) {
    qrCodeContainer.value.innerHTML = ''

    try {
      const canvas = await QRCode.toCanvas(mnemonic, {
        width: 200,
        margin: 2,
        color: {
          dark: '#000000',
          light: '#FFFFFF'
        }
      })
      qrCodeContainer.value.appendChild(canvas)
    } catch (error) {
      const placeholder = document.createElement('div')
      placeholder.className = 'text-red-500 text-center p-4'
      placeholder.textContent = 'QR 코드 생성 실패'
      qrCodeContainer.value.appendChild(placeholder)
    }
  }
}

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    showSuccessMessage('클립보드에 복사되었습니다')
  } catch (error) {
    showErrorMessage('복사에 실패했습니다')
  }
}

// Utility functions
const showSuccessMessage = (message) => {
  successMessage.value = message
  setTimeout(() => {
    successMessage.value = ''
  }, 3000)
}

const showErrorMessage = (message) => {
  errorMessage.value = message
  setTimeout(() => {
    errorMessage.value = ''
  }, 3000)
}
</script>