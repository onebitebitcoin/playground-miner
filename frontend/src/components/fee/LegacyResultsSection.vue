<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
      <h2 class="text-lg sm:text-xl font-semibold text-gray-900">수수료 비교 결과</h2>
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

    <div v-if="viewMode === 'cards'" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      <div
        v-for="(result, index) in sortedResults"
        :key="result.id"
        :class="[
          'bg-white rounded-lg shadow-sm p-6 border transition-all hover:shadow-md',
          isOptimal(result)
            ? 'border-emerald-200 ring-2 ring-emerald-100 bg-emerald-50/40'
            : 'border-gray-200 hover:border-gray-300'
        ]"
      >
        <div class="flex items-start justify-between mb-5">
          <h3 class="text-lg font-semibold text-slate-900 leading-tight pr-2">{{ result.title }}</h3>
          <div v-if="isOptimal(result)" class="bg-emerald-600 text-white px-3 py-1.5 rounded-full text-sm font-medium flex items-center gap-1.5 flex-shrink-0 shadow-sm">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            최적
          </div>
        </div>

        <div class="space-y-4">
          <div class="text-sm text-slate-600">
            <div class="font-medium leading-relaxed">{{ result.description }}</div>
          </div>

          <div class="md:hidden">
            <button
              class="mt-1 mb-2 text-sm px-3 py-2 rounded-lg bg-slate-50 text-slate-700 hover:bg-slate-100 border border-slate-200 w-full font-medium flex items-center justify-center gap-2 transition-colors"
              @click="toggleDetails(result.id)"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              {{ detailsOpenById[result.id] ? '상세 수수료 접기' : '상세 수수료 보기' }}
            </button>
          </div>

          <div v-show="!isMobile || detailsOpenById[result.id]">
            <div v-if="result.exchanges && result.exchanges.length > 0" class="bg-slate-50 p-4 rounded-xl mb-3 border border-slate-100">
              <div class="text-sm font-semibold text-slate-800 mb-3 flex items-center gap-2">
                <svg class="w-4 h-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                거래소별 수수료율
              </div>
              <div class="space-y-2">
                <div v-for="exchange in result.exchanges" :key="exchange.name" class="text-sm">
                  <div class="flex justify-between items-center py-1">
                    <span class="text-slate-700 font-medium">{{ exchange.name }}</span>
                    <span class="font-bold text-gray-900 bg-gray-100 px-2 py-1 rounded-md">{{ exchange.rate }}%</span>
                  </div>
                  <div
                    v-if="(exchange.note && exchange.note !== '') || (exchange.eventDetails && exchange.eventDetails !== '')"
                    class="text-xs text-indigo-800 mt-2 bg-indigo-50 px-3 py-2 rounded-lg border border-indigo-200"
                  >
                    <div class="font-semibold mb-1 flex items-center gap-2">
                      <svg class="w-3 h-3 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      이벤트
                    </div>
                    <div class="whitespace-pre-line">
                      <template v-if="exchange.note && exchange.note !== ''">{{ exchange.note }}</template>
                      <template v-if="exchange.eventDetails && exchange.eventDetails !== ''">
                        <span v-if="exchange.note && exchange.note !== ''"> — </span>{{ exchange.eventDetails }}
                      </template>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="result.withdrawalFees && result.withdrawalFees.length > 0" class="bg-gray-50 p-4 rounded-lg mb-3 border border-gray-200">
              <div class="text-sm font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <svg class="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                출금 수수료
              </div>
              <div class="space-y-3">
                <div v-for="fee in result.withdrawalFees" :key="fee.name" class="text-sm">
                  <div class="flex justify-between items-center py-2 px-3 bg-white rounded-lg border border-gray-200">
                    <span class="text-gray-700 font-medium">{{ fee.name }}</span>
                    <div class="text-right">
                      <div class="font-bold text-gray-900">{{ fee.amount }} BTC</div>
                      <div class="text-xs text-gray-500">({{ formatPrice(fee.amountKrw) }}원)</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="result.lightningServices && result.lightningServices.length > 0" class="bg-gray-50 p-4 rounded-lg mb-3 border border-gray-200">
              <div class="text-sm font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <svg class="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                {{ getLightningHeader(result.lightningServices) }}
              </div>
              <div class="space-y-2">
                <div v-for="service in result.lightningServices" :key="service.name" class="text-sm">
                  <div class="flex justify-between items-center py-2 px-3 bg-white rounded-lg border border-gray-200">
                    <div class="flex flex-col">
                      <div class="flex items-center gap-2">
                        <span class="text-gray-700 font-medium">
                          <template v-if="getServiceUrl(service.name)">
                            <a :href="getServiceUrl(service.name)" target="_blank" rel="noopener noreferrer" class="text-gray-900 hover:text-gray-700 underline decoration-2 underline-offset-2 transition-colors">
                              {{ service.name }}
                            </a>
                          </template>
                          <template v-else>
                            {{ service.name }}
                          </template>
                        </span>
                        <span :class="['text-xs px-2 py-1 rounded-md font-medium', service.isKyc ? 'bg-red-500 text-white' : 'bg-green-500 text-white']">
                          {{ service.isKyc ? 'KYC' : 'non-KYC' }}
                        </span>
                      </div>
                    </div>
                    <span class="font-bold text-gray-900 bg-gray-100 px-2 py-1 rounded-md">{{ service.rate }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="border-t border-slate-200 pt-4 mt-4">
            <div class="space-y-3">
              <div class="flex justify-between items-center text-slate-700 text-sm py-2">
                <span class="font-medium">거래 수수료</span>
                <span class="font-semibold">{{ formatPrice(result.tradingFee) }}원</span>
              </div>
              <div v-if="result.transferFee > 0" class="flex justify-between items-center text-slate-700 text-sm py-2">
                <span class="font-medium">송금 수수료</span>
                <span class="font-semibold">{{ formatPrice(result.transferFee) }}원</span>
              </div>
              <div v-if="result.lightningFee > 0" class="flex justify-between items-center text-slate-700 text-sm py-2">
                <span class="font-medium">라이트닝 수수료</span>
                <span class="font-semibold">{{ formatPrice(result.lightningFee) }}원</span>
              </div>
              <div class="flex justify-between items-center font-semibold text-rose-900 border border-rose-200 pt-3 mt-3 text-base bg-rose-50 px-4 py-3 rounded-lg">
                <span class="flex items-center gap-2">
                  <svg class="w-5 h-5 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                  </svg>
                  총 수수료
                </span>
                <span class="text-rose-700 font-extrabold">{{ formatPrice(result.totalFee) }}원</span>
              </div>
              <div class="flex justify-between items-center font-semibold text-sky-900 text-base bg-sky-50 px-4 py-3 rounded-lg border border-sky-200">
                <span class="flex items-center gap-2">
                  <svg class="w-5 h-5 text-sky-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  수령 가능 금액
                </span>
                <span class="text-sky-800 font-extrabold">{{ formatPrice(result.actualAmount) }}원</span>
              </div>
              <div class="text-center text-sm text-gray-600 mt-3 bg-gray-100 py-3 rounded-lg flex items-center justify-center gap-2">
                <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                총 수수료율: <span class="font-bold">{{ result.feeRate }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="viewMode === 'flow'" class="space-y-8">
      <div
        v-for="(result, index) in sortedResults"
        :key="result.id"
        :class="[
          'bg-white rounded-2xl shadow-lg border transition-all overflow-visible',
          'p-3 sm:p-6',
          isOptimal(result) ? 'border-emerald-200 ring-2 ring-emerald-100 bg-emerald-50/30' : 'border-slate-200'
        ]"
      >
        <div class="flex flex-col sm:flex-row sm:items-center justify-between mb-4 sm:mb-6 gap-3">
          <div class="flex items-center gap-2 sm:gap-4">
            <div v-if="isOptimal(result)" class="bg-emerald-600 text-white px-2 py-1 sm:px-3 sm:py-2 rounded-full text-xs sm:text-sm font-bold flex items-center gap-1 sm:gap-2 flex-shrink-0">
              <svg class="w-3 h-3 sm:w-4 sm:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              최적 #{{ index + 1 }}
            </div>
            <div v-else class="bg-gray-500 text-white px-2 py-1 sm:px-3 sm:py-2 rounded-full text-xs sm:text-sm font-bold flex-shrink-0">
              #{{ index + 1 }}
            </div>
            <h3 class="text-sm sm:text-lg font-bold text-gray-900 min-w-0">{{ result.title }}</h3>
          </div>
          <div class="text-left sm:text-right">
            <div class="text-lg sm:text-2xl font-bold text-red-600">{{ formatPrice(result.totalFee) }}원</div>
            <div class="text-xs sm:text-sm text-gray-500">총 수수료 ({{ result.feeRate }}%)</div>
          </div>
        </div>

        <div class="relative overflow-y-visible overflow-x-auto -mx-2 px-2 sm:mx-0 sm:px-0" :ref="el => setFlowContainerRef(result.id, el)">
          <div v-if="flowOverflowById[result.id]" class="sm:hidden text-[10px] text-gray-500 px-1 pb-1">좌우로 스크롤해 전체 흐름 보기</div>
          <div v-if="flowOverflowById[result.id]" class="pointer-events-none absolute inset-y-0 right-0 w-6 bg-gradient-to-l from-gray-50 to-transparent sm:hidden"></div>
          <div class="flex items-center justify-start sm:justify-between gap-1 sm:gap-3 py-4 sm:py-6 px-1 sm:px-4">
        <div class="flex flex-col items-center shrink-0">
          <div class="w-12 h-10 sm:w-16 sm:h-12 bg-gray-800 text-white rounded-lg flex flex-col items-center justify-center shadow">
            <svg class="w-4 h-4 sm:w-6 sm:h-6 mb-0.5 sm:mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            <div class="text-[10px] sm:text-xs font-medium">사용자</div>
          </div>
          <div class="text-[10px] sm:text-xs text-gray-600 mt-1 sm:mt-2 text-center max-w-16 sm:max-w-none break-words">
            {{ formatPrice(originalAmount) }}원
          </div>
        </div>

            <div class="flex flex-col items-center h-12 sm:h-16 justify-center shrink-0">
              <svg class="w-5 h-4 sm:w-8 sm:h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
              <div class="text-[8px] sm:text-[10px] text-gray-500 mt-0.5 sm:mt-1 text-center leading-tight">
                <div>원화충전</div>
                <div>(24h 대기)</div>
              </div>
            </div>

            <div class="flex flex-col items-center relative px-1 sm:px-3 pt-2 sm:pt-3 pb-1 sm:pb-2 shrink-0">
              <component
                v-for="(exchange, exIndex) in result.exchanges.slice(0, 1)"
                :key="exIndex"
                :is="getExchangeUrl(exchange.name) ? 'a' : 'div'"
                :href="getExchangeUrl(exchange.name) || undefined"
                target="_blank"
                rel="noopener noreferrer"
                class="w-14 h-10 sm:w-20 sm:h-12 bg-white border border-gray-300 text-gray-800 rounded-lg flex flex-col items-center justify-center shadow relative block"
              >
                <svg class="w-4 h-4 sm:w-6 sm:h-6 mb-0.5 sm:mb-1 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                <div class="text-[9px] sm:text-xs font-medium text-center leading-tight px-0.5 sm:px-1">{{ exchange.name }}</div>
                <div
                  v-if="exchange.note"
                  class="absolute -top-2 sm:-top-3 -right-2 sm:-right-3 bg-orange-500 text-white text-[8px] sm:text-xs px-1 sm:px-1.5 py-0.5 rounded-full font-medium shadow whitespace-nowrap"
                >
                  이벤트
                </div>
              </component>
              <div v-if="getPurchaseLabelForExchange(result.exchanges[0]?.name, result.exchanges[0]?.rate)" class="text-[9px] sm:text-[11px] text-gray-700 mt-1">
                {{ getPurchaseLabelForExchange(result.exchanges[0].name, result.exchanges[0].rate) }}
              </div>
              <div class="text-[9px] sm:text-xs text-center mt-1 sm:mt-2 space-y-0.5 sm:space-y-1">
                <div class="text-gray-900 font-medium">{{ formatPrice(result.firstTradingFee) }}원</div>
                <div class="text-gray-500">{{ result.exchanges[0].rate === 0 ? '바로 출금' : `거래수수료 (${result.exchanges[0].rate}%)` }}</div>
              </div>
            </div>

            <div
              v-if="result.exchanges.length > 1"
              class="flex flex-col items-center justify-center shrink-0"
              :class="result.exchanges[0].name && result.exchanges[0].name.includes('BTC') ? 'h-16 sm:h-20' : 'h-10 sm:h-12'"
            >
              <svg class="w-5 h-4 sm:w-8 sm:h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
              <div class="text-[8px] sm:text-[10px] text-gray-500 mt-0.5 sm:mt-1 text-center leading-tight">
                <div v-if="result.exchanges[0].name && result.exchanges[0].name.includes('BTC')">
                  <div>BTC출금</div>
                  <div v-if="result.withdrawalFees && result.withdrawalFees.length > 0" class="text-[7px] sm:text-[9px] font-medium text-orange-600 mt-0.5 leading-tight">
                    <div>{{ formatPrice(result.withdrawalFees[0].amountKrw) }}원</div>
                    <div class="text-[6px] sm:text-[8px] text-gray-500">({{ result.withdrawalFees[0].amount }} BTC)</div>
                  </div>
                </div>
                <div v-else>
                  <div>USDT전송</div>
                  <div>(무료)</div>
                </div>
              </div>
            </div>

            <div v-if="result.exchanges.length > 1" class="flex flex-col items-center relative px-2 sm:px-5 pt-3 sm:pt-5 pb-2 sm:pb-3 shrink-0">
              <component
                :is="getExchangeUrl(result.exchanges[1].name) ? 'a' : 'div'"
                :href="getExchangeUrl(result.exchanges[1].name) || undefined"
                target="_blank"
                rel="noopener noreferrer"
                class="w-14 h-10 sm:w-20 sm:h-12 bg-white border border-gray-300 text-gray-800 rounded-lg flex flex-col items-center justify-center shadow relative block"
              >
                <svg class="w-4 h-4 sm:w-6 sm:h-6 mb-0.5 sm:mb-1 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7" />
                </svg>
                <div class="text-[9px] sm:text-xs font-medium text-center leading-tight px-0.5 sm:px-1">{{ result.exchanges[1].name }}</div>
                <div
                  v-if="result.exchanges[1].note"
                  class="absolute -top-2 sm:-top-3 -right-2 sm:-right-3 bg-orange-500 text-white text-[8px] sm:text-xs px-1 sm:px-1.5 py-0.5 rounded-full font-medium shadow whitespace-nowrap"
                >
                  이벤트
                </div>
              </component>
              <div v-if="getPurchaseLabelForExchange(result.exchanges[1]?.name, result.exchanges[1]?.rate)" class="text-[9px] sm:text-[11px] text-gray-700 mt-1">
                {{ getPurchaseLabelForExchange(result.exchanges[1].name, result.exchanges[1].rate) }}
              </div>
              <div class="text-[9px] sm:text-xs text-center mt-1 sm:mt-2 space-y-0.5 sm:space-y-1">
                <div class="text-gray-900 font-medium">{{ formatPrice(result.secondTradingFee) }}원</div>
                <div class="text-gray-500">
                  {{ result.exchanges[1].rate === 0 ? '바로 출금' : `거래수수료 (${result.exchanges[1].rate}%)` }}
                </div>
              </div>
            </div>

            <div v-if="result.lightningServices && result.lightningServices.length > 0" class="flex flex-col items-center h-10 sm:h-12 justify-center shrink-0">
              <svg class="w-5 h-4 sm:w-8 sm:h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
              <div class="text-[8px] sm:text-[10px] text-gray-500 mt-0.5 sm:mt-1">라이트닝</div>
              <div v-if="result.lightningArrowFee" class="text-[7px] sm:text-[9px] font-medium text-orange-600 text-center mt-0.5 sm:mt-1 leading-tight">
                <div>출금수수료</div>
                <div>{{ result.lightningArrowFee.amount }}원</div>
                <div class="text-[6px] sm:text-[8px] text-gray-500">({{ result.lightningArrowFee.btc }} BTC)</div>
              </div>
            </div>

            <div v-if="result.lightningServices && result.lightningServices.length > 0" class="flex flex-col items-center relative px-1 sm:px-4 pt-2 sm:pt-3 pb-1 sm:pb-2 shrink-0">
              <component
                :is="getServiceUrl(result.lightningServices[0].name) ? 'a' : 'div'"
                :href="getServiceUrl(result.lightningServices[0].name) || undefined"
                target="_blank"
                rel="noopener noreferrer"
                class="w-14 h-10 sm:w-20 sm:h-12 bg-white border border-gray-300 text-gray-800 rounded-lg flex flex-col items-center justify-center shadow relative block"
              >
                <svg class="w-4 h-4 sm:w-6 sm:h-6 mb-0.5 sm:mb-1 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <div class="text-[9px] sm:text-xs font-medium text-center leading-tight px-0.5 sm:px-1">{{ result.lightningServices[0].name }}</div>
                <div
                  class="absolute -top-2 sm:-top-3 -right-2 sm:-right-3 text-[8px] sm:text-xs px-1 sm:px-1.5 py-0.5 rounded-full font-medium shadow whitespace-nowrap"
                  :class="result.lightningServices[0].isKyc ? 'bg-red-500 text-white' : 'bg-green-500 text-white'"
                >
                  {{ result.lightningServices[0].isKyc ? 'KYC' : 'non-KYC' }}
                </div>
                <div
                  class="absolute -top-2 sm:-top-3 -left-2 sm:-left-3 text-[8px] sm:text-xs px-1 sm:px-1.5 py-0.5 rounded-full font-medium shadow whitespace-nowrap"
                  :class="result.lightningServices[0].isCustodial ? 'bg-blue-500 text-white' : 'bg-purple-500 text-white'"
                >
                  {{ result.lightningServices[0].isCustodial ? '수탁형' : '비수탁형' }}
                </div>
              </component>
              <div class="text-[9px] sm:text-xs text-center mt-1 sm:mt-2 space-y-0.5 sm:space-y-1">
                <div class="text-gray-900 font-medium">{{ formatPrice(result.lightningFee) }}원</div>
                <div class="text-gray-500">온체인 전환 수수료 ({{ result.lightningServices[0].rate }}%)</div>
              </div>
            </div>

            <div class="flex flex-col items-center justify-center py-2 shrink-0">
              <svg class="w-5 h-4 sm:w-8 sm:h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
              <div class="text-[8px] sm:text-[10px] text-gray-500 mt-0.5 sm:mt-1 text-center">
                {{ result.finalTransferType }}
              </div>
              <div
                v-if="result.finalArrowWithdrawalFee"
                class="text-[7px] sm:text-[9px] font-medium text-center mt-0.5 sm:mt-1 leading-tight"
                :class="result.finalArrowWithdrawalFee.amount === '0' ? 'text-green-600' : 'text-orange-600'"
              >
                <div>출금수수료</div>
                <div>{{ result.finalArrowWithdrawalFee.amount }}원</div>
                <div v-if="result.finalArrowWithdrawalFee.amount !== '0'" class="text-[6px] sm:text-[8px] text-gray-500">({{ result.finalArrowWithdrawalFee.btc }} BTC)</div>
              </div>
              <div v-if="getStrikeFinalWithdrawalDisplay(result)" class="text-[7px] sm:text-[9px] font-medium mt-1 text-center text-green-600 leading-tight">
                <div>Strike→지갑</div>
                <div>무료</div>
              </div>
            </div>

            <div class="flex flex-col items-center shrink-0">
              <div class="w-12 h-10 sm:w-16 sm:h-12 bg-gray-900 text-white rounded-lg flex flex-col items-center justify-center shadow">
                <svg class="w-4 h-4 sm:w-6 sm:h-6 mb-0.5 sm:mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                </svg>
                <div class="text-[10px] sm:text-xs font-medium">개인지갑</div>
              </div>
              <div class="text-[9px] sm:text-xs text-center mt-1 sm:mt-2 space-y-0.5 sm:space-y-1">
                <div class="text-gray-900 font-bold">{{ formatPrice(result.actualAmount) }}원</div>
                <div class="text-gray-500">수령금액</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  results: {
    type: Array,
    default: () => []
  },
  viewMode: {
    type: String,
    default: 'flow'
  },
  originalAmount: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['update:viewMode'])

const formatPrice = (price) => {
  return new Intl.NumberFormat('ko-KR').format(Math.round(price || 0))
}

const sortedResults = computed(() => {
  return [...props.results].sort((a, b) => a.totalFee - b.totalFee)
})

const bestResults = computed(() => {
  if (!sortedResults.value.length) return []
  const minFee = sortedResults.value[0].totalFee
  return sortedResults.value.filter(result => Math.abs(result.totalFee - minFee) < 0.01)
})

const isOptimal = (result) => {
  return bestResults.value.some(best => best.id === result.id)
}

const maxSavings = computed(() => {
  if (sortedResults.value.length < 2) return 0
  return sortedResults.value[sortedResults.value.length - 1].totalFee - sortedResults.value[0].totalFee
})

const getLightningHeader = (services) => {
  if (!services || services.length === 0) return '라이트닝 서비스'
  const names = services.map(s => (s?.name || '')).join(' ').toLowerCase()
  if (names.includes('coinos')) {
    return '라이트닝 & 온체인 출금'
  }
  return '라이트닝 서비스'
}

const getServiceUrl = (name) => {
  const n = (name || '').toLowerCase()
  if (n.includes('boltz')) return 'https://boltz.exchange'
  if (n.includes('coinos')) return 'https://coinos.io'
  if (n.includes('월렛오브사토시') || n.includes('walletofsatoshi')) return 'https://walletofsatoshi.com'
  if (n.includes('strike')) return 'https://strike.me'
  return null
}

const getExchangeUrl = (name) => {
  const n = (name || '').toLowerCase()
  if (n.includes('업비트') || n.includes('upbit')) return 'https://upbit.com'
  if (n.includes('빗썸') || n.includes('bithumb')) return 'https://www.bithumb.com'
  if (n.includes('바이낸스') || n.includes('binance')) return 'https://www.binance.com'
  if (n.includes('okx')) return 'https://www.okx.com'
  return null
}

const getPurchaseLabelForExchange = (name, rate) => {
  const n = (name || '').toLowerCase()
  if (n.includes('업비트') || n.includes('bithumb') || n.includes('빗썸')) {
    if (n.includes('usdt')) return '원화로 USDT 구매'
    if (n.includes('btc')) return '원화로 BTC 구매'
    return '원화로 BTC 구매'
  }
  if (n.includes('binance') || n.includes('바이낸스') || n.includes('okx')) {
    if (rate > 0) {
      return 'USDT로 BTC 구매'
    }
    return ''
  }
  if (n.includes('usdt')) return '원화로 USDT 구매'
  if (n.includes('btc')) return '원화로 BTC 구매'
  return ''
}

const getStrikeFinalWithdrawalDisplay = (result) => {
  if (!result.lightningServices || result.lightningServices.length === 0) {
    return null
  }
  const lightningServiceName = result.lightningServices[0]?.name || ''
  if (lightningServiceName === 'Strike') {
    return 'Strike → 개인지갑\n라이트닝 출금 무료'
  }
  return null
}

const detailsOpenById = ref({})
const isMobile = ref(false)

const resetDetailsState = () => {
  if (!isMobile.value) {
    detailsOpenById.value = {}
    return
  }
  const map = {}
  for (const r of props.results) {
    map[r.id] = false
  }
  detailsOpenById.value = map
}

const toggleDetails = (id) => {
  detailsOpenById.value = {
    ...detailsOpenById.value,
    [id]: !detailsOpenById.value[id]
  }
}

watch(
  () => props.results,
  () => resetDetailsState(),
  { deep: true, immediate: true }
)

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
  [sortedResults, () => props.viewMode],
  () => {
    nextTick(() => checkAllOverflows())
  },
  { deep: true }
)

const mediaQuery = typeof window !== 'undefined' ? window.matchMedia('(max-width: 767px)') : null
const handleMobileChange = () => {
  isMobile.value = mediaQuery ? mediaQuery.matches : false
  resetDetailsState()
}

onMounted(() => {
  handleMobileChange()
  if (mediaQuery) {
    try {
      mediaQuery.addEventListener('change', handleMobileChange)
    } catch (_) {
      mediaQuery.addListener(handleMobileChange)
    }
  }

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
  if (mediaQuery) {
    try {
      mediaQuery.removeEventListener('change', handleMobileChange)
    } catch (_) {
      mediaQuery.removeListener(handleMobileChange)
    }
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
