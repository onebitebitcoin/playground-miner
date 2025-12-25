<template>
  <component
    :is="clickable ? 'button' : 'div'"
    class="w-full text-left rounded-xl border border-slate-200 bg-slate-50/80 p-3 sm:p-4 transition-all"
    :class="{
      'hover:shadow-md hover:bg-white cursor-pointer': clickable,
      'cursor-default': !clickable
    }"
    @click="clickable && $emit('click')"
  >
    <div class="flex items-center gap-2">
      <component v-if="icon" :is="icon" class="w-4 h-4 sm:w-5 sm:h-5 text-slate-500 flex-shrink-0" />
      <div class="text-[10px] sm:text-xs font-medium text-slate-500 uppercase tracking-wide">
        {{ title }}
      </div>
    </div>
    <div
      class="mt-1 text-xl sm:text-2xl font-bold text-slate-900 leading-tight"
      :class="{ 'tabular-nums': isNumeric }"
    >
      {{ formattedValue }}
    </div>
    <div
      v-if="showSubtitle"
      class="text-xs text-slate-400 mt-1"
    >
      {{ subtitle }}
    </div>
  </component>
</template>

<script setup>
import { computed } from 'vue'

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
  clickable: {
    type: Boolean,
    default: false
  },
  prefix: {
    type: String,
    default: ''
  },
  suffix: {
    type: String,
    default: ''
  },
  icon: {
    type: Object,
    default: null
  }
})

defineEmits(['click'])

const isNumeric = computed(() => typeof props.value === 'number')

const formattedValue = computed(() => {
  const val = props.value
  const suffix = props.suffix ? ` ${props.suffix}` : ''
  return props.prefix + (typeof val === 'number' ? val.toLocaleString() : val) + suffix
})

const showSubtitle = computed(() => Boolean(props.subtitle && props.subtitle !== props.title))
</script>
