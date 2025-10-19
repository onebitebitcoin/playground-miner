<template>
  <div>
    <WalletMenuTabs active="kingstone" />
    <div class="device-wrapper">
      <div class="device-frame">
        <div class="device-notch"></div>
        <div class="device-screen">
        <!-- Receive Address Screen -->
        <div v-if="receiveOpen" class="screen-content-full">
          <div class="flex items-center justify-between mb-2">
            <button
              type="button"
              class="p-2 text-gray-600 hover:text-gray-900"
              @click="closeReceive"
              title="뒤로가기"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
              <span class="sr-only">뒤로가기</span>
            </button>
            <h2 class="text-lg font-semibold text-gray-900">받기</h2>
            <div class="w-9"></div>
          </div>

          <div v-if="receiveLoading" class="flex items-center justify-center py-12">
            <svg class="w-8 h-8 animate-spin text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </div>

          <div v-else-if="receiveError" class="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
            {{ receiveError }}
          </div>

          <div v-else-if="receiveAddress" class="space-y-3">
            <div class="bg-white border border-gray-200 rounded-xl p-4 flex flex-col items-center gap-2">
              <div class="w-60 h-60 bg-white flex items-center justify-center border border-gray-200 rounded-xl" ref="receiveQrContainer">
                <!-- QR code will be rendered here -->
              </div>
              <div class="text-center w-full">
                <p class="text-xs text-gray-500 break-all font-mono px-2">{{ receiveAddress }}</p>
              </div>
            </div>

            <button
              type="button"
              class="w-full px-4 py-3 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center justify-between"
              @click="goToAddressList"
            >
              <span class="text-sm text-gray-700">주소-{{ receiveAddressIndex }}</span>
              <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Address List Screen -->
        <div v-else-if="addressListOpen" class="screen-content-full">
          <div class="flex items-center justify-between mb-4">
            <button
              type="button"
              class="p-2 text-gray-600 hover:text-gray-900"
              @click="closeAddressList"
              title="뒤로가기"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
              <span class="sr-only">뒤로가기</span>
            </button>
            <h2 class="text-lg font-semibold text-gray-900">주소 목록</h2>
            <div class="w-9"></div>
          </div>

          <div v-if="addressListLoading" class="flex items-center justify-center py-12">
            <svg class="w-8 h-8 animate-spin text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </div>

          <div v-else class="space-y-2">
            <div
              v-for="addr in addressList"
              :key="addr.index"
              class="bg-white border border-gray-200 rounded-lg p-4"
            >
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-gray-700">주소-{{ addr.index }}</span>
              </div>
              <p class="text-xs text-gray-500 break-all font-mono">{{ addr.address }}</p>
            </div>
          </div>
        </div>

        <!-- Main Content Screen -->
        <div v-else class="screen-content space-y-6">
          <!-- Main Header - only show when no sub-screen is open -->
          <div v-if="!softwareDialogOpen && !deviceSettingsOpen && !walletSettingsOpen" class="flex items-start justify-between gap-3">
            <div class="flex-1">
              <h1 class="text-2xl font-bold text-gray-900">{{ walletNameDisplay }}</h1>
            </div>

            <div class="flex items-center gap-2">
              <button
                type="button"
                class="p-2 text-gray-700 border border-gray-200 rounded-lg hover:text-red-600 hover:border-red-300"
                @click="goBack"
                title="전원 끄기"
              >
                <span class="sr-only">전원 끄기</span>
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>

              <div class="relative">
                <button
                  type="button"
                  class="p-2 text-gray-700 border border-gray-200 rounded-lg hover:text-gray-900 hover:border-gray-300"
                  @click="toggleSettings"
                  title="메뉴"
                >
                  <span class="sr-only">메뉴</span>
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                  </svg>
                </button>

                <div
                  v-if="settingsOpen"
                  class="absolute right-0 mt-2 w-56 bg-white border border-gray-200 rounded-lg shadow-xl z-20"
                >
                  <button
                    type="button"
                    class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-t-lg"
                    @click="openSoftwareDialog"
                  >
                    소프트웨어 지갑 연결하기
                  </button>
                  <button
                    type="button"
                    class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-b-lg"
                    @click="openDeviceSettings"
                  >
                    디바이스 설정
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div v-if="deviceSettingsOpen && !walletSettingsOpen" class="space-y-4">
            <div class="flex items-center justify-between">
              <button
                type="button"
                class="p-2 text-gray-600 hover:text-gray-900"
                @click="closeDeviceSettings"
                title="뒤로가기"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                </svg>
                <span class="sr-only">뒤로가기</span>
              </button>
              <h2 class="text-lg font-semibold text-gray-900">디바이스 설정</h2>
              <div class="w-9"></div>
            </div>
            <div class="space-y-2">
              <button
                type="button"
                class="w-full px-4 py-3 text-left rounded-lg border border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50 transition"
                @click="openWalletSettings"
              >
                <div class="font-medium text-gray-900">지갑 설정</div>
              </button>
              <button
                type="button"
                class="w-full px-4 py-3 text-left rounded-lg border border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed"
                disabled
              >
                <div class="font-medium">시스템 설정 (준비 중)</div>
              </button>
              <button
                type="button"
                class="w-full px-4 py-3 text-left rounded-lg border border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed"
                disabled
              >
                <div class="font-medium">연결 (준비 중)</div>
              </button>
            </div>
          </div>

          <div v-if="walletSettingsOpen" class="space-y-4">
            <div class="flex items-center justify-between">
              <button
                type="button"
                class="p-2 text-gray-600 hover:text-gray-900"
                @click="backToDeviceSettings"
                title="뒤로가기"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                </svg>
                <span class="sr-only">뒤로가기</span>
              </button>
              <h2 class="text-lg font-semibold text-gray-900">지갑 설정</h2>
              <div class="relative">
                <button
                  type="button"
                  class="p-2 text-gray-700 hover:text-gray-900"
                  @click="toggleWalletMenu"
                  title="메뉴"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                  </svg>
                  <span class="sr-only">메뉴</span>
                </button>
                <div
                  v-if="walletMenuOpen"
                  class="absolute right-0 mt-2 w-40 bg-white border border-gray-200 rounded-lg shadow-xl z-20"
                >
                  <button
                    type="button"
                    class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg"
                    @click="confirmDeleteWallet"
                  >
                    지갑 삭제
                  </button>
                </div>
              </div>
            </div>
            <div class="text-sm text-gray-600 p-4 bg-gray-50 rounded-lg">
              지갑 정보를 관리합니다.
            </div>
          </div>

          <!-- Software Wallet Selection -->
          <div v-if="softwareDialogOpen && !showZpubQR" class="space-y-4">
            <div class="flex items-center justify-between">
              <button
                type="button"
                class="p-2 text-gray-600 hover:text-gray-900"
                @click="closeSoftwareDialog"
                title="뒤로가기"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                </svg>
                <span class="sr-only">뒤로가기</span>
              </button>
              <h2 class="text-lg font-semibold text-gray-900">지갑을 선택하세요</h2>
              <div class="w-9"></div>
            </div>
            <div class="space-y-2">
              <button
                v-for="option in softwareOptions"
                :key="option.id"
                type="button"
                class="w-full px-4 py-3 text-left rounded-lg border transition"
                :class="selectedSoftware === option.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50'"
                @click="selectSoftware(option.id)"
              >
                <div class="font-medium text-gray-900">{{ option.label }}</div>
              </button>
            </div>
          </div>

          <!-- Zpub QR Code Screen -->
          <div v-if="softwareDialogOpen && showZpubQR" class="space-y-4">
            <div class="flex items-center justify-between">
              <button
                type="button"
                class="p-2 text-gray-600 hover:text-gray-900"
                @click="backToSoftwareSelection"
                title="뒤로가기"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                </svg>
                <span class="sr-only">뒤로가기</span>
              </button>
              <h2 class="text-lg font-semibold text-gray-900">{{ softwareLabel }}</h2>
              <div class="w-9"></div>
            </div>

            <div v-if="zpubLoading" class="flex items-center justify-center py-12">
              <div class="flex items-center gap-2 text-gray-600">
                <svg class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>QR 코드 생성 중...</span>
              </div>
            </div>

            <div v-else-if="zpubError" class="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
              {{ zpubError }}
            </div>

            <div v-else-if="zpubValue" class="space-y-3">
              <div class="bg-white border border-gray-200 rounded-xl p-4 flex flex-col items-center gap-2">
                <div class="w-60 h-60 bg-white flex items-center justify-center border border-gray-200 rounded-xl" ref="qrContainer">
                  <!-- QR code will be rendered here -->
                </div>
              </div>
              <div class="text-center">
                <p class="text-xs text-gray-500 break-all font-mono px-2">{{ zpubValue }}</p>
              </div>
            </div>
          </div>

          <!-- Fixed Bottom Buttons -->
          <div v-if="!softwareDialogOpen && !deviceSettingsOpen && !walletSettingsOpen" class="fixed-bottom-buttons">
            <button
              type="button"
              class="w-full px-4 py-3 bg-gray-200 text-gray-700 text-base font-semibold rounded-lg hover:bg-gray-300"
              @click="openReceive"
            >
              받기
            </button>
            <button
              type="button"
              class="w-full px-4 py-3 bg-orange-500 text-white text-base font-semibold rounded-lg hover:bg-orange-600"
            >
              스캔
            </button>
          </div>
        </div>

        <!-- Delete Confirmation Modal -->
        <div v-if="showDeleteModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div class="bg-white rounded-xl shadow-xl max-w-sm w-full p-6 space-y-4">
            <h3 class="text-lg font-semibold text-gray-900">지갑을 삭제하시겠습니까?</h3>
            <p class="text-sm text-gray-600">이 작업은 되돌릴 수 없습니다. 지갑의 모든 정보가 삭제됩니다.</p>
            <div class="flex justify-end gap-2">
              <button
                type="button"
                class="px-4 py-2 text-sm text-gray-600 hover:text-gray-900"
                @click="cancelDeleteWallet"
                :disabled="deleteLoading"
              >
                취소
              </button>
              <button
                type="button"
                class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                @click="executeDeleteWallet"
                :disabled="deleteLoading"
              >
                <span v-if="deleteLoading" class="flex items-center gap-2">
                  <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  삭제 중...
                </span>
                <span v-else>확인</span>
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { computed, reactive, ref, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import WalletMenuTabs from '../components/WalletMenuTabs.vue'
import QRCode from 'qrcode'
import { apiGetKingstoneWallets, apiGetKingstoneWalletAddress } from '../api'

const route = useRoute()
const router = useRouter()

const walletId = computed(() => route.params.id ? String(route.params.id) : '')
const walletNameDisplay = computed(() => route.query.name ? String(route.query.name) : '상세')

const settingsOpen = ref(false)
const softwareDialogOpen = ref(false)
const deviceSettingsOpen = ref(false)
const walletSettingsOpen = ref(false)
const walletMenuOpen = ref(false)
const showDeleteModal = ref(false)
const deleteLoading = ref(false)
const selectedSoftware = ref('')
const zpubValue = ref('')
const zpubLoading = ref(false)
const zpubError = ref('')
const qrContainer = ref(null)
const showZpubQR = ref(false)

// Receive address states
const receiveOpen = ref(false)
const receiveAddress = ref('')
const receiveAddressIndex = ref(0)
const receiveQrContainer = ref(null)
const receiveLoading = ref(false)
const receiveError = ref('')

// Address list states
const addressListOpen = ref(false)
const addressList = ref([])
const addressListLoading = ref(false)

const softwareOptions = reactive([
  { id: 'bluewallet', label: 'BlueWallet' },
  { id: 'sparrow', label: 'Sparrow' },
  { id: 'nunchuk', label: 'Nunchuk' }
])

const softwareLabel = computed(() => softwareOptions.find(opt => opt.id === selectedSoftware.value)?.label || '선택되지 않음')

const toggleSettings = () => {
  settingsOpen.value = !settingsOpen.value
}

const openSoftwareDialog = () => {
  softwareDialogOpen.value = true
  settingsOpen.value = false
  selectedSoftware.value = ''
  zpubValue.value = ''
  zpubError.value = ''
}

const closeSoftwareDialog = () => {
  softwareDialogOpen.value = false
  selectedSoftware.value = ''
  zpubValue.value = ''
  zpubError.value = ''
}

const openDeviceSettings = () => {
  deviceSettingsOpen.value = true
  settingsOpen.value = false
}

const closeDeviceSettings = () => {
  deviceSettingsOpen.value = false
  walletSettingsOpen.value = false
  walletMenuOpen.value = false
}

const openWalletSettings = () => {
  walletSettingsOpen.value = true
}

const backToDeviceSettings = () => {
  walletSettingsOpen.value = false
  walletMenuOpen.value = false
}

const toggleWalletMenu = () => {
  walletMenuOpen.value = !walletMenuOpen.value
}

const confirmDeleteWallet = () => {
  walletMenuOpen.value = false
  showDeleteModal.value = true
}

const cancelDeleteWallet = () => {
  showDeleteModal.value = false
}

const executeDeleteWallet = async () => {
  if (!walletId.value) return

  deleteLoading.value = true
  try {
    const username = localStorage.getItem('nickname') || 'anonymous'
    // Call delete API (to be implemented in backend)
    const response = await fetch(`/api/kingstone/wallet/delete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        username,
        wallet_id: walletId.value
      })
    })

    const result = await response.json()
    if (result.ok) {
      // Redirect to kingstone wallet page
      router.push('/wallet/kingstone')
    } else {
      alert(result.error || '지갑 삭제에 실패했습니다')
    }
  } catch (error) {
    console.error('Failed to delete wallet:', error)
    alert('네트워크 오류가 발생했습니다')
  } finally {
    deleteLoading.value = false
    showDeleteModal.value = false
  }
}

const loadZpub = async () => {
  if (!walletId.value) return

  zpubLoading.value = true
  zpubError.value = ''
  zpubValue.value = ''

  try {
    const username = localStorage.getItem('nickname') || 'anonymous'
    const result = await apiGetKingstoneWallets(username)

    console.log('API result:', result)
    console.log('Looking for walletId:', walletId.value)

    if (result.success && result.wallets) {
      console.log('Wallets:', result.wallets)
      const wallet = result.wallets.find(w => w.wallet_id === walletId.value)
      console.log('Found wallet:', wallet)

      if (wallet) {
        if (wallet.zpub) {
          zpubValue.value = wallet.zpub
          zpubLoading.value = false

          // Wait for DOM to render with zpubValue
          await nextTick()
          await nextTick()
          await nextTick()

          await generateQRCode(wallet.zpub)
        } else {
          zpubError.value = `zpub 정보를 찾을 수 없습니다. 지갑 데이터: ${JSON.stringify(wallet)}`
          zpubLoading.value = false
        }
      } else {
        zpubError.value = `지갑 ID ${walletId.value}를 찾을 수 없습니다. 사용 가능한 지갑: ${result.wallets.map(w => w.wallet_id).join(', ')}`
        zpubLoading.value = false
      }
    } else {
      zpubError.value = result.error || '지갑 정보를 불러올 수 없습니다'
      zpubLoading.value = false
    }
  } catch (error) {
    console.error('Error loading zpub:', error)
    zpubError.value = `네트워크 오류: ${error.message}`
    zpubLoading.value = false
  }
}

const generateQRCode = async (data) => {
  await nextTick()
  await nextTick() // Extra tick for modal rendering

  if (!qrContainer.value) {
    console.error('qrContainer is null')
    return
  }

  // Clear previous QR code
  while (qrContainer.value.firstChild) {
    qrContainer.value.removeChild(qrContainer.value.firstChild)
  }

  try {
    // Create canvas element
    const canvas = document.createElement('canvas')

    // Generate QR code on the canvas
    await QRCode.toCanvas(canvas, data, {
      width: 240,
      margin: 1,
      color: {
        dark: '#000000',
        light: '#FFFFFF'
      }
    })

    qrContainer.value.appendChild(canvas)
    console.log('QR code generated successfully')
  } catch (error) {
    console.error('Failed to generate QR code:', error)
    zpubError.value = 'QR 코드 생성에 실패했습니다'
  }
}

const selectSoftware = async (id) => {
  selectedSoftware.value = id
  showZpubQR.value = true
  await loadZpub()
}

const backToSoftwareSelection = () => {
  showZpubQR.value = false
  zpubValue.value = ''
  zpubError.value = ''
  selectedSoftware.value = ''
}

const goBack = () => {
  router.push('/wallet/kingstone')
}

// Receive address functions
const openReceive = async () => {
  receiveOpen.value = true
  receiveLoading.value = true
  receiveError.value = ''
  receiveAddress.value = ''
  receiveAddressIndex.value = 0

  try {
    const username = localStorage.getItem('nickname') || 'anonymous'

    // Get address at index 0 directly from wallet
    const addressResult = await apiGetKingstoneWalletAddress(username, walletId.value, { index: 0, account: 0, change: 0 })

    if (addressResult.success && addressResult.address) {
      receiveAddress.value = addressResult.address
      receiveAddressIndex.value = addressResult.index
      receiveLoading.value = false

      // Wait for DOM to update with the address
      await nextTick()
      await nextTick() // Extra nextTick to ensure DOM is ready

      await generateReceiveQRCode(addressResult.address)
    } else {
      receiveError.value = addressResult.error || '주소를 불러올 수 없습니다'
      receiveLoading.value = false
    }
  } catch (error) {
    console.error('Error loading receive address:', error)
    receiveError.value = `네트워크 오류: ${error.message}`
    receiveLoading.value = false
  }
}

const closeReceive = () => {
  receiveOpen.value = false
  receiveAddress.value = ''
  receiveError.value = ''
}

const generateReceiveQRCode = async (address) => {
  await nextTick()
  if (!receiveQrContainer.value) {
    console.error('receiveQrContainer is null')
    return
  }

  // Clear previous QR code
  while (receiveQrContainer.value.firstChild) {
    receiveQrContainer.value.removeChild(receiveQrContainer.value.firstChild)
  }

  try {
    // Create canvas element
    const canvas = document.createElement('canvas')

    // Generate QR code on the canvas
    await QRCode.toCanvas(canvas, address, {
      width: 240,
      margin: 1,
      color: {
        dark: '#000000',
        light: '#FFFFFF'
      }
    })

    receiveQrContainer.value.appendChild(canvas)
    console.log('QR code generated successfully')
  } catch (error) {
    console.error('Failed to generate receive QR code:', error)
    receiveError.value = 'QR 코드 생성에 실패했습니다'
  }
}

const openAddressList = async () => {
  addressListOpen.value = true
  addressListLoading.value = true
  addressList.value = []

  try {
    const username = localStorage.getItem('nickname') || 'anonymous'

    // Load addresses 0-4 directly from wallet
    const addresses = []
    for (let i = 0; i < 5; i++) {
      const addressResult = await apiGetKingstoneWalletAddress(username, walletId.value, { index: i, account: 0, change: 0 })
      if (addressResult.success && addressResult.address) {
        addresses.push({
          index: i,
          address: addressResult.address
        })
      }
    }
    addressList.value = addresses
  } catch (error) {
    console.error('Error loading address list:', error)
  } finally {
    addressListLoading.value = false
  }
}

const closeAddressList = () => {
  addressListOpen.value = false
  addressList.value = []
}

const goToAddressList = () => {
  closeReceive()
  openAddressList()
}

// Watch for software dialog close to reset state
watch(softwareDialogOpen, (isOpen) => {
  if (!isOpen) {
    selectedSoftware.value = ''
    zpubValue.value = ''
    zpubError.value = ''
  }
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
  position: relative;
  background: #f9fafb;
  border-radius: 24px;
  min-height: 640px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.screen-content {
  flex: 1;
  padding: 24px 20px 0;
  padding-bottom: 140px; /* Space for fixed buttons */
}

.screen-content-full {
  flex: 1;
  padding: 12px 20px 20px;
}

.fixed-bottom-buttons {
  position: sticky;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 20px;
  background: linear-gradient(to top, #f9fafb 85%, transparent);
  border-radius: 0 0 24px 24px;
}
</style>
