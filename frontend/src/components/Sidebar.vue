<template>
  <aside class="w-64 h-full bg-white border-r border-gray-200 px-6 py-8 flex flex-col overflow-y-auto min-h-0">
    <nav class="space-y-1 flex-1">
      <button
        v-for="item in items"
        :key="item.key"
        class="w-full text-left px-3 py-2.5 rounded-lg font-medium transition-colors flex items-center gap-3"
        :class="active === item.key
          ? 'bg-gray-900 text-white shadow-sm'
          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'"
        @click="$emit('select', item.key)"
      >
        <component :is="getIcon(item.key)" class="w-5 h-5" />
        {{ item.label }}
      </button>
    </nav>
  </aside>
</template>

<script setup>
import { defineComponent, h } from 'vue'

defineProps({
  items: { type: Array, default: () => [] },
  active: { type: String, default: '' },
})

const getIcon = (key) => {
  const icons = {
    learn: () => h('svg', {
      fill: 'none',
      stroke: 'currentColor',
      viewBox: '0 0 24 24'
    }, [
      h('path', {
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        'stroke-width': '2',
        d: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253'
      })
    ]),
    // Miner icon (helmet + head + shoulders)
    mining: () => h('svg', {
      fill: 'none',
      stroke: 'currentColor',
      viewBox: '0 0 24 24'
    }, [
      // head
      h('circle', { cx: '12', cy: '8', r: '3', 'stroke-width': '2' }),
      // helmet brim
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M8 7h8' }),
      // shoulders/torso
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M6 20v-2a6 6 0 0 1 12 0v2' })
    ]),
    // Coin icon (circle)
    utxo: () => h('svg', {
      fill: 'none',
      stroke: 'currentColor',
      viewBox: '0 0 24 24'
    }, [
      h('circle', { cx: '12', cy: '12', r: '8', 'stroke-width': '2' })
    ]),
    wallet: () => h('svg', {
      fill: 'none',
      stroke: 'currentColor',
      viewBox: '0 0 24 24'
    }, [
      h('path', {
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        'stroke-width': '2',
        d: 'M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z'
      })
    ]),
    finance: () => h('svg', {
      fill: 'none',
      stroke: 'currentColor',
      viewBox: '0 0 24 24'
    }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4 19h16M8 19V9m4 10v-6m4 6V5' }),
      h('circle', { cx: '12', cy: '7', r: '1', 'stroke-width': '2' })
    ]),
    // Dollar icon for fee calculator
    fee: () => h('svg', {
      fill: 'none',
      stroke: 'currentColor',
      viewBox: '0 0 24 24'
    }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 6v12' }),
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M16 8c0-1.657-2.239-3-4-3s-4 1.343-4 3 1.343 3 4 3 4 1.343 4 3-2.239 3-4 3-4-1.343-4-3' })
    ]),
    compatibility: () => h('svg', {
      fill: 'none',
      stroke: 'currentColor',
      viewBox: '0 0 24 24'
    }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4 6a4 4 0 017.07-2.83L12 4.1l.93-.93A4 4 0 1120 6c0 4-8 10-8 10S4 10 4 6z' })
    ]),
    // Time capsule icon (clock/archive)
    timecapsule: () => h('svg', {
      fill: 'none',
      stroke: 'currentColor',
      viewBox: '0 0 24 24'
    }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' })
    ]),
    // Admin user icon
    admin: () => h('svg', {
      fill: 'none',
      stroke: 'currentColor',
      viewBox: '0 0 24 24'
    }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 14c-4.418 0-8 1.79-8 4v2h16v-2c0-2.21-3.582-4-8-4z' }),
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 12a4 4 0 100-8 4 4 0 000 8z' })
    ])
  }
  return icons[key] || icons.learn
}
</script>

<style scoped>
</style>
