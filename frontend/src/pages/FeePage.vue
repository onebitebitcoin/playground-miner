<template>
  <div class="min-h-screen bg-gray-50 p-4">
    <div class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">수수료 계산기</h1>
        <p class="text-gray-600">거래소별 수수료를 비교하여 가장 효율적인 송금 방법을 찾아보세요.</p>
      </div>

      <!-- Input Section -->
      <div class="bg-white rounded-lg shadow-md p-4 sm:p-6 mb-6">
        <h2 class="text-xl font-semibold text-gray-900 mb-4">송금 금액 입력</h2>
        <div class="mb-4">
          <label for="amount" class="block text-sm font-medium text-gray-700 mb-2">
            송금할 금액
          </label>
          <div class="flex gap-2">
            <input
              id="amount"
              v-model="inputAmount"
              type="number"
              :placeholder="getPlaceholder()"
              class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              @input="calculateFees"
            />
            <select
              v-model="selectedUnit"
              class="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white min-w-[80px]"
              @change="calculateFees"
            >
              <option value="1">원</option>
              <option value="10000">만원</option>
              <option value="100000000">억원</option>
            </select>
          </div>
          <div v-if="inputAmount" class="mt-2 text-sm text-gray-600">
            총 금액: {{ formatPrice(getActualAmount()) }}원
          </div>
        </div>

        <!-- Quick Amount Buttons -->
        <div class="mb-4">
          <div class="text-sm font-medium text-gray-700 mb-2">빠른 입력</div>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="preset in quickAmounts"
              :key="preset.value"
              class="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
              @click="setQuickAmount(preset.value, preset.unit)"
            >
              {{ preset.label }}
            </button>
          </div>
        </div>

        <div v-if="bitcoinPrice" class="text-sm text-gray-600">
          현재 비트코인 가격: {{ formatPrice(bitcoinPrice) }}원
        </div>
      </div>

      <!-- Results Section -->
      <div v-if="inputAmount && results.length > 0" class="space-y-6">
        <h2 class="text-xl font-semibold text-gray-900">수수료 비교 결과</h2>

        <!-- Option Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          <div
            v-for="(result, index) in sortedResults"
            :key="result.id"
            :class="[
              'bg-white rounded-lg shadow-md p-4 sm:p-6 border-2 transition-all',
              index === 0 ? 'border-green-500 ring-2 ring-green-200' : 'border-gray-200'
            ]"
          >
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-base sm:text-lg font-semibold text-gray-900">{{ result.title }}</h3>
              <div v-if="index === 0" class="bg-green-500 text-white px-3 py-1 rounded-full text-sm font-medium">
                최적
              </div>
            </div>

            <div class="space-y-3">
              <div class="text-sm text-gray-600">
                <div class="font-medium">{{ result.description }}</div>
              </div>

              <!-- Mobile: toggle to show details -->
              <div class="md:hidden">
                <button
                  class="mt-1 mb-2 text-sm px-3 py-2 rounded bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 w-full font-medium"
                  @click="toggleDetails(result.id)"
                >
                  {{ detailsOpenById[result.id] ? '📋 상세 수수료 접기' : '📋 상세 수수료 보기' }}
                </button>
              </div>

              <!-- Details wrapper: always visible on md+, toggled on mobile -->
              <div v-show="!isMobile || detailsOpenById[result.id]">
                <!-- Exchange Fee Details -->
                <div v-if="result.exchanges && result.exchanges.length > 0" class="bg-gray-50 p-3 rounded-lg mb-3">
                  <div class="text-sm font-semibold text-gray-800 mb-2 flex items-center">
                    🏪 거래소별 수수료율
                  </div>
                  <div class="space-y-2">
                    <div v-for="exchange in result.exchanges" :key="exchange.name" class="text-sm">
                      <div class="flex justify-between items-center">
                        <span class="text-gray-700 font-medium">{{ exchange.name }}:</span>
                        <span class="font-bold text-blue-600">{{ exchange.rate }}%</span>
                      </div>
                      <div v-if="exchange.note && exchange.note !== ''" class="text-xs text-orange-600 font-medium mt-1 bg-orange-50 px-2 py-1 rounded">
                        ⚠️ {{ exchange.note }}
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Withdrawal Fee Details -->
                <div v-if="result.withdrawalFees && result.withdrawalFees.length > 0" class="bg-blue-50 p-3 rounded-lg mb-3">
                  <div class="text-sm font-semibold text-gray-800 mb-2 flex items-center">
                    💸 출금 수수료
                  </div>
                  <div class="space-y-2">
                    <div v-for="fee in result.withdrawalFees" :key="fee.name" class="text-sm">
                      <div class="flex justify-between items-center">
                        <span class="text-gray-700 font-medium">{{ fee.name }}:</span>
                        <div class="text-right">
                          <div class="font-bold text-blue-600">{{ fee.amount }} BTC</div>
                          <div class="text-xs text-gray-600">({{ formatPrice(fee.amountKrw) }}원)</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Lightning Service Details -->
                <div v-if="result.lightningServices && result.lightningServices.length > 0" class="bg-yellow-50 p-3 rounded-lg mb-3">
                  <div class="text-sm font-semibold text-gray-800 mb-2 flex items-center">
                    ⚡ {{ getLightningHeader(result.lightningServices) }}
                  </div>
                  <div class="space-y-2">
                    <div v-for="service in result.lightningServices" :key="service.name" class="text-sm">
                      <div class="flex justify-between items-center">
                        <span class="text-gray-700 font-medium">
                          <template v-if="getServiceUrl(service.name)">
                            <a :href="getServiceUrl(service.name)" target="_blank" rel="noopener noreferrer" class="underline hover:text-blue-800 text-blue-600">
                              {{ service.name }}
                            </a>:
                          </template>
                          <template v-else>
                            {{ service.name }}:
                          </template>
                        </span>
                        <span class="font-bold text-yellow-600">{{ service.rate }}%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Fee Breakdown -->
              <div class="border-t-2 border-gray-200 pt-4 mt-4">
                <div class="space-y-2">
                  <div class="flex justify-between text-gray-700 text-sm">
                    <span class="font-medium">거래 수수료:</span>
                    <span class="font-bold">{{ formatPrice(result.tradingFee) }}원</span>
                  </div>
                  <div v-if="result.transferFee > 0" class="flex justify-between text-gray-700 text-sm">
                    <span class="font-medium">송금 수수료:</span>
                    <span class="font-bold">{{ formatPrice(result.transferFee) }}원</span>
                  </div>
                  <div v-if="result.lightningFee > 0" class="flex justify-between text-gray-700 text-sm">
                    <span class="font-medium">라이트닝 수수료:</span>
                    <span class="font-bold">{{ formatPrice(result.lightningFee) }}원</span>
                  </div>
                  <div class="flex justify-between font-bold text-gray-900 border-t-2 border-gray-300 pt-3 mt-3 text-base">
                    <span>💰 총 수수료:</span>
                    <span class="text-red-600">{{ formatPrice(result.totalFee) }}원</span>
                  </div>
                  <div class="flex justify-between font-bold text-green-700 text-base bg-green-50 px-3 py-2 rounded-lg">
                    <span>✅ 수령 가능 금액:</span>
                    <span>{{ formatPrice(result.actualAmount) }}원</span>
                  </div>
                  <div class="text-center text-sm text-gray-600 mt-3 bg-gray-50 py-2 rounded-lg">
                    📊 총 수수료율: <span class="font-bold">{{ result.feeRate }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Savings Information -->
        <div v-if="maxSavings > 0" class="bg-green-50 border border-green-200 rounded-lg p-6">
          <div class="flex items-center">
            <svg class="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
            <div>
              <h3 class="text-lg font-semibold text-green-800">절약 효과</h3>
              <p class="text-green-700">최적 방법 선택 시 최대 {{ formatPrice(maxSavings) }}원을 절약할 수 있습니다!</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <p class="text-gray-600">비트코인 가격 정보를 불러오는 중...</p>
      </div>

      <!-- Error State -->
      <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-6">
        <div class="flex items-center">
          <svg class="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
          <p class="text-red-700">{{ error }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { apiGetExchangeRates, apiGetWithdrawalFees, apiGetLightningServices } from '../api'

// Reactive data
const inputAmount = ref('')
const selectedUnit = ref('10000') // Default to 만원
const bitcoinPrice = ref(null)
const isLoading = ref(false)
const error = ref(null)
const results = ref([])
const isMobile = ref(false)
const detailsOpenById = ref({})

// Quick amount presets
const quickAmounts = ref([
  { label: '100만원', value: 100, unit: '10000' },
  { label: '500만원', value: 500, unit: '10000' },
  { label: '1천만원', value: 1000, unit: '10000' },
  { label: '5천만원', value: 5000, unit: '10000' },
  { label: '1억원', value: 1, unit: '100000000' },
  { label: '5억원', value: 5, unit: '100000000' },
  { label: '10억원', value: 10, unit: '100000000' }
])

// Fee rates and related data
const feeRates = ref({
  upbit_btc: 0.05,
  upbit_usdt: 0.01,
  bithumb: 0.04,
  okx: 0.1,
  binance: 0.1
})

const withdrawalFees = ref({
  okx_onchain: 0.00001,
  okx_lightning: 0.00001,
  binance_onchain: 0.00003,
  binance_lightning: 0.00001
})

const lightningServices = ref({
  boltz: 0.1,
  coinos: 0.4
})

const exchangeRatesInfo = ref({})
const withdrawalFeesInfo = ref({})
const lightningServicesInfo = ref({})

// Fixed transfer fee (0.0002 BTC for traditional transfers)
const btcTransferFee = 0.0002

// Computed properties
const sortedResults = computed(() => {
  return [...results.value].sort((a, b) => a.totalFee - b.totalFee)
})

const maxSavings = computed(() => {
  if (results.value.length < 2) return 0
  const sorted = sortedResults.value
  return sorted[sorted.length - 1].totalFee - sorted[0].totalFee
})

// Methods
const formatPrice = (price) => {
  return new Intl.NumberFormat('ko-KR').format(Math.round(price))
}

const getLightningHeader = (services) => {
  if (!services || services.length === 0) return '라이트닝 서비스'
  const names = services.map(s => (s?.name || '')).join(' ').toLowerCase()
  if (names.includes('boltz') || names.includes('coinos')) {
    return '라이트닝 & 온체인 출금'
  }
  return '라이트닝 서비스'
}

const getServiceUrl = (name) => {
  const n = (name || '').toLowerCase()
  if (n.includes('boltz')) return 'https://boltz.exchange'
  if (n.includes('coinos')) return 'https://coinos.io'
  return null
}

const getPlaceholder = () => {
  const unit = selectedUnit.value
  if (unit === '1') return '예: 1000000'
  if (unit === '10000') return '예: 100'
  if (unit === '100000000') return '예: 1'
  return '금액을 입력하세요'
}

const getActualAmount = () => {
  if (!inputAmount.value) return 0
  return parseFloat(inputAmount.value) * parseFloat(selectedUnit.value)
}

const setQuickAmount = (value, unit) => {
  inputAmount.value = value.toString()
  selectedUnit.value = unit
  calculateFees()
}

const fetchBitcoinPrice = async () => {
  isLoading.value = true
  error.value = null

  try {
    const response = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=krw')
    const data = await response.json()

    if (data.bitcoin && data.bitcoin.krw) {
      bitcoinPrice.value = data.bitcoin.krw
    } else {
      throw new Error('비트코인 가격 정보를 가져올 수 없습니다.')
    }
  } catch (err) {
    error.value = '비트코인 가격을 불러오는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
    console.error('Bitcoin price fetch error:', err)
  } finally {
    isLoading.value = false
  }
}

const loadData = async () => {
  try {
    // Load exchange rates
    const exchangeResponse = await apiGetExchangeRates()
    if (exchangeResponse.success && exchangeResponse.rates) {
      exchangeResponse.rates.forEach(rate => {
        feeRates.value[rate.exchange] = rate.fee_rate
        exchangeRatesInfo.value[rate.exchange] = rate
      })
    }

    // Load withdrawal fees
    const withdrawalResponse = await apiGetWithdrawalFees()
    if (withdrawalResponse.success && withdrawalResponse.fees) {
      withdrawalResponse.fees.forEach(fee => {
        const key = `${fee.exchange}_${fee.withdrawal_type}`
        withdrawalFees.value[key] = fee.fee_btc
        withdrawalFeesInfo.value[key] = fee
      })
    }

    // Load lightning services
    const lightningResponse = await apiGetLightningServices()
    if (lightningResponse.success && lightningResponse.services) {
      lightningResponse.services.forEach(service => {
        lightningServices.value[service.service] = service.fee_rate
        lightningServicesInfo.value[service.service] = service
      })
    }
  } catch (err) {
    console.error('Data fetch error:', err)
  }
}

const calculateFees = () => {
  if (!inputAmount.value || !bitcoinPrice.value || inputAmount.value <= 0) {
    results.value = []
    return
  }

  const amount = getActualAmount()
  const newResults = []

  // Scenarios with direct BTC transfer from Korean exchanges to international exchanges
  // 1. 업비트 BTC → 바이낸스 → 온체인 개인지갑
  newResults.push({
    id: 'upbit-btc-binance-onchain',
    title: '업비트 BTC → 바이낸스 → 온체인 개인지갑',
    description: '업비트 비트코인 직접 송금 → 바이낸스 → 온체인 개인지갑 출금',
    exchanges: [
      {
        name: '업비트 (BTC)',
        rate: feeRates.value.upbit_btc,
        note: exchangeRatesInfo.value.upbit_btc?.is_event ? '한시적 이벤트' : ''
      }
    ],
    withdrawalFees: [
      {
        name: '업비트 BTC 송금',
        amount: btcTransferFee,
        amountKrw: btcTransferFee * bitcoinPrice.value
      },
      {
        name: '바이낸스 온체인 개인지갑',
        amount: withdrawalFees.value.binance_onchain,
        amountKrw: withdrawalFees.value.binance_onchain * bitcoinPrice.value
      }
    ],
    tradingFee: amount * (feeRates.value.upbit_btc / 100),
    transferFee: btcTransferFee * bitcoinPrice.value + withdrawalFees.value.binance_onchain * bitcoinPrice.value,
    lightningFee: 0,
    totalFee: 0,
    actualAmount: 0,
    feeRate: 0
  })

  // 2. 업비트 BTC → OKX → 온체인 개인지갑
  newResults.push({
    id: 'upbit-btc-okx-onchain',
    title: '업비트 BTC → OKX → 온체인 개인지갑',
    description: '업비트 비트코인 직접 송금 → OKX → 온체인 개인지갑 출금',
    exchanges: [
      {
        name: '업비트 (BTC)',
        rate: feeRates.value.upbit_btc,
        note: exchangeRatesInfo.value.upbit_btc?.is_event ? '한시적 이벤트' : ''
      }
    ],
    withdrawalFees: [
      {
        name: '업비트 BTC 송금',
        amount: btcTransferFee,
        amountKrw: btcTransferFee * bitcoinPrice.value
      },
      {
        name: 'OKX 온체인 개인지갑',
        amount: withdrawalFees.value.okx_onchain,
        amountKrw: withdrawalFees.value.okx_onchain * bitcoinPrice.value
      }
    ],
    tradingFee: amount * (feeRates.value.upbit_btc / 100),
    transferFee: btcTransferFee * bitcoinPrice.value + withdrawalFees.value.okx_onchain * bitcoinPrice.value,
    lightningFee: 0,
    totalFee: 0,
    actualAmount: 0,
    feeRate: 0
  })

  // 3. 바이낸스 BTC → OKX → 온체인 개인지갑
  newResults.push({
    id: 'binance-btc-okx-onchain',
    title: '바이낸스 BTC → OKX → 온체인 개인지갑',
    description: '바이낸스 비트코인 직접 송금 → OKX → 온체인 개인지갑 출금',
    exchanges: [
      {
        name: '바이낸스 (BTC)',
        rate: feeRates.value.binance,
        note: exchangeRatesInfo.value.binance?.is_event ? '한시적 이벤트' : ''
      }
    ],
    withdrawalFees: [
      {
        name: '바이낸스 BTC 송금',
        amount: withdrawalFees.value.binance_onchain,
        amountKrw: withdrawalFees.value.binance_onchain * bitcoinPrice.value
      },
      {
        name: 'OKX 온체인 개인지갑',
        amount: withdrawalFees.value.okx_onchain,
        amountKrw: withdrawalFees.value.okx_onchain * bitcoinPrice.value
      }
    ],
    tradingFee: amount * (feeRates.value.binance / 100),
    transferFee: withdrawalFees.value.binance_onchain * bitcoinPrice.value + withdrawalFees.value.okx_onchain * bitcoinPrice.value,
    lightningFee: 0,
    totalFee: 0,
    actualAmount: 0,
    feeRate: 0
  })

  // Scenarios ending in onchain personal wallet via USDT
  // 4. 업비트 → OKX → 온체인 개인지갑
  newResults.push({
    id: 'upbit-usdt-okx-onchain',
    title: '업비트 → OKX → 온체인 개인지갑',
    description: '업비트 USDT → OKX 비트코인 매수 → 온체인 개인지갑 출금',
    exchanges: [
      {
        name: '업비트 (USDT)',
        rate: feeRates.value.upbit_usdt,
        note: exchangeRatesInfo.value.upbit_usdt?.is_event ? '한시적 이벤트' : ''
      },
      {
        name: 'OKX',
        rate: feeRates.value.okx,
        note: exchangeRatesInfo.value.okx?.is_event ? '한시적 이벤트' : ''
      }
    ],
    withdrawalFees: [{
      name: 'OKX 온체인 개인지갑',
      amount: withdrawalFees.value.okx_onchain,
      amountKrw: withdrawalFees.value.okx_onchain * bitcoinPrice.value
    }],
    tradingFee: amount * (feeRates.value.upbit_usdt / 100) + amount * (feeRates.value.okx / 100),
    transferFee: withdrawalFees.value.okx_onchain * bitcoinPrice.value,
    lightningFee: 0,
    totalFee: 0,
    actualAmount: 0,
    feeRate: 0
  })

  // 5. 업비트 → 바이낸스 → 온체인 개인지갑
  newResults.push({
    id: 'upbit-usdt-binance-onchain',
    title: '업비트 → 바이낸스 → 온체인 개인지갑',
    description: '업비트 USDT → 바이낸스 비트코인 매수 → 온체인 개인지갑 출금',
    exchanges: [
      {
        name: '업비트 (USDT)',
        rate: feeRates.value.upbit_usdt,
        note: exchangeRatesInfo.value.upbit_usdt?.is_event ? '한시적 이벤트' : ''
      },
      {
        name: '바이낸스',
        rate: feeRates.value.binance,
        note: exchangeRatesInfo.value.binance?.is_event ? '한시적 이벤트' : ''
      }
    ],
    withdrawalFees: [{
      name: '바이낸스 온체인 개인지갑',
      amount: withdrawalFees.value.binance_onchain,
      amountKrw: withdrawalFees.value.binance_onchain * bitcoinPrice.value
    }],
    tradingFee: amount * (feeRates.value.upbit_usdt / 100) + amount * (feeRates.value.binance / 100),
    transferFee: withdrawalFees.value.binance_onchain * bitcoinPrice.value,
    lightningFee: 0,
    totalFee: 0,
    actualAmount: 0,
    feeRate: 0
  })

  // Direct BTC transfer scenarios with Lightning
  // 6. 업비트 BTC → 바이낸스 → Boltz → 온체인 개인지갑
  newResults.push({
    id: 'upbit-btc-binance-lightning-boltz',
    title: '업비트 BTC → 바이낸스 → Boltz → 온체인 개인지갑',
    description: '업비트 비트코인 직접 송금 → 바이낸스 → 라이트닝 → Boltz → 온체인 개인지갑',
    exchanges: [
      {
        name: '업비트 (BTC)',
        rate: feeRates.value.upbit_btc,
        note: exchangeRatesInfo.value.upbit_btc?.is_event ? '한시적 이벤트' : ''
      }
    ],
    withdrawalFees: [
      {
        name: '업비트 BTC 송금',
        amount: btcTransferFee,
        amountKrw: btcTransferFee * bitcoinPrice.value
      },
      {
        name: '바이낸스 라이트닝',
        amount: withdrawalFees.value.binance_lightning,
        amountKrw: withdrawalFees.value.binance_lightning * bitcoinPrice.value
      }
    ],
    lightningServices: [{
      name: 'Boltz Exchange',
      rate: lightningServices.value.boltz
    }],
    tradingFee: amount * (feeRates.value.upbit_btc / 100),
    transferFee: btcTransferFee * bitcoinPrice.value + withdrawalFees.value.binance_lightning * bitcoinPrice.value,
    lightningFee: amount * (lightningServices.value.boltz / 100),
    totalFee: 0,
    actualAmount: 0,
    feeRate: 0
  })

  // 7. 업비트 BTC → 바이낸스 → Coinos → 온체인 개인지갑
  newResults.push({
    id: 'upbit-btc-binance-lightning-coinos',
    title: '업비트 BTC → 바이낸스 → Coinos → 온체인 개인지갑',
    description: '업비트 비트코인 직접 송금 → 바이낸스 → 라이트닝 → Coinos → 온체인 개인지갑',
    exchanges: [
      {
        name: '업비트 (BTC)',
        rate: feeRates.value.upbit_btc,
        note: exchangeRatesInfo.value.upbit_btc?.is_event ? '한시적 이벤트' : ''
      }
    ],
    withdrawalFees: [
      {
        name: '업비트 BTC 송금',
        amount: btcTransferFee,
        amountKrw: btcTransferFee * bitcoinPrice.value
      },
      {
        name: '바이낸스 라이트닝',
        amount: withdrawalFees.value.binance_lightning,
        amountKrw: withdrawalFees.value.binance_lightning * bitcoinPrice.value
      }
    ],
    lightningServices: [{
      name: 'Coinos',
      rate: lightningServices.value.coinos
    }],
    tradingFee: amount * (feeRates.value.upbit_btc / 100),
    transferFee: btcTransferFee * bitcoinPrice.value + withdrawalFees.value.binance_lightning * bitcoinPrice.value,
    lightningFee: amount * (lightningServices.value.coinos / 100),
    totalFee: 0,
    actualAmount: 0,
    feeRate: 0
  })

  // 8. 업비트 BTC → OKX → Boltz → 온체인 개인지갑
  newResults.push({
    id: 'upbit-btc-okx-lightning-boltz',
    title: '업비트 BTC → OKX → Boltz → 온체인 개인지갑',
    description: '업비트 비트코인 직접 송금 → OKX → 라이트닝 → Boltz → 온체인 개인지갑',
    exchanges: [
      {
        name: '업비트 (BTC)',
        rate: feeRates.value.upbit_btc,
        note: exchangeRatesInfo.value.upbit_btc?.is_event ? '한시적 이벤트' : ''
      }
    ],
    withdrawalFees: [
      {
        name: '업비트 BTC 송금',
        amount: btcTransferFee,
        amountKrw: btcTransferFee * bitcoinPrice.value
      },
      {
        name: 'OKX 라이트닝',
        amount: withdrawalFees.value.okx_lightning,
        amountKrw: withdrawalFees.value.okx_lightning * bitcoinPrice.value
      }
    ],
    lightningServices: [{
      name: 'Boltz Exchange',
      rate: lightningServices.value.boltz
    }],
    tradingFee: amount * (feeRates.value.upbit_btc / 100),
    transferFee: btcTransferFee * bitcoinPrice.value + withdrawalFees.value.okx_lightning * bitcoinPrice.value,
    lightningFee: amount * (lightningServices.value.boltz / 100),
    totalFee: 0,
    actualAmount: 0,
    feeRate: 0
  })

  // 9. 업비트 BTC → OKX → Coinos → 온체인 개인지갑
  newResults.push({
    id: 'upbit-btc-okx-lightning-coinos',
    title: '업비트 BTC → OKX → Coinos → 온체인 개인지갑',
    description: '업비트 비트코인 직접 송금 → OKX → 라이트닝 → Coinos → 온체인 개인지갑',
    exchanges: [
      {
        name: '업비트 (BTC)',
        rate: feeRates.value.upbit_btc,
        note: exchangeRatesInfo.value.upbit_btc?.is_event ? '한시적 이벤트' : ''
      }
    ],
    withdrawalFees: [
      {
        name: '업비트 BTC 송금',
        amount: btcTransferFee,
        amountKrw: btcTransferFee * bitcoinPrice.value
      },
      {
        name: 'OKX 라이트닝',
        amount: withdrawalFees.value.okx_lightning,
        amountKrw: withdrawalFees.value.okx_lightning * bitcoinPrice.value
      }
    ],
    lightningServices: [{
      name: 'Coinos',
      rate: lightningServices.value.coinos
    }],
    tradingFee: amount * (feeRates.value.upbit_btc / 100),
    transferFee: btcTransferFee * bitcoinPrice.value + withdrawalFees.value.okx_lightning * bitcoinPrice.value,
    lightningFee: amount * (lightningServices.value.coinos / 100),
    totalFee: 0,
    actualAmount: 0,
    feeRate: 0
  })

  // USDT Lightning scenarios
  // 10. 업비트 → OKX → Boltz → 온체인 개인지갑
  newResults.push({
    id: 'upbit-usdt-okx-lightning-boltz',
    title: '업비트 → OKX → Boltz → 온체인 개인지갑',
    description: '업비트 USDT → OKX → 라이트닝 → Boltz → 온체인 개인지갑',
    exchanges: [
      {
        name: '업비트 (USDT)',
        rate: feeRates.value.upbit_usdt,
        note: exchangeRatesInfo.value.upbit_usdt?.is_event ? '한시적 이벤트' : ''
      },
      {
        name: 'OKX',
        rate: feeRates.value.okx,
        note: exchangeRatesInfo.value.okx?.is_event ? '한시적 이벤트' : ''
      }
    ],
    withdrawalFees: [{
      name: 'OKX 라이트닝',
      amount: withdrawalFees.value.okx_lightning,
      amountKrw: withdrawalFees.value.okx_lightning * bitcoinPrice.value
    }],
    lightningServices: [{
      name: 'Boltz Exchange',
      rate: lightningServices.value.boltz
    }],
    tradingFee: amount * (feeRates.value.upbit_usdt / 100) + amount * (feeRates.value.okx / 100),
    transferFee: withdrawalFees.value.okx_lightning * bitcoinPrice.value,
    lightningFee: amount * (lightningServices.value.boltz / 100),
    totalFee: 0,
    actualAmount: 0,
    feeRate: 0
  })

  // 11. 업비트 → OKX → Coinos → 온체인 개인지갑
  newResults.push({
    id: 'upbit-usdt-okx-lightning-coinos',
    title: '업비트 → OKX → Coinos → 온체인 개인지갑',
    description: '업비트 USDT → OKX → 라이트닝 → Coinos → 온체인 개인지갑',
    exchanges: [
      {
        name: '업비트 (USDT)',
        rate: feeRates.value.upbit_usdt,
        note: exchangeRatesInfo.value.upbit_usdt?.is_event ? '한시적 이벤트' : ''
      },
      {
        name: 'OKX',
        rate: feeRates.value.okx,
        note: exchangeRatesInfo.value.okx?.is_event ? '한시적 이벤트' : ''
      }
    ],
    withdrawalFees: [{
      name: 'OKX 라이트닝',
      amount: withdrawalFees.value.okx_lightning,
      amountKrw: withdrawalFees.value.okx_lightning * bitcoinPrice.value
    }],
    lightningServices: [{
      name: 'Coinos',
      rate: lightningServices.value.coinos
    }],
    tradingFee: amount * (feeRates.value.upbit_usdt / 100) + amount * (feeRates.value.okx / 100),
    transferFee: withdrawalFees.value.okx_lightning * bitcoinPrice.value,
    lightningFee: amount * (lightningServices.value.coinos / 100),
    totalFee: 0,
    actualAmount: 0,
    feeRate: 0
  })

  // 12. 업비트 → 바이낸스 → Boltz → 온체인 개인지갑
  newResults.push({
    id: 'upbit-usdt-binance-lightning-boltz',
    title: '업비트 → 바이낸스 → Boltz → 온체인 개인지갑',
    description: '업비트 USDT → 바이낸스 → 라이트닝 → Boltz → 온체인 개인지갑',
    exchanges: [
      {
        name: '업비트 (USDT)',
        rate: feeRates.value.upbit_usdt,
        note: exchangeRatesInfo.value.upbit_usdt?.is_event ? '한시적 이벤트' : ''
      },
      {
        name: '바이낸스',
        rate: feeRates.value.binance,
        note: exchangeRatesInfo.value.binance?.is_event ? '한시적 이벤트' : ''
      }
    ],
    withdrawalFees: [{
      name: '바이낸스 라이트닝',
      amount: withdrawalFees.value.binance_lightning,
      amountKrw: withdrawalFees.value.binance_lightning * bitcoinPrice.value
    }],
    lightningServices: [{
      name: 'Boltz Exchange',
      rate: lightningServices.value.boltz
    }],
    tradingFee: amount * (feeRates.value.upbit_usdt / 100) + amount * (feeRates.value.binance / 100),
    transferFee: withdrawalFees.value.binance_lightning * bitcoinPrice.value,
    lightningFee: amount * (lightningServices.value.boltz / 100),
    totalFee: 0,
    actualAmount: 0,
    feeRate: 0
  })

  // 13. 업비트 → 바이낸스 → Coinos → 온체인 개인지갑
  newResults.push({
    id: 'upbit-usdt-binance-lightning-coinos',
    title: '업비트 → 바이낸스 → Coinos → 온체인 개인지갑',
    description: '업비트 USDT → 바이낸스 → 라이트닝 → Coinos → 온체인 개인지갑',
    exchanges: [
      {
        name: '업비트 (USDT)',
        rate: feeRates.value.upbit_usdt,
        note: exchangeRatesInfo.value.upbit_usdt?.is_event ? '한시적 이벤트' : ''
      },
      {
        name: '바이낸스',
        rate: feeRates.value.binance,
        note: exchangeRatesInfo.value.binance?.is_event ? '한시적 이벤트' : ''
      }
    ],
    withdrawalFees: [{
      name: '바이낸스 라이트닝',
      amount: withdrawalFees.value.binance_lightning,
      amountKrw: withdrawalFees.value.binance_lightning * bitcoinPrice.value
    }],
    lightningServices: [{
      name: 'Coinos',
      rate: lightningServices.value.coinos
    }],
    tradingFee: amount * (feeRates.value.upbit_usdt / 100) + amount * (feeRates.value.binance / 100),
    transferFee: withdrawalFees.value.binance_lightning * bitcoinPrice.value,
    lightningFee: amount * (lightningServices.value.coinos / 100),
    totalFee: 0,
    actualAmount: 0,
    feeRate: 0
  })

  // Calculate totals and final amounts for all scenarios
  newResults.forEach(result => {
    result.totalFee = result.tradingFee + result.transferFee + result.lightningFee
    result.actualAmount = amount - result.totalFee
    result.feeRate = ((result.totalFee / amount) * 100).toFixed(3)
  })

  results.value = newResults
  // Initialize detail toggle states for new results on mobile
  if (isMobile.value) {
    const map = {}
    for (const r of newResults) map[r.id] = false
    detailsOpenById.value = map
  }
}

const toggleDetails = (id) => {
  detailsOpenById.value[id] = !detailsOpenById.value[id]
}

// Initialize data
onMounted(async () => {
  // Detect mobile viewport
  const mq = window.matchMedia('(max-width: 767px)')
  const updateMobile = () => { isMobile.value = mq.matches }
  updateMobile()
  try { mq.addEventListener('change', updateMobile) } catch (_) { mq.addListener(updateMobile) }

  await fetchBitcoinPrice()
  await loadData()

  // Calculate fees if there's already an amount entered
  if (inputAmount.value) {
    calculateFees()
  }
})
</script>
