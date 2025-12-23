<template>
  <component
    :is="clickable ? 'button' : 'div'"
    class="flex items-center justify-center gap-1 sm:gap-2 transition-colors rounded-lg"
    :class="{
      'hover:bg-slate-50 p-1 sm:p-2 cursor-pointer': clickable,
      'cursor-default': !clickable
    }"
    @click="clickable && $emit('click')"
  >
    <div 
      class="w-6 h-6 sm:w-8 sm:h-8 rounded-lg flex items-center justify-center"
      :class="iconClasses"
    >
      <Icon 
        :name="icon" 
        class="w-3 h-3 sm:w-4 sm:h-4"
        :class="iconColorClasses"
      />
    </div>
    <div>
      <div 
        class="font-bold text-slate-800 text-sm sm:text-base"
        :class="{ 'tabular-nums': isNumeric }"
      >
        {{ formattedValue }}
      </div>
      <div class="text-[10px] sm:text-xs text-slate-500">
        {{ subtitle }}
      </div>
    </div>
  </component>
</template>

<script setup>
import { computed } from 'vue'
import Icon from './Icon.vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number],
    required: true
  },
  subtitle: {
    type: String,
    required: true
  },
  icon: {
    type: String,
    required: true
  },
  color: {
    type: String,
    default: 'slate',
    validator: (value) => ['amber', 'emerald', 'slate'].includes(value)
  },
  clickable: {
    type: Boolean,
    default: false
  },
  prefix: {
    type: String,
    default: ''
  }
})

defineEmits(['click'])

const colorMap = {
  amber: {
    bg: 'bg-amber-100',
    text: 'text-amber-600'
  },
  emerald: {
    bg: 'bg-emerald-100',
    text: 'text-emerald-600'
  },
  slate: {
    bg: 'bg-slate-100',
    text: 'text-slate-600'
  }
}

const iconClasses = computed(() => colorMap[props.color]?.bg || colorMap.slate.bg)
const iconColorClasses = computed(() => colorMap[props.color]?.text || colorMap.slate.text)

const isNumeric = computed(() => typeof props.value === 'number')

const formattedValue = computed(() => {
  const val = props.value
  return props.prefix + (typeof val === 'number' ? val.toLocaleString() : val)
})
</script>
