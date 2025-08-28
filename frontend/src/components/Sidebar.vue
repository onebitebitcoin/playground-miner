<template>
  <aside class="w-64 bg-white border-r border-slate-200 p-4">
    <div class="mb-4">
      <h2 class="text-lg font-semibold">게임 목록</h2>
    </div>
    <nav class="space-y-1">
      <button
        v-for="item in items"
        :key="item.key"
        class="w-full text-left px-3 py-2 rounded-md hover:bg-slate-100"
        :class="{ 'bg-slate-200 font-medium' : active === item.key }"
        @click="$emit('select', item.key)"
      >
        {{ item.label }}
      </button>
    </nav>
  </aside>
</template>

<script setup>
defineProps({
  items: { type: Array, default: () => [] },
  active: { type: String, default: '' },
})
</script>

<style scoped>
</style>

