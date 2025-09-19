<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Clean header -->
    <header class="border-b border-gray-200 bg-white shadow-sm">
      <div class="w-full px-2 sm:px-4 py-3 sm:py-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="h-8 w-8 rounded-lg bg-gray-900 text-white flex items-center justify-center">
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M17.09 12.25l-2.5-1.5c-.28-.17-.64-.17-.92 0l-2.5 1.5c-.28.17-.46.48-.46.82v3c0 .34.18.65.46.82l2.5 1.5c.28.17.64.17.92 0l2.5-1.5c.28-.17.46-.48.46-.82v-3c0-.34-.18-.65-.46-.82zM12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/>
            </svg>
          </div>
          <div>
            <h1 class="text-base sm:text-lg font-semibold text-gray-900">한입 비트코인 놀이터</h1>
          </div>
        </div>
        
        <!-- Right side: User info + Header buttons -->
        <div v-if="!isNicknameSetup" class="flex items-center gap-2 sm:gap-4">
          <!-- User info -->
          <div v-if="currentNickname" class="hidden sm:flex items-center gap-2 bg-gray-100 px-3 py-1.5 rounded-lg">
            <div class="h-6 w-6 rounded-full bg-gray-600 text-white flex items-center justify-center text-xs font-medium">
              {{ currentNickname.charAt(0).toUpperCase() }}
            </div>
            <span class="text-sm text-gray-700">{{ currentNickname }}</span>
          </div>

          <!-- Header buttons -->
          <div class="flex items-center gap-1 sm:gap-2">
          <button
            v-if="currentNickname"
            class="hidden sm:inline-flex px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
            @click="logout"
          >
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            로그아웃
          </button>
          <button
            class="px-2 py-1.5 sm:px-3 text-xs sm:text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
            @click="showResetDialog"
          >
            <svg class="w-4 h-4 mr-1 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            초기화
          </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Nickname setup page (full width, no sidebar) -->
    <div v-if="isNicknameSetup" class="min-h-[calc(100vh-80px)]">
      <router-view />
    </div>

    <!-- Main app with sidebar -->
    <div v-else class="flex min-h-[calc(100vh-70px)]">
      <!-- Sidebar -->
      <div class="hidden md:block">
        <Sidebar
          :items="menuItems"
          :active="currentRouteName"
          @select="onMenuSelect"
        />
      </div>


      <!-- Main Content -->
      <main class="flex-1 overflow-auto bg-gray-50">
        <!-- Mobile nav tabs -->
        <div class="md:hidden border-b border-gray-200 bg-white px-4 py-2">
          <div class="flex gap-1 overflow-x-auto scrollbar-hide">
            <button
              v-for="item in menuItems"
              :key="item.key"
              class="flex-shrink-0 px-3 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap"
              :class="currentRouteName === item.key
                ? 'bg-gray-900 text-white'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'"
              @click="onMenuSelect(item.key)"
            >
              {{ item.label }}
            </button>
          </div>
        </div>

        <div class="p-4 sm:p-6">
          <router-view />
        </div>
      </main>
    </div>

    <!-- Reset Dialog -->
    <div v-if="resetDialogOpen" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-4 sm:p-6">
        <div class="flex items-center mb-4">
          <div class="h-10 w-10 rounded-full bg-gray-100 flex items-center justify-center mr-3">
            <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-900">초기화 확인</h3>
        </div>
        <p class="text-gray-600 mb-4">모든 블록 데이터가 삭제됩니다. 계속하시려면 비밀번호를 입력해주세요.</p>
        <input
          v-model="resetPassword"
          type="password"
          placeholder="비밀번호 입력"
          class="w-full px-3 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-gray-900 focus:border-gray-900 outline-none mb-4"
          @keyup.enter="confirmReset"
        />
        <div class="flex gap-3">
          <button
            @click="resetDialogOpen = false; resetPassword = ''"
            class="flex-1 px-4 py-2.5 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors font-medium"
          >취소</button>
          <button
            @click="confirmReset"
            class="flex-1 px-4 py-2.5 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors font-medium"
          >초기화</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref as vueRef, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import { apiInitReset } from './api'

const router = useRouter()
const route = useRoute()

const menuItems = computed(() => {
  const items = [
    { key: 'mining', label: '비트코인 채굴' },
    { key: 'utxo', label: 'UTXO' },
    { key: 'wallet', label: '지갑' },
    { key: 'fee', label: '수수료 계산' },
  ]

  // Add admin menu only for admin users
  const nickname = localStorage.getItem('nickname')
  const adminStatus = localStorage.getItem('isAdmin')
  if (nickname === 'admin' && adminStatus === 'true') {
    items.push({ key: 'admin', label: '관리자' })
  }

  return items
})

// Computed properties for routing
const currentRouteName = computed(() => route.name || 'mining')
const isNicknameSetup = computed(() => route.name === 'nickname')

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

function onMenuSelect(key) {
  router.push({ name: key })
  mobileMenuOpen.value = false
}

function logout() {
  // Clear nickname and admin status from localStorage
  localStorage.removeItem('nickname')
  localStorage.removeItem('isAdmin')

  // Trigger event to update header immediately
  window.dispatchEvent(new CustomEvent('nicknameChanged', { detail: '' }))

  // Update current nickname
  currentNickname.value = ''

  // Navigate to nickname setup page
  router.push({ name: 'nickname' })
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
