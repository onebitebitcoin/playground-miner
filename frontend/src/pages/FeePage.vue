<template>
  <section class="space-y-6">
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">수수료 계산기</h1>
      <p class="text-gray-600">거래소별 수수료를 비교하여 가장 효율적인 송금 방법을 찾아보세요.</p>
    </div>

    <FeeInputSection
      :input-amount="inputAmount"
      :selected-unit="selectedUnit"
      :quick-amounts="quickAmounts"
      :placeholder="placeholderText"
      :formatted-total-amount="formattedTotalAmount"
      :formatted-bitcoin-price="formattedBitcoinPrice"
      :price-updated-text="priceUpdatedText"
      @update:input-amount="updateInputAmount"
      @update:selected-unit="updateSelectedUnit"
      @quick-select="handleQuickSelect"
    />

    <FinalPathsSection
      v-if="inputAmount"
      :has-input="Boolean(inputAmount)"
      :paths="optimalPaths"
      :actual-amount="actualAmountKRW"
      :bitcoin-price="bitcoinPrice"
      :usdt-price="usdtPriceKrw"
      :view-mode="viewMode"
      @update:viewMode="updateViewMode"
    />

    <LegacyResultsSection
      v-else-if="inputAmount && results.length > 0"
      :results="results"
      :view-mode="viewMode"
      :original-amount="actualAmountKRW"
      @update:viewMode="updateViewMode"
    />

    <div v-if="isLoading" class="bg-blue-50 border border-blue-200 rounded-lg p-6">
      <p class="text-gray-600">비트코인 가격 정보를 불러오는 중...</p>
    </div>

    <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-6">
      <div class="flex items-center">
        <svg class="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
        </svg>
        <p class="text-red-700">{{ error }}</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import FeeInputSection from '../components/fee/FeeInputSection.vue'
import FinalPathsSection from '../components/fee/FinalPathsSection.vue'
import LegacyResultsSection from '../components/fee/LegacyResultsSection.vue'
import { apiGetExchangeRates, apiGetLightningServices, apiGetOptimalPaths, apiGetWithdrawalFees } from '../api'
import { getUpbitBtcPriceKrwWithTime } from '../utils/btcPriceProvider'
import { getBtcPriceUsdt } from '../utils/btcUsdtPriceProvider'
import { buildFeeScenarios } from '../services/feeScenarioBuilder'

const inputAmount = ref('')
const selectedUnit = ref('10000')
const bitcoinPrice = ref(null)
const bitcoinPriceUpdatedAt = ref(null)
const btcPriceUsdt = ref(null)
const isLoading = ref(false)
const error = ref(null)
const results = ref([])
const optimalPaths = ref([])
const viewMode = ref('flow')

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
  boltz: 0.5,
  coinos: 0.0,
  walletofsatoshi: 1.95,
  strike: 0.0
})

const exchangeRatesInfo = ref({})
const lightningServicesInfo = ref({})

const usdtPriceKrw = computed(() => {
  const btcKrw = bitcoinPrice.value
  const btcUsdt = btcPriceUsdt.value
  if (!btcKrw || !btcUsdt) return null
  if (!Number.isFinite(btcUsdt) || btcUsdt === 0) return null
  return btcKrw / btcUsdt
})

const quickAmounts = ref([
  { label: '100만원', value: 100, unit: '10000' },
  { label: '500만원', value: 500, unit: '10000' },
  { label: '1천만원', value: 1000, unit: '10000' },
  { label: '5천만원', value: 5000, unit: '10000' },
  { label: '1억원', value: 1, unit: '100000000' },
  { label: '5억원', value: 5, unit: '100000000' },
  { label: '10억원', value: 10, unit: '100000000' }
])

const btcTransferFee = 0.0002

const actualAmountKRW = computed(() => {
  if (!inputAmount.value) return 0
  return parseFloat(inputAmount.value) * parseFloat(selectedUnit.value)
})

const formatPrice = (price) => {
  return new Intl.NumberFormat('ko-KR').format(Math.round(price || 0))
}

const formattedTotalAmount = computed(() => {
  if (!inputAmount.value) return ''
  return formatPrice(actualAmountKRW.value)
})

const formattedBitcoinPrice = computed(() => {
  if (!bitcoinPrice.value) return ''
  return formatPrice(bitcoinPrice.value)
})

const priceUpdatedText = computed(() => formatUpdatedTime(bitcoinPriceUpdatedAt.value))
const placeholderText = computed(() => getPlaceholder())

const updateInputAmount = (value) => {
  inputAmount.value = value
  calculateFees()
}

const updateSelectedUnit = (value) => {
  selectedUnit.value = value
  calculateFees()
}

const handleQuickSelect = ({ value, unit }) => {
  setQuickAmount(value, unit)
}

const updateViewMode = (mode) => {
  viewMode.value = mode
}

const getPlaceholder = () => {
  const unit = selectedUnit.value
  if (unit === '1') return '예: 1000000'
  if (unit === '10000') return '예: 100'
  if (unit === '100000000') return '예: 1'
  return '금액을 입력하세요'
}

const getActualAmount = () => {
  return actualAmountKRW.value
}

const setQuickAmount = (value, unit) => {
  inputAmount.value = value.toString()
  selectedUnit.value = unit
  calculateFees()
}

const fetchBitcoinPrice = async (force = false) => {
  if (!force && bitcoinPrice.value !== null && btcPriceUsdt.value !== null && !isLoading.value) {
    return
  }
  isLoading.value = true
  error.value = null

  try {
    const [priceData, priceUsdt] = await Promise.all([
      getUpbitBtcPriceKrwWithTime(force),
      getBtcPriceUsdt(force).catch(err => {
        console.error('BTC/USDT price fetch error:', err)
        return btcPriceUsdt.value
      })
    ])
    bitcoinPrice.value = priceData.price
    bitcoinPriceUpdatedAt.value = priceData.updatedAt
    if (priceUsdt) {
      btcPriceUsdt.value = priceUsdt
    }
  } catch (err) {
    error.value = '비트코인 가격을 불러오는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
    console.error('Upbit Bitcoin price fetch error:', err)
  } finally {
    isLoading.value = false
  }
}

const formatUpdatedTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  const seconds = date.getSeconds().toString().padStart(2, '0')
  return `${hours}:${minutes}:${seconds}`
}

const loadData = async () => {
  try {
    const exchangeResponse = await apiGetExchangeRates()
    if (exchangeResponse.success && exchangeResponse.rates) {
      exchangeResponse.rates.forEach(rate => {
        feeRates.value[rate.exchange] = rate.fee_rate
        exchangeRatesInfo.value[rate.exchange] = rate
      })
    }

    const withdrawalResponse = await apiGetWithdrawalFees()
    if (withdrawalResponse.success && withdrawalResponse.fees) {
      withdrawalResponse.fees.forEach(fee => {
        const key = `${fee.exchange}_${fee.withdrawal_type}`
        withdrawalFees.value[key] = fee.fee_btc
      })
    }

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

const nodeTypeOptions = ['exchange', 'service', 'wallet', 'user']
const inferNodeTypeFromService = (service = '') => {
  if (!service) return 'service'
  if (service === 'user') return 'user'
  if (service === 'personal_wallet') return 'wallet'
  if (/^(upbit|bithumb|binance|okx)/.test(service)) return 'exchange'
  return 'service'
}
const normalizeNodeTypeValue = (value, service = '') => {
  if (value && nodeTypeOptions.includes(value)) {
    return value
  }
  return inferNodeTypeFromService(service)
}
const withDefaultNodeType = (node) => {
  if (!node || typeof node !== 'object') return node
  return {
    ...node,
    node_type: normalizeNodeTypeValue(node.node_type, node.service)
  }
}

const loadFinalPaths = async () => {
  try {
    const res = await apiGetOptimalPaths(500)
    if (res.success) {
      optimalPaths.value = (res.paths || []).map(path => ({
        ...path,
        routes: (path.routes || []).map(route => ({
          ...route,
          source: withDefaultNodeType(route.source),
          destination: withDefaultNodeType(route.destination)
        }))
      }))
    }
  } catch (e) {
    console.error('최종 경로를 불러오지 못했습니다', e)
  }
}

const calculateFees = () => {
  if (!inputAmount.value || !bitcoinPrice.value || inputAmount.value <= 0) {
    results.value = []
    return
  }

  const amount = getActualAmount()
  const newResults = buildFeeScenarios({
    amount,
    bitcoinPrice: bitcoinPrice.value,
    btcTransferFee,
    feeRates: feeRates.value,
    withdrawalFees: withdrawalFees.value,
    lightningServices: lightningServices.value,
    lightningServicesInfo: lightningServicesInfo.value,
    exchangeRatesInfo: exchangeRatesInfo.value
  })

  results.value = newResults
}

onMounted(async () => {
  await loadFinalPaths().catch(() => {})
  await fetchBitcoinPrice()
  await loadData()

  if (inputAmount.value) {
    calculateFees()
  }
})
</script>
