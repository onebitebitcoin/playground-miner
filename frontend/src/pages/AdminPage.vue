<template>
  <div class="min-h-screen bg-gray-50 p-4">
    <div class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">관리자 패널</h1>
        <p class="text-gray-600">시스템 설정을 관리하고 데이터를 모니터링하세요.</p>
      </div>

      <!-- Access Denied -->
      <div v-if="!isAdmin" class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <svg class="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
        <h2 class="text-xl font-semibold text-red-900 mb-2">접근 권한 없음</h2>
        <p class="text-red-700">관리자 권한이 필요합니다.</p>
      </div>

      <!-- Admin Content -->
      <div v-else>
        <!-- Admin Tabs -->
        <div class="mb-6">
          <div class="border-b border-gray-200">
            <nav class="-mb-px flex space-x-8" aria-label="Tabs">
              <button
                @click="activeTab = 'mnemonics'"
                :class="[
                  activeTab === 'mnemonics'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm'
                ]"
              >
                니모닉 관리
              </button>
              <button
                @click="activeTab = 'fees'"
                :class="[
                  activeTab === 'fees'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm'
                ]"
              >
                수수료 관리
              </button>
            </nav>
          </div>
        </div>

        <!-- Mnemonics Tab Content -->
        <div v-if="activeTab === 'mnemonics'" class="grid lg:grid-cols-2 gap-8">
          <!-- Mnemonic Pool Management -->
          <div class="space-y-6">
            <div class="bg-white rounded-lg shadow-md p-6">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">니모닉 풀 관리</h3>

              <!-- Auto Generate Pool -->
              <div class="bg-blue-50 p-4 rounded-lg mb-4">
                <h4 class="font-medium text-blue-800 mb-3">자동 생성 풀</h4>
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

                  <div v-if="manualPoolError" class="text-red-600 text-sm">
                    {{ manualPoolError }}
                  </div>

                  <button @click="addManualMnemonicToPool"
                          :disabled="loading || !isValidAdminMnemonicInput"
                          class="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed">
                    {{ loading ? '추가 중...' : '풀에 추가' }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Mnemonic Pool Status -->
          <div class="space-y-6">
            <div class="bg-white rounded-lg shadow-md p-6">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">풀 상태</h3>

              <div class="bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
                <div v-if="adminMnemonics.length === 0" class="text-gray-500 text-center py-8">
                  저장된 니모닉이 없습니다
                </div>
                <div v-else class="space-y-2">
                  <div v-for="mnemonic in adminMnemonics" :key="mnemonic.id"
                       class="flex justify-between items-center p-3 bg-white rounded border">
                    <div class="flex-1">
                      <div class="flex items-center gap-2">
                        <span class="text-sm font-medium text-gray-900">{{ mnemonic.username }}</span>
                        <span v-if="mnemonic.is_assigned"
                              class="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                          할당됨
                        </span>
                        <span v-else
                              class="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                          대기중
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
              <div class="bg-yellow-50 p-4 rounded-lg mt-4">
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

        <!-- Fee Management Tab Content -->
        <div v-if="activeTab === 'fees'" class="space-y-6">
          <!-- Fee Sub-tabs -->
          <div class="bg-white rounded-lg shadow-md">
            <div class="border-b border-gray-200">
              <nav class="-mb-px flex space-x-8 px-6 pt-4" aria-label="Fee tabs">
                <button
                  @click="activeFeeTab = 'exchange'"
                  :class="[
                    activeFeeTab === 'exchange'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                    'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm'
                  ]"
                >
                  거래소 수수료
                </button>
                <button
                  @click="activeFeeTab = 'withdrawal'"
                  :class="[
                    activeFeeTab === 'withdrawal'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                    'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm'
                  ]"
                >
                  출금 수수료
                </button>
                <button
                  @click="activeFeeTab = 'lightning'"
                  :class="[
                    activeFeeTab === 'lightning'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                    'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm'
                  ]"
                >
                  라이트닝 서비스
                </button>
              </nav>
            </div>

            <div class="p-6">
              <!-- Exchange Rates Tab -->
              <div v-if="activeFeeTab === 'exchange'">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">거래소 수수료 관리</h3>
                <div class="space-y-4">
                  <div v-for="rate in exchangeRates" :key="rate.exchange" class="border border-gray-200 rounded-lg p-4">
                    <div class="flex items-center justify-between mb-3">
                      <h4 class="font-medium text-gray-900">{{ rate.exchange_name }}</h4>
                      <div class="flex items-center gap-2">
                        <label class="flex items-center">
                          <input
                            v-model="rate.is_event"
                            type="checkbox"
                            class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span class="ml-2 text-sm text-gray-700">이벤트</span>
                        </label>
                      </div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                          수수료율 (%)
                        </label>
                        <input
                          v-model="rate.fee_rate"
                          type="number"
                          step="0.0001"
                          min="0"
                          max="100"
                          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                          설명
                        </label>
                        <input
                          v-model="rate.description"
                          type="text"
                          placeholder="수수료 조건 설명"
                          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                    </div>

                    <!-- Event details field (shown only for events) -->
                    <div v-if="rate.is_event" class="mt-4">
                      <label class="block text-sm font-medium text-gray-700 mb-1">
                        이벤트 상세 정보
                      </label>
                      <textarea
                        v-model="rate.event_details"
                        placeholder="이벤트 조건, 기간, 주의사항 등 자세한 내용을 입력하세요"
                        rows="3"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                      ></textarea>
                      <div class="text-xs text-gray-500 mt-1">
                        이벤트 관련 자세한 내용이 수수료 계산 페이지에 표시됩니다
                      </div>
                    </div>

                    <div class="mt-4 flex justify-between items-center">
                      <div class="text-sm text-gray-500">
                        <span v-if="rate.is_event" class="text-orange-600 font-medium">⚠️ 한시적 이벤트</span>
                        <span v-else class="text-green-600">일반 수수료</span>
                      </div>
                      <button
                        @click="updateExchangeRate(rate)"
                        :disabled="feeUpdateLoading"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {{ feeUpdateLoading ? '업데이트 중...' : '업데이트' }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Withdrawal Fees Tab -->
              <div v-if="activeFeeTab === 'withdrawal'">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">출금 수수료 관리</h3>
                <div class="space-y-4">
                  <div v-for="fee in withdrawalFees" :key="`${fee.exchange}-${fee.withdrawal_type}`" class="border border-gray-200 rounded-lg p-4">
                    <div class="flex items-center justify-between mb-3">
                      <h4 class="font-medium text-gray-900">{{ fee.exchange_name }} - {{ fee.withdrawal_type_name }}</h4>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                          출금 수수료 (BTC)
                        </label>
                        <input
                          v-model="fee.fee_btc"
                          type="number"
                          step="0.00000001"
                          min="0"
                          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                          설명
                        </label>
                        <input
                          v-model="fee.description"
                          type="text"
                          placeholder="출금 조건 설명"
                          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                    </div>

                    <div class="mt-4 flex justify-end">
                      <button
                        @click="updateWithdrawalFee(fee)"
                        :disabled="feeUpdateLoading"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {{ feeUpdateLoading ? '업데이트 중...' : '업데이트' }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Lightning Services Tab -->
              <div v-if="activeFeeTab === 'lightning'">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">라이트닝 서비스 수수료 관리</h3>
                <div class="space-y-4">
                  <div v-for="service in lightningServices" :key="service.service" class="border border-gray-200 rounded-lg p-4">
                    <div class="flex items-center justify-between mb-3">
                      <h4 class="font-medium text-gray-900">{{ service.service_name }}</h4>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                          수수료율 (%)
                        </label>
                        <input
                          v-model="service.fee_rate"
                          type="number"
                          step="0.0001"
                          min="0"
                          max="100"
                          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                          KYC 상태
                        </label>
                        <div class="flex items-center gap-2 mt-2">
                          <label class="flex items-center">
                            <input
                              v-model="service.is_kyc"
                              type="checkbox"
                              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            />
                            <span class="ml-2 text-sm text-gray-700">KYC 필요</span>
                          </label>
                        </div>
                        <div class="text-xs text-gray-500 mt-1">
                          {{ service.is_kyc ? 'KYC 인증 필요' : 'non-KYC 서비스' }}
                        </div>
                      </div>
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                          설명
                        </label>
                        <input
                          v-model="service.description"
                          type="text"
                          placeholder="서비스 설명"
                          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                    </div>

                    <div class="mt-4 flex justify-end">
                      <button
                        @click="updateLightningService(service)"
                        :disabled="feeUpdateLoading"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {{ feeUpdateLoading ? '업데이트 중...' : '업데이트' }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Success/Error Messages -->
              <div v-if="feeUpdateSuccess" class="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                <div class="flex items-center">
                  <svg class="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                  </svg>
                  <p class="text-green-700">수수료가 성공적으로 업데이트되었습니다!</p>
                </div>
              </div>

              <div v-if="feeUpdateError" class="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <div class="flex items-center">
                  <svg class="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                  </svg>
                  <p class="text-red-700">{{ feeUpdateError }}</p>
                </div>
              </div>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  apiRequestMnemonic,
  apiGenerateMnemonic,
  apiSaveMnemonic,
  apiGetAdminMnemonics,
  apiGetAdminExchangeRates,
  apiUpdateExchangeRate,
  apiGetAdminWithdrawalFees,
  apiUpdateWithdrawalFee,
  apiGetAdminLightningServices,
  apiUpdateLightningService
} from '../api'

// State
const loading = ref(false)
const successMessage = ref('')
const errorMessage = ref('')
const activeTab = ref('mnemonics')
const activeFeeTab = ref('exchange')

// Mnemonic management state
const mnemonicCount = ref(10)
const manualPoolMnemonicText = ref('')
const adminMnemonicWords = ref(Array(12).fill(''))
const manualPoolError = ref('')
const adminMnemonics = ref([])

// Fee management state
const exchangeRates = ref([])
const withdrawalFees = ref([])
const lightningServices = ref([])
const feeUpdateLoading = ref(false)
const feeUpdateSuccess = ref(false)
const feeUpdateError = ref('')

// Computed
const isAdmin = computed(() => {
  const nickname = localStorage.getItem('nickname')
  const adminStatus = localStorage.getItem('isAdmin')
  return nickname === 'admin' && adminStatus === 'true'
})

const availableMnemonicsCount = computed(() => {
  return adminMnemonics.value.filter(m => !m.is_assigned).length
})

const isValidAdminMnemonicInput = computed(() => {
  const words = adminMnemonicWords.value.filter(w => w.trim().length > 0)
  return words.length === 12 || (manualPoolMnemonicText.value.trim().split(/\s+/).length === 12)
})

// Utility functions
const getCurrentUsername = () => {
  return localStorage.getItem('nickname') || 'anonymous'
}

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

const formatDate = (dateString) => {
  try {
    return new Date(dateString).toLocaleString('ko-KR')
  } catch {
    return dateString
  }
}

// Mnemonic management functions
const updateAdminManualMnemonic = () => {
  const words = adminMnemonicWords.value.filter(w => w.trim().length > 0)
  manualPoolMnemonicText.value = adminMnemonicWords.value.join(' ').trim()
}

const updateAdminFromTextarea = () => {
  const words = manualPoolMnemonicText.value.trim().split(/\s+/).filter(w => w.length > 0)

  for (let i = 0; i < 12; i++) {
    adminMnemonicWords.value[i] = words[i] || ''
  }
}

const handleAdminPaste = (event, startIndex) => {
  event.preventDefault()
  const pastedText = (event.clipboardData || window.clipboardData).getData('text')
  const words = pastedText.trim().split(/\s+/).filter(w => w.length > 0)

  for (let i = 0; i < 12; i++) {
    adminMnemonicWords.value[i] = words[i] || ''
  }

  updateAdminManualMnemonic()
}

const addMnemonicPool = async () => {
  if (!mnemonicCount.value || mnemonicCount.value < 1) return

  loading.value = true
  let addedCount = 0

  try {
    for (let i = 0; i < mnemonicCount.value; i++) {
      const username = `pool_${Date.now()}_${i}`
      const response = await apiGenerateMnemonic()

      if (response.ok && response.mnemonic) {
        const saveResponse = await apiSaveMnemonic(username, response.mnemonic)
        if (saveResponse.ok) {
          addedCount++
        }
      }
    }

    if (addedCount > 0) {
      showSuccessMessage(`${addedCount}개의 니모닉이 풀에 추가되었습니다`)
      await loadAdminData()
    } else {
      showErrorMessage('니모닉 추가에 실패했습니다')
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
    const username = `manual_${Date.now()}`
    const response = await apiSaveMnemonic(username, finalMnemonic)

    if (response.ok) {
      showSuccessMessage('니모닉이 풀에 추가되었습니다')

      // Clear all inputs
      manualPoolMnemonicText.value = ''
      adminMnemonicWords.value = Array(12).fill('')

      await loadAdminData()
    } else {
      manualPoolError.value = response.error || '니모닉 저장에 실패했습니다'
    }
  } catch (error) {
    manualPoolError.value = '네트워크 오류가 발생했습니다'
  } finally {
    loading.value = false
  }
}

const showMnemonicInAdmin = (mnemonic) => {
  alert(`니모닉: ${mnemonic}`)
}


// Exchange rate management functions
const loadExchangeRates = async () => {
  try {
    const username = getCurrentUsername()
    const response = await apiGetAdminExchangeRates(username)
    if (response.success) {
      exchangeRates.value = response.rates
    } else {
      feeUpdateError.value = response.error || '수수료 데이터 로드에 실패했습니다'
    }
  } catch (error) {
    feeUpdateError.value = '네트워크 오류'
  }
}

const updateExchangeRate = async (rate) => {
  feeUpdateLoading.value = true
  feeUpdateSuccess.value = false
  feeUpdateError.value = ''

  try {
    const username = getCurrentUsername()
    const response = await apiUpdateExchangeRate(
      username,
      rate.exchange,
      rate.fee_rate,
      rate.is_event,
      rate.description,
      rate.event_details
    )

    if (response.success) {
      feeUpdateSuccess.value = true
      // Update the local rate data
      const index = exchangeRates.value.findIndex(r => r.exchange === rate.exchange)
      if (index !== -1) {
        exchangeRates.value[index] = response.rate
      }

      // Clear success message after 3 seconds
      setTimeout(() => {
        feeUpdateSuccess.value = false
      }, 3000)
    } else {
      feeUpdateError.value = response.error || '수수료 업데이트에 실패했습니다'
    }
  } catch (error) {
    feeUpdateError.value = '네트워크 오류'
  } finally {
    feeUpdateLoading.value = false
  }
}

// Withdrawal fee management functions
const loadWithdrawalFees = async () => {
  try {
    const username = getCurrentUsername()
    const response = await apiGetAdminWithdrawalFees(username)
    if (response.success) {
      withdrawalFees.value = response.fees
    } else {
      feeUpdateError.value = response.error || '출금 수수료 데이터 로드에 실패했습니다'
    }
  } catch (error) {
    feeUpdateError.value = '네트워크 오류'
  }
}

const updateWithdrawalFee = async (fee) => {
  feeUpdateLoading.value = true
  feeUpdateSuccess.value = false
  feeUpdateError.value = ''

  try {
    const username = getCurrentUsername()
    const response = await apiUpdateWithdrawalFee(
      username,
      fee.exchange,
      fee.withdrawal_type,
      fee.fee_btc,
      fee.description
    )

    if (response.success) {
      feeUpdateSuccess.value = true
      // Update the local fee data
      const index = withdrawalFees.value.findIndex(f =>
        f.exchange === fee.exchange && f.withdrawal_type === fee.withdrawal_type
      )
      if (index !== -1) {
        withdrawalFees.value[index] = response.fee
      }

      // Clear success message after 3 seconds
      setTimeout(() => {
        feeUpdateSuccess.value = false
      }, 3000)
    } else {
      feeUpdateError.value = response.error || '출금 수수료 업데이트에 실패했습니다'
    }
  } catch (error) {
    feeUpdateError.value = '네트워크 오류'
  } finally {
    feeUpdateLoading.value = false
  }
}

// Lightning service management functions
const loadLightningServices = async () => {
  try {
    const username = getCurrentUsername()
    const response = await apiGetAdminLightningServices(username)
    if (response.success) {
      lightningServices.value = response.services
    } else {
      feeUpdateError.value = response.error || '라이트닝 서비스 데이터 로드에 실패했습니다'
    }
  } catch (error) {
    feeUpdateError.value = '네트워크 오류'
  }
}

const updateLightningService = async (service) => {
  feeUpdateLoading.value = true
  feeUpdateSuccess.value = false
  feeUpdateError.value = ''

  try {
    const username = getCurrentUsername()
    const response = await apiUpdateLightningService(
      username,
      service.service,
      service.fee_rate,
      service.is_kyc,
      service.description
    )

    if (response.success) {
      feeUpdateSuccess.value = true
      // Update the local service data
      const index = lightningServices.value.findIndex(s => s.service === service.service)
      if (index !== -1) {
        lightningServices.value[index] = response.service
      }

      // Clear success message after 3 seconds
      setTimeout(() => {
        feeUpdateSuccess.value = false
      }, 3000)
    } else {
      feeUpdateError.value = response.error || '라이트닝 서비스 업데이트에 실패했습니다'
    }
  } catch (error) {
    feeUpdateError.value = '네트워크 오류'
  } finally {
    feeUpdateLoading.value = false
  }
}

// Enhanced loadAdminData to include all fee types
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

    // Load all fee management data
    await Promise.all([
      loadExchangeRates(),
      loadWithdrawalFees(),
      loadLightningServices()
    ])
  } catch (error) {
    showErrorMessage('네트워크 오류가 발생했습니다')
  } finally {
    loading.value = false
  }
}

// Load admin data on mount if admin
onMounted(() => {
  if (isAdmin.value) {
    loadAdminData()
  }
})
</script>