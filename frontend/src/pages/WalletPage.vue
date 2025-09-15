<template>
  <div class="max-w-4xl mx-auto">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900 mb-2">비트코인 지갑</h1>
      <p class="text-gray-600">니모닉을 관리하고 새로운 지갑을 생성하세요</p>
    </div>

    <!-- Admin Button (only for admin user) -->
    <div v-if="isAdmin" class="mb-6">
      <button @click="showAdminPanel = true"
              class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors">
        관리자 패널 열기
      </button>
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

    <!-- Admin Panel Modal -->
    <div v-if="showAdminPanel" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl shadow-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <!-- Admin Panel Header -->
        <div class="flex justify-between items-center p-6 border-b">
          <h2 class="text-xl font-semibold text-gray-900">관리자 패널</h2>
          <button @click="showAdminPanel = false" class="text-gray-500 hover:text-gray-700">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Admin Panel Content -->
        <div class="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          <div class="grid md:grid-cols-2 gap-6">
            <!-- Mnemonic Pool Management -->
            <div class="space-y-4">
              <h3 class="text-lg font-semibold text-gray-900">니모닉 풀 관리</h3>

              <!-- Add Multiple Mnemonics -->
              <div class="bg-blue-50 p-4 rounded-lg">
                <h4 class="font-medium text-blue-800 mb-3">니모닉 풀 추가</h4>
                <div class="space-y-3">
                  <div class="flex gap-2">
                    <input v-model="mnemonicCount"
                           type="number"
                           min="1"
                           max="50"
                           placeholder="생성할 개수"
                           class="flex-1 px-3 py-2 border border-blue-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
                    <button @click="addMnemonicPool"
                            :disabled="loading || !mnemonicCount || mnemonicCount < 1"
                            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
                      {{ loading ? '생성 중...' : '풀 추가' }}
                    </button>
                  </div>
                  <p class="text-sm text-blue-600">자동으로 생성된 니모닉을 풀에 추가합니다</p>
                </div>
              </div>

              <!-- Manual Mnemonic Add -->
              <div class="bg-green-50 p-4 rounded-lg">
                <h4 class="font-medium text-green-800 mb-3">개별 니모닉 추가</h4>
                <div class="space-y-3">
                  <!-- Individual word inputs -->
                  <div class="grid grid-cols-3 gap-2">
                    <div v-for="i in 12" :key="i" class="relative">
                      <label :for="`admin-word-${i}`" class="block text-xs font-medium text-green-600 mb-1">
                        {{ i }}
                      </label>
                      <input
                        :id="`admin-word-${i}`"
                        v-model="adminMnemonicWords[i-1]"
                        @input="updateAdminManualMnemonic"
                        @paste="handleAdminPaste($event, i-1)"
                        type="text"
                        :placeholder="`단어 ${i}`"
                        class="w-full px-2 py-2 text-sm border border-green-200 rounded focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none"
                        :class="{ 'border-red-300': manualPoolError }"
                      />
                    </div>
                  </div>

                  <!-- Alternative textarea input -->
                  <div class="border-t border-green-200 pt-3">
                    <label class="block text-sm font-medium text-green-700 mb-2">
                      또는 한번에 입력:
                    </label>
                    <textarea v-model="manualPoolMnemonicText"
                              @input="updateAdminFromTextarea"
                              placeholder="12개의 영어 단어를 공백으로 구분하여 입력"
                              class="w-full h-16 px-3 py-2 text-sm border border-green-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none resize-none"
                              :class="{ 'border-red-300': manualPoolError }"></textarea>
                  </div>

                  <div v-if="manualPoolError" class="text-sm text-red-600">{{ manualPoolError }}</div>

                  <button @click="addManualMnemonicToPool"
                          :disabled="loading || !isValidAdminMnemonicInput"
                          class="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50">
                    {{ loading ? '추가 중...' : '풀에 추가' }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Stored Mnemonics List -->
            <div class="space-y-4">
              <div class="flex justify-between items-center">
                <h3 class="text-lg font-semibold text-gray-900">저장된 니모닉 목록</h3>
                <button @click="loadAdminData"
                        :disabled="loading"
                        class="px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50">
                  새로고침
                </button>
              </div>

              <div class="bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
                <div v-if="adminMnemonics.length === 0" class="text-gray-500 text-center py-8">
                  저장된 니모닉이 없습니다
                </div>
                <div v-else class="space-y-2">
                  <div v-for="mnemonic in adminMnemonics" :key="mnemonic.id"
                       class="flex justify-between items-center p-3 bg-white rounded border">
                    <div class="flex-1">
                      <div class="flex items-center gap-2">
                        <span class="font-medium">{{ mnemonic.username }}</span>
                        <span v-if="mnemonic.is_assigned"
                              class="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded">
                          할당됨
                        </span>
                        <span v-else
                              class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                          사용가능
                        </span>
                      </div>
                      <span class="text-sm text-gray-500">{{ formatDate(mnemonic.created_at) }}</span>
                    </div>
                    <button @click="showMnemonicInAdmin(mnemonic.mnemonic)"
                            class="text-sm text-blue-600 hover:text-blue-800">
                      보기
                    </button>
                  </div>
                </div>
              </div>

              <!-- Pool Statistics -->
              <div class="bg-yellow-50 p-4 rounded-lg">
                <h4 class="font-medium text-yellow-800 mb-2">통계</h4>
                <div class="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span class="text-yellow-700">전체 니모닉:</span>
                    <span class="font-medium ml-1">{{ adminMnemonics.length }}</span>
                  </div>
                  <div>
                    <span class="text-yellow-700">사용 가능:</span>
                    <span class="font-medium ml-1">{{ availableMnemonicsCount }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import QRCode from 'qrcode'

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

// Admin panel state
const showAdminPanel = ref(false)
const mnemonicCount = ref(10)
const manualPoolMnemonic = ref('')
const manualPoolMnemonicText = ref('')
const adminMnemonicWords = ref(Array(12).fill(''))
const manualPoolError = ref('')

// Admin state
const isAdmin = computed(() => {
  const nickname = localStorage.getItem('nickname')
  const adminStatus = localStorage.getItem('isAdmin')
  return nickname === 'admin' && adminStatus === 'true'
})
const adminMnemonics = ref([])

// Computed for available mnemonics count
const availableMnemonicsCount = computed(() => {
  return adminMnemonics.value.filter(m => !m.is_assigned).length
})

// Computed for valid mnemonic input
const isValidMnemonicInput = computed(() => {
  const words = mnemonicWords.value.filter(w => w.trim().length > 0)
  return words.length === 12 || (manualMnemonicText.value.trim().split(/\s+/).length === 12)
})

// Computed for valid admin mnemonic input
const isValidAdminMnemonicInput = computed(() => {
  const words = adminMnemonicWords.value.filter(w => w.trim().length > 0)
  return words.length === 12 || (manualPoolMnemonicText.value.trim().split(/\s+/).length === 12)
})

// Get current username
const getCurrentUsername = () => {
  return localStorage.getItem('nickname') || 'anonymous'
}

import {
  apiRequestMnemonic,
  apiGenerateMnemonic,
  apiSaveMnemonic,
  apiGetAdminMnemonics
} from '../api'

// Mnemonic validation
const validateMnemonic = (mnemonic) => {
  const words = mnemonic.trim().split(/\s+/)
  if (words.length !== 12) {
    return '정확히 12개의 단어를 입력해야 합니다'
  }

  const englishWordPattern = /^[a-zA-Z]+$/
  for (let word of words) {
    if (!englishWordPattern.test(word)) {
      return '모든 단어는 영어로 입력해야 합니다'
    }
  }

  return null
}

// Actions
const requestExistingMnemonic = async () => {
  loading.value = true
  try {
    const response = await apiRequestMnemonic()
    if (response.success) {
      assignedMnemonic.value = response.mnemonic
      showSuccessMessage('기존 니모닉이 할당되었습니다')
    } else {
      showErrorMessage(response.error || '니모닉 요청에 실패했습니다')
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
    if (response.success) {
      newMnemonic.value = response.mnemonic
      const username = getCurrentUsername()
      const saveResponse = await apiSaveMnemonic(response.mnemonic, username)
      if (saveResponse.success) {
        showSuccessMessage('새 니모닉이 생성되고 저장되었습니다')
      } else {
        showErrorMessage(saveResponse.error || '니모닉 저장에 실패했습니다')
      }
    } else {
      showErrorMessage(response.error || '니모닉 생성에 실패했습니다')
    }
  } catch (error) {
    showErrorMessage('네트워크 오류가 발생했습니다')
  } finally {
    loading.value = false
  }
}

// Mode switching function
const switchGenerationMode = (mode) => {
  generationMode.value = mode
  // Clear the new mnemonic display when switching modes
  newMnemonic.value = ''
  mnemonicError.value = ''
}

// Input handling functions
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
  const pasteData = event.clipboardData.getData('text')
  const words = pasteData.trim().split(/\s+/)

  if (words.length >= 12) {
    event.preventDefault()

    for (let i = 0; i < 12; i++) {
      mnemonicWords.value[i] = words[i] || ''
    }

    updateManualMnemonic()
  }
}

// Admin panel input handling functions
const updateAdminManualMnemonic = () => {
  const words = adminMnemonicWords.value.filter(w => w.trim().length > 0)
  manualPoolMnemonic.value = words.join(' ')
  manualPoolMnemonicText.value = adminMnemonicWords.value.join(' ').trim()
}

const updateAdminFromTextarea = () => {
  const words = manualPoolMnemonicText.value.trim().split(/\s+/).filter(w => w.length > 0)

  for (let i = 0; i < 12; i++) {
    adminMnemonicWords.value[i] = words[i] || ''
  }

  manualPoolMnemonic.value = words.slice(0, 12).join(' ')
}

const handleAdminPaste = (event, startIndex) => {
  const pasteData = event.clipboardData.getData('text')
  const words = pasteData.trim().split(/\s+/)

  if (words.length >= 12) {
    event.preventDefault()

    for (let i = 0; i < 12; i++) {
      adminMnemonicWords.value[i] = words[i] || ''
    }

    updateAdminManualMnemonic()
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
      mnemonicWords.value = Array(12).fill('')
      manualMnemonicText.value = ''
      manualMnemonic.value = ''
      showSuccessMessage(response.message || '니모닉이 저장되었습니다')
    } else {
      showErrorMessage(response.error || '니모닉 저장에 실패했습니다')
    }
  } catch (error) {
    showErrorMessage('네트워크 오류가 발생했습니다')
  } finally {
    loading.value = false
  }
}

const showQRCode = async (mnemonic) => {
  currentMnemonic.value = mnemonic
  showQR.value = true

  await nextTick()
  if (qrCodeContainer.value) {
    qrCodeContainer.value.innerHTML = ''
    try {
      const canvas = document.createElement('canvas')
      await QRCode.toCanvas(canvas, mnemonic, {
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
      placeholder.className = 'w-48 h-48 bg-gray-200 flex items-center justify-center text-gray-500 text-sm'
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

const loadAdminData = async () => {
  if (!isAdmin.value) return

  loading.value = true
  try {
    const username = getCurrentUsername()
    const response = await apiGetAdminMnemonics(username)
    if (response.success) {
      adminMnemonics.value = response.mnemonics
    } else {
      showErrorMessage(response.error || '관리자 데이터 로드에 실패했습니다')
    }
  } catch (error) {
    showErrorMessage('네트워크 오류가 발생했습니다')
  } finally {
    loading.value = false
  }
}

const showMnemonicInAdmin = (mnemonic) => {
  alert(`니모닉: ${mnemonic}`)
}

// Admin panel functions
const addMnemonicPool = async () => {
  const count = parseInt(mnemonicCount.value)
  if (!count || count < 1 || count > 50) {
    showErrorMessage('1-50 사이의 숫자를 입력하세요')
    return
  }

  loading.value = true
  try {
    let successCount = 0
    const poolUsername = `pool_${Date.now()}`

    for (let i = 0; i < count; i++) {
      const response = await apiGenerateMnemonic()
      if (response.success) {
        const saveResponse = await apiSaveMnemonic(response.mnemonic, `${poolUsername}_${i + 1}`)
        if (saveResponse.success) {
          successCount++
        }
      }
    }

    if (successCount > 0) {
      showSuccessMessage(`${successCount}개의 니모닉이 풀에 추가되었습니다`)
      await loadAdminData()
      mnemonicCount.value = 10
    } else {
      showErrorMessage('니모닉 풀 추가에 실패했습니다')
    }
  } catch (error) {
    showErrorMessage('네트워크 오류가 발생했습니다')
  } finally {
    loading.value = false
  }
}

const addManualMnemonicToPool = async () => {
  manualPoolError.value = ''

  const finalMnemonic = manualPoolMnemonicText.value.trim() || adminMnemonicWords.value.join(' ').trim()
  const error = validateMnemonic(finalMnemonic)
  if (error) {
    manualPoolError.value = error
    return
  }

  loading.value = true
  try {
    const poolUsername = `manual_pool_${Date.now()}`
    const response = await apiSaveMnemonic(finalMnemonic, poolUsername)
    if (response.success) {
      showSuccessMessage('니모닉이 풀에 추가되었습니다')

      // Clear all inputs
      manualPoolMnemonic.value = ''
      manualPoolMnemonicText.value = ''
      adminMnemonicWords.value = Array(12).fill('')

      await loadAdminData()
    } else {
      manualPoolError.value = response.error || '풀 추가에 실패했습니다'
    }
  } catch (error) {
    manualPoolError.value = '네트워크 오류가 발생했습니다'
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString) => {
  try {
    return new Date(dateString).toLocaleString('ko-KR')
  } catch {
    return dateString
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

// Load admin data on mount if admin
onMounted(() => {
  if (isAdmin.value) {
    loadAdminData()
  }
})

// Watch for admin panel open to refresh data
watch(showAdminPanel, (newValue) => {
  if (newValue && isAdmin.value) {
    loadAdminData()
  }
})
</script>