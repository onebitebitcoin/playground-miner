<template>
  <div class="min-h-[calc(100vh-70px)] w-full flex items-center justify-center px-3 py-4 bg-gray-50 overflow-y-auto">
    <div class="max-w-sm w-full space-y-8">
      <!-- Header -->
      <div class="text-center">
        <div class="h-12 w-12 mx-auto bg-gray-900 rounded-xl flex items-center justify-center mb-4">
          <svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M17.09 12.25l-2.5-1.5c-.28-.17-.64-.17-.92 0l-2.5 1.5c-.28.17-.46.48-.46.82v3c0 .34.18.65.46.82l2.5 1.5c.28.17.64.17.92 0l2.5-1.5c.28-.17.46-.48.46-.82v-3c0-.34-.18-.65-.46-.82zM12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/>
          </svg>
        </div>
        <h2 class="text-xl font-semibold text-gray-900">
          {{ mode === 'login' ? '로그인' : '회원가입' }}
        </h2>
        <p class="text-sm text-gray-600 mt-2">
          {{ mode === 'login' ? '기존 닉네임으로 로그인하세요' : '사용할 닉네임을 만들어주세요' }}
        </p>
      </div>

      <!-- Mode Selection -->
      <div class="flex bg-gray-100 p-1 rounded-lg">
        <button
          @click="switchMode('login')"
          :class="mode === 'login' ? 'bg-white text-gray-900 shadow' : 'text-gray-600'"
          class="flex-1 px-3 py-2 text-sm font-medium rounded-md transition-all"
        >
          로그인
        </button>
        <button
          @click="switchMode('signup')"
          :class="mode === 'signup' ? 'bg-white text-gray-900 shadow' : 'text-gray-600'"
          class="flex-1 px-3 py-2 text-sm font-medium rounded-md transition-all"
        >
          회원가입
        </button>
      </div>

      <!-- Input Section -->
      <div class="space-y-4">
        <!-- Login Mode -->
        <div v-if="mode === 'login'">
          <div class="space-y-3">
            <input
              v-model="nick"
              @input="onNicknameInput"
              @keyup.enter="loginSubmit"
              class="w-full border border-gray-200 rounded-lg px-4 py-3 focus:ring-2 focus:ring-gray-900 focus:border-gray-900 outline-none transition-all"
              :class="{
                'border-red-300 focus:ring-red-500 focus:border-red-500': error
              }"
              placeholder="닉네임 입력"
              maxlength="20"
            />
          </div>
        </div>

        <!-- Signup Mode -->
        <div v-if="mode === 'signup'">
          <div class="flex gap-2">
            <input
              v-model="nick"
              @input="onNicknameInput"
              @keyup.enter="checkDuplicateThenSubmit"
              class="flex-1 border border-gray-200 rounded-lg px-4 py-3 focus:ring-2 focus:ring-gray-900 focus:border-gray-900 outline-none transition-all"
              :class="{
                'border-red-300 focus:ring-red-500 focus:border-red-500': error,
                'border-green-500 focus:ring-green-500 focus:border-green-500': isAvailable && nick.trim()
              }"
              placeholder="닉네임 입력"
              maxlength="20"
            />
            <button
              @click="checkDuplicate"
              :disabled="!nick.trim() || checkingDuplicate || isAdmin"
              class="px-4 py-3 bg-gray-900 hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors whitespace-nowrap"
            >
              <span v-if="checkingDuplicate" class="flex items-center gap-1">
                <svg class="animate-spin h-3 w-3" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                확인
              </span>
              <span v-else>중복체크</span>
            </button>
          </div>
        </div>

        <!-- Admin Password Input (shown when nickname is 'admin') -->
        <div v-if="isAdmin" class="space-y-2">
          <input
            v-model="adminPassword"
            type="password"
            @keyup.enter="submit"
            class="w-full border border-gray-200 rounded-lg px-4 py-3 focus:ring-2 focus:ring-gray-900 focus:border-gray-900 outline-none transition-all"
            :class="{
              'border-red-300 focus:ring-red-500 focus:border-red-500': error
            }"
            placeholder="관리자 비밀번호 입력"
            maxlength="10"
          />
          <p class="text-xs text-gray-600">관리자 계정을 사용하려면 비밀번호를 입력하세요.</p>
        </div>

        <!-- Status Messages -->
        <div class="min-h-[20px]">
          <div v-if="error" class="text-sm text-red-600">
            {{ error }}
          </div>
          <div v-else-if="isAdmin && nick.trim()" class="text-sm text-gray-700">
            관리자 계정입니다. 비밀번호를 입력하세요.
          </div>
          <div v-else-if="mode === 'signup' && isAvailable && nick.trim()" class="text-sm text-green-600">
            사용 가능한 닉네임입니다
          </div>
          <div v-else-if="mode === 'signup' && nick.trim()" class="text-sm text-gray-500">
            중복체크 버튼을 눌러주세요
          </div>
          <div v-else-if="mode === 'login' && nick.trim()" class="text-sm text-gray-600">
            로그인할 닉네임을 입력하세요
          </div>
        </div>
      </div>

      <!-- Submit Button -->
      <button
        @click="mode === 'login' ? loginSubmit() : submit()"
        :disabled="getSubmitDisabled"
        class="w-full bg-gray-900 hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg px-4 py-3 font-medium transition-colors"
      >
        <span v-if="submitting" class="flex items-center justify-center gap-2">
          <svg class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ mode === 'login' ? '로그인 중...' : '등록 중...' }}
        </span>
        <span v-else>{{ mode === 'login' ? '로그인' : '회원가입' }}</span>
      </button>

      <!-- Tips -->
      <div class="bg-white border border-gray-200 rounded-lg p-4">
        <p class="text-xs text-gray-600">
          {{ mode === 'login' ?
            '기존에 생성한 닉네임을 입력하여 로그인하세요.' :
            '2-20자 사이로 입력해주세요. 한글, 영문, 숫자 사용 가능합니다.'
          }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { apiRegisterNickname, apiCheckNickname } from '../api'

const router = useRouter()
const nick = ref(localStorage.getItem('nickname') || '')
const error = ref('')
const isAvailable = ref(false)
const checkingDuplicate = ref(false)
const submitting = ref(false)
const adminPassword = ref('')
const mode = ref('login')

// Check if current nickname is admin
const isAdmin = computed(() => nick.value.toLowerCase() === 'admin')

// Computed for submit button disabled state
const getSubmitDisabled = computed(() => {
  if (!nick.value.trim() || submitting.value) return true

  if (isAdmin.value && !adminPassword.value.trim()) return true

  if (mode.value === 'signup' && !isAdmin.value && !isAvailable.value) return true

  return false
})

// Mode switching function
function switchMode(newMode) {
  mode.value = newMode
  error.value = ''
  isAvailable.value = false
  adminPassword.value = ''
}

function onNicknameInput() {
  error.value = ''
  if (mode.value === 'signup') {
    isAvailable.value = false
  }
  adminPassword.value = ''
}

// Login function - checks if nickname exists and logs in
async function loginSubmit() {
  const name = (nick.value || '').trim()
  if (!name) {
    error.value = '닉네임을 입력하세요'
    return
  }

  // Handle admin login
  if (name.toLowerCase() === 'admin') {
    if (!adminPassword.value.trim()) {
      error.value = '관리자 비밀번호를 입력하세요'
      return
    }

    if (adminPassword.value !== '0000') {
      error.value = '비밀번호가 올바르지 않습니다'
      return
    }

    // Admin login successful
    localStorage.setItem('nickname', 'admin')
    localStorage.setItem('isAdmin', 'true')
    window.dispatchEvent(new CustomEvent('nicknameChanged', { detail: 'admin' }))
    router.push({ name: 'mining' })
    return
  }

  submitting.value = true
  error.value = ''

  try {
    // Check if nickname exists
    const res = await apiCheckNickname(name)
    if (res && res.ok) {
      if (res.exists) {
        // Nickname exists, log in
        localStorage.setItem('nickname', name)
        localStorage.removeItem('isAdmin')
        window.dispatchEvent(new CustomEvent('nicknameChanged', { detail: name }))
        router.push({ name: 'mining' })
      } else {
        error.value = '존재하지 않는 닉네임입니다. 회원가입을 이용하세요.'
      }
    } else {
      error.value = res?.error || '로그인 확인에 실패했습니다'
    }
  } catch (e) {
    error.value = '네트워크 오류가 발생했습니다'
  } finally {
    submitting.value = false
  }
}

async function checkDuplicate() {
  const name = (nick.value || '').trim()
  if (!name) {
    error.value = '닉네임을 입력하세요'
    return
  }

  // Skip validation for admin account
  if (name.toLowerCase() === 'admin') {
    isAvailable.value = true
    return
  }

  if (name.length < 2) {
    error.value = '닉네임은 2자 이상이어야 합니다'
    return
  }

  if (name.length > 20) {
    error.value = '닉네임은 20자 이하여야 합니다'
    return
  }

  checkingDuplicate.value = true
  error.value = ''

  try {
    const res = await apiCheckNickname(name)
    if (res && res.ok) {
      if (!res.exists) {
        isAvailable.value = true
        error.value = ''
      } else {
        isAvailable.value = false
        error.value = '이미 사용 중인 닉네임입니다'
      }
    } else {
      isAvailable.value = false
      error.value = res?.error || '중복 체크 실패'
    }
  } catch (e) {
    error.value = '중복 체크 실패. 네트워크를 확인해주세요'
    isAvailable.value = false
  } finally {
    checkingDuplicate.value = false
  }
}

async function checkDuplicateThenSubmit() {
  if (!isAvailable.value && !isAdmin.value) {
    await checkDuplicate()
  }
  if (isAvailable.value || isAdmin.value) {
    await submit()
  }
}

async function submit() {
  const name = (nick.value || '').trim()
  if (!name) {
    error.value = '닉네임을 입력하세요'
    return
  }

  // Handle admin login
  if (name.toLowerCase() === 'admin') {
    if (!adminPassword.value.trim()) {
      error.value = '관리자 비밀번호를 입력하세요'
      return
    }

    if (adminPassword.value !== '0000') {
      error.value = '비밀번호가 올바르지 않습니다'
      return
    }

    // Admin login successful
    localStorage.setItem('nickname', 'admin')
    // Store admin status
    localStorage.setItem('isAdmin', 'true')
    // Dispatch custom event for same-tab updates
    window.dispatchEvent(new CustomEvent('nicknameChanged', { detail: 'admin' }))
    // Navigate to mining page
    router.push({ name: 'mining' })
    return
  }

  // Regular user flow
  if (!isAvailable.value) {
    error.value = '중복체크를 먼저 해주세요'
    return
  }

  submitting.value = true
  error.value = ''

  try {
    const res = await apiRegisterNickname(name)
    if (res && res.ok) {
      localStorage.setItem('nickname', res.nickname)
      // Remove admin status if set
      localStorage.removeItem('isAdmin')
      // Dispatch custom event for same-tab updates
      window.dispatchEvent(new CustomEvent('nicknameChanged', { detail: res.nickname }))
      // Navigate to mining page
      router.push({ name: 'mining' })
    } else {
      error.value = res?.error || '등록 실패'
      isAvailable.value = false // 등록 실패 시 중복체크 다시 해야함
    }
  } catch (e) {
    error.value = '네트워크 오류 또는 서버 오류'
    isAvailable.value = false
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
</style>
