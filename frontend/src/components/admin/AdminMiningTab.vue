<template>
  <div class="bg-white rounded-lg shadow-md p-6 max-w-xl">
    <h3 class="text-lg font-semibold text-gray-900 mb-2">채굴 데이터 초기화</h3>
    <p class="text-sm text-gray-600 mb-4">모든 블록 데이터를 삭제합니다. 관리자만 실행할 수 있습니다.</p>
    <div class="space-y-3">
      <input
        v-model="adminResetPassword"
        type="password"
        placeholder="관리자 비밀번호 입력"
        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-gray-900"
      />
      <div class="flex gap-2">
        <button
          @click="confirmAdminReset"
          :disabled="!isAdmin || adminResetLoading"
          class="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50"
        >
          {{ adminResetLoading ? '초기화 중...' : '초기화' }}
        </button>
        <span v-if="!isAdmin" class="text-sm text-gray-500 self-center">관리자 모드가 아닙니다</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  isAdmin: { type: Boolean, default: false },
  showSuccess: { type: Function, required: true },
  showError: { type: Function, required: true }
})

const adminResetPassword = ref('')
const adminResetLoading = ref(false)

const confirmAdminReset = async () => {
  if (!props.isAdmin) {
    props.showError('관리자만 가능합니다')
    return
  }
  if (!adminResetPassword.value) {
    props.showError('비밀번호를 입력하세요')
    return
  }

  adminResetLoading.value = true
  try {
    const response = await fetch((import.meta.env.VITE_API_BASE || '') + '/api/init_reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ token: adminResetPassword.value })
    })

    let data = null
    try {
      data = await response.json()
    } catch (_) {
      data = null
    }

    if (response.ok && data?.ok) {
      props.showSuccess('초기화가 완료되었습니다')
    } else {
      props.showError(data?.error || '초기화 실패')
    }
  } catch (_) {
    props.showError('네트워크 오류')
  } finally {
    adminResetLoading.value = false
  }
}
</script>
