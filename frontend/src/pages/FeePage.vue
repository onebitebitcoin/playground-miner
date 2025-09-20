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
              class="flex-1 min-w-0 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              @input="calculateFees"
            />
            <select
              v-model="selectedUnit"
              class="flex-shrink-0 px-2 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white w-16 text-sm"
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
        <div class="flex justify-between items-center">
          <h2 class="text-xl font-semibold text-gray-900">수수료 비교 결과</h2>

          <!-- View Mode Toggle -->
          <div class="flex bg-gray-100 rounded-lg p-1">
            <button
              @click="viewMode = 'flow'"
              :class="[
                'px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
                viewMode === 'flow'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              ]"
            >
              <svg class="w-4 h-4 mr-1 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              흐름도
            </button>
            <button
              @click="viewMode = 'cards'"
              :class="[
                'px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
                viewMode === 'cards'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              ]"
            >
              <svg class="w-4 h-4 mr-1 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              카드
            </button>
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

        <!-- Cards View -->
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

              <!-- Mobile: toggle to show details -->
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

              <!-- Details wrapper: always visible on md+, toggled on mobile -->
              <div v-show="!isMobile || detailsOpenById[result.id]">
                <!-- Exchange Fee Details -->
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

                <!-- Withdrawal Fee Details -->
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

                <!-- Lightning Service Details -->
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
                            <span :class="[
                              'text-xs px-2 py-1 rounded-md font-medium',
                              service.isKyc
                                ? 'bg-red-500 text-white'
                                : 'bg-green-500 text-white'
                            ]">
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

              <!-- Fee Breakdown -->
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


        <!-- Flow View -->
        <div v-if="viewMode === 'flow'" class="space-y-8">
          <div
            v-for="(result, index) in sortedResults"
            :key="result.id"
            :class="[
              'bg-white rounded-2xl shadow-lg p-6 border transition-all overflow-visible',
              isOptimal(result) ? 'border-emerald-200 ring-2 ring-emerald-100 bg-emerald-50/30' : 'border-slate-200'
            ]"
          >
            <!-- Header with ranking and total cost -->
            <div class="flex items-center justify-between mb-6">
              <div class="flex items-center gap-4">
                <div v-if="isOptimal(result)" class="bg-emerald-600 text-white px-3 py-2 rounded-full text-sm font-bold flex items-center gap-2">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  최적 #{{ index + 1 }}
                </div>
                <div v-else class="bg-gray-500 text-white px-3 py-2 rounded-full text-sm font-bold">
                  #{{ index + 1 }}
                </div>
                <h3 class="text-lg font-bold text-gray-900">{{ result.title }}</h3>
              </div>
              <div class="text-right">
                <div class="text-2xl font-bold text-red-600">{{ formatPrice(result.totalFee) }}원</div>
                <div class="text-sm text-gray-500">총 수수료 ({{ result.feeRate }}%)</div>
              </div>
            </div>

            <!-- Flow Diagram -->
            <div class="relative overflow-x-auto overflow-y-visible">
              <div class="flex items-center justify-between min-w-max gap-6 py-10 px-10">

                <!-- Start: User Wallet -->
                <div class="flex flex-col items-center">
                  <div class="w-20 h-16 bg-gray-800 text-white rounded-lg flex flex-col items-center justify-center shadow">
                    <svg class="w-6 h-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    <div class="text-xs font-medium">사용자</div>
                  </div>
                  <div class="text-xs text-gray-600 mt-2 text-center">
                    {{ formatPrice(getActualAmount()) }}원
                  </div>
                </div>

                <!-- Arrow 1 -->
                <div class="flex flex-col items-center h-16 justify-center">
                  <svg class="w-8 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                  </svg>
                  <div class="text-xs text-gray-500 mt-1">원화구매</div>
                </div>

                <!-- Exchange 1 -->
                <div class="flex flex-col items-center relative px-5 pt-5 pb-3">
                  <component v-for="(exchange, exIndex) in result.exchanges.slice(0, 1)" :key="exIndex"
                             :is="getExchangeUrl(exchange.name) ? 'a' : 'div'"
                             :href="getExchangeUrl(exchange.name) || undefined"
                             target="_blank" rel="noopener noreferrer"
                             class="w-24 h-16 bg-white border border-gray-300 text-gray-800 rounded-lg flex flex-col items-center justify-center shadow relative block">

                    <!-- Exchange icon -->
                    <svg class="w-6 h-6 mb-1 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                    <div class="text-xs font-medium text-center leading-tight px-1">{{ exchange.name }}</div>

                    <!-- Event badge (prevent navigation) -->
                    <div v-if="exchange.note"
                         @click.prevent.stop="showEventDetails(exchange.eventDetails)"
                         class="absolute -top-3 -right-3 bg-orange-500 text-white text-xs px-1.5 py-0.5 rounded-full font-medium shadow whitespace-nowrap cursor-pointer hover:bg-orange-600 transition-colors">
                      이벤트
                    </div>
                  </component>
                  <!-- Purchase label for first exchange -->
                  <div v-if="getPurchaseLabelForExchange(result.exchanges[0]?.name)" class="text-[11px] text-gray-700 mt-1">
                    {{ getPurchaseLabelForExchange(result.exchanges[0].name) }}
                  </div>
                  <div class="text-xs text-center mt-2 space-y-1">
                    <div class="text-gray-900 font-medium">{{ formatPrice(getFirstTradingFee(result)) }}원</div>
                    <div class="text-gray-500">거래수수료 ({{ result.exchanges[0].rate }}%)</div>
                  </div>
                </div>

                <!-- Arrow 2 (if there's a second exchange or withdrawal) -->
                <div v-if="result.exchanges.length > 1 || result.transferFee > 0" class="flex flex-col items-center h-16 justify-center">
                  <svg class="w-8 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                  </svg>
                  <div class="text-xs text-gray-500 mt-1">
                    {{ result.exchanges.length > 1 ? 'USDT전송' : 'BTC출금' }}
                  </div>
                </div>

                <!-- Exchange 2 or Withdrawal -->
                <div v-if="result.exchanges.length > 1 || result.transferFee > 0" class="flex flex-col items-center relative px-5 pt-5 pb-3">
                  <component v-if="result.exchanges.length > 1"
                             :is="getExchangeUrl(result.exchanges[1].name) ? 'a' : 'div'"
                             :href="getExchangeUrl(result.exchanges[1].name) || undefined"
                             target="_blank" rel="noopener noreferrer"
                             class="w-24 h-16 bg-white border border-gray-300 text-gray-800 rounded-lg flex flex-col items-center justify-center shadow relative block">

                    <!-- Second exchange icon -->
                    <svg class="w-6 h-6 mb-1 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7" />
                    </svg>
                    <div class="text-xs font-medium text-center leading-tight px-1">{{ result.exchanges[1].name }}</div>

                    <!-- Event badge for second exchange (prevent navigation) -->
                    <div v-if="result.exchanges[1].note"
                         @click.prevent.stop="showEventDetails(result.exchanges[1].eventDetails)"
                         class="absolute -top-3 -right-3 bg-orange-500 text-white text-xs px-1.5 py-0.5 rounded-full font-medium shadow whitespace-nowrap cursor-pointer hover:bg-orange-600 transition-colors">
                      이벤트
                    </div>
                  </component>
                  <div v-else class="w-24 h-16 bg-gray-700 text-white rounded-lg flex flex-col items-center justify-center shadow">
                    <svg class="w-6 h-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                    <div class="text-xs font-medium text-center leading-tight px-1">출금</div>
                  </div>

                  <!-- Purchase label for second exchange (if present) -->
                  <div v-if="result.exchanges.length > 1 && getPurchaseLabelForExchange(result.exchanges[1]?.name)" class="text-[11px] text-gray-700 mt-1">
                    {{ getPurchaseLabelForExchange(result.exchanges[1].name) }}
                  </div>
                  <div class="text-xs text-center mt-2 space-y-1">
                    <div class="text-gray-900 font-medium">
                      {{ formatPrice(result.exchanges.length > 1 ? getSecondTradingFee(result) : result.transferFee) }}원
                    </div>
                    <div class="text-gray-500">
                      {{ result.exchanges.length > 1 ? `거래수수료 (${result.exchanges[1].rate}%)` : '출금수수료' }}
                      <div v-if="getBtcWithdrawalFee(result)" class="text-xs text-gray-400 mt-0.5">
                        ({{ getBtcWithdrawalFee(result) }} BTC)
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Arrow 3 (to Lightning if applicable) -->
                <div v-if="result.lightningServices && result.lightningServices.length > 0" class="flex flex-col items-center h-16 justify-center">
                  <svg class="w-8 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                  </svg>
                  <div class="text-xs text-gray-500 mt-1">라이트닝</div>
                </div>

                <!-- Lightning Service -->
                <div v-if="result.lightningServices && result.lightningServices.length > 0" class="flex flex-col items-center relative px-6 pt-5 pb-3">
                  <component :is="getServiceUrl(result.lightningServices[0].name) ? 'a' : 'div'"
                             :href="getServiceUrl(result.lightningServices[0].name) || undefined"
                             target="_blank" rel="noopener noreferrer"
                             class="w-24 h-16 bg-white border border-gray-300 text-gray-800 rounded-lg flex flex-col items-center justify-center shadow relative block">

                    <!-- Lightning service icon -->
                    <svg class="w-6 h-6 mb-1 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    <div class="text-xs font-medium text-center leading-tight px-1">{{ result.lightningServices[0].name }}</div>

                    <!-- KYC badge -->
                    <div class="absolute -top-3 -right-3 text-xs px-1.5 py-0.5 rounded-full font-medium shadow whitespace-nowrap"
                         :class="result.lightningServices[0].isKyc
                           ? 'bg-red-500 text-white'
                           : 'bg-green-500 text-white'">
                      {{ result.lightningServices[0].isKyc ? 'KYC' : 'non-KYC' }}
                    </div>
                  </component>
                  <div class="text-xs text-center mt-2 space-y-1">
                    <div class="text-gray-900 font-medium">{{ formatPrice(getLightningFee(result)) }}원</div>
                    <div class="text-gray-500">온체인 전환 수수료 ({{ result.lightningServices[0].rate }}%)</div>
                  </div>
                </div>

                <!-- Final Arrow -->
                <div class="flex flex-col items-center h-16 justify-center">
                  <svg class="w-8 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                  </svg>
                  <div class="text-xs text-gray-500 mt-1">최종출금</div>
                </div>

                <!-- End: Personal Wallet -->
                <div class="flex flex-col items-center">
                  <div class="w-20 h-16 bg-gray-900 text-white rounded-lg flex flex-col items-center justify-center shadow">
                    <svg class="w-6 h-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                    </svg>
                    <div class="text-xs font-medium">개인지갑</div>
                  </div>
                  <div class="text-xs text-center mt-2 space-y-1">
                    <div class="text-gray-900 font-bold">{{ formatPrice(result.actualAmount) }}원</div>
                    <div class="text-gray-500">수령금액</div>
                  </div>
                </div>

              </div>
            </div>

            <!-- Event Guide Message in Flow View -->
            <div v-if="result.exchanges.some(ex => ex.note)" class="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
              <div class="text-sm text-gray-700">
                자세한 이벤트를 보려면 이벤트 표시를 클릭하세요
              </div>
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

    <!-- Event Details Modal -->
    <div v-if="showEventModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" @click="closeEventModal">
      <div class="bg-white rounded-lg max-w-md w-full p-6" @click.stop>
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-semibold text-gray-900">이벤트 상세정보</h3>
          <button @click="closeEventModal" class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="text-gray-700">
          <p v-if="selectedEventDetails" class="whitespace-pre-wrap">{{ selectedEventDetails }}</p>
          <p v-else class="text-gray-500 italic">이벤트 상세정보가 없습니다.</p>
        </div>
        <div class="mt-6 text-right">
          <button @click="closeEventModal" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors">
            닫기
          </button>
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
const viewMode = ref('flow') // 'cards' or 'flow'
const showEventModal = ref(false)
const selectedEventDetails = ref('')

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
  boltz: 0.5,
  coinos: 0.0,
  walletofsatoshi: 1.95,
  strike: 0.0
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

const bestResults = computed(() => {
  if (!sortedResults.value.length) return []
  const minFee = sortedResults.value[0].totalFee
  return sortedResults.value.filter(result => Math.abs(result.totalFee - minFee) < 0.01)
})

const isOptimal = (result) => {
  return bestResults.value.some(best => best.id === result.id)
}

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
  if (n.includes('월렛오브사토시') || n.includes('walletofsatoshi')) return 'https://walletofsatoshi.com'
  if (n.includes('strike')) return 'https://strike.me'
  return null
}

// Exchange official sites
const getExchangeUrl = (name) => {
  const n = (name || '').toLowerCase()
  if (n.includes('업비트') || n.includes('upbit')) return 'https://upbit.com'
  if (n.includes('빗썸') || n.includes('bithumb')) return 'https://www.bithumb.com'
  if (n.includes('바이낸스') || n.includes('binance')) return 'https://www.binance.com'
  if (n.includes('okx')) return 'https://www.okx.com'
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
        note: exchangeRatesInfo.value.upbit_btc?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.upbit_btc?.event_details || ''
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
        note: exchangeRatesInfo.value.upbit_btc?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.upbit_btc?.event_details || ''
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

  // 3. 빗썸 BTC → OKX → 온체인 개인지갑
  newResults.push({
    id: 'bithumb-btc-okx-onchain',
    title: '빗썸 BTC → OKX → 온체인 개인지갑',
    description: '빗썸 비트코인 직접 송금 → OKX → 온체인 개인지갑 출금',
    exchanges: [
      {
        name: '빗썸 (BTC)',
        rate: feeRates.value.bithumb,
        note: exchangeRatesInfo.value.bithumb?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.bithumb?.event_details || ''
      }
    ],
    withdrawalFees: [
      {
        name: '빗썸 BTC 송금',
        amount: btcTransferFee,
        amountKrw: btcTransferFee * bitcoinPrice.value
      },
      {
        name: 'OKX 온체인 개인지갑',
        amount: withdrawalFees.value.okx_onchain,
        amountKrw: withdrawalFees.value.okx_onchain * bitcoinPrice.value
      }
    ],
    tradingFee: amount * (feeRates.value.bithumb / 100),
    transferFee: btcTransferFee * bitcoinPrice.value + withdrawalFees.value.okx_onchain * bitcoinPrice.value,
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
        note: exchangeRatesInfo.value.upbit_usdt?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.upbit_usdt?.event_details || ''
      },
      {
        name: 'OKX',
        rate: feeRates.value.okx,
        note: exchangeRatesInfo.value.okx?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.okx?.event_details || ''
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
        note: exchangeRatesInfo.value.upbit_usdt?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.upbit_usdt?.event_details || ''
      },
      {
        name: '바이낸스',
        rate: feeRates.value.binance,
        note: exchangeRatesInfo.value.binance?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.binance?.event_details || ''
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
        note: exchangeRatesInfo.value.upbit_btc?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.upbit_btc?.event_details || ''
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
      rate: lightningServices.value.boltz,
      isKyc: lightningServicesInfo.value.boltz?.is_kyc || false
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
        note: exchangeRatesInfo.value.upbit_btc?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.upbit_btc?.event_details || ''
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
      rate: lightningServices.value.coinos,
      isKyc: lightningServicesInfo.value.coinos?.is_kyc || false
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
        note: exchangeRatesInfo.value.upbit_btc?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.upbit_btc?.event_details || ''
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
      rate: lightningServices.value.boltz,
      isKyc: lightningServicesInfo.value.boltz?.is_kyc || false
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
        note: exchangeRatesInfo.value.upbit_btc?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.upbit_btc?.event_details || ''
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
      rate: lightningServices.value.coinos,
      isKyc: lightningServicesInfo.value.coinos?.is_kyc || false
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
        note: exchangeRatesInfo.value.upbit_usdt?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.upbit_usdt?.event_details || ''
      },
      {
        name: 'OKX',
        rate: feeRates.value.okx,
        note: exchangeRatesInfo.value.okx?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.okx?.event_details || ''
      }
    ],
    withdrawalFees: [{
      name: 'OKX 라이트닝',
      amount: withdrawalFees.value.okx_lightning,
      amountKrw: withdrawalFees.value.okx_lightning * bitcoinPrice.value
    }],
    lightningServices: [{
      name: 'Boltz Exchange',
      rate: lightningServices.value.boltz,
      isKyc: lightningServicesInfo.value.boltz?.is_kyc || false
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
        note: exchangeRatesInfo.value.upbit_usdt?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.upbit_usdt?.event_details || ''
      },
      {
        name: 'OKX',
        rate: feeRates.value.okx,
        note: exchangeRatesInfo.value.okx?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.okx?.event_details || ''
      }
    ],
    withdrawalFees: [{
      name: 'OKX 라이트닝',
      amount: withdrawalFees.value.okx_lightning,
      amountKrw: withdrawalFees.value.okx_lightning * bitcoinPrice.value
    }],
    lightningServices: [{
      name: 'Coinos',
      rate: lightningServices.value.coinos,
      isKyc: lightningServicesInfo.value.coinos?.is_kyc || false
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
        note: exchangeRatesInfo.value.upbit_usdt?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.upbit_usdt?.event_details || ''
      },
      {
        name: '바이낸스',
        rate: feeRates.value.binance,
        note: exchangeRatesInfo.value.binance?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.binance?.event_details || ''
      }
    ],
    withdrawalFees: [{
      name: '바이낸스 라이트닝',
      amount: withdrawalFees.value.binance_lightning,
      amountKrw: withdrawalFees.value.binance_lightning * bitcoinPrice.value
    }],
    lightningServices: [{
      name: 'Boltz Exchange',
      rate: lightningServices.value.boltz,
      isKyc: lightningServicesInfo.value.boltz?.is_kyc || false
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
        note: exchangeRatesInfo.value.upbit_usdt?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.upbit_usdt?.event_details || ''
      },
      {
        name: '바이낸스',
        rate: feeRates.value.binance,
        note: exchangeRatesInfo.value.binance?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.binance?.event_details || ''
      }
    ],
    withdrawalFees: [{
      name: '바이낸스 라이트닝',
      amount: withdrawalFees.value.binance_lightning,
      amountKrw: withdrawalFees.value.binance_lightning * bitcoinPrice.value
    }],
    lightningServices: [{
      name: 'Coinos',
      rate: lightningServices.value.coinos,
      isKyc: lightningServicesInfo.value.coinos?.is_kyc || false
    }],
    tradingFee: amount * (feeRates.value.upbit_usdt / 100) + amount * (feeRates.value.binance / 100),
    transferFee: withdrawalFees.value.binance_lightning * bitcoinPrice.value,
    lightningFee: amount * (lightningServices.value.coinos / 100),
    totalFee: 0,
    actualAmount: 0,
    feeRate: 0
  })

  // Add new lightning service scenarios with 월렛오브사토시 and Strike
  // 14. 업비트 → OKX → 월렛오브사토시 → 온체인 개인지갑
  newResults.push({
    id: 'upbit-usdt-okx-lightning-walletofsatoshi',
    title: '업비트 → OKX → 월렛오브사토시 → 온체인 개인지갑',
    description: '업비트 USDT → OKX → 라이트닝 → 월렛오브사토시 → 온체인 개인지갑',
    exchanges: [
      {
        name: '업비트 (USDT)',
        rate: feeRates.value.upbit_usdt,
        note: exchangeRatesInfo.value.upbit_usdt?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.upbit_usdt?.event_details || ''
      },
      {
        name: 'OKX',
        rate: feeRates.value.okx,
        note: exchangeRatesInfo.value.okx?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.okx?.event_details || ''
      }
    ],
    withdrawalFees: [{
      name: 'OKX 라이트닝',
      amount: withdrawalFees.value.okx_lightning,
      amountKrw: withdrawalFees.value.okx_lightning * bitcoinPrice.value
    }],
    lightningServices: [{
      name: '월렛오브사토시',
      rate: lightningServices.value.walletofsatoshi,
      isKyc: lightningServicesInfo.value.walletofsatoshi?.is_kyc || false
    }],
    tradingFee: amount * (feeRates.value.upbit_usdt / 100) + amount * (feeRates.value.okx / 100),
    transferFee: withdrawalFees.value.okx_lightning * bitcoinPrice.value,
    lightningFee: amount * (lightningServices.value.walletofsatoshi / 100),
    totalFee: 0,
    actualAmount: 0,
    feeRate: 0
  })

  // 업비트 → OKX → Strike → 온체인 개인지갑 (문구에서 0% 언급 제거)
  newResults.push({
    id: 'upbit-usdt-okx-lightning-strike',
    title: '업비트 → OKX → Strike → 온체인 개인지갑',
    description: '업비트 USDT → OKX → 라이트닝 → Strike → 온체인 개인지갑',
    exchanges: [
      {
        name: '업비트 (USDT)',
        rate: feeRates.value.upbit_usdt,
        note: exchangeRatesInfo.value.upbit_usdt?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.upbit_usdt?.event_details || ''
      },
      {
        name: 'OKX',
        rate: feeRates.value.okx,
        note: exchangeRatesInfo.value.okx?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.okx?.event_details || ''
      }
    ],
    withdrawalFees: [{
      name: 'OKX 라이트닝',
      amount: withdrawalFees.value.okx_lightning,
      amountKrw: withdrawalFees.value.okx_lightning * bitcoinPrice.value
    }],
    lightningServices: [{
      name: 'Strike',
      rate: lightningServices.value.strike,
      isKyc: lightningServicesInfo.value.strike?.is_kyc || true
    }],
    tradingFee: amount * (feeRates.value.upbit_usdt / 100) + amount * (feeRates.value.okx / 100),
    transferFee: withdrawalFees.value.okx_lightning * bitcoinPrice.value,
    lightningFee: amount * (lightningServices.value.strike / 100),
    totalFee: 0,
    actualAmount: 0,
    feeRate: 0
  })

  

  // 16. 업비트 BTC → OKX → 월렛오브사토시 → 온체인 개인지갑
  newResults.push({
    id: 'upbit-btc-okx-lightning-walletofsatoshi',
    title: '업비트 BTC → OKX → 월렛오브사토시 → 온체인 개인지갑',
    description: '업비트 비트코인 직접 송금 → OKX → 라이트닝 → 월렛오브사토시 → 온체인 개인지갑',
    exchanges: [
      {
        name: '업비트 (BTC)',
        rate: feeRates.value.upbit_btc,
        note: exchangeRatesInfo.value.upbit_btc?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.upbit_btc?.event_details || ''
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
      name: '월렛오브사토시',
      rate: lightningServices.value.walletofsatoshi,
      isKyc: lightningServicesInfo.value.walletofsatoshi?.is_kyc || false
    }],
    tradingFee: amount * (feeRates.value.upbit_btc / 100),
    transferFee: btcTransferFee * bitcoinPrice.value + withdrawalFees.value.okx_lightning * bitcoinPrice.value,
    lightningFee: amount * (lightningServices.value.walletofsatoshi / 100),
    totalFee: 0,
    actualAmount: 0,
    feeRate: 0
  })

  // 업비트 BTC → OKX → Strike → 온체인 개인지갑 (문구에서 0% 언급 제거)
  newResults.push({
    id: 'upbit-btc-okx-lightning-strike',
    title: '업비트 BTC → OKX → Strike → 온체인 개인지갑',
    description: '업비트 비트코인 직접 송금 → OKX → 라이트닝 → Strike → 온체인 개인지갑',
    exchanges: [
      {
        name: '업비트 (BTC)',
        rate: feeRates.value.upbit_btc,
        note: exchangeRatesInfo.value.upbit_btc?.is_event ? '한시적 이벤트' : '',
        eventDetails: exchangeRatesInfo.value.upbit_btc?.event_details || ''
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
      name: 'Strike',
      rate: lightningServices.value.strike,
      isKyc: lightningServicesInfo.value.strike?.is_kyc || true
    }],
    tradingFee: amount * (feeRates.value.upbit_btc / 100),
    transferFee: btcTransferFee * bitcoinPrice.value + withdrawalFees.value.okx_lightning * bitcoinPrice.value,
    lightningFee: amount * (lightningServices.value.strike / 100),
    totalFee: 0,
    actualAmount: 0,
    feeRate: 0
  })

  

  // Calculate totals and final amounts for all scenarios with step-by-step deduction
  newResults.forEach(result => {
    let currentAmount = amount

    // Step 1: Apply trading fee (첫 번째 거래소 수수료)
    const actualTradingFee = currentAmount * (result.exchanges[0].rate / 100)
    currentAmount -= actualTradingFee

    // Step 2: Apply transfer fee (출금 수수료 - 고정)
    currentAmount -= result.transferFee

    // Step 3: Apply second exchange trading fee if exists
    let secondTradingFee = 0
    if (result.exchanges.length > 1) {
      secondTradingFee = currentAmount * (result.exchanges[1].rate / 100)
      currentAmount -= secondTradingFee
    }

    // Step 4: Apply lightning service fee on remaining amount
    let actualLightningFee = 0
    if (result.lightningServices && result.lightningServices.length > 0) {
      actualLightningFee = currentAmount * (result.lightningServices[0].rate / 100)
      currentAmount -= actualLightningFee
    }

    // Update result with corrected values
    result.tradingFee = actualTradingFee + secondTradingFee
    result.lightningFee = actualLightningFee
    result.totalFee = result.tradingFee + result.transferFee + result.lightningFee
    result.actualAmount = currentAmount
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

const showEventDetails = (eventDetails) => {
  selectedEventDetails.value = eventDetails
  showEventModal.value = true
}

const closeEventModal = () => {
  showEventModal.value = false
  selectedEventDetails.value = ''
}

const getBtcWithdrawalFee = (result) => {
  // 업비트/빗썸의 BTC 출금 수수료는 0.0002 BTC
  if (result.exchanges.length === 1 && result.transferFee > 0) {
    return 0.0002
  }
  return null
}

const getFirstTradingFee = (result) => {
  const amount = getActualAmount()
  return amount * (result.exchanges[0].rate / 100)
}

const getSecondTradingFee = (result) => {
  if (result.exchanges.length <= 1) return 0

  const amount = getActualAmount()
  const afterFirstTrading = amount - getFirstTradingFee(result)
  const afterTransfer = afterFirstTrading - result.transferFee

  return afterTransfer * (result.exchanges[1].rate / 100)
}

const getLightningFee = (result) => {
  if (!result.lightningServices || result.lightningServices.length === 0) return 0

  const amount = getActualAmount()
  let currentAmount = amount

  // Step 1: 첫 번째 거래소 수수료 차감
  currentAmount -= getFirstTradingFee(result)

  // Step 2: 출금 수수료 차감
  currentAmount -= result.transferFee

  // Step 3: 두 번째 거래소 수수료 차감 (있는 경우)
  if (result.exchanges.length > 1) {
    currentAmount -= getSecondTradingFee(result)
  }

  // Step 4: 라이트닝 서비스 수수료 계산
  return currentAmount * (result.lightningServices[0].rate / 100)
}

// Determine purchase label text for an exchange name
const getPurchaseLabelForExchange = (name) => {
  const n = (name || '').toLowerCase()
  // Upbit/Bithumb: show BTC or USDT explicitly
  if (n.includes('업비트') || n.includes('bithumb') || n.includes('빗썸')) {
    if (n.includes('usdt')) return 'USDT 구매'
    if (n.includes('btc')) return 'BTC 구매'
    // Fallback if asset not in name
    return 'BTC 구매'
  }
  // Binance/OKX: always show BTC purchase per requirement
  if (n.includes('binance') || n.includes('바이낸스') || n.includes('okx')) {
    return 'BTC 구매'
  }
  // Generic detection from name
  if (n.includes('usdt')) return 'USDT 구매'
  if (n.includes('btc')) return 'BTC 구매'
  return ''
}

// Initialize data
onMounted(async () => {
  // Detect mobile viewport
  const mq = window.matchMedia('(max-width: 767px)')
  const updateMobile = () => { isMobile.value = mq.matches }
  updateMobile()
  try { mq.addEventListener('change', updateMobile) } catch (_) { mq.addListener(updateMobile) }

  // ESC key listener for modal
  const handleEscKey = (event) => {
    if (event.key === 'Escape' && showEventModal.value) {
      closeEventModal()
    }
  }
  document.addEventListener('keydown', handleEscKey)

  await fetchBitcoinPrice()
  await loadData()

  // Calculate fees if there's already an amount entered
  if (inputAmount.value) {
    calculateFees()
  }
})
</script>
