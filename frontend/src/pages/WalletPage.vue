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
          {{ loading ? '요청 중...' : '니모닉 받기' }}
        </button>

      <div v-if="assignedMnemonic" class="mt-4 p-3 bg-green-50 border border-green-200 rounded">
        <p class="text-sm text-green-800 mb-2">니모닉이 할당되었습니다:</p>
        <div class="font-mono text-sm bg-white p-2 rounded border break-all">
          {{ assignedMnemonic }}
        </div>
          <div class="mt-2 flex flex-wrap items-center gap-2">
            <!-- QR icon button -->
            <button @click="showQRCode(assignedMnemonic)"
                    class="p-1.5 rounded text-gray-700 hover:text-gray-900"
                    title="QR 코드 보기">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"></path>
              </svg>
              <span class="sr-only">QR 코드</span>
            </button>
            <!-- Copy icon button -->
            <button @click="copyToClipboard(assignedMnemonic)"
                    class="p-1.5 rounded text-gray-700 hover:text-gray-900"
                    title="복사">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <rect x="9" y="7" width="11" height="13" rx="2" ry="2"></rect>
                <rect x="4" y="4" width="11" height="13" rx="2" ry="2"></rect>
              </svg>
              <span class="sr-only">복사</span>
            </button>
            <!-- Refresh balance icon -->
            <button v-if="assignedMnemonicId" @click="refreshAssignedBalance"
                    :disabled="assignedBalanceLoading"
                    class="p-1.5 rounded text-blue-600 hover:text-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="잔액 새로고침">
              <svg v-if="assignedBalanceLoading" class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span class="sr-only">잔액 새로고침</span>
            </button>
            <div class="text-sm text-gray-700 ml-1">
              <template v-if="assignedBalanceLoading">잔액 조회중...</template>
              <template v-else-if="assignedBalanceSats !== null">
                잔액: <span class="font-semibold">{{ assignedBalanceSats.toLocaleString() }} sats</span>
                <span class="text-gray-500">({{ formatBtc(assignedBalanceSats) }})</span>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 2: Generate New Mnemonic (visible after assignment) -->
      <div v-if="assignedMnemonicId" class="bg-white border border-gray-200 rounded-lg p-6">
        <div class="flex items-center justify-between mb-2">
          <div>
            <h2 class="text-xl font-semibold text-gray-900">2단계: 새 니모닉 생성</h2>
            <p class="text-gray-600">관리자 인터페이스와 동일한 입력 방식</p>
          </div>
          <div class="flex items-center gap-2">
            <!-- Plus: auto-generate and fill 12 words -->
            <button @click="generateAndFillWalletMnemonic" class="p-2 rounded text-gray-700 hover:text-gray-900" title="자동 생성">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v12" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 12h12" />
              </svg>
              <span class="sr-only">자동 생성</span>
            </button>
            <!-- Trash: clear 12 words -->
            <button @click="clearWalletManualMnemonic" class="p-2 rounded text-gray-700 hover:text-gray-900" title="지우기">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m-3 0h14" />
              </svg>
              <span class="sr-only">지우기</span>
            </button>
          </div>
        </div>

        <div class="space-y-4">
          <!-- Manual Input (admin-like) -->
          <div>
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
                    :class="{ 'border-red-300': mnemonicError || (walletMnemonicUnknown && walletMnemonicUnknown.length && walletMnemonicUnknown.includes((mnemonicWords[i-1]||'').trim().toLowerCase())) }"
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
                      placeholder="12/15/18/21/24개의 영어 단어를 공백으로 구분하여 입력하세요"
                      class="w-full h-16 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                      :class="{ 'border-red-300': mnemonicError }"></textarea>
            <div class="mt-2 space-y-2">
              <button @click="checkWalletMnemonic" class="w-full px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900">유효성 검사</button>
              <div v-if="walletMnemonicValidity !== null" :class="walletMnemonicValidity ? 'text-green-700' : 'text-red-600'" class="text-sm">
                {{ walletMnemonicValidity ? '유효한 BIP39 니모닉' : '유효하지 않은 니모닉' }}
                <span v-if="walletMnemonicWordCount"> ({{ walletMnemonicWordCount }}단어)</span>
                <span v-if="!walletMnemonicValidity && walletMnemonicUnknown && walletMnemonicUnknown.length" class="ml-2 text-xs text-red-600">[{{ walletMnemonicUnknown.join(', ') }}]</span>
                <span v-if="!walletMnemonicValidity && (!walletMnemonicUnknown || walletMnemonicUnknown.length === 0) && walletMnemonicErrorCode === 'checksum_failed'" class="ml-2 text-xs text-red-600">(체크섬 불일치)</span>
              </div>
            </div>
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
            <div class="mt-2 flex flex-wrap items-center gap-2">
              <!-- QR icon button -->
              <button @click="showQRCode(newMnemonic)"
                      class="p-1.5 rounded text-gray-700 hover:text-gray-900"
                      title="QR 코드 보기">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"></path>
                </svg>
                <span class="sr-only">QR 코드</span>
              </button>
              <!-- Copy icon button -->
              <button @click="copyToClipboard(newMnemonic)"
                      class="p-1.5 rounded text-gray-700 hover:text-gray-900"
                      title="복사">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <rect x="9" y="7" width="11" height="13" rx="2" ry="2"></rect>
                  <rect x="4" y="4" width="11" height="13" rx="2" ry="2"></rect>
                </svg>
                <span class="sr-only">복사</span>
              </button>
              <!-- Refresh balance icon -->
              <button v-if="savedMnemonicId" @click="refreshSavedBalance"
                      :disabled="savedBalanceLoading"
                      class="p-1.5 rounded text-blue-600 hover:text-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      title="잔액 새로고침">
                <svg v-if="savedBalanceLoading" class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span class="sr-only">잔액 새로고침</span>
              </button>
              <div v-if="savedBalanceSats !== null" class="text-sm text-gray-700 ml-1">
                잔액: <span class="font-semibold">{{ savedBalanceSats.toLocaleString() }} sats</span>
                <span class="text-gray-500">({{ formatBtc(savedBalanceSats) }})</span>
              </div>
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
  apiSaveMnemonic,
  apiGetMnemonicBalance,
  apiGetOnchainBalanceById,
  apiValidateMnemonic
} from '../api'

// State
const loading = ref(false)
const assignedMnemonic = ref('')
const assignedMnemonicId = ref(null)
const assignedBalanceSats = ref(null)
const newMnemonic = ref('')
const savedMnemonicId = ref(null)
const savedBalanceSats = ref(null)
// Admin-like input UI (no tabs)
const manualMnemonic = ref('')
const mnemonicWords = ref(Array(12).fill(''))
const manualMnemonicText = ref('')
const mnemonicError = ref('')
const showQR = ref(false)
const currentMnemonic = ref('')
const qrCodeContainer = ref(null)
const successMessage = ref('')
const errorMessage = ref('')
const walletMnemonicValidity = ref(null)
const walletMnemonicWordCount = ref(0)
const walletMnemonicUnknown = ref([])
const walletMnemonicErrorCode = ref('')

// Balance loading states
const assignedBalanceLoading = ref(false)
const savedBalanceLoading = ref(false)

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

// Removed generation mode/tabs; using single admin-like interface

// Manual mnemonic input handling
const updateManualMnemonic = () => {
  const words = mnemonicWords.value.filter(w => w.trim().length > 0)
  manualMnemonic.value = words.join(' ')
  manualMnemonicText.value = mnemonicWords.value.join(' ').trim()

  // Auto-validate when 12 words are entered
  if (words.length === 12) {
    checkWalletMnemonic()
  } else {
    walletMnemonicValidity.value = null
    walletMnemonicWordCount.value = 0
  }
}

const updateFromTextarea = () => {
  const words = manualMnemonicText.value.trim().split(/\s+/).filter(w => w.length > 0)

  for (let i = 0; i < 12; i++) {
    mnemonicWords.value[i] = words[i] || ''
  }

  manualMnemonic.value = words.slice(0, 12).join(' ')

  // Auto-validate when 12 words are entered
  if (words.length === 12) {
    checkWalletMnemonic()
  } else {
    walletMnemonicValidity.value = null
    walletMnemonicWordCount.value = 0
  }
}

const handlePaste = (event, startIndex) => {
  event.preventDefault()
  const pastedText = (event.clipboardData || window.clipboardData).getData('text')
  const words = pastedText.trim().split(/\s+/).filter(w => w.length > 0)

  // If multiple words are pasted, fill from index 0
  if (words.length > 1) {
    for (let i = 0; i < 12; i++) {
      mnemonicWords.value[i] = words[i] || ''
    }
  } else {
    // If single word is pasted, put it at the current field
    if (words.length === 1) {
      mnemonicWords.value[startIndex] = words[0]
    }
  }

  updateManualMnemonic()
}

// API functions
const requestExistingMnemonic = async () => {
  loading.value = true
  try {
    const response = await apiRequestMnemonic(getCurrentUsername())

    if (response.success && response.mnemonic) {
      assignedMnemonic.value = response.mnemonic
      assignedMnemonicId.value = response.id || null
      // Fetch only stored DB balance initially (no on-chain scan)
      if (assignedMnemonicId.value) await fetchAssignedBalance()
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

    if (response.success && response.mnemonic) {
      newMnemonic.value = response.mnemonic
      showSuccessMessage('새 니모닉이 생성되었습니다')
    } else {
      showErrorMessage(response.error || '니모닉 생성에 실패했습니다')
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
    const response = await apiSaveMnemonic(finalMnemonic, username)

    if (response.success) {
      newMnemonic.value = finalMnemonic
      savedMnemonicId.value = response.id || null
      // Fetch only stored DB balance initially (no on-chain scan)
      if (savedMnemonicId.value) await fetchSavedBalance()
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

// Balance helpers
const fetchAssignedBalance = async () => {
  try {
    if (!assignedMnemonicId.value) return
    const res = await apiGetMnemonicBalance(assignedMnemonicId.value)
    if (res.success) assignedBalanceSats.value = res.balance_sats
  } catch (_) {}
}

const fetchSavedBalance = async () => {
  try {
    if (!savedMnemonicId.value) return
    const res = await apiGetMnemonicBalance(savedMnemonicId.value)
    if (res.success) savedBalanceSats.value = res.balance_sats
  } catch (_) {}
}

const formatBtc = (sats) => {
  try {
    const btc = (Number(sats || 0) / 1e8)
    return `${btc.toFixed(8)} BTC`
  } catch { return `${sats} sats` }
}

// Refresh handlers (manual)
const refreshAssignedBalance = async () => {
  if (!assignedMnemonicId.value) return
  assignedBalanceLoading.value = true
  try {
    // Use on-chain scan similar to admin to get latest balance
    const res = await apiGetOnchainBalanceById(assignedMnemonicId.value, { count: 20 })
    if (res.success) {
      const total = res.total_sats || 0
      assignedBalanceSats.value = total
    } else {
      showErrorMessage(res.error || '온체인 잔액 조회 실패')
    }
  } catch (_) {
    showErrorMessage('네트워크 오류가 발생했습니다')
  } finally {
    assignedBalanceLoading.value = false
  }
}

const refreshSavedBalance = async () => {
  if (!savedMnemonicId.value) return
  savedBalanceLoading.value = true
  try {
    await fetchSavedBalance()
  } finally {
    savedBalanceLoading.value = false
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

// Admin-like helpers for Step 2
const generateAndFillWalletMnemonic = async () => {
  try {
    const response = await apiGenerateMnemonic()
    if (response.success && response.mnemonic) {
      const words = (response.mnemonic || '').trim().split(/\s+/)
      for (let i = 0; i < 12; i++) {
        mnemonicWords.value[i] = words[i] || ''
      }
      manualMnemonicText.value = words.slice(0, 12).join(' ')
      // Reset validation state
      walletMnemonicValidity.value = null
      walletMnemonicWordCount.value = 0
      walletMnemonicUnknown.value = []
      walletMnemonicErrorCode.value = ''
      mnemonicError.value = ''
    } else {
      showErrorMessage(response.error || '니모닉 생성에 실패했습니다')
    }
  } catch (_) {
    showErrorMessage('네트워크 오류가 발생했습니다')
  }
}

const clearWalletManualMnemonic = () => {
  manualMnemonicText.value = ''
  mnemonicWords.value = Array(12).fill('')
  walletMnemonicValidity.value = null
  walletMnemonicWordCount.value = 0
  walletMnemonicUnknown.value = []
  walletMnemonicErrorCode.value = ''
  mnemonicError.value = ''
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

const checkWalletMnemonic = async () => {
  const text = (manualMnemonicText.value || mnemonicWords.value.join(' ')).trim()
  if (!text) { 
    walletMnemonicValidity.value = null; 
    walletMnemonicWordCount.value = 0; 
    showErrorMessage('니모닉을 입력하세요')
    return 
  }
  const res = await apiValidateMnemonic(text)
  if (res.success) {
    walletMnemonicValidity.value = !!res.valid
    walletMnemonicWordCount.value = res.word_count || 0
    walletMnemonicErrorCode.value = res.error || ''
    if (!res.valid) {
      let msg = '유효하지 않은 니모닉입니다'
      if (res.error === 'invalid_word_count') msg = '단어 개수가 올바르지 않습니다 (12/15/18/21/24)'
      else if (res.error === 'checksum_failed') msg = '체크섬이 일치하지 않습니다'
      const unknown = (res.unknown_words || [])
      if (unknown.length) {
        msg += `: [${unknown.join(', ')}]`
      }
      walletMnemonicUnknown.value = unknown
      mnemonicError.value = msg
      showErrorMessage(msg)
    } else {
      walletMnemonicUnknown.value = []
      walletMnemonicErrorCode.value = ''
      mnemonicError.value = ''
      showSuccessMessage('유효성 검사에 문제가 없습니다')
    }
  } else {
    walletMnemonicUnknown.value = res.unknown_words || []
    const msg = walletMnemonicUnknown.value.length ? `유효하지 않은 단어: [${walletMnemonicUnknown.value.join(', ')}]` : (res.error || '검증 실패')
    mnemonicError.value = msg
    showErrorMessage(msg)
  }
}
</script>
