<template>
  <aside class="w-64 bg-white border-r border-gray-100 px-6 py-8">
    <nav class="space-y-1">
      <button
        v-for="item in items"
        :key="item.key"
        class="w-full text-left px-3 py-2.5 rounded-lg font-medium transition-colors flex items-center gap-3"
        :class="active === item.key 
          ? 'bg-slate-800 text-white' 
          : 'text-slate-600 hover:text-slate-800 hover:bg-orange-50'"
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

