<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
    <!-- Modern top header with brand and nav -->
    <header class="sticky top-0 z-20 bg-white/90 backdrop-blur-sm shadow-sm border-b border-blue-100">
      <div class="container max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="h-10 w-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white flex items-center justify-center shadow-lg">
            <span class="text-lg">⛏️</span>
          </div>
          <div>
            <h1 class="text-xl md:text-2xl font-bold text-slate-800">비트코인 채굴 놀이터</h1>
            <p class="text-xs text-slate-500 hidden md:block">재미있게 배우는 채굴 시뮬레이션</p>
          </div>
        </div>
        <nav class="hidden md:flex items-center gap-3">
          <button
            v-for="item in menuItems"
            :key="item.key"
            class="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200"
            :class="state.active === item.key ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-600 hover:bg-blue-50 hover:text-blue-600'"
            @click="onSelect(item.key)"
          >{{ item.label }}</button>
          <button
            class="ml-1 px-4 py-2 text-sm font-medium rounded-lg border-2 border-red-200 text-red-600 hover:bg-red-50 hover:border-red-300 transition-all duration-200"
            @click="showResetDialog"
          >초기화</button>
        </nav>
        <!-- Mobile menu button -->
        <button 
          class="md:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100"
          @click="mobileMenuOpen = !mobileMenuOpen"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>
      <!-- Mobile nav -->
      <div v-if="mobileMenuOpen" class="md:hidden px-4 pb-4 border-t border-blue-100 bg-white/95">
        <nav class="flex flex-wrap gap-2 pt-4">
          <button
            v-for="item in menuItems"
            :key="item.key"
            class="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200"
            :class="state.active === item.key ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-600 hover:bg-blue-50 border border-slate-200'"
            @click="onSelect(item.key); mobileMenuOpen = false"
          >{{ item.label }}</button>
          <button
            class="px-4 py-2 text-sm font-medium rounded-lg border-2 border-red-200 text-red-600 hover:bg-red-50"
            @click="showResetDialog"
          >초기화</button>
        </nav>
      </div>
    </header>

    <main class="container max-w-6xl mx-auto p-4 md:p-6 text-slate-800">
      <component :is="currentComponent" />
    </main>

    <!-- Reset Password Dialog -->
    <div v-if="resetDialogOpen" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
        <h3 class="text-lg font-semibold text-slate-800 mb-4">초기화 확인</h3>
        <p class="text-slate-600 mb-4">모든 블록 데이터가 삭제됩니다. 계속하시려면 비밀번호를 입력해주세요.</p>
        <input 
          v-model="resetPassword"
          type="password"
          placeholder="비밀번호 입력"
          class="w-full px-4 py-3 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none mb-4"
          @keyup.enter="confirmReset"
        />
        <div class="flex gap-3">
          <button 
            @click="resetDialogOpen = false; resetPassword = ''"
            class="flex-1 px-4 py-2 text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
          >취소</button>
          <button 
            @click="confirmReset"
            class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
          >초기화</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject, computed, ref as vueRef } from 'vue'
import Sidebar from './components/Sidebar.vue'
import BitcoinMining from './pages/mining/BitcoinMining.vue'
import NicknameSetup from './pages/NicknameSetup.vue'
import { apiInitReset } from './api'

const state = inject('appState')

const menuItems = [
  { key: 'mining', label: '비트코인 채굴' },
  // { key: 'coming', label: '다른 게임 (준비중)' }, // Hidden for now
]

const componentsMap = {
  nick: NicknameSetup,
  mining: BitcoinMining,
  coming: {
    template: '<div class="text-center py-12"><div class="text-6xl mb-4">🚧</div><div class="text-slate-500 text-lg">준비중입니다…</div></div>'
  }
}

const currentComponent = computed(() => componentsMap[state.active] ?? componentsMap.mining)

// Mobile menu state
const mobileMenuOpen = vueRef(false)

// Reset dialog state
const resetDialogOpen = vueRef(false)
const resetPassword = vueRef('')

function onSelect(key) {
  state.active = key
}

// Force nickname setup if not set
if (!localStorage.getItem('nickname')) {
  state.active = 'nick'
}

function showResetDialog() {
  resetDialogOpen.value = true
  mobileMenuOpen.value = false
}

async function confirmReset() {
  if (resetPassword.value !== '0000') {
    alert('비밀번호가 올바르지 않습니다.')
    return
  }
  
  try {
    const res = await apiInitReset('0000')
    if (res && res.ok) {
      alert('초기화가 완료되었습니다.')
      resetDialogOpen.value = false
      resetPassword.value = ''
      window.location.reload()
    } else {
      alert(res?.error || '초기화에 실패했습니다.')
    }
  } catch (e) {
    alert('네트워크 오류가 발생했습니다.')
  }
}

</script>

<style scoped>
</style>
