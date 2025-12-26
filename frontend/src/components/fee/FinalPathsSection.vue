<template>
  <div v-if="hasInput" class="space-y-6">
    <div v-if="hasAnyPaths" class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
      <h2 class="text-lg sm:text-xl font-semibold text-gray-900">
        최종 경로 기반 수수료 비교 ({{ sortedPaths.length }}개)
      </h2>
      <div class="flex flex-col sm:flex-row sm:flex-wrap sm:items-center sm:justify-end gap-3">
        <div class="flex flex-col sm:flex-row sm:items-center gap-2 bg-transparent border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700">
          <label class="inline-flex items-center gap-2">
            <input type="checkbox" v-model="finalFilterExcludeLightning" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500">
            라이트닝 경로 제외
          </label>
          <label class="inline-flex items-center gap-2">
            <input type="checkbox" v-model="finalFilterExcludeKycWithdrawal" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500">
            KYC 제외
          </label>
          <label class="inline-flex items-center gap-2">
            <input type="checkbox" v-model="finalFilterExcludeCustodialWithdrawal" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500">
            수탁형 제외
          </label>
          <label class="inline-flex items-center gap-2">
            <input type="checkbox" v-model="finalFilterOnlyEvents" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500">
            이벤트 경로만 보기
          </label>
        </div>
        <select
          v-model="finalFilterNode"
          class="self-start sm:self-auto px-2 py-1.5 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-sm"
        >
          <option value="">전체 경로</option>
          <option v-for="node in finalNodeOptions" :key="node.value" :value="node.value">
            {{ node.label }}
          </option>
        </select>

        <div class="flex bg-gray-100 rounded-lg p-1 self-start sm:self-auto">
          <button
            @click="emit('update:viewMode', 'flow')"
            :class="[
              'px-2 sm:px-3 py-1.5 text-xs sm:text-sm font-medium rounded-md transition-colors flex items-center gap-1',
              viewMode === 'flow'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            ]"
          >
            <svg class="w-3 h-3 sm:w-4 sm:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            흐름도
          </button>
          <button
            @click="emit('update:viewMode', 'cards')"
            :class="[
              'px-2 sm:px-3 py-1.5 text-xs sm:text-sm font-medium rounded-md transition-colors flex items-center gap-1',
              viewMode === 'cards'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            ]"
          >
            <svg class="w-3 h-3 sm:w-4 sm:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            카드
          </button>
        </div>
      </div>
    </div>

    <template v-if="hasVisiblePaths">

      <div v-if="viewMode === 'cards'" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        <div v-for="(path, idx) in sortedPaths" :key="path.path_signature || idx" class="bg-white rounded-lg shadow-sm p-6 border transition-all hover:shadow-md">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="inline-flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-800 font-semibold">{{ idx + 1 }}</span>
              <h3 class="text-base sm:text-lg font-semibold text-gray-900">경로 #{{ idx + 1 }}</h3>
              <span v-if="pathHasEvent(path)" class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 border border-amber-200">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                이벤트 포함
              </span>
            </div>
            <div class="text-right">
              <div class="text-lg sm:text-2xl font-extrabold text-red-600">{{ formatPrice(computeTotalFeeKRW(path)) }}원</div>
              <div class="text-[11px] sm:text-xs text-gray-500">총 예상 수수료</div>
            </div>
          </div>
          <div class="flex flex-wrap items-center text-sm">
            <template v-for="(r, i) in path.routes" :key="i">
              <span
                class="px-2 py-1 bg-blue-50 text-blue-800 rounded transition hover:bg-blue-100"
                :class="nodeHasUrl(r.source) ? 'cursor-pointer' : ''"
                @click="navigateToNode(r.source)"
              >
                {{ r.source.display_name }}
              </span>
              <span class="inline-flex items-center mx-1 text-gray-400 gap-1">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
                <span v-if="r.is_event" class="px-1.5 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-800 border border-amber-200">이벤트</span>
              </span>
              <span
                v-if="i === path.routes.length - 1"
                class="px-2 py-1 bg-green-50 text-green-800 rounded transition hover:bg-green-100"
                :class="nodeHasUrl(r.destination) ? 'cursor-pointer' : ''"
                @click="navigateToNode(r.destination)"
              >
                {{ r.destination.display_name }}
              </span>
            </template>
          </div>
          <div class="mt-3 grid grid-cols-1 gap-2 text-xs text-gray-600">
            <div v-for="(r, i) in path.routes" :key="'d'+i" class="bg-gray-50 px-2 py-1 rounded border border-gray-100">
              <div class="flex justify-between">
                <span>{{ r.source.display_name }} → {{ r.destination.display_name }} ({{ r.route_type_display }})</span>
                <span>
                  <template v-if="r.fee_rate !== null">{{ r.fee_rate }}%</template>
                  <template v-if="r.fee_fixed !== null">
                    {{ r.fee_rate !== null ? ' + ' : ''}}{{ formatFixedAmount(r.fee_fixed, r.fee_fixed_currency) }} {{ normalizeFeeCurrency(r.fee_fixed_currency) }}
                  </template>
                  <template v-if="r.fee_rate === null && r.fee_fixed === null">무료</template>
                </span>
              </div>
            </div>
          </div>
          <div class="mt-4 pt-3 border-t text-xs text-gray-600 space-y-4">
            <div v-if="pathHasEvent(path)" class="space-y-1 text-amber-900 bg-amber-50 border border-amber-200 rounded px-2 py-2">
              <div class="flex items-center gap-2 font-semibold text-amber-800">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>이 경로에 이벤트가 포함되어 있습니다</span>
              </div>
              <div class="space-y-1">
                <div
                  v-for="(eventRoute, eventIdx) in getEventRoutes(path)"
                  :key="`event-${idx}-${eventIdx}`"
                  class="bg-white/60 px-2 py-1 rounded border border-amber-100"
                >
                  <div class="font-medium">{{ formatEventRouteTitle(eventRoute) }}</div>
                  <div class="text-[11px] text-amber-700">{{ previewEventDescription(eventRoute.event_description) }}</div>
                  <div v-if="eventRoute.event_url" class="text-[11px] mt-0.5">
                    <a :href="eventRoute.event_url" target="_blank" rel="noopener noreferrer" class="text-blue-700 underline break-all">이벤트 링크 열기</a>
                  </div>
                </div>
              </div>
            </div>
            <template v-for="pathFees in [computePathFees(path.routes)]" :key="`card-fees-${idx}`">
              <div class="mt-3">
                총 비율 수수료: <span class="font-semibold">{{ pathFees.rate.toFixed(4) }}%</span>
                • 총 고정 수수료: <span class="font-semibold">{{ formatFixedFeeSummary(pathFees.fixedByCurrency) }}</span>
                <template v-if="computeFixedFeeKRW(pathFees.fixedByCurrency)">
                  (≈ {{ formatPrice(computeFixedFeeKRW(pathFees.fixedByCurrency)) }}원)
                </template>
              </div>
            </template>
          </div>
        </div>
      </div>

      <div v-else class="space-y-4">
        <div v-for="(path, idx) in sortedPaths" :key="path.path_signature || idx" class="bg-white rounded-lg shadow-sm p-4 sm:p-6 border">
          <div class="flex items-center justify-between mb-3">
            <div class="font-medium text-gray-900 flex items-center gap-2">
              경로 #{{ idx + 1 }}
              <span v-if="pathHasEvent(path)" class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-amber-100 text-amber-800 border border-amber-200">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                이벤트
              </span>
            </div>
            <div class="text-right">
              <div class="text-lg sm:text-2xl font-extrabold text-red-600">{{ formatPrice(computeTotalFeeKRW(path)) }}원</div>
              <div class="text-[11px] sm:text-xs text-gray-500">총 예상 수수료</div>
            </div>
          </div>
          <div class="relative overflow-x-auto -mx-2 px-2 pr-4 pb-2 sm:mx-0 sm:px-0" :ref="el => setFlowContainerRef(`final-${idx}`, el)">
            <div v-if="flowOverflowById[`final-${idx}`]" class="sm:hidden text-[10px] text-gray-500 px-1 pb-1">좌우로 스크롤해 전체 흐름 보기</div>
            <div class="flex items-center py-1 min-w-full">
              <template v-if="path.routes && path.routes.length > 0">
                <div class="flex flex-col items-center shrink-0 mr-2">
                  <div
                    class="w-24 sm:w-32 bg-white border border-gray-300 rounded-lg p-2 text-center shadow"
                    :class="nodeHasUrl(path.routes[0].source) ? 'cursor-pointer hover:border-blue-400 hover:shadow-md transition' : ''"
                    @click="navigateToNode(path.routes[0].source)"
                  >
                    <div class="text-[11px] sm:text-sm font-semibold text-gray-900 truncate">{{ path.routes[0].source.display_name }}</div>
                    <div class="mt-1 flex items-center justify-center gap-1">
                      <span
                        class="text-[9px] px-1.5 py-0.5 rounded-full"
                        :class="path.routes[0].source.is_kyc ? 'bg-red-100 text-red-700 border border-red-200' : 'bg-green-100 text-green-700 border border-green-200'"
                      >
                        {{ path.routes[0].source.is_kyc ? 'KYC' : 'non-KYC' }}
                      </span>
                      <span
                        class="text-[9px] px-1.5 py-0.5 rounded-full"
                        :class="path.routes[0].source.is_custodial ? 'bg-blue-100 text-blue-700 border border-blue-200' : 'bg-purple-100 text-purple-700 border border-purple-200'"
                      >
                        {{ path.routes[0].source.is_custodial ? '수탁형' : '비수탁형' }}
                      </span>
                    </div>
                  </div>
                </div>
              </template>
              <template v-for="(r, i) in path.routes" :key="'flow-'+i">
                <div class="flex flex-col items-center mx-2 shrink-0">
                  <div class="flex items-center gap-2">
                    <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                    </svg>
                    <span v-if="r.is_event" class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-800 border border-amber-200">이벤트</span>
                  </div>
                  <div class="mt-1 text-[10px] sm:text-xs text-center leading-tight">
                    <div v-if="r.fee_rate !== null" class="text-gray-700">{{ r.fee_rate }}%</div>
                    <div v-if="r.fee_fixed !== null" :class="Number(r.fee_fixed) === 0 ? 'text-green-600' : 'text-orange-600'">
                      {{ formatFixedAmount(r.fee_fixed, r.fee_fixed_currency) }} {{ normalizeFeeCurrency(r.fee_fixed_currency) }}
                      <template v-if="getCurrencyKrwPrice(r.fee_fixed_currency) && Number(r.fee_fixed)">
                        <span class="text-[10px] text-gray-500">(≈ {{ formatPrice(r.fee_fixed * getCurrencyKrwPrice(r.fee_fixed_currency)) }}원)</span>
                      </template>
                    </div>
                    <div class="text-[9px] text-gray-500">{{ r.route_type_display }}</div>
                  </div>
                </div>
                <div :class="['flex flex-col items-center shrink-0', i === path.routes.length - 1 ? 'mr-0' : 'mr-2']">
                  <div
                    class="w-24 sm:w-32 bg-white border border-gray-300 rounded-lg p-2 text-center shadow"
                    :class="nodeHasUrl(r.destination) ? 'cursor-pointer hover:border-blue-400 hover:shadow-md transition' : ''"
                    @click="navigateToNode(r.destination)"
                  >
                    <div class="text-[11px] sm:text-sm font-semibold text-gray-900 truncate">{{ r.destination.display_name }}</div>
                    <div class="mt-1 flex items-center justify-center gap-1">
                      <span
                        class="text-[9px] px-1.5 py-0.5 rounded-full"
                        :class="r.destination.is_kyc ? 'bg-red-100 text-red-700 border border-red-200' : 'bg-green-100 text-green-700 border border-green-200'"
                      >
                        {{ r.destination.is_kyc ? 'KYC' : 'non-KYC' }}
                      </span>
                      <span
                        class="text-[9px] px-1.5 py-0.5 rounded-full"
                        :class="r.destination.is_custodial ? 'bg-blue-100 text-blue-700 border border-blue-200' : 'bg-purple-100 text-purple-700 border border-purple-200'"
                      >
                        {{ r.destination.is_custodial ? '수탁형' : '비수탁형' }}
                      </span>
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </div>
          <div class="mt-3 pt-2 border-t text-xs text-gray-600 space-y-4">
            <div v-if="pathHasEvent(path)" class="space-y-1 text-amber-900 bg-amber-50 border border-amber-200 rounded px-2 py-2">
              <div class="flex items-center gap-2 font-semibold text-amber-800">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>이 경로에 이벤트가 포함되어 있습니다</span>
              </div>
              <div class="space-y-1">
                <div
                  v-for="(eventRoute, eventIdx) in getEventRoutes(path)"
                  :key="`flow-event-${idx}-${eventIdx}`"
                  class="bg-white/60 px-2 py-1 rounded border border-amber-100"
                >
                  <div class="font-medium">{{ formatEventRouteTitle(eventRoute) }}</div>
                  <div class="text-[11px] text-amber-700">{{ previewEventDescription(eventRoute.event_description) }}</div>
                  <div v-if="eventRoute.event_url" class="text-[11px] mt-0.5">
                    <a :href="eventRoute.event_url" target="_blank" rel="noopener noreferrer" class="text-blue-700 underline break-all">이벤트 링크 열기</a>
                  </div>
                </div>
              </div>
            </div>
            <template v-for="pathFees in [computePathFees(path.routes)]" :key="`flow-fees-${idx}`">
              <div class="mt-3">
                총 비율 수수료: <span class="font-semibold">{{ pathFees.rate.toFixed(4) }}%</span>
                • 총 고정 수수료: <span class="font-semibold">{{ formatFixedFeeSummary(pathFees.fixedByCurrency) }}</span>
                <template v-if="computeFixedFeeKRW(pathFees.fixedByCurrency)">
                  (≈ {{ formatPrice(computeFixedFeeKRW(pathFees.fixedByCurrency)) }}원)
                </template>
              </div>
            </template>
          </div>
        </div>
      </div>
    </template>
    <div v-else class="bg-white border border-dashed border-gray-200 rounded-lg p-6 text-center text-gray-600">
      선택한 필터 조건에 맞는 최종 경로가 없습니다. 다른 필터를 선택하거나 금액을 변경해보세요.
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  paths: {
    type: Array,
    default: () => []
  },
  actualAmount: {
    type: Number,
    default: 0
  },
  bitcoinPrice: {
    type: Number,
    default: null
  },
  usdtPrice: {
    type: Number,
    default: null
  },
  viewMode: {
    type: String,
    default: 'flow'
  },
  hasInput: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:viewMode'])

const finalFilterExcludeLightning = ref(false)
const finalFilterExcludeKycWithdrawal = ref(false)
const finalFilterOnlyEvents = ref(false)
const finalFilterExcludeCustodialServices = ref(false)
const finalFilterNode = ref('')
const finalFilterExcludeCustodialWithdrawal = ref(false)

const formatPrice = (price = 0) => {
  return new Intl.NumberFormat('ko-KR').format(Math.round(price || 0))
}

const supportedFeeCurrencies = new Set(['BTC', 'USDT'])

const normalizeFeeCurrency = (currency = 'BTC') => {
  const upper = (currency || 'BTC').toString().toUpperCase()
  return supportedFeeCurrencies.has(upper) ? upper : 'BTC'
}

const formatFixedAmount = (value, currency = 'BTC') => {
  const normalized = normalizeFeeCurrency(currency)
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '0'
  const decimals = normalized === 'USDT' ? 4 : 8
  const formatted = Number(value).toFixed(decimals)
  const trimmed = formatted.includes('.') ? formatted.replace(/\.?0+$/, '') : formatted
  return trimmed.length ? trimmed : '0'
}

const formatFixedFeeSummary = (fixedByCurrency = {}) => {
  const entries = Object.entries(fixedByCurrency)
    .filter(([, amount]) => amount !== null && amount !== undefined)
    .map(([currency, amount]) => `${formatFixedAmount(amount, currency)} ${normalizeFeeCurrency(currency)}`)
  if (!entries.length) return '없음'
  return entries.join(' + ')
}

const getCurrencyKrwPrice = (currency = 'BTC') => {
  const normalized = normalizeFeeCurrency(currency)
  if (normalized === 'USDT') return props.usdtPrice
  return props.bitcoinPrice
}

const computeFixedFeeKRW = (fixedByCurrency = {}) => {
  let total = 0
  for (const [currency, amount] of Object.entries(fixedByCurrency)) {
    if (amount === null || amount === undefined) continue
    const price = getCurrencyKrwPrice(currency)
    if (!price) continue
    total += Number(amount) * price
  }
  return total
}

const computePathFees = (pathRoutes) => {
  let totalRate = 0
  const fixedByCurrency = {}
  for (const r of pathRoutes || []) {
    if (r.fee_rate !== null && r.fee_rate !== undefined) totalRate += Number(r.fee_rate) || 0
    if (r.fee_fixed !== null && r.fee_fixed !== undefined) {
      const amount = Number(r.fee_fixed)
      if (!Number.isFinite(amount)) continue
      const currency = normalizeFeeCurrency(r.fee_fixed_currency)
      fixedByCurrency[currency] = (fixedByCurrency[currency] || 0) + amount
    }
  }
  return { rate: totalRate, fixedByCurrency }
}

const computeTotalFeeKRW = (path) => {
  if (!path || !Array.isArray(path.routes)) return 0
  const { rate, fixedByCurrency } = computePathFees(path.routes)
  const rateFee = (props.actualAmount || 0) * (Number(rate) || 0) / 100
  const fixedFee = computeFixedFeeKRW(fixedByCurrency)
  return Math.max(0, Math.floor(rateFee + fixedFee))
}

const pathHasEvent = (path) => Array.isArray(path?.routes) && path.routes.some(route => route.is_event)
const getEventRoutes = (path) => {
  if (!Array.isArray(path?.routes)) return []
  return path.routes.filter(route => route.is_event)
}
const previewEventDescription = (desc) => {
  if (!desc) return '이벤트 상세정보가 없습니다.'
  const trimmed = desc.trim()
  if (trimmed.length > 80) return `${trimmed.slice(0, 80)}…`
  return trimmed
}
const formatEventRouteTitle = (route) => {
  if (!route) return '이벤트'
  if (route.event_title) return route.event_title
  const source = route.source?.display_name || ''
  const dest = route.destination?.display_name || ''
  if (source || dest) {
    return `${source} → ${dest} 이벤트`.trim()
  }
  return '이벤트'
}
const nodeHasUrl = (node) => Boolean(node?.website_url)
const navigateToNode = (node) => {
  if (!nodeHasUrl(node)) return
  window.open(node.website_url, '_blank', 'noopener,noreferrer')
}

const nodeTypeOptions = ['exchange', 'service', 'wallet', 'user']
const toTruthyBoolean = (value) => value === true || value === 1 || value === '1' || value === 'true'
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
const isLightningRoute = (route) => route?.route_type === 'withdrawal_lightning'
const pathHasLightningRoute = (path) => Array.isArray(path?.routes) && path.routes.some(isLightningRoute)
const isPersonalWalletNode = (node) => {
  if (!node) return false
  const nodeType = normalizeNodeTypeValue(node.node_type, node.service)
  if (nodeType === 'wallet') return true
  return (node.service || '').toString().toLowerCase() === 'personal_wallet'
}
const pathHasKycBeforePersonalWallet = (path) => {
  if (!Array.isArray(path?.routes) || path.routes.length === 0) return false
  const lastRoute = path.routes[path.routes.length - 1]
  if (!lastRoute || !isPersonalWalletNode(lastRoute.destination)) return false
  return toTruthyBoolean(lastRoute.source?.is_kyc)
}
const isCustodialServiceNode = (node) => {
  if (!node) return false
  const nodeType = normalizeNodeTypeValue(node.node_type, node.service)
  const isCustodial = toTruthyBoolean(node.is_custodial)
  return nodeType === 'service' && isCustodial
}
const pathHasCustodialBeforePersonalWallet = (path) => {
  if (!Array.isArray(path?.routes) || path.routes.length === 0) return false
  const lastRoute = path.routes[path.routes.length - 1]
  if (!lastRoute || !isPersonalWalletNode(lastRoute.destination)) return false
  return toTruthyBoolean(lastRoute.source?.is_custodial)
}
const routeHasCustodialServiceNode = (route) => {
  if (!route) return false
  return isCustodialServiceNode(route.source) || isCustodialServiceNode(route.destination)
}
const nodeMatchesFilter = (node, target) => {
  if (!node || !target) return false
  const service = (node.service || '').toString().toLowerCase()
  const name = (node.display_name || '').toString().toLowerCase()
  const t = target.toString().toLowerCase()
  return service === t || name === t
}
const pathContainsNode = (path, target) => {
  if (!target) return true
  if (!Array.isArray(path?.routes)) return false
  return path.routes.some(route => nodeMatchesFilter(route.source, target) || nodeMatchesFilter(route.destination, target))
}

const finalNodeOptions = computed(() => {
  const seen = new Set()
  const options = []
  for (const path of props.paths || []) {
    for (const route of path.routes || []) {
      for (const node of [route.source, route.destination]) {
        if (!node) continue
        const val = (node.service || node.display_name || '').toString()
        if (!val || seen.has(val)) continue
        seen.add(val)
        const label = node.display_name || node.service || val
        options.push({ value: val, label })
      }
    }
  }
  return options.sort((a, b) => a.label.localeCompare(b.label, 'ko'))
})

const filteredPaths = computed(() => {
  return (props.paths || []).filter(path => {
    if (!Array.isArray(path.routes)) return true
    if (finalFilterOnlyEvents.value && !pathHasEvent(path)) return false
    if (finalFilterExcludeCustodialServices.value && path.routes.some(routeHasCustodialServiceNode)) return false
    if (finalFilterExcludeLightning.value && pathHasLightningRoute(path)) return false
    if (finalFilterExcludeKycWithdrawal.value && pathHasKycBeforePersonalWallet(path)) return false
    if (finalFilterExcludeCustodialWithdrawal.value && pathHasCustodialBeforePersonalWallet(path)) return false
    if (finalFilterNode.value && !pathContainsNode(path, finalFilterNode.value)) return false
    return true
  })
})

const sortedPaths = computed(() => {
  const arr = [...filteredPaths.value]
  if ((props.actualAmount || 0) > 0) {
    arr.sort((a, b) => computeTotalFeeKRW(a) - computeTotalFeeKRW(b))
  }
  return arr
})

const hasVisiblePaths = computed(() => sortedPaths.value.length > 0)
const hasAnyPaths = computed(() => Array.isArray(props.paths) && props.paths.length > 0)

const flowOverflowById = ref({})
const flowContainerRefs = new Map()

const setFlowContainerRef = (id, el) => {
  if (!id) return
  if (el) {
    flowContainerRefs.set(id, el)
    if (!el.__overflowScrollAttached) {
      const onScroll = () => checkOverflowForId(id)
      el.__overflowScrollHandler = onScroll
      el.addEventListener('scroll', onScroll, { passive: true })
      el.__overflowScrollAttached = true
    }
    requestAnimationFrame(() => checkOverflowForId(id))
  } else if (flowContainerRefs.has(id)) {
    const node = flowContainerRefs.get(id)
    if (node && node.__overflowScrollHandler) {
      node.removeEventListener('scroll', node.__overflowScrollHandler)
      delete node.__overflowScrollHandler
    }
    flowContainerRefs.delete(id)
  }
}

const checkOverflowForId = (id) => {
  const el = flowContainerRefs.get(id)
  if (!el) return
  const hasOverflow = (el.scrollWidth - el.clientWidth) > 1
  const prev = flowOverflowById.value[id]
  if (prev !== hasOverflow) {
    flowOverflowById.value = { ...flowOverflowById.value, [id]: hasOverflow }
  }
}

const checkAllOverflows = () => {
  requestAnimationFrame(() => {
    for (const id of flowContainerRefs.keys()) {
      checkOverflowForId(id)
    }
  })
}

watch(
  [filteredPaths, () => props.viewMode, finalFilterExcludeLightning, finalFilterExcludeKycWithdrawal, finalFilterExcludeCustodialWithdrawal, finalFilterOnlyEvents, finalFilterExcludeCustodialServices, finalFilterNode],
  () => {
    nextTick(() => checkAllOverflows())
  },
  { deep: true }
)

onMounted(() => {
  try {
    window.addEventListener('resize', checkAllOverflows, { passive: true })
  } catch (_) {
    window.addEventListener('resize', checkAllOverflows)
  }
  nextTick(() => checkAllOverflows())
})

onBeforeUnmount(() => {
  try {
    window.removeEventListener('resize', checkAllOverflows)
  } catch (_) {
    // ignore
  }
  for (const node of flowContainerRefs.values()) {
    if (node && node.__overflowScrollHandler) {
      node.removeEventListener('scroll', node.__overflowScrollHandler)
      delete node.__overflowScrollHandler
    }
  }
  flowContainerRefs.clear()
})
</script>
