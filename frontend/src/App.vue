<template>
  <div class="min-h-screen flex">
    <!-- Desktop sidebar -->
    <div class="hidden md:block">
      <Sidebar
        :items="menuItems"
        :active="state.active"
        @select="onSelect"
      />
    </div>

    <main class="flex-1 p-4 md:p-6 space-y-4 md:space-y-6">
      <!-- Mobile topbar with nav -->
      <div class="md:hidden sticky top-0 z-10 -mx-4 px-4 py-3 bg-slate-50/80 backdrop-blur border-b border-slate-200">
        <div class="flex items-center justify-between">
          <h1 class="text-xl font-bold">플레이그라운드</h1>
        </div>
        <nav class="mt-3 flex gap-2 overflow-x-auto">
          <button
            v-for="item in menuItems"
            :key="item.key"
            class="px-3 py-1.5 rounded-full text-sm whitespace-nowrap border"
            :class="state.active === item.key ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-700 border-slate-300'"
            @click="onSelect(item.key)"
          >
            {{ item.label }}
          </button>
        </nav>
      </div>

      <!-- Desktop header -->
      <header class="hidden md:flex items-center justify-between">
        <h1 class="text-2xl font-bold">플레이그라운드</h1>
        <div class="flex items-center gap-2">
          <button
            class="px-3 py-1.5 text-sm rounded border border-red-300 text-red-600 hover:bg-red-50"
            @click="onInitReset"
          >초기화</button>
        </div>
      </header>

      <section>
        <component :is="currentComponent" />
      </section>
    </main>
  </div>
  
</template>

<script setup>
import { inject, computed } from 'vue'
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
</script>

<style scoped>
</style>
