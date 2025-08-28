<template>
  <div class="max-w-md mx-auto bg-white rounded-lg shadow-sm border border-slate-200 p-6 space-y-4">
    <h2 class="text-xl font-semibold">닉네임 등록</h2>
    <p class="text-sm text-slate-600">채굴장에서 사용할 닉네임을 입력해 주세요.</p>
    <input v-model="nick" @keyup.enter="submit" class="w-full border rounded px-3 py-2" placeholder="예: satoshi" />
    <button class="w-full bg-indigo-600 hover:bg-indigo-700 text-white rounded px-4 py-2 font-medium" :disabled="!nick" @click="submit">
      시작하기
    </button>
    <div v-if="error" class="text-sm text-red-600">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, inject } from 'vue'
import { apiRegisterNickname } from '../api'

const state = inject('appState')
const nick = ref(localStorage.getItem('nickname') || '')
const error = ref('')

async function submit() {
  error.value = ''
  const name = (nick.value || '').trim()
  if (!name) { error.value = '닉네임을 입력하세요.'; return }
  try {
    const res = await apiRegisterNickname(name)
    if (res && res.ok) {
      localStorage.setItem('nickname', res.nickname)
      state.active = 'mining'
    } else {
      error.value = res?.error || '등록 실패'
    }
  } catch (e) {
    error.value = '네트워크 오류 또는 서버 오류'
  }
}
</script>

<style scoped>
</style>

