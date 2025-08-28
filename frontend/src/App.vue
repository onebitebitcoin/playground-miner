<template>
  <div class="min-h-screen bg-gradient-to-b from-slate-50 to-white dark:from-slate-900 dark:to-slate-900 transition-base" :class="{ compact: density === 'compact' }">
    <!-- Modern top header with brand and nav -->
    <header class="sticky top-0 z-20 bg-white/70 dark:bg-slate-900/70 backdrop-blur border-b border-slate-200 dark:border-slate-800 transition-base">
      <div class="container max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="h-8 w-8 rounded-lg bg-slate-900 text-white flex items-center justify-center">⛏️</div>
          <h1 class="text-lg md:text-xl font-bold dark:text-slate-100">Playground</h1>
        </div>
        <nav class="hidden md:flex items-center gap-2">
          <button
            v-for="item in menuItems"
            :key="item.key"
            class="px-3 py-1.5 rounded-full text-sm border transition"
            :class="state.active === item.key ? 'bg-slate-900 text-white border-slate-900' : 'bg-white dark:bg-slate-800 dark:text-slate-200 text-slate-700 border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700'"
            @click="onSelect(item.key)"
          >{{ item.label }}</button>
          <div class="h-5 w-px bg-slate-200 dark:bg-slate-700 mx-1" />
          <button
            class="px-3 py-1.5 text-sm rounded-full border border-slate-300 dark:border-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
            @click="toggleDensity"
          >{{ density === 'compact' ? 'Compact' : 'Comfort' }}</button>
          <button
            class="px-3 py-1.5 text-sm rounded-full border border-slate-300 dark:border-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
            @click="toggleDark"
          >{{ isDark ? 'Light' : 'Dark' }}</button>
          <button
            class="ml-2 px-3 py-1.5 text-sm rounded-full border border-red-300 text-red-600 hover:bg-red-50"
            @click="onInitReset"
          >초기화</button>
        </nav>
      </div>
      <!-- Mobile nav -->
      <div class="md:hidden px-4 pb-3">
        <nav class="flex gap-2 overflow-x-auto">
          <button
            v-for="item in menuItems"
            :key="item.key"
            class="px-3 py-1.5 rounded-full text-sm border"
            :class="state.active === item.key ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-700 border-slate-300'"
            @click="onSelect(item.key)"
          >{{ item.label }}</button>
          <button
            class="px-3 py-1.5 text-sm rounded-full border border-red-300 text-red-600"
            @click="onInitReset"
          >초기화</button>
          <button
            class="px-3 py-1.5 text-sm rounded-full border border-slate-300 dark:border-slate-700"
            @click="toggleDensity"
          >{{ density === 'compact' ? 'Compact' : 'Comfort' }}</button>
          <button
            class="px-3 py-1.5 text-sm rounded-full border border-slate-300 dark:border-slate-700"
            @click="toggleDark"
          >{{ isDark ? 'Light' : 'Dark' }}</button>
        </nav>
      </div>
    </header>

    <main class="container max-w-5xl mx-auto p-4 md:p-6 text-slate-900 dark:text-slate-100 transition-base">
      <component :is="currentComponent" />
    </main>
  </div>
</template>

<script setup>
import { inject, computed, ref as vueRef, onMounted } from 'vue'
import Sidebar from './components/Sidebar.vue'
import BitcoinMining from './pages/mining/BitcoinMining.vue'
import NicknameSetup from './pages/NicknameSetup.vue'
import { apiInitReset } from './api'

const state = inject('appState')

const menuItems = [
  { key: 'mining', label: '비트코인 채굴(간이)' },
  { key: 'coming', label: '다른 게임 (준비중)' },
]

const componentsMap = {
  nick: NicknameSetup,
  mining: BitcoinMining,
  coming: {
    template: '<div class="text-slate-500">준비중입니다…</div>'
  }
}

const currentComponent = computed(() => componentsMap[state.active] ?? componentsMap.mining)

function onSelect(key) {
  state.active = key
}

// Force nickname setup if not set
if (!localStorage.getItem('nickname')) {
  state.active = 'nick'
}

async function onInitReset() {
  try {
    const res = await apiInitReset('0000')
    if (res && res.ok) {
      alert('초기화 완료')
      // Optional: reload page state
      window.location.reload()
    } else {
      alert(res?.error || '초기화 실패')
    }
  } catch (e) {}
}

// Dark mode + density state
const isDark = vueRef((localStorage.getItem('theme') || 'light') === 'dark')
const density = vueRef(localStorage.getItem('density') || 'compact')
function applyTheme() {
  const root = document.documentElement
  if (isDark.value) root.classList.add('dark'); else root.classList.remove('dark')
}
function toggleDark() {
  isDark.value = !isDark.value
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  applyTheme()
}
function toggleDensity() {
  density.value = density.value === 'compact' ? 'comfort' : 'compact'
  localStorage.setItem('density', density.value)
}
onMounted(() => applyTheme())
</script>

<style scoped>
</style>
