<template>
  <div>
    <WalletMenuTabs active="kingstone" />
    <div class="device-wrapper">
      <div class="device-frame">
        <div class="device-notch"></div>
        <div class="device-screen">
          <div class="mb-6">
            <h1 class="text-2xl font-bold text-gray-900">킹스톤 지갑</h1>
          </div>

          <div class="space-y-6">
      <div v-if="loadError" class="p-4 bg-red-50 border border-red-200 text-sm text-red-700 rounded-lg">
        {{ loadError }}
      </div>

      <div
        v-if="!hasWallets && mode !== 'register'"
        class="bg-white border border-gray-200 rounded-xl p-6 text-center"
      >
        <h2 class="text-xl font-semibold text-gray-900 mb-2">아직 생성된 지갑이 없습니다</h2>
        <p class="text-gray-600 text-sm mb-4">새로운 핀번호로 첫 지갑을 만들어 보세요.</p>
        <button
          type="button"
          class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          :disabled="!canRegister"
          @click="switchToRegister()"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          새로운 지갑 생성
        </button>
        <p v-if="!canRegister" class="mt-3 text-xs text-red-600">새 지갑을 만들 수 있는 한도에 도달했습니다.</p>
      </div>

      <div v-if="hasWallets && mode === 'verify'" class="bg-white border border-gray-200 rounded-xl p-6">
        <div class="space-y-4">
          <div class="flex flex-col items-center gap-4">
            <div class="flex justify-center gap-2">
              <span
                v-for="i in PIN_LENGTH"
                :key="`verify-slot-${i}`"
                class="w-8 h-8 rounded-full border flex items-center justify-center text-base font-medium"
                :class="pinInput.length >= i ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-400 border-gray-300'"
              >
                {{ pinInput[i-1] ? '*' : '' }}
              </span>
            </div>

            <div class="grid grid-cols-3 gap-2 w-full sm:max-w-xs">
              <button
                v-for="digit in ['1','2','3','4','5','6','7','8','9']"
                :key="`verify-digit-${digit}`"
                type="button"
                class="px-4 py-3 text-lg font-semibold rounded-lg border border-gray-200 bg-gray-50 hover:bg-gray-100"
                @click="appendDigit('verify', digit)"
              >
                {{ digit }}
              </button>
              <button
                type="button"
                class="px-4 py-3 text-sm font-medium rounded-lg border border-gray-200 bg-gray-50 hover:bg-gray-100"
                @click="removeDigit('verify')"
              >
                지우기
              </button>
              <button
                type="button"
                class="px-4 py-3 text-lg font-semibold rounded-lg border border-gray-200 bg-gray-50 hover:bg-gray-100"
                @click="appendDigit('verify', '0')"
              >
                0
              </button>
              <button
                type="button"
                class="px-4 py-3 text-sm font-medium rounded-lg border border-gray-200 bg-gray-50 hover:bg-gray-100"
                @click="clearPin('verify')"
              >
                초기화
              </button>
            </div>
          </div>

          <div class="flex justify-end">
            <button
              type="button"
              @click="switchToRegister()"
              class="text-sm text-gray-600 hover:text-gray-900"
            >
              새 지갑 생성하기
            </button>
          </div>

          <div v-if="verifyError" class="text-sm text-red-600">{{ verifyError }}</div>
        </div>

      </div>

      <div v-if="mode === 'register'" class="bg-white border border-gray-200 rounded-xl p-6 space-y-6">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <h2 class="text-xl font-semibold text-gray-900">새 지갑 생성</h2>
          <span class="text-sm text-gray-500">{{ registerStepTitle }}</span>
        </div>

        <div v-if="registerError" class="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {{ registerError }}
        </div>

        <template v-if="registerStep === REGISTER_STEPS.PIN">
          <div class="flex justify-center gap-2 mt-4">
            <span
              v-for="i in PIN_LENGTH"
              :key="`register-slot-${i}`"
              class="w-8 h-8 rounded-full border flex items-center justify-center text-base font-medium"
              :class="registerPin.length >= i ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-400 border-gray-300'"
            >
              {{ registerPin[i-1] ? '*' : '' }}
            </span>
          </div>
          <div class="grid grid-cols-3 gap-2 w-full sm:max-w-xs mx-auto mt-4">
            <button
              v-for="digit in ['1','2','3','4','5','6','7','8','9']"
              :key="`register-digit-${digit}`"
              type="button"
              class="px-4 py-3 text-lg font-semibold rounded-lg border border-gray-200 bg-gray-50 hover:bg-gray-100"
              :disabled="!canRegister"
              @click="appendDigit('register', digit)"
            >
              {{ digit }}
            </button>
            <button
              type="button"
              class="px-4 py-3 text-sm font-medium rounded-lg border border-gray-200 bg-gray-50 hover:bg-gray-100"
              :disabled="!canRegister"
              @click="removeDigit('register')"
            >
              지우기
            </button>
            <button
              type="button"
              class="px-4 py-3 text-lg font-semibold rounded-lg border border-gray-200 bg-gray-50 hover:bg-gray-100"
              :disabled="!canRegister"
              @click="appendDigit('register', '0')"
            >
              0
            </button>
            <button
              type="button"
              class="px-4 py-3 text-sm font-medium rounded-lg border border-gray-200 bg-gray-50 hover:bg-gray-100"
              :disabled="!canRegister"
              @click="clearPin('register')"
            >
              초기화
            </button>
          </div>
          <div class="flex justify-between items-center mt-6">
            <button
              v-if="hasWallets"
              type="button"
              class="text-sm text-gray-600 hover:text-gray-900"
              @click="handleRegisterBackToVerify"
            >
              뒤로가기
            </button>
            <span v-else></span>
            <button
              type="button"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              :disabled="registerPin.length !== PIN_LENGTH"
              @click="handlePinNext"
            >
              다음
            </button>
          </div>
        </template>

        <template v-else-if="registerStep === REGISTER_STEPS.NAME">
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1" for="wallet-name-input">지갑 이름</label>
              <input
                id="wallet-name-input"
                v-model="walletNameInput"
                type="text"
                maxlength="64"
                placeholder="지갑 이름을 입력하세요"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div class="flex justify-between items-center">
              <button type="button" class="text-sm text-gray-600 hover:text-gray-900" @click="handleNameBack">뒤로가기</button>
              <button
                type="button"
                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                :disabled="!walletNameInput.trim()"
                @click="handleNameNext"
              >
                다음
              </button>
            </div>
          </div>
        </template>

        <template v-else-if="registerStep === REGISTER_STEPS.METHOD">
          <div class="space-y-4">
            <button
              type="button"
              class="w-full border border-blue-200 bg-blue-50 hover:border-blue-300 hover:bg-blue-100 rounded-lg p-4 text-left transition"
              @click="handleSelectStandard"
            >
              <div class="text-base font-semibold text-gray-900 mb-1">표준 시드 문구</div>
              <p class="text-sm text-gray-600">BIP39 표준에 따른 12 또는 24 단어</p>
            </button>
            <div class="w-full border border-gray-200 rounded-lg p-4 text-left bg-gray-50 text-gray-400 cursor-not-allowed">
              <div class="text-base font-semibold mb-1">샤미르 백업 (준비 중)</div>
              <p class="text-sm">현재는 사용하실 수 없습니다.</p>
            </div>
          </div>
          <div class="flex justify-between items-center mt-6">
            <button type="button" class="text-sm text-gray-600 hover:text-gray-900" @click="handleMethodBack">뒤로가기</button>
            <span class="text-sm text-gray-400">표준 시드 문구를 선택하세요</span>
          </div>
        </template>

        <template v-else-if="registerStep === REGISTER_STEPS.MNEMONIC">
          <div class="flex justify-end mb-4">
            <select
              v-model="mnemonicLength"
              @change="handleMnemonicLengthChange(mnemonicLength)"
              class="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option :value="12">12</option>
              <option :value="24">24</option>
            </select>
          </div>

          <div v-if="!registerMnemonicWords.length" class="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-700">
            단어 목록을 불러오는 중입니다. 다시 시도하려면 다시 만들기를 눌러주세요.
          </div>
          <div v-else class="grid sm:grid-cols-2 gap-2">
            <div
              v-for="(word, idx) in registerMnemonicWords"
              :key="`mnemonic-word-${idx}`"
              class="flex items-center gap-3 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2"
            >
              <span class="w-6 text-xs font-semibold text-gray-500">{{ idx + 1 }}</span>
              <span class="font-mono text-sm text-gray-900">{{ word }}</span>
            </div>
          </div>

          <button
            type="button"
            class="w-full inline-flex items-center justify-center gap-2 px-4 py-3 text-sm border border-gray-300 rounded-lg text-gray-700 hover:text-gray-900 hover:border-gray-400 bg-white hover:bg-gray-50 mt-4"
            @click="handleMnemonicRefresh"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            다시 만들기
          </button>

          <div class="flex justify-between items-center mt-6">
            <button type="button" class="text-sm text-gray-600 hover:text-gray-900" @click="handleMnemonicBack">뒤로가기</button>
            <button
              type="button"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              :disabled="!registerMnemonicWords.length"
              @click="handleMnemonicNext"
            >
              다음
            </button>
          </div>
        </template>

        <template v-else-if="registerStep === REGISTER_STEPS.VERIFY">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <p class="text-sm text-gray-600">니모닉을 올바른 순서로 선택하세요</p>
            <div class="flex items-center gap-2">
              <span class="text-sm text-gray-500">{{ verificationSelection.length }} / {{ registerMnemonicWords.length }}</span>
              <button
                type="button"
                class="inline-flex items-center gap-2 px-3 py-2 text-sm border border-gray-200 rounded-lg text-gray-700 hover:text-gray-900 hover:border-gray-300"
                @click="handleVerificationReset"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                새로고침
              </button>
            </div>
          </div>

          <div class="grid sm:grid-cols-2 gap-2 mt-6">
            <button
              v-for="option in verificationOptions"
              :key="`verify-option-${option.word}-${option.correctIndex}`"
              type="button"
              class="relative px-4 py-3 text-left border rounded-lg transition"
              :class="option.selectedOrder ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-800 border-gray-200 hover:border-blue-300 hover:bg-blue-50'"
              @click="handleSelectVerificationWord(option)"
              :disabled="option.selectedOrder > 0 || registerLoading"
            >
              <span
                v-if="option.selectedOrder"
                class="absolute -top-2 -left-2 w-6 h-6 rounded-full bg-blue-600 text-white text-xs font-semibold flex items-center justify-center"
              >
                {{ option.selectedOrder }}
              </span>
              <span class="font-mono text-sm">{{ option.word }}</span>
            </button>
          </div>

          <div class="flex justify-between items-center mt-6">
            <button type="button" class="text-sm text-gray-600 hover:text-gray-900" @click="handleVerificationBack">뒤로가기</button>
            <div class="flex gap-2">
              <button
                type="button"
                class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                :disabled="registerLoading"
                @click="handleVerificationSkip"
              >
                건너뛰기
              </button>
              <button
                type="button"
                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                :disabled="!verificationComplete || registerLoading"
                @click="handleVerificationConfirm"
              >
                <span v-if="registerLoading" class="flex items-center gap-2">
                  <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  확인 중...
                </span>
                <span v-else>확인</span>
              </button>
            </div>
          </div>
          <div v-if="verificationError" class="text-sm text-red-600">{{ verificationError }}</div>
        </template>

        <template v-else-if="registerStep === REGISTER_STEPS.COMPLETE">
          <div class="space-y-4">
            <p class="text-sm text-gray-600">새 지갑이 성공적으로 생성되었습니다.</p>
            <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-2">
              <div class="text-sm text-gray-700"><span class="font-semibold text-gray-900">지갑 이름:</span> {{ registerSuccess?.wallet_name }}</div>
              <div class="text-sm text-gray-700"><span class="font-semibold text-gray-900">지갑 ID:</span> <span class="font-mono text-xs">{{ registerSuccess?.wallet_id }}</span></div>
              <div class="text-sm text-gray-700"><span class="font-semibold text-gray-900">생성일:</span> {{ formatDate(registerSuccess?.created_at) }}</div>
              <div class="text-sm text-gray-700">
                <span class="font-semibold text-gray-900">니모닉</span>
                <div class="grid sm:grid-cols-2 gap-2 mt-2">
                  <div
                    v-for="(word, idx) in registerSuccessMnemonic"
                    :key="`summary-word-${idx}`"
                    class="flex items-center gap-3 bg-white border border-gray-200 rounded-lg px-3 py-2"
                  >
                    <span class="w-6 text-xs font-semibold text-gray-500">{{ idx + 1 }}</span>
                    <span class="font-mono text-sm text-gray-900">{{ word }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="flex flex-wrap gap-2">
              <button
                type="button"
                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                @click="handleCompleteToVerify"
              >
                지갑 목록으로
              </button>
              <button
                type="button"
                class="px-4 py-2 text-sm text-gray-600 hover:text-gray-900"
                @click="handleCompleteNew"
              >
                새 지갑 추가
              </button>
            </div>
          </div>
        </template>

          </div>

          <div
            v-if="showStandardWarning"
            class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
          >
            <div class="bg-white rounded-xl shadow-xl max-w-sm w-full p-6 space-y-4">
              <h3 class="text-lg font-semibold text-gray-900">주변을 확인하세요</h3>
              <p class="text-sm text-gray-600">시드 문구는 누구와도 공유하지 마세요. 주변에 다른 사람이 없는지 확인한 후 진행하세요.</p>
              <div class="flex justify-end gap-2">
                <button type="button" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-900" @click="handleCancelStandard">취소</button>
                <button type="button" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700" @click="handleConfirmStandard">확인</button>
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import WalletMenuTabs from '../components/WalletMenuTabs.vue'
import * as bip39 from 'bip39'
import {
  apiGetKingstoneWallets,
  apiRegisterKingstonePin,
  apiVerifyKingstonePin,
  apiGenerateMnemonic
} from '../api'

const PIN_LENGTH = 6
const REGISTER_STEPS = Object.freeze({
  PIN: 'pin',
  NAME: 'name',
  METHOD: 'method',
  MNEMONIC: 'mnemonic',
  VERIFY: 'verify',
  COMPLETE: 'complete'
})
const REGISTER_STEP_TITLES = {
  [REGISTER_STEPS.PIN]: '1단계: 핀번호 설정',
  [REGISTER_STEPS.NAME]: '2단계: 지갑 이름',
  [REGISTER_STEPS.METHOD]: '3단계: 백업 방식 선택',
  [REGISTER_STEPS.MNEMONIC]: '4단계: 시드 문구 확인',
  [REGISTER_STEPS.VERIFY]: '5단계: 시드 문구 검증',
  [REGISTER_STEPS.COMPLETE]: '지갑 생성 완료'
}
const bip39Wordlist = bip39.wordlists?.english || []
const router = useRouter()

const wallets = ref([])
const walletLimit = ref(3)
const loadingWallets = ref(false)
const loadError = ref('')

const mode = ref('verify')
const pinInput = ref('')
const verifyError = ref('')
const verifyLoading = ref(false)
const pinStatusMessage = computed(() => {
  if (verifyLoading.value) return '확인 중...'
  return '핀번호를 입력하면 지갑이 자동으로 열립니다.'
})

const registerPin = ref('')
const registerStep = ref(REGISTER_STEPS.PIN)
const registerError = ref('')
const registerLoading = ref(false)
const registerSuccess = ref(null)
const registerSuccessMnemonic = ref([])

const walletNameInput = ref('')
const showStandardWarning = ref(false)
const mnemonicLength = ref(12)
const registerMnemonicWords = ref([])
const verificationOptions = ref([])
const verificationSelection = ref([])
const verificationError = ref('')

const username = computed(() => localStorage.getItem('nickname') || 'anonymous')
const hasWallets = computed(() => wallets.value.length > 0)
const canRegister = computed(() => wallets.value.length < walletLimit.value)
const registerStepTitle = computed(() => REGISTER_STEP_TITLES[registerStep.value] || '지갑 생성')
const verificationComplete = computed(() => registerMnemonicWords.value.length > 0 && verificationSelection.value.length === registerMnemonicWords.value.length)

const orderedWallets = computed(() => {
  return [...wallets.value].sort((a, b) => (a.index || 0) - (b.index || 0))
})

const nextWalletName = computed(() => {
  const used = new Set(wallets.value.map(w => w.index))
  for (let i = 1; i <= walletLimit.value; i += 1) {
    if (!used.has(i)) return `지갑${i}`
  }
  return `지갑${walletLimit.value}`
})

const formatDate = (iso) => {
  if (!iso) return '-'
  try {
    const d = new Date(iso)
    if (Number.isNaN(d.getTime())) return '-'
    return d.toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' })
  } catch (e) {
    return '-'
  }
}

const shuffleArray = (array) => array
  .map(item => ({ item, sort: Math.random() }))
  .sort((a, b) => a.sort - b.sort)
  .map(({ item }) => item)

const generateNewMnemonic = async () => {
  try {
    // Always use server-side generation to avoid Buffer issues
    const response = await apiGenerateMnemonic()
    if (response.success && response.mnemonic) {
      const words = response.mnemonic.trim().split(/\s+/)
      // Server returns 12-word mnemonic, use it directly
      registerMnemonicWords.value = words.slice(0, mnemonicLength.value)

      // If 24 words requested but server returned 12, generate another one
      if (mnemonicLength.value === 24 && words.length === 12) {
        const response2 = await apiGenerateMnemonic()
        if (response2.success && response2.mnemonic) {
          const words2 = response2.mnemonic.trim().split(/\s+/)
          registerMnemonicWords.value = [...words, ...words2].slice(0, 24)
        }
      }
    } else {
      throw new Error(response.error || 'Failed to generate mnemonic')
    }
  } catch (error) {
    console.error('Failed to generate mnemonic:', error)
    alert('니모닉 생성에 실패했습니다. 다시 시도해주세요.')
    registerMnemonicWords.value = []
  }
  verificationOptions.value = []
  verificationSelection.value = []
  verificationError.value = ''
}

const prepareVerification = () => {
  if (!registerMnemonicWords.value.length) return
  const options = registerMnemonicWords.value.map((word, index) => ({ word, correctIndex: index, selectedOrder: 0 }))
  verificationOptions.value = shuffleArray(options)
  verificationSelection.value = []
  verificationError.value = ''
}

const resetVerificationSelections = () => {
  verificationOptions.value = verificationOptions.value.map(option => ({ ...option, selectedOrder: 0 }))
  verificationSelection.value = []
  verificationError.value = ''
}

const handleVerificationReset = () => {
  prepareVerification()
}

const handleSelectVerificationWord = (option) => {
  if (option.selectedOrder || registerLoading.value) return
  if (verificationSelection.value.length >= registerMnemonicWords.value.length) return
  option.selectedOrder = verificationSelection.value.length + 1
  verificationSelection.value = [...verificationSelection.value, option.word]
}

const resetRegisterState = () => {
  registerStep.value = REGISTER_STEPS.PIN
  registerLoading.value = false
  registerSuccess.value = null
  registerSuccessMnemonic.value = []
  walletNameInput.value = ''
  mnemonicLength.value = 12
  registerMnemonicWords.value = []
  verificationOptions.value = []
  verificationSelection.value = []
  verificationError.value = ''
  registerError.value = ''
  showStandardWarning.value = false
  registerPin.value = ''
}

const switchToRegister = (message = '', { preservePinValue = '' } = {}) => {
  if (!canRegister.value) {
    registerError.value = `핀번호는 최대 ${walletLimit.value}개까지 등록할 수 있습니다.`
    mode.value = 'verify'
    return
  }
  mode.value = 'register'
  clearPin('verify')
  resetRegisterState()
  if (preservePinValue) {
    registerPin.value = preservePinValue.slice(0, PIN_LENGTH)
  }
  registerError.value = message
}

const switchToVerify = () => {
  mode.value = 'verify'
  resetRegisterState()
  verifyError.value = ''
  clearPin('verify')
  clearPin('register')
}

const loadWallets = async () => {
  loadingWallets.value = true
  loadError.value = ''
  try {
    const result = await apiGetKingstoneWallets(username.value)
    if (result.success) {
      wallets.value = Array.isArray(result.wallets) ? result.wallets : []
      walletLimit.value = result.limit ?? 3
      if (!wallets.value.length) {
        clearPin('verify')
      }
    } else {
      loadError.value = result.error || '지갑 정보를 불러오지 못했습니다.'
    }
  } catch (error) {
    loadError.value = '지갑 정보를 불러오지 못했습니다.'
  } finally {
    loadingWallets.value = false
  }
}

const handleVerify = async () => {
  if (verifyLoading.value) return
  verifyError.value = ''

  if (pinInput.value.length !== PIN_LENGTH || !/^\d+$/.test(pinInput.value)) {
    verifyError.value = `핀번호는 ${PIN_LENGTH}자리 숫자여야 합니다.`
    return
  }

  verifyLoading.value = true
  try {
    const result = await apiVerifyKingstonePin(username.value, pinInput.value)
    if (result.success && result.wallet) {
      verifyError.value = ''
      router.push({
        name: 'wallet-kingstone-detail',
        params: { id: result.wallet.wallet_id },
        query: { name: result.wallet.wallet_name }
      })
    } else {
      const message = result.error || '핀번호 확인에 실패했습니다.'
      verifyError.value = message
    }
  } catch (error) {
    verifyError.value = '핀번호 확인 중 문제가 발생했습니다.'
  } finally {
    verifyLoading.value = false
  }
}

const handleRegisterBackToVerify = () => {
  switchToVerify()
}

const handlePinNext = () => {
  if (registerPin.value.length !== PIN_LENGTH || !/^\d+$/.test(registerPin.value)) {
    registerError.value = `핀번호는 ${PIN_LENGTH}자리 숫자여야 합니다.`
    return
  }
  registerError.value = ''
  registerStep.value = REGISTER_STEPS.NAME
}

const handleNameBack = () => {
  registerError.value = ''
  registerStep.value = REGISTER_STEPS.PIN
}

const handleNameNext = () => {
  if (!walletNameInput.value.trim()) {
    registerError.value = '지갑 이름을 입력하세요.'
    return
  }
  registerError.value = ''
  registerStep.value = REGISTER_STEPS.METHOD
}

const handleMethodBack = () => {
  registerError.value = ''
  registerStep.value = REGISTER_STEPS.NAME
}

const handleSelectStandard = () => {
  registerError.value = ''
  showStandardWarning.value = true
}

const handleCancelStandard = () => {
  showStandardWarning.value = false
}

const handleConfirmStandard = () => {
  showStandardWarning.value = false
  if (!registerMnemonicWords.value.length) {
    generateNewMnemonic()
  }
  registerError.value = ''
  registerStep.value = REGISTER_STEPS.MNEMONIC
}

const handleMnemonicLengthChange = (length) => {
  if (mnemonicLength.value === length) return
  mnemonicLength.value = length
  generateNewMnemonic()
}

const handleMnemonicRefresh = () => {
  generateNewMnemonic()
}

const handleMnemonicBack = () => {
  registerError.value = ''
  registerStep.value = REGISTER_STEPS.METHOD
}

const handleMnemonicNext = () => {
  if (!registerMnemonicWords.value.length) {
    generateNewMnemonic()
  }
  registerError.value = ''
  registerStep.value = REGISTER_STEPS.VERIFY
  prepareVerification()
}

const handleVerificationBack = () => {
  registerError.value = ''
  registerStep.value = REGISTER_STEPS.MNEMONIC
  resetVerificationSelections()
}

const handleVerificationConfirm = async () => {
  if (!verificationComplete.value) {
    verificationError.value = '모든 단어를 순서대로 선택하세요.'
    return
  }
  const isMatch = verificationSelection.value.every((word, index) => word === registerMnemonicWords.value[index])
  if (!isMatch) {
    verificationError.value = '선택한 순서가 올바르지 않습니다. 새로고침하여 다시 시도하세요.'
    return
  }
  verificationError.value = ''
  await submitRegister()
}

const handleVerificationSkip = async () => {
  verificationError.value = ''
  await submitRegister()
}

const submitRegister = async () => {
  if (!canRegister.value) {
    registerError.value = `핀번호는 최대 ${walletLimit.value}개까지 등록할 수 있습니다.`
    return
  }
  if (registerPin.value.length !== PIN_LENGTH || !/^\d+$/.test(registerPin.value)) {
    registerError.value = `핀번호는 ${PIN_LENGTH}자리 숫자여야 합니다.`
    registerStep.value = REGISTER_STEPS.PIN
    return
  }

  const safeWalletName = walletNameInput.value.trim() || nextWalletName.value

  registerLoading.value = true
  registerError.value = ''
  try {
    const result = await apiRegisterKingstonePin(username.value, registerPin.value, {
      walletName: safeWalletName,
      mnemonic: registerMnemonicWords.value.join(' ')
    })
    if (result.success && result.wallet) {
      registerSuccess.value = result.wallet
      registerSuccessMnemonic.value = [...registerMnemonicWords.value]
      registerPin.value = ''
      walletNameInput.value = safeWalletName
      await loadWallets()

      // 바로 생성된 지갑 페이지로 이동
      router.push({
        name: 'wallet-kingstone-detail',
        params: { id: result.wallet.wallet_id },
        query: { name: result.wallet.wallet_name }
      })
    } else {
      registerError.value = result.error || '핀번호 등록에 실패했습니다.'
      if (result.code === 'duplicate_pin') {
        switchToVerify()
      }
    }
  } catch (error) {
    registerError.value = '핀번호 등록 중 문제가 발생했습니다.'
  } finally {
    registerLoading.value = false
  }
}

const handleCompleteToVerify = () => {
  switchToVerify()
  loadWallets()
  if (registerSuccess.value?.wallet_id) {
    router.push(`/wallet/kingstone/${registerSuccess.value.wallet_id}`)
  }
}

const handleCompleteNew = () => {
  switchToRegister()
}

const getPinRef = (target) => (target === 'register' ? registerPin : pinInput)

const appendDigit = (target, digit) => {
  const ref = getPinRef(target)
  if (ref.value.length >= PIN_LENGTH) return
  ref.value += digit
  if (target === 'verify' && ref.value.length === PIN_LENGTH && !verifyLoading.value) {
    void handleVerify()
  }
}

const removeDigit = (target) => {
  const ref = getPinRef(target)
  if (!ref.value.length) return
  ref.value = ref.value.slice(0, -1)
  if (target === 'verify') {
    verifyError.value = ''
  }
}

const clearPin = (target) => {
  const ref = getPinRef(target)
  ref.value = ''
  if (target === 'verify') {
    verifyError.value = ''
  }
}

onMounted(() => {
  loadWallets()
})
</script>

<style scoped>
.device-wrapper {
  display: flex;
  justify-content: center;
  width: 100%;
}

.device-frame {
  position: relative;
  width: min(100%, 360px);
  background: linear-gradient(180deg, #1f2937 0%, #111827 100%);
  border-radius: 34px;
  padding: 18px 14px 20px;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.35);
  border: 1px solid rgba(148, 163, 184, 0.25);
}

.device-notch {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  width: 40%;
  height: 6px;
  background: rgba(148, 163, 184, 0.65);
  border-radius: 9999px;
}

.device-screen {
  background: #f9fafb;
  border-radius: 24px;
  padding: 24px 20px 28px;
  min-height: 640px;
  overflow-y: auto;
}
</style>
