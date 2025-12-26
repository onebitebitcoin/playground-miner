<template>
  <div class="bg-white rounded-lg shadow-md p-4 sm:p-6 mb-6">
    <h2 class="text-xl font-semibold text-gray-900 mb-4">송금 금액 입력</h2>
    <div class="mb-4">
      <label for="amount" class="block text-sm font-medium text-gray-700 mb-2">
        송금할 금액
      </label>
      <div class="flex gap-2">
        <input
          id="amount"
          :value="inputAmount"
          type="number"
          :placeholder="placeholder"
          class="flex-1 min-w-0 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          @input="onInputChange"
        />
        <select
          :value="selectedUnit"
          class="flex-shrink-0 px-2 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white w-16 text-sm"
          @change="onUnitChange"
        >
          <option value="1">원</option>
          <option value="10000">만원</option>
          <option value="100000000">억원</option>
        </select>
      </div>
      <div v-if="showTotalAmount" class="mt-2 text-sm text-gray-600">
        총 금액: {{ formattedTotalAmount }}원
      </div>
    </div>

    <div v-if="quickAmounts.length" class="mb-4">
      <div class="text-sm font-medium text-gray-700 mb-2">빠른 입력</div>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="preset in quickAmounts"
          :key="preset.value"
          :disabled="isLoadingPaths"
          :class="[
            'px-3 py-1.5 text-sm rounded-lg transition-colors',
            isLoadingPaths
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-gray-100 hover:bg-gray-200 text-gray-700 cursor-pointer'
          ]"
          @click="emit('quick-select', preset)"
        >
          {{ preset.label }}
        </button>
      </div>
    </div>

    <div v-if="formattedBitcoinPrice" class="text-sm text-gray-600">
      현재 비트코인 가격(업비트 기준): {{ formattedBitcoinPrice }}원
      <span v-if="priceUpdatedText" class="text-xs text-gray-500 ml-2">
        (업데이트: {{ priceUpdatedText }})
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  inputAmount: {
    type: [String, Number],
    default: ''
  },
  selectedUnit: {
    type: String,
    default: '1'
  },
  quickAmounts: {
    type: Array,
    default: () => []
  },
  placeholder: {
    type: String,
    default: ''
  },
  formattedTotalAmount: {
    type: String,
    default: ''
  },
  formattedBitcoinPrice: {
    type: String,
    default: ''
  },
  priceUpdatedText: {
    type: String,
    default: ''
  },
  isLoadingPaths: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:inputAmount', 'update:selectedUnit', 'quick-select'])

const showTotalAmount = computed(() => Boolean(props.formattedTotalAmount))

const onInputChange = (event) => {
  emit('update:inputAmount', event.target.value)
}

const onUnitChange = (event) => {
  emit('update:selectedUnit', event.target.value)
}
</script>
