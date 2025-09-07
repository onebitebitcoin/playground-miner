<template>
  <div class="relative">
    <select
      :value="modelValue"
      @change="$emit('update:modelValue', $event.target.value)"
      :class="[
        'w-full px-4 py-3 pr-10 text-sm font-medium bg-white border rounded-lg',
        'focus:ring-2 focus:outline-none transition-all duration-200 shadow-sm',
        variant === 'blue' 
          ? 'border-blue-200 text-blue-700 focus:ring-blue-500 focus:border-blue-500 hover:border-blue-300'
          : 'border-slate-300 text-slate-700 focus:ring-blue-500 focus:border-blue-500 hover:border-slate-400'
      ]"
      :style="getSelectStyles()"
    >
      <slot></slot>
    </select>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  variant: {
    type: String,
    default: 'default' // 'default' or 'blue'
  }
})

defineEmits(['update:modelValue'])

// Helper function for styles
function getSelectStyles() {
  const arrowColor = props.variant === 'blue' ? '%233B82F6' : '%23374151'
  const svgIcon = `data:image/svg+xml;charset=US-ASCII,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='2' stroke='${arrowColor}'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M19.5 8.25l-7.5 7.5-7.5-7.5'/%3e%3c/svg%3e`
  
  return {
    appearance: 'none',
    WebkitAppearance: 'none',
    MozAppearance: 'none',
    backgroundImage: `url("${svgIcon}")`,
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'right 0.75rem center',
    backgroundSize: '1.25rem 1.25rem',
    minHeight: '44px'
  }
}
</script>

<style scoped>
/* Additional Safari-specific overrides */
select {
  -webkit-appearance: none !important;
  -moz-appearance: none !important;
  appearance: none !important;
}

select::-ms-expand {
  display: none;
}

/* Webkit specific focus styles */
select:focus {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
}

/* Option text overflow prevention */
select option {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

/* Mobile-specific option styling */
@media (max-width: 640px) {
  select {
    font-size: 12px !important;
  }
  
  select option {
    font-size: 12px;
    padding: 8px 4px;
  }
}
</style>