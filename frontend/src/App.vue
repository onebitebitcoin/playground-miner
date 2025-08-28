<template>
  <div class="min-h-screen flex">
    <Sidebar
      :items="menuItems"
      :active="state.active"
      @select="onSelect"
    />

    <main class="flex-1 p-6 space-y-6">
      <header class="flex items-center justify-between">
        <h1 class="text-2xl font-bold">플레이그라운드</h1>
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

const state = inject('appState')

const menuItems = [
  { key: 'mining', label: '비트코인 채굴(간이)' },
  { key: 'coming', label: '다른 게임 (준비중)' },
]

const componentsMap = {
  mining: BitcoinMining,
  coming: {
    template: '<div class="text-slate-500">준비중입니다…</div>'
  }
}

const currentComponent = computed(() => componentsMap[state.active] ?? componentsMap.mining)

function onSelect(key) {
  state.active = key
}
</script>

<style scoped>
</style>
