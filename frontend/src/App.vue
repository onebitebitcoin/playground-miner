<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
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
        
        <!-- Right side: User info -->
        <div v-if="!isNicknameSetup" class="flex items-center gap-2 sm:gap-4">
          <!-- User info (desktop) -->
          <div v-if="currentNickname" class="hidden sm:flex items-center gap-2 bg-gray-100 px-3 py-1.5 rounded-lg">
            <div class="h-6 w-6 rounded-full bg-gray-600 text-white flex items-center justify-center text-xs font-medium">
              {{ currentNickname.charAt(0).toUpperCase() }}
            </div>
            <span class="text-sm text-gray-700">{{ currentNickname }}</span>
          </div>

          <!-- User avatar (mobile) -->
          <div v-if="currentNickname" class="sm:hidden flex items-center">
            <div class="h-7 w-7 rounded-full bg-gray-700 text-white flex items-center justify-center text-xs font-medium">
              {{ currentNickname.charAt(0).toUpperCase() }}
            </div>
          </div>
          
          <!-- Header button: logout -->
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

          <!-- Mobile logout icon -->
          <button
            v-if="currentNickname"
            class="sm:hidden inline-flex p-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors"
            @click="logout"
            title="로그아웃"
            aria-label="로그아웃"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </div>
    </header>

    <!-- Nickname setup page (full width, no sidebar) -->
    <div v-if="isNicknameSetup" class="flex-1 overflow-y-auto min-h-0">
      <router-view />
    </div>

    <!-- Main app with sidebar -->
    <div v-else class="flex flex-1 min-h-0">
      <!-- Sidebar -->
      <div class="hidden md:flex md:flex-col md:h-full md:flex-shrink-0 md:min-h-0">
        <Sidebar
          :items="menuItems"
          :active="currentRouteName"
          @select="onMenuSelect"
        />
      </div>


      <!-- Main Content -->
      <main class="flex-1 min-h-0 overflow-y-auto bg-gray-50">
        <!-- Mobile nav tabs -->
        <div class="md:hidden border-b border-gray-200 bg-white px-3 py-2">
          <div class="flex gap-1 overflow-x-auto">
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

        <div class="px-3 py-4 sm:px-6 sm:py-6">
          <router-view />
        </div>
      </main>
    </div>

    
  </div>
</template>

<script setup>
import { computed, ref as vueRef, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import { apiGetSidebarConfig } from './api'

const router = useRouter()
const route = useRoute()

const sidebarConfig = vueRef({
  show_mining: true,
  show_utxo: true,
  show_wallet: true,
  show_fee: true,
  show_finance: false
})

// Current nickname/admin flags
const currentNickname = vueRef(localStorage.getItem('nickname') || '')
const isAdminFlag = vueRef(localStorage.getItem('isAdmin') === 'true')

const menuItems = computed(() => {
  const items = []

  // Add menu items based on sidebar config
  if (sidebarConfig.value.show_mining) {
    items.push({ key: 'mining', label: '비트코인 채굴' })
  }

  if (sidebarConfig.value.show_utxo) {
    items.push({ key: 'utxo', label: 'UTXO' })
  }

  if (sidebarConfig.value.show_wallet) {
    items.push({ key: 'wallet', label: '지갑' })
  }

  if (sidebarConfig.value.show_fee) {
    items.push({ key: 'fee', label: '수수료 계산' })
  }

  if (sidebarConfig.value.show_finance) {
    items.push({ key: 'finance', label: '재무 관리' })
  }

  // Add admin menu only for admin users
  if (currentNickname.value === 'admin' && isAdminFlag.value) {
    items.push({ key: 'admin', label: '관리자' })
  }

  return items
})

// Computed properties for routing
const currentRouteName = computed(() => {
  const name = route.name || 'mining'
  if (name === 'wallet-kingstone' || name === 'wallet-kingstone-detail') return 'wallet'
  return name
})
const isNicknameSetup = computed(() => route.name === 'nickname')

// Mobile menu state
const mobileMenuOpen = vueRef(false)


// Load sidebar config
const loadSidebarConfig = async () => {
  try {
    const result = await apiGetSidebarConfig()
    if (result.success && result.config) {
      sidebarConfig.value = result.config
    }
  } catch (error) {
    console.error('Failed to load sidebar config:', error)
  }
}

// Update nickname when localStorage changes
onMounted(() => {
  // Load sidebar config on mount
  loadSidebarConfig()

  // Listen for storage changes
  window.addEventListener('storage', (e) => {
    if (e.key === 'nickname') {
      currentNickname.value = e.newValue || ''
    }
    if (e.key === 'isAdmin') {
      isAdminFlag.value = e.newValue === 'true'
    }
  })

  // Also listen for custom events for same-tab updates
  window.addEventListener('nicknameChanged', (e) => {
    currentNickname.value = e.detail || ''
    isAdminFlag.value = localStorage.getItem('isAdmin') === 'true'
  })

  // Listen for sidebar config updates
  window.addEventListener('sidebarConfigUpdated', () => {
    loadSidebarConfig()
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
  isAdminFlag.value = false

  // Navigate to nickname setup page
  router.push({ name: 'nickname' })
  mobileMenuOpen.value = false
}

</script>

<style scoped>
</style>
