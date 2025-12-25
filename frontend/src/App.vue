<template>
  <router-view v-slot="{ Component }">
    <div class="min-h-screen flex flex-col pastel-page">
      <header class="border-b pastel-nav shadow-sm">
        <div class="w-full px-2 sm:px-4 py-3 sm:py-4 flex flex-col gap-3">
          <div class="flex flex-wrap items-center gap-3">
            <div class="flex items-center gap-3 flex-shrink-0">
              <img
                src="/icons/logo-runner.png"
                alt="한입 놀이터 로고"
                class="h-12 w-12 flex-shrink-0"
                decoding="async"
              />
              <h1 class="text-base sm:text-lg font-semibold text-gray-900">한입 놀이터</h1>
            </div>

            <div class="flex items-center gap-2 ml-auto">
              <nav class="hidden md:flex items-center gap-2">
                <button
                  v-for="item in menuItems"
                  :key="item.key"
                  class="px-3 py-2 rounded-full text-sm font-semibold transition-all"
                  :class="currentRouteName === item.key
                    ? 'bg-gray-900 text-white shadow-sm'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-white/70'"
                  @click="onMenuSelect(item.key)"
                >
                  {{ item.label }}
                </button>
              </nav>

              <button
                v-if="currentNickname"
                class="inline-flex items-center gap-1 text-sm sm:text-base text-gray-600 hover:text-gray-900 transition-colors"
                @click="logout"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                로그아웃
              </button>
            </div>
          </div>

          <div class="md:hidden">
            <div class="flex gap-2 overflow-x-auto pb-1">
              <button
                v-for="item in menuItems"
                :key="item.key"
                class="flex-shrink-0 px-3 py-2 rounded-full text-sm font-semibold transition-all whitespace-nowrap"
                :class="currentRouteName === item.key
                  ? 'bg-gray-900 text-white shadow-sm'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-white/70'"
                @click="onMenuSelect(item.key)"
              >
                {{ item.label }}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main class="flex-1 min-h-0 overflow-y-auto pastel-main">
        <div class="px-3 py-4 sm:px-6 sm:py-6">
          <component :is="Component" />
        </div>
      </main>
    </div>
  </router-view>
</template>

<script setup>
import { computed, ref as vueRef, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { loadSidebarConfig, sidebarConfig } from '@/stores/sidebarConfig'

const router = useRouter()
const route = useRoute()

// Current nickname/admin flags
const currentNickname = vueRef(localStorage.getItem('nickname') || '')
const isAdminFlag = vueRef(localStorage.getItem('isAdmin') === 'true')

const menuItems = computed(() => {
  const items = [{ key: 'home', label: '홈' }]

  // Add menu items based on sidebar config (fee/finance before mining)
  if (sidebarConfig.value.show_fee) {
    items.push({ key: 'fee', label: '수수료 계산' })
  }

  if (sidebarConfig.value.show_finance) {
    items.push({ key: 'finance', label: '재무 관리' })
  }

  if (sidebarConfig.value.show_mining) {
    items.push({ key: 'mining', label: '비트코인 채굴' })
  }

  if (sidebarConfig.value.show_utxo) {
    items.push({ key: 'utxo', label: 'UTXO' })
  }

  if (sidebarConfig.value.show_wallet) {
    items.push({ key: 'wallet', label: '지갑' })
  }

  if (sidebarConfig.value.show_compatibility) {
    items.push({ key: 'compatibility', label: '궁합' })
  }

  if (sidebarConfig.value.show_timecapsule) {
    items.push({ key: 'timecapsule', label: '타임캡슐' })
  }

  // Add admin menu only for admin users
  if (currentNickname.value === 'admin' && isAdminFlag.value) {
    items.push({ key: 'admin', label: '관리자' })
  }

  return items
})

// Computed properties for routing
const currentRouteName = computed(() => {
  const name = route.name || 'home'
  if (name === 'wallet-kingstone' || name === 'wallet-kingstone-detail') return 'wallet'
  return name
})
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
    loadSidebarConfig(true)
  })
})

function onMenuSelect(key) {
  router.push({ name: key })
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

  // Navigate to home page
  router.push({ name: 'home' })
}

</script>

<style scoped>
</style>
