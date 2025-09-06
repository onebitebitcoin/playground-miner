<template>
  <div class="min-h-[calc(100vh-65px)] flex items-center justify-center p-6">
    <div class="max-w-sm w-full space-y-8">
      <!-- Header -->
      <div class="text-center">
        <div class="h-12 w-12 mx-auto bg-orange-500 rounded-lg flex items-center justify-center mb-4">
          <span class="text-lg text-white font-medium">₿</span>
        </div>
        <h2 class="text-xl font-semibold text-slate-800">닉네임 설정</h2>
        <p class="text-sm text-slate-600 mt-1">사용할 닉네임을 입력해주세요</p>
      </div>

      <!-- Input Section -->
      <div class="space-y-4">
        <div>
          <div class="flex gap-2">
            <input 
              v-model="nick" 
              @input="onNicknameInput"
              @keyup.enter="checkDuplicateThenSubmit" 
              class="flex-1 border border-gray-200 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition-all"
              :class="{
                'border-red-300 focus:ring-red-500 focus:border-red-500': error,
                'border-green-500 focus:ring-green-500 focus:border-green-500': isAvailable && nick.trim()
              }"
              placeholder="닉네임 입력" 
              maxlength="20"
            />
            <button 
              @click="checkDuplicate"
              :disabled="!nick.trim() || checkingDuplicate"
              class="px-4 py-2.5 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors whitespace-nowrap"
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

        <!-- Status Messages -->
        <div class="min-h-[20px]">
          <div v-if="error" class="text-sm text-red-600">
            {{ error }}
          </div>
          <div v-else-if="isAvailable && nick.trim()" class="text-sm text-green-600">
            사용 가능한 닉네임입니다
          </div>
          <div v-else-if="nick.trim()" class="text-sm text-gray-500">
            중복체크 버튼을 눌러주세요
          </div>
        </div>
      </div>

      <!-- Submit Button -->
      <button 
        @click="submit"
        :disabled="!nick.trim() || !isAvailable || submitting"
        class="w-full bg-slate-800 hover:bg-slate-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg px-4 py-2.5 font-medium transition-colors"
      >
        <span v-if="submitting" class="flex items-center justify-center gap-2">
          <svg class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          등록 중...
        </span>
        <span v-else>시작하기</span>
      </button>

      <!-- Tips -->
      <div class="bg-gray-50 rounded-lg p-4">
        <p class="text-xs text-gray-600">
          2-20자 사이로 입력해주세요. 한글, 영문, 숫자 사용 가능합니다.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject } from 'vue'
import { apiRegisterNickname, apiCheckNickname } from '../api'

const state = inject('appState')
const nick = ref(localStorage.getItem('nickname') || '')
const error = ref('')
const isAvailable = ref(false)
const checkingDuplicate = ref(false)
const submitting = ref(false)

function onNicknameInput() {
  error.value = ''
  isAvailable.value = false
}

async function checkDuplicate() {
  const name = (nick.value || '').trim()
  if (!name) {
    error.value = '닉네임을 입력하세요'
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
  if (!isAvailable.value) {
    await checkDuplicate()
  }
  if (isAvailable.value) {
    await submit()
  }
}

async function submit() {
  if (!isAvailable.value) {
    error.value = '중복체크를 먼저 해주세요'
    return
  }
  
  const name = (nick.value || '').trim()
  if (!name) {
    error.value = '닉네임을 입력하세요'
    return
  }
  
  submitting.value = true
  error.value = ''
  
  try {
    const res = await apiRegisterNickname(name)
    if (res && res.ok) {
      localStorage.setItem('nickname', res.nickname)
      // Dispatch custom event for same-tab updates
      window.dispatchEvent(new CustomEvent('nicknameChanged', { detail: res.nickname }))
      state.active = 'mining'
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

