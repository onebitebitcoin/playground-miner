<template>
  <div class="min-h-screen bg-white">
    <!-- Clean header -->
    <header class="border-b border-gray-100 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="h-8 w-8 rounded-lg bg-orange-500 text-white flex items-center justify-center">
            <span class="text-sm font-medium">₿</span>
          </div>
          <div>
            <h1 class="text-base sm:text-lg font-semibold text-slate-800">한입 비트코인 놀이터</h1>
          </div>
        </div>
        
        <!-- User info -->
        <div v-if="currentNickname && state.active !== 'nick'" class="hidden sm:flex items-center gap-2 bg-blue-50 px-3 py-1.5 rounded-lg">
          <div class="h-6 w-6 rounded-full bg-blue-500 text-white flex items-center justify-center text-xs font-medium">
            {{ currentNickname.charAt(0).toUpperCase() }}
          </div>
          <span class="text-sm text-blue-700">{{ currentNickname }}</span>
        </div>
        
        <!-- Header buttons -->
        <div v-if="state.active !== 'nick'" class="flex items-center gap-1 sm:gap-2">
          <button 
            class="md:hidden p-2 hover:bg-gray-50 rounded-lg"
            @click="mobileMenuOpen = !mobileMenuOpen"
          >
            <svg class="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <button
            v-if="currentNickname"
            class="hidden sm:inline-flex px-3 py-1.5 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
            @click="changeNickname"
          >닉네임 변경</button>
          <button
            class="px-2 py-1.5 sm:px-3 text-xs sm:text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
            @click="showResetDialog"
          >초기화</button>
        </div>
      </div>
    </header>

    <!-- Nickname setup page (full width, no sidebar) -->
    <div v-if="state.active === 'nick'" class="min-h-[calc(100vh-80px)]">
      <component :is="currentComponent" />
    </div>
    
    <!-- Main app with sidebar -->
    <div v-else class="flex min-h-[calc(100vh-65px)]">
      <!-- Sidebar -->
      <div class="hidden md:block">
        <Sidebar 
          :items="menuItems" 
          :active="state.active" 
          @select="onSelect" 
        />
      </div>
      
      <!-- Mobile Menu Overlay -->
      <div v-if="mobileMenuOpen" class="fixed inset-0 z-30 md:hidden">
        <div class="absolute inset-0 bg-black/20" @click="mobileMenuOpen = false"></div>
        <div class="relative">
          <Sidebar 
            :items="menuItems" 
            :active="state.active" 
            @select="onSelect"
            @click="mobileMenuOpen = false"
          />
        </div>
      </div>
      
      <!-- Main Content -->
      <main class="flex-1 overflow-auto">
        <!-- Mobile nav tabs -->
        <div class="md:hidden border-b border-gray-100 bg-white px-4 py-3">
          <div class="flex gap-1 overflow-x-auto">
            <button
              v-for="item in menuItems"
              :key="item.key"
              class="flex-shrink-0 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              :class="state.active === item.key 
                ? 'bg-slate-800 text-white' 
                : 'text-slate-600 hover:text-slate-800 hover:bg-orange-50'"
              @click="onSelect(item.key)"
            >
              {{ item.label }}
            </button>
          </div>
        </div>
        
        <div class="p-4 sm:p-6">
          <component :is="currentComponent" />
        </div>
      </main>
    </div>

    <!-- Reset Dialog -->
    <div v-if="resetDialogOpen" class="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl shadow-lg max-w-md w-full mx-4 p-4 sm:p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-3">초기화 확인</h3>
        <p class="text-gray-600 mb-4">모든 블록 데이터가 삭제됩니다. 계속하시려면 비밀번호를 입력해주세요.</p>
        <input 
          v-model="resetPassword"
          type="password"
          placeholder="비밀번호 입력"
          class="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-gray-900 focus:border-gray-900 outline-none mb-4"
          @keyup.enter="confirmReset"
        />
        <div class="flex gap-2">
          <button 
            @click="resetDialogOpen = false; resetPassword = ''"
            class="flex-1 px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition-colors"
          >취소</button>
          <button 
            @click="confirmReset"
            class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >초기화</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject, computed, ref as vueRef, onMounted } from 'vue'
import Sidebar from './components/Sidebar.vue'
import BitcoinMining from './pages/mining/BitcoinMining.vue'
import NicknameSetup from './pages/NicknameSetup.vue'
import UTXOPage from './pages/UTXOPage.vue'
import { apiInitReset } from './api'

const state = inject('appState')

const menuItems = [
  { key: 'mining', label: '비트코인 채굴' },
  { key: 'utxo', label: 'UTXO' },
]

const componentsMap = {
  nick: NicknameSetup,
  mining: BitcoinMining,
  utxo: UTXOPage,
}

const currentComponent = computed(() => componentsMap[state.active] ?? componentsMap.mining)

// Mobile menu state
const mobileMenuOpen = vueRef(false)

// Reset dialog state
const resetDialogOpen = vueRef(false)
const resetPassword = vueRef('')

// Current nickname
const currentNickname = vueRef(localStorage.getItem('nickname') || '')

// Update nickname when localStorage changes
onMounted(() => {
  // Listen for storage changes
  window.addEventListener('storage', (e) => {
    if (e.key === 'nickname') {
      currentNickname.value = e.newValue || ''
    }
  })
  
  // Also listen for custom events for same-tab updates
  window.addEventListener('nicknameChanged', (e) => {
    currentNickname.value = e.detail || ''
  })
})

function onSelect(key) {
  state.active = key
}

// Force nickname setup if not set
if (!localStorage.getItem('nickname')) {
  state.active = 'nick'
}

function changeNickname() {
  state.active = 'nick'
  mobileMenuOpen.value = false
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
