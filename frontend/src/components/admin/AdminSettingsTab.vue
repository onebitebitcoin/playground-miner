<template>
  <div class="space-y-6">
    <div class="bg-white rounded-lg shadow-md p-6 max-w-xl">
      <h3 class="text-lg font-semibold text-gray-900 mb-2">사이드바 메뉴 설정</h3>
      <p class="text-sm text-gray-600 mb-4">사용자에게 보여질 사이드바 메뉴를 설정합니다.</p>

      <div v-if="sidebarConfigLoading" class="text-center py-8 text-gray-500">
        로딩 중...
      </div>

      <div v-else class="space-y-4">
        <div
          v-for="option in sidebarOptions"
          :key="option.key"
          class="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
        >
          <div>
            <h4 class="font-medium text-gray-900">{{ option.label }}</h4>
            <p class="text-sm text-gray-500">{{ option.description }}</p>
          </div>
          <button
            :disabled="!isAdmin"
            @click="toggleSidebarItem(option.key)"
            :class="[
              sidebarConfig[option.key] ? 'bg-blue-600' : 'bg-gray-300',
              'relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
            ]"
          >
            <span
              :class="[
                sidebarConfig[option.key] ? 'translate-x-6' : 'translate-x-1',
                'inline-block h-4 w-4 transform rounded-full bg-white transition-transform'
              ]"
            />
          </button>
        </div>
      </div>
    </div>

    <div class="bg-white rounded-lg shadow-md p-6 max-w-xl">
      <h3 class="text-lg font-semibold text-gray-900 mb-2">비밀번호 설정</h3>
      <p class="text-sm text-gray-600 mb-4">페이지 접근 관련 비밀번호를 관리합니다.</p>

      <div class="p-4 border border-gray-200 rounded-lg space-y-3">
        <div class="flex items-center justify-between mb-3">
          <h4 class="font-medium text-gray-900">지갑 페이지</h4>
        </div>
        <div class="text-sm text-gray-600">
          현재 비밀번호:
          <span class="font-mono text-gray-800">{{ displayWalletPassword }}</span>
        </div>
        <div class="flex flex-col sm:flex-row gap-2">
          <input
            v-model="walletPasswordInput"
            type="password"
            class="flex-1 px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-gray-300 focus:border-gray-500 outline-none"
            placeholder="새 비밀번호 (빈칸 입력 시 해제)"
          />
          <button
            @click="saveWalletPassword"
            :disabled="savingWalletPassword || !isAdmin"
            class="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ savingWalletPassword ? '저장 중...' : '저장' }}
          </button>
        </div>
        <div
          v-if="!isAdmin"
          class="text-xs text-yellow-700 bg-yellow-50 border border-yellow-200 rounded p-2"
        >
          관리자 권한이 아닙니다. 설정은 비활성화됩니다.
        </div>
        <div
          v-if="walletPasswordMessage"
          class="text-sm"
          :class="walletPasswordMessage.includes('성공') ? 'text-green-700' : 'text-red-600'"
        >
          {{ walletPasswordMessage }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { apiGetWalletPassword, apiSetWalletPassword, apiGetSidebarConfig, apiUpdateSidebarConfig } from '../../api'
import { getCurrentUsername } from '../../utils/adminAuth'

const props = defineProps({
  isAdmin: { type: Boolean, default: false },
  showSuccess: { type: Function, required: true },
  showError: { type: Function, required: true }
})

const sidebarConfig = ref({
  show_mining: true,
  show_utxo: true,
  show_wallet: true,
  show_fee: true,
  show_finance: false,
  show_compatibility: true
})
const sidebarOptions = [
  { key: 'show_mining', label: '비트코인 채굴', description: '채굴 페이지 메뉴 표시' },
  { key: 'show_utxo', label: 'UTXO', description: 'UTXO 페이지 메뉴 표시' },
  { key: 'show_wallet', label: '지갑', description: '지갑 페이지 메뉴 표시' },
  { key: 'show_fee', label: '수수료 계산', description: '수수료 계산 페이지 메뉴 표시' },
  { key: 'show_finance', label: '재무 관리', description: '재무 관리 페이지 메뉴 표시' },
  { key: 'show_compatibility', label: '궁합', description: '비트코인 궁합 분석 페이지 메뉴 표시' }
]
const sidebarConfigLoading = ref(false)
const walletPasswordInput = ref('')
const savingWalletPassword = ref(false)
const walletPasswordMessage = ref('')
const currentWalletPassword = ref('')

const displayWalletPassword = computed(() => {
  return currentWalletPassword.value && currentWalletPassword.value.length
    ? currentWalletPassword.value
    : '설정되지 않음'
})

const loadSidebarConfig = async () => {
  sidebarConfigLoading.value = true
  try {
    const result = await apiGetSidebarConfig()
    if (result.success && result.config) {
      sidebarConfig.value = {
        ...sidebarConfig.value,
        ...result.config
      }
    }
  } catch (error) {
    console.error('Failed to load sidebar config:', error)
  } finally {
    sidebarConfigLoading.value = false
  }
}

const toggleSidebarItem = async (key) => {
  if (!props.isAdmin) return

  try {
    const result = await apiUpdateSidebarConfig(getCurrentUsername(), {
      [key]: !sidebarConfig.value[key]
    })
    if (result.success && result.config) {
      sidebarConfig.value = result.config
      props.showSuccess('사이드바 설정이 업데이트되었습니다')
      window.dispatchEvent(new CustomEvent('sidebarConfigUpdated'))
    } else {
      props.showError(result.error || '설정 업데이트 실패')
    }
  } catch (error) {
    props.showError('설정 업데이트 중 오류 발생')
    console.error('Failed to update sidebar config:', error)
  }
}

const loadCurrentWalletPassword = async () => {
  try {
    const res = await apiGetWalletPassword()
    if (res.success) {
      currentWalletPassword.value = res.password || ''
    }
  } catch (_) {
    // noop
  }
}

const saveWalletPassword = async () => {
  walletPasswordMessage.value = ''
  savingWalletPassword.value = true
  try {
    const passwordToSet = walletPasswordInput.value || ''
    const res = await apiSetWalletPassword(passwordToSet)
    if (res.success) {
      walletPasswordMessage.value = res.wallet_password_set ? '비밀번호 설정 성공' : '비밀번호 해제 성공'
      currentWalletPassword.value = passwordToSet
      walletPasswordInput.value = ''
    } else {
      walletPasswordMessage.value = res.error || '설정 실패'
    }
  } catch (_) {
    walletPasswordMessage.value = '요청 실패'
  } finally {
    savingWalletPassword.value = false
  }
}

onMounted(async () => {
  await loadSidebarConfig()
  await loadCurrentWalletPassword()
})
</script>
