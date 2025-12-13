<template>
  <div class="space-y-6">
    <section class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6">
      <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 class="text-lg font-semibold text-slate-900">재무 관리</h2>
          <p class="text-sm text-slate-500 mt-1">
            비트코인과 주요 자산군의 과거/미래 수익률을 한 화면에서 비교하세요.
          </p>
        </div>
        <div class="flex rounded-xl bg-slate-100 p-full md:w-auto">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            class="flex-1 px-4 py-2 text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            :class="activeTab === tab.key
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-500'"
            :disabled="tab.disabled"
            :aria-disabled="tab.disabled ? 'true' : 'false'"
            :title="tab.disabled ? tab.disabledLabel || '현재 비활성화된 탭입니다' : undefined"
            @click="handleTabClick(tab)"
          >
            {{ tab.label }}
          </button>
        </div>
      </div>
    </section>

    <section v-if="activeTab === 'historical'" class="space-y-6">
      <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 space-y-5">
        <div class="flex flex-col gap-1">
          <h3 class="text-base font-semibold text-slate-900">
            {{ analysisResultType === 'price' ? '자산의 가격 분석' : analysisResultType === 'cumulative' ? '자산의 누적 수익률 분석' : analysisResultType === 'yearly_growth' ? '자산의 전년 대비 증감률 분석' : '비트코인을 다른 자산과 비교해보자' }}
          </h3>
          <p class="text-xs text-slate-500 mt-1">
            아래 텍스트의 숫자는 선택하여 수정할 수 있습니다.
          </p>
        </div>

        <div class="space-y-4">
          <div class="bg-slate-900 rounded-2xl p-5 sm:p-6 shadow-inner flex flex-col gap-4">
          <div class="flex items-center justify-between gap-4">
            <div class="relative flex-1 min-h-[3.5rem] sm:min-h-[3.8rem] flex items-center">
              <p
                class="typewriter-text text-2xl sm:text-3xl font-black leading-tight tracking-tight text-[#ffd400] flex flex-wrap items-center gap-2"
                :class="heroAnimationActive ? 'opacity-0' : 'opacity-100 transition-opacity duration-300'"
                :key="heroAnimationKey"
              >
                <span
                  class="editable-chunk"
                  contenteditable="true"
                  spellcheck="false"
                  role="textbox"
                  aria-label="투자 시점(년 전)"
                  @focus="handleEditableFocus"
                  @keydown="handleEditableKeydown"
                  @paste="handleEditablePaste"
                  @blur="handleEditableBlur('year', $event)"
                >{{ investmentYearsAgo }}</span>
                <span>&nbsp;년 전에&nbsp;</span>
                <span class="font-black">비트코인&nbsp;</span>
                <span
                  class="editable-chunk"
                  contenteditable="true"
                  spellcheck="false"
                  role="textbox"
                  aria-label="투자 금액"
                  @focus="handleEditableFocus"
                  @keydown="handleEditableKeydown"
                  @paste="handleEditablePaste"
                  @blur="handleEditableBlur('amount', $event)"
                >{{ formattedInvestmentAmountNumber }}</span>
                <span>&nbsp;만원을 샀다면 지금 얼마일까?</span>
              </p>

              <p
                v-if="heroAnimationActive"
                class="hero-typewriter-overlay text-2xl sm:text-3xl font-black leading-tight tracking-tight text-[#ffd400] flex items-center"
                aria-hidden="true"
              >
                {{ displayedHeroText }}<span class="hero-typewriter-cursor"></span>
              </p>
            </div>
            
            <button 
              @click="handleSearchClick"
              :disabled="loading || customAssetResolving"
              class="p-3 rounded-xl text-[#ffd400] hover:text-[#ffc400] active:scale-95 transition-all flex-shrink-0 group disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100"
              :class="{'animate-attention': searchButtonAttention}"
              aria-label="분석 시작"
            >
              <svg class="w-6 h-6 group-hover:rotate-12 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
            </button>
          </div>

          <!-- Quick Compare Buttons -->
          <div
            v-if="quickCompareGroups.length || quickCompareGroupsLoading"
            class="flex flex-wrap gap-3 items-center pt-4 border-t border-slate-700/50"
          >
            <span class="text-slate-400 text-sm mr-2">빠른 비교:</span>
            <div class="flex flex-wrap gap-2">
              <template v-if="quickCompareGroups.length">
                <button
                  v-for="group in quickCompareGroups"
                  :key="group.key"
                  class="px-3 py-1 rounded-full text-xs border transition flex items-center gap-1"
                  :class="selectedQuickCompareGroup === group.key ? 'bg-transparent text-[#ffd400] border-[#ffd400]' : 'bg-slate-800 text-slate-200 border-slate-700 hover:border-slate-500'"
                  :disabled="quickCompareLoadingKey === group.key"
                  @click="applyQuickCompare(group.key, { autoRun: false })"
                >
                  <span>{{ group.label }}</span>
                  <svg
                    v-if="quickCompareLoadingKey === group.key"
                    class="w-3 h-3 animate-spin text-current"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke-width="4"></circle>
                    <path class="opacity-75" stroke-width="4" d="M4 12a8 8 0 018-8"></path>
                  </svg>
                </button>
              </template>
              <span
                v-else
                class="text-xs text-slate-400 flex items-center gap-1"
              >
                <svg class="w-3 h-3 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke-width="4"></circle>
                  <path class="opacity-75" stroke-width="4" d="M4 12a8 8 0 018-8"></path>
                </svg>
                그룹을 불러오는 중...
              </span>
            </div>
            <button
              class="px-3 py-1 rounded-full text-xs border border-slate-700 text-slate-300 hover:border-slate-500 transition disabled:opacity-50"
              :disabled="customAssetResolving || loading || !customAssets.length"
              @click="clearAllCustomAssets"
            >
              모두 제거
            </button>
          </div>
          <p v-else class="text-xs text-slate-500 pt-4 border-t border-slate-700/50">
            등록된 빠른 비교 그룹이 없습니다.
          </p>

          <!-- Custom Assets Input -->
          <div class="flex flex-wrap gap-2 items-center">
            <span class="text-slate-400 text-sm mr-2">비교 종목:</span>
            <div 
              v-for="(asset, index) in customAssets" 
              :key="`${asset.label}-${asset.ticker || index}`" 
              class="bg-slate-800 text-slate-200 px-3 py-1 rounded-full text-sm flex items-center gap-2 border border-slate-700 animate-fade-in"
            >
              {{ asset.display || asset.label }}
              <button @click="removeAsset(index)" class="text-slate-500 hover:text-slate-300">×</button>
            </div>
            
            <div class="relative group">
              <input 
                v-model="newAssetInput"
                @keydown.enter.prevent="handleAssetEnter"
                type="text" 
                placeholder="종목명 (Enter)"
                :disabled="customAssetResolving || loading"
                class="bg-slate-800/50 text-white placeholder-slate-500 border border-slate-700 rounded-full px-4 py-1 text-sm focus:outline-none focus:border-[#ffd400] w-32 focus:w-48 transition-all disabled:opacity-50"
              />
              <button 
                @click="addAsset" 
                :disabled="customAssetResolving || loading"
                class="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-[#ffd400] transition-colors disabled:opacity-40"
              >
                <span v-if="!customAssetResolving">+</span>
                <svg v-else class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke-width="4"></circle>
                  <path class="opacity-75" stroke-width="4" d="M4 12a8 8 0 018-8"></path>
                </svg>
              </button>
            </div>
          </div>
          <p v-if="customAssetError" class="text-xs text-rose-400">{{ customAssetError }}</p>
        </div>

          <p v-if="errorMessage" class="text-xs text-rose-600">{{ errorMessage }}</p>
        </div>
      </div>

      <!-- Chart and Details Section -->
      <div v-if="analysis && !loading" class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 space-y-5">
        <!-- AI Analysis Summary (slider-reactive) -->
        <div
          v-if="bitcoinHeroSummary"
          class="space-y-3 text-slate-900 mb-6"
        >
          <p class="text-2xl sm:text-3xl font-black leading-snug">
            {{ bitcoinHeroSummary.startYear }}년부터 {{ bitcoinHeroSummary.endYear }}년까지 비트코인은
            {{ bitcoinHeroSummary.duration }}년 동안 원금의
            <span class="px-3 py-1 rounded-xl bg-yellow-200 text-yellow-900 font-black">
              {{ bitcoinHeroSummary.multipleText }}
            </span>
            가 되었습니다.
          </p>
          <p class="text-2xl sm:text-3xl font-black text-slate-900">
            같은 기간 연평균 상승률은
            <span class="px-3 py-1 rounded-xl bg-yellow-200 text-yellow-900 font-black">
              {{ bitcoinHeroSummary.cagrText }}
            </span>
            였습니다.
          </p>
          <p class="text-2xl sm:text-3xl font-black text-slate-900">
            {{ bitcoinHeroSummary.investmentText }}을 비트코인에 투자했다면 지금은
            <span class="px-3 py-1 rounded-xl bg-emerald-200 text-emerald-900 font-black">
              {{ bitcoinHeroSummary.finalText }}
            </span>
            정도입니다.
          </p>
        </div>
        <div v-else-if="analysisSummary" class="mb-2">
          <div v-html="analysisSummary" class="analysis-summary-content"></div>
        </div>

        <p class="text-xs text-slate-500">
          1 USD ≈ ₩{{ formatFxRate(fxRate) }} (실시간 환율)
        </p>

        <FinanceLineChart
          :series="chartSeries"
          :colors="colorMap"
          :currency-mode="'usd'"
          :fx-rate="fxRate"
          :loading="loading"
          :logs="analysisLogs"
          :start-year="displayStartYear || sliderMinYear"
          :end-year="analysis?.end_year"
          :original-start-year="sliderMinYear"
          :show-year-slider="!!analysis"
          :tax-included="includeTax"
          :show-tax-toggle="true"
          :dividend-included="includeDividends"
          :show-dividend-toggle="true"
          :dividend-toggle-pending="dividendTogglePending"
          :price-data="priceTableData"
          :calculation-method="analysisResultType"
          :bitcoin-summary="bitcoinPerformanceText"
          @update:start-year="displayStartYear = $event"
          @toggle-tax="includeTax = !includeTax"
          @toggle-dividends="handleDividendToggle"
        />

        <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 space-y-4">
          <div class="flex items-center justify-between">
            <h4 class="text-sm font-semibold text-slate-900">범례</h4>
            <span class="text-[11px] text-slate-500">
              {{ analysisResultType === 'price' ? '연평균 상승률' : analysisResultType === 'cumulative' ? '누적 수익률' : analysisResultType === 'yearly_growth' ? '전년 대비 증감률' : '연평균 상승률' }} 순서로 정렬
            </span>
          </div>
          <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
            <button
              v-for="series in sortedLegend"
              :key="series.id"
              class="flex items-center justify-between rounded-2xl border px-4 py-3 text-left transition"
              :class="[
                hiddenSeries.has(series.id)
                  ? 'border-slate-200 text-slate-400 bg-slate-50'
                  : 'border-slate-200 text-slate-800 hover:border-slate-400',
                isBitcoinLegend(series) ? 'border-amber-400 shadow-[0_0_12px_rgba(255,215,0,0.6)]' : ''
              ]"
              @click="toggleSeries(series.id)"
            >
              <div class="flex items-center gap-3">
                <span
                  class="w-9 h-2 rounded-full"
                  :style="{ backgroundColor: colorMap[series.id] || lineColors[0], opacity: hiddenSeries.has(series.id) ? 0.3 : 1 }"
                ></span>
                <div class="min-w-0">
                  <div class="flex items-center gap-2 flex-wrap">
                    <p class="text-sm font-semibold">{{ getLegendLabel(series) }}</p>
                  </div>
                  <p class="text-xs text-slate-500">
                    {{ formatAssetCategory(series) }}
                  </p>
                  <p
                    v-if="getDividendYieldText(series)"
                    class="text-[11px] text-emerald-600 mt-1"
                  >
                    {{ getDividendYieldText(series) }}
                  </p>
                </div>
              </div>
              <div class="text-xs text-slate-500 text-right">
                <p>{{ analysisResultType === 'price' ? '연평균 상승률' : analysisResultType === 'yearly_growth' ? '평균 증감률' : '연평균' }} {{ formatPercent(series.annualized_return_pct) }}</p>
                <p>{{ formatMultiple(series.multiple_from_start) }}배</p>
              </div>
            </button>
          </div>
          <p class="text-[11px] text-slate-500">
            데이터 출처: <span v-html="dataSourcesText"></span>
          </p>
        </div>

        <div
          v-if="tableYears.length && sortedLegend.length"
          class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 space-y-3"
        >
          <div class="text-sm font-semibold text-slate-900">
            {{ analysisResultType === 'price' ? '연도별 가격 비교' : analysisResultType === 'cumulative' ? '연도별 누적 수익률 비교' : analysisResultType === 'yearly_growth' ? '연도별 전년 대비 증감률 비교' : '연도별 연평균 상승률 비교' }}
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full table-fixed text-xs text-slate-600 border-collapse">
              <thead>
                <tr class="bg-slate-50 text-slate-500">
                  <th class="py-2 px-2 text-left font-medium w-40">자산</th>
                  <th
                    v-for="year in tableYears"
                    :key="`ret-year-${year}`"
                    class="py-2 px-2 text-right font-medium"
                  >
                    {{ year }}년
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="series in sortedLegend"
                  :key="`ret-table-${series.id}`"
                  class="border-t border-slate-100"
                >
                  <td class="py-2 px-2 text-left font-semibold text-slate-700">
                    <a
                      v-if="getAssetUrl(series)"
                      :href="getAssetUrl(series)"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="hover:underline hover:text-blue-600 inline-flex items-center gap-1"
                      title="실제 가격 확인"
                    >
                      {{ getLegendLabel(series) }}
                      <svg class="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                      </svg>
                    </a>
                    <span v-else>{{ getLegendLabel(series) }}</span>
                  </td>
                  <td
                    v-for="year in tableYears"
                    :key="`ret-cell-${series.id}-${year}`"
                    class="py-2 px-2 text-right font-mono"
                    :class="getReturnCellClass(series, year)"
                  >
                    {{ getReturnForYear(series, year) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="flex items-center gap-2 text-xs text-slate-400 pt-3 border-t border-slate-100">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <span>{{ analysis.start_year }}년부터 {{ analysis.end_year }}년까지의 과거 데이터를 기반으로 계산되었습니다</span>
        </div>
      </div>

      <!-- Loading / Empty States -->
      <template v-if="loading">
        <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-8">
          <div class="flex flex-col items-center gap-4 text-center">
            <div class="space-y-1">
              <p class="text-sm font-semibold text-slate-900">{{ currentLoadingStageLabel }}</p>
              <p class="text-xs text-slate-500">{{ getLoadingMessage() }}</p>
            </div>
            <div class="w-full max-w-md">
              <div class="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
                <div
                  class="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-300 ease-out"
                  :style="{ width: `${loadingProgress}%` }"
                ></div>
              </div>
            </div>
            <p class="text-xs text-slate-500">진행률 {{ loadingProgress }}%</p>
            <button
              class="flex items-center gap-2 px-3 py-1.5 border border-rose-200 text-rose-500 text-xs rounded-full hover:bg-rose-50 transition-colors"
              @click="cancelRequest"
            >
              <svg class="w-3.5 h-3.5 animate-spin" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
              취소
            </button>
          </div>
        </div>
      </template>
      <template v-else>
        <div
          class="bg-slate-50 border border-dashed border-slate-200 rounded-2xl p-6 text-sm text-slate-600"
        >
          아직 분석된 데이터가 없습니다. 상단 텍스트를 조정하거나 빠른 비교 태그를 눌러 예시 요청을 실행해 보세요.
        </div>
      </template>

      <AdminPromptPanel
        class="mt-6"
        :show-debug="showLogs"
        :display-logs="displayLogs"
        @update:show-debug="showLogs = $event"
      />
    </section>

    <section v-else class="space-y-4">
      <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 space-y-4">
        <h3 class="text-base font-semibold text-slate-900">미래 비트코인 수익률 시나리오</h3>
        <p class="text-sm text-slate-600">
          온체인 사이클, 거시 환경, 채택률을 기준으로 3가지 시나리오를 구성했습니다.
          실사용 데이터가 업데이트되면 자동으로 보정하도록 설계되어 있습니다.
        </p>
        <div class="grid gap-4 md:grid-cols-3">
          <div
            v-for="scenario in futureScenarios"
            :key="scenario.title"
            class="rounded-2xl border border-slate-200 p-4 bg-slate-50"
          >
            <p class="text-xs font-semibold text-slate-500 uppercase mb-1">{{ scenario.title }}</p>
            <p class="text-sm font-semibold text-slate-900 mb-2">{{ scenario.headline }}</p>
            <ul class="space-y-1 text-xs text-slate-500">
              <li>1년 기대 수익률: {{ scenario.oneYear }}</li>
              <li>3년 연평균: {{ scenario.threeYear }}</li>
              <li>핵심 변수: {{ scenario.trigger }}</li>
            </ul>
          </div>
        </div>
        <p class="text-xs text-slate-500">
          실제 투자 판단은 별도의 리서치를 병행하세요. 본 시나리오는 참고용입니다.
        </p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, ref, watch, onBeforeUnmount, onMounted, reactive } from 'vue'
import FinanceLineChart from '@/components/FinanceLineChart.vue'
import AdminPromptPanel from '@/components/AdminPromptPanel.vue'
import { fetchHistoricalReturnsStream, fetchHistoricalReturns, resolveCustomAsset, fetchFinanceQuickCompareGroups } from '@/services/financeService'
import { defaultFinanceQuickCompareGroups } from '@/config/financeQuickCompareGroups'
const TAX_RATE = 0.22
const HERO_ANIMATION_DURATION = 2800
const MIN_DIVIDEND_YIELD_DISPLAY = 0.1
const LOADING_STAGES = [
  {
    key: 'init',
    label: '요청 준비 중',
    description: '멀티 에이전트 구성을 시작하고 있어요.',
    minProgress: 5,
    maxProgress: 12,
    fallbackDelayMs: 0,
    autoIncrement: 1,
    matchers: ['시스템:', '분석 시작', '분석 요청']
  },
  {
    key: 'intent',
    label: '프롬프트 해석 중',
    description: '요청에서 비교할 자산을 해석하고 있어요.',
    minProgress: 15,
    maxProgress: 30,
    fallbackDelayMs: 1500,
    autoIncrement: 2,
    matchers: ['[의도 분석]', 'intent']
  },
  {
    key: 'data',
    label: '자산 데이터 수집 중',
    description: '각 자산의 연도별 가격 데이터를 불러오고 있어요.',
    minProgress: 30,
    maxProgress: 70,
    fallbackDelayMs: 3500,
    autoIncrement: 2,
    matchers: ['[데이터 수집]', 'price retriever', '데이터 가져오는 중']
  },
  {
    key: 'calc',
    label: '수익률 계산 중',
    description: '불러온 데이터를 바탕으로 수익률을 계산하고 있어요.',
    minProgress: 70,
    maxProgress: 90,
    fallbackDelayMs: 7000,
    autoIncrement: 1,
    matchers: ['[수익률 계산]', 'calculator']
  },
  {
    key: 'summary',
    label: '결과 정리 중',
    description: '분석 내용을 정리하고 보고서를 구성하고 있어요.',
    minProgress: 90,
    maxProgress: 99,
    fallbackDelayMs: 9500,
    autoIncrement: 1,
    matchers: ['[분석 생성]', 'analysis', '요약']
  }
]
const DATA_STAGE_KEY = 'data'

const tabs = [
  { key: 'historical', label: '과거 수익률' },
  { key: 'future', label: '미래 시나리오', disabled: true, disabledLabel: '준비 중인 기능입니다' }
]

const QUICK_COMPARE_CONTEXT_MAP = {
  frequent: 'safe_assets',
  safe_assets: 'safe_assets',
  us_bigtech: 'us_bigtech',
  kr_bluechips: 'kr_equity',
  kr_equity: 'kr_equity',
  dividend_favorites: 'safe_assets'
}

const futureScenarios = [
  {
    title: 'Defensive',
    headline: '보수적인 미래 수익률',
    oneYear: '연 +5% ~ +8%',
    threeYear: '연평균 +10%',
    trigger: '고금리·규제 강화'
  },
  {
    title: 'Base',
    headline: '기본 시나리오 수익률',
    oneYear: '연 +12% ~ +20%',
    threeYear: '연평균 +22%',
    trigger: 'ETF 유입·기관 수요'
  },
  {
    title: 'Growth',
    headline: '고성장 수익률 전망',
    oneYear: '연 +25% ~ +40%',
    threeYear: '연평균 +35%',
    trigger: '온체인 확장·네트워크 효과'
  }
]

const investmentYearsAgo = ref(10)
const investmentAmount = ref(100)
const heroAnimationKey = ref(0)
const heroAnimationActive = ref(false)
const searchButtonAttention = ref(false)
const heroTypewriterSnapshot = ref('')
const displayedHeroText = ref('')
let heroAnimationTimer = null
let typingInterval = null
const pendingAgentCall = ref(false)

// 라인 차트 색상 (진한 색상)
const lineColors = ['#0f172a', '#2563eb', '#f97316', '#dc2626', '#059669', '#7c3aed', '#ea580c', '#0891b2', '#be185d', '#4338ca']

const activeTab = ref('historical')
const handleTabClick = (tab) => {
  if (tab.disabled) return
  activeTab.value = tab.key
}
const prompt = ref('')
const selectedContextKey = ref('safe_assets')
const hiddenSeries = ref(new Set())
const quickCompareLoadingKey = ref('')
const includeTax = ref(false)
const includeDividends = ref(false)
const dividendResultCache = reactive({ 'true': null, 'false': null })
const dividendDataReady = reactive({ 'true': false, 'false': false })
const pendingDividendTarget = ref(null)
let dividendPrefetchController = null
let dividendPrefetchTarget = null
const lastAnalysisRequest = ref(null)
const currentYear = new Date().getFullYear()
const priceDisplayMode = ref('usd')
const yearlyPriceMap = ref({})
const priceTableLoading = ref(false)
const priceTableError = ref('')
let priceRequestId = 0
const showWonMode = computed(() => selectedContextKey.value === 'kr_equity')
const showTaxToggle = computed(() => selectedContextKey.value === 'us_bigtech' && !loading.value && !!analysis.value)
const dividendTogglePending = computed(() => {
  if (!analysis.value) return false
  const targetValue = !includeDividends.value
  return !dividendDataReady[cacheKeyForDividends(targetValue)]
})
const chartStartYear = computed(() => {
  if (displayStartYear.value) return displayStartYear.value
  if (analysis.value?.start_year) return analysis.value.start_year
  const fallbackYear = currentYear - Math.max(1, Number(investmentYearsAgo.value) || 1)
  return Math.max(2010, fallbackYear)
})
const loading = ref(false)
const errorMessage = ref('')
const analysis = ref(null)
const analysisResultType = ref('cagr') // 'cagr' or 'cumulative'
const displayStartYear = ref(null)
const sliderMinYear = ref(null)
let abortController = null
const progressLogs = ref([])
function appendProgressLogs(...messages) {
  if (!messages.length) return
  progressLogs.value = [...progressLogs.value, ...messages]
}
const loadingProgress = ref(0)
const loadingStageIndex = ref(0)
const currentLoadingStage = computed(() => LOADING_STAGES[loadingStageIndex.value] || LOADING_STAGES[0])
const currentLoadingStageLabel = computed(() => currentLoadingStage.value?.label || '데이터를 준비하고 있어요.')
const stageFallbackTimers = new Map()
let loadingProgressInterval = null
let priceDataProgressBumps = 0
// showDetails ref removed
const analysisSummary = ref('')
const backendAnalysisSummary = ref('') // Store backend AI analysis separately

const showLogs = ref(false)

watch(loading, (isLoading) => {
  if (!isLoading && pendingAgentCall.value) {
    pendingAgentCall.value = false
    requestAgentAnalysis()
  }
})

watch(loading, (isLoading) => {
  if (!isLoading) {
    stopLoadingStageTracking()
  }
})

watch([loading, heroAnimationActive], ([isLoading, heroActive]) => {
  if (!isLoading && !heroActive) {
    searchButtonAttention.value = true
  }
}, { immediate: true })

function formatAssetCategory(series) {
  if (series.market_cap_group && typeof series.market_cap_rank === 'number') {
    return `${series.market_cap_group} ${series.market_cap_rank}위`
  }
  return series.market_cap_info || series.category || '자산군 정보 없음'
}

function getSeriesMetaValue(series, key) {
  if (!series || !key) return undefined
  if (Object.prototype.hasOwnProperty.call(series, key)) {
    return series[key]
  }
  if (series.metadata && Object.prototype.hasOwnProperty.call(series.metadata, key)) {
    return series.metadata[key]
  }
  return undefined
}

function getDividendYieldValue(series) {
  const value = Number(getSeriesMetaValue(series, 'dividend_yield_pct'))
  return Number.isFinite(value) ? value : null
}

function getDividendYieldText(series) {
  const value = getDividendYieldValue(series)
  if (!Number.isFinite(value) || value < MIN_DIVIDEND_YIELD_DISPLAY) return ''
  return `현재 배당률 ${formatPercent(value)}`
}

function formatPercent(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '0.0%'
  return `${value.toFixed(1)}%`
}

function handleEditableFocus(event) {
  selectEditableContents(event.target)
}

function handleEditableKeydown(event) {
  if (event.key === 'Enter') {
    event.preventDefault()
    event.currentTarget?.blur()
    handleSearchClick()
    return
  }

  const allowedKeys = [
    'Backspace', 'Delete', 'Tab', 'Escape',
    'ArrowLeft', 'ArrowRight', 'Home', 'End'
  ]
  if (allowedKeys.includes(event.key)) return
  if (event.ctrlKey || event.metaKey) return

  // Allow strictly numbers
  if (!/^\d$/.test(event.key)) {
    event.preventDefault()
  }
}

function handleEditablePaste(event) {
  event.preventDefault()
  const clipboard = (event.clipboardData || window.clipboardData)
  if (!clipboard) return
  const text = clipboard.getData('text')
  document.execCommand('insertText', false, text.replace(/[^\d]/g, ''))
}

function handleEditableBlur(field, event) {
  const rawText = event.target.innerText.replace(/[^\d]/g, '')
  const parsed = rawText ? parseInt(rawText, 10) : 0
  
  if (field === 'year') {
    // Watcher will clamp this value
    investmentYearsAgo.value = parsed || 1
    // Force DOM update to clamped/clean string (in case Vue doesn't re-render)
    // We use setTimeout to let the watcher run first if needed, 
    // though synchronous update usually works for simple refs.
    // But since watcher clamps it, we want the clamped value.
    // The watcher runs synchronously for refs.
    event.target.innerText = String(investmentYearsAgo.value)
  } else if (field === 'amount') {
    investmentAmount.value = parsed || 1
    event.target.innerText = formattedInvestmentAmountNumber.value
  }
}

function selectEditableContents(el) {
  if (!el || !window.getSelection) return
  const selection = window.getSelection()
  if (!selection) return
  const range = document.createRange()
  range.selectNodeContents(el)
  selection.removeAllRanges()
  selection.addRange(range)
}

onBeforeUnmount(() => {
  if (heroAnimationTimer) clearTimeout(heroAnimationTimer)
  if (typingInterval) clearInterval(typingInterval)
  cancelDividendPrefetch()
  stopLoadingStageTracking()
})

onMounted(() => {
  // Auto-start hero typewriter animation for the intro copy
  startHeroTypewriterAnimation()
  loadQuickCompareGroups()
})

function handleSearchClick() {
  if (loading.value || customAssetResolving.value) return
  searchButtonAttention.value = false
  prompt.value = buildPromptFromInputs()
  heroAnimationKey.value += 1
  displayStartYear.value = null
  // Trigger analysis
  requestAgentAnalysis()
}

function buildPromptFromInputs() {
  const years = Math.max(1, Math.min(30, Number(investmentYearsAgo.value) || 1))
  const amount = Math.max(1, Math.min(100000, Number(investmentAmount.value) || 1))
  const amountText = `${amount.toLocaleString('ko-KR')}만원`
  const assetText = customAssets.value.length
    ? customAssets.value.map((asset) => asset.display || asset.label).join(', ')
    : '대표 자산군'

  return `${years}년 전에 비트코인에 ${amountText}을 투자했다면 지금 얼마인지 알려주고, 비트코인과 비교 종목(${assetText})을 비교해줘.`
}

function startHeroTypewriterAnimation() {
  const fullText = heroTypewriterText.value
  heroTypewriterSnapshot.value = fullText
  displayedHeroText.value = ''
  heroAnimationKey.value += 1
  heroAnimationActive.value = true
  
  if (heroAnimationTimer) clearTimeout(heroAnimationTimer)
  if (typingInterval) clearInterval(typingInterval)
  
  let currentIndex = 0
  // Faster typing speed (e.g. 40ms per char) for smoother feel
  typingInterval = setInterval(() => {
    if (currentIndex < fullText.length) {
      displayedHeroText.value += fullText[currentIndex]
      currentIndex++
    } else {
      clearInterval(typingInterval)
      // Hold for a moment before showing the editable fields
      heroAnimationTimer = setTimeout(() => {
        heroAnimationActive.value = false
        searchButtonAttention.value = true
      }, 800)
    }
  }, 45)
}

function requestAgentAnalysis() {
  if (!prompt.value?.trim()) return
  if (loading.value) {
    pendingAgentCall.value = true
    return
  }
  pendingAgentCall.value = false
  runAnalysis()
}

const comparisonYears = computed(() => {
  if (!analysis.value) return 0
  const startYear = displayStartYear.value || analysis.value?.start_year
  return Math.max(1, analysis.value.end_year - startYear)
})

const defaultSummary = computed(() => {
  if (!analysis.value) return ''
  const period = `${analysis.value.start_year}년부터 ${analysis.value.end_year}년까지의`
  if (analysisResultType.value === 'cumulative') {
    return `${period} 누적 수익률입니다.`
  }
  return `${period} 연평균 상승률입니다.`
})

const formattedInvestmentAmountNumber = computed(() => {
  const value = Number(investmentAmount.value)
  if (!Number.isFinite(value) || value <= 0) return '0'
  return value.toLocaleString('ko-KR')
})

const heroTypewriterText = computed(() => {
  return `${investmentYearsAgo.value}년 전에 비트코인 ${formattedInvestmentAmountNumber.value}만원을 샀다면 지금 얼마일까?`
})

const quickCompareGroups = ref([])
const quickCompareGroupsLoading = ref(false)
const selectedQuickCompareGroup = ref('')
const customAssets = ref([])
const newAssetInput = ref('')
const customAssetResolving = ref(false)
const customAssetError = ref('')
let customAssetLoadId = 0
let quickCompareInitialized = false

watch(investmentYearsAgo, (value) => {
  let sanitized = Number(value)
  if (!Number.isFinite(sanitized)) sanitized = 1
  sanitized = Math.min(30, Math.max(1, Math.round(sanitized)))
  if (sanitized !== value) {
    investmentYearsAgo.value = sanitized
  }
})

watch(investmentAmount, (value) => {
  let sanitized = Number(value)
  if (!Number.isFinite(sanitized)) sanitized = 1
  sanitized = Math.min(100000, Math.max(1, Math.round(sanitized)))
  if (sanitized !== value) {
    investmentAmount.value = sanitized
  }
})

const promptIncludesBitcoin = computed(() => {
  const combined = (prompt.value || '').toLowerCase()
  return combined.includes('비트코인') || combined.includes('bitcoin') || combined.includes('btc')
})

const filteredSeries = computed(() => {
  if (!analysis.value?.series?.length) return []
  const startYear = displayStartYear.value || analysis.value?.start_year
  const baseSeries = analysis.value.series.filter((series) => promptIncludesBitcoin.value || !isBitcoinLabel(series?.label))
  if (!startYear) return baseSeries

  const isPriceMode = analysisResultType.value === 'price'

  return baseSeries.map((series) => {
    const filteredPoints = series.points.filter((point) => point.year >= startYear)
    if (filteredPoints.length < 2) return null

    const sortedPoints = [...filteredPoints].sort((a, b) => a.year - b.year)
    const appliesTax = includeTax.value && shouldApplyTax(series)
    const taxMultiplier = appliesTax ? 1 - TAX_RATE : 1

    if (isPriceMode) {
      const startPrice = getPointPrice(sortedPoints[0])
      const endPrice = getPointPrice(sortedPoints[sortedPoints.length - 1])
      if (!Number.isFinite(startPrice) || !Number.isFinite(endPrice) || startPrice <= 0 || endPrice <= 0) {
        return null
      }
      const years = sortedPoints[sortedPoints.length - 1].year - sortedPoints[0].year
      let annualizedReturnPct = 0
      let multipleFromStart = endPrice / startPrice

      if (years > 0) {
        const cagr = Math.pow(endPrice / startPrice, 1 / years) - 1
        const adjustedCagr = cagr * taxMultiplier
        annualizedReturnPct = adjustedCagr * 100
        if (1 + adjustedCagr > 0) {
          multipleFromStart = Math.pow(1 + adjustedCagr, years)
        }
      }

      const normalizedPoints = sortedPoints.map((point) => {
        const price = getPointPrice(point)
        if (!Number.isFinite(price) || price <= 0) {
          return null
        }
        const normalizedMultiple = price / startPrice
        return {
          ...point,
          unit: series.unit || point.unit,
          multiple: normalizedMultiple,
          value: normalizedMultiple
        }
      }).filter(Boolean)

      if (normalizedPoints.length < 2) return null

      return {
        ...series,
        points: normalizedPoints,
        annualized_return_pct: annualizedReturnPct,
        multiple_from_start: multipleFromStart
      }
    }

    const startMultiple = Number(sortedPoints[0].multiple)
    const endMultiple = Number(sortedPoints[sortedPoints.length - 1].multiple)
    const years = sortedPoints[sortedPoints.length - 1].year - sortedPoints[0].year

    let annualizedReturnPct = 0
    let multipleFromStart = 1

    if (startMultiple && endMultiple && years > 0) {
      const cagr = Math.pow(endMultiple / startMultiple, 1 / years) - 1
      const adjustedCagr = cagr * taxMultiplier
      annualizedReturnPct = adjustedCagr * 100
      if (years > 0 && 1 + adjustedCagr > 0) {
        multipleFromStart = Math.pow(1 + adjustedCagr, years)
      } else {
        multipleFromStart = endMultiple / startMultiple
      }
    }

    const rebasedPoints = sortedPoints.map((point) => {
      const pointMultiple = Number(point.multiple)
      let normalizedMultiple = pointMultiple
      if (Number.isFinite(pointMultiple) && Number.isFinite(startMultiple) && startMultiple > 0) {
        normalizedMultiple = pointMultiple / startMultiple
      }
      if (!Number.isFinite(normalizedMultiple) || normalizedMultiple <= 0) {
        normalizedMultiple = 1
      }
      const yearsElapsed = point.year - sortedPoints[0].year
      let recalculatedValue = 0
      if (yearsElapsed > 0) {
        const growthRate = Math.pow(normalizedMultiple, 1 / yearsElapsed) - 1
        if (Number.isFinite(growthRate)) {
          const adjustedGrowth = appliesTax ? growthRate * taxMultiplier : growthRate
          recalculatedValue = adjustedGrowth * 100
        }
      }
      return {
        ...point,
        multiple: normalizedMultiple,
        value: recalculatedValue
      }
    })

    return {
      ...series,
      points: rebasedPoints,
      annualized_return_pct: annualizedReturnPct,
      multiple_from_start: multipleFromStart
    }
  }).filter(Boolean)
})

function getPointPrice(point) {
  if (!point) return null
  const raw = Number(point.raw_value ?? point.rawValue)
  if (Number.isFinite(raw)) return raw
  const value = Number(point.value)
  return Number.isFinite(value) ? value : null
}

const chartSeries = computed(() => {
  if (!filteredSeries.value.length) return []
  return filteredSeries.value.filter((series) => !hiddenSeries.value.has(series.id))
})

const sortedLegend = computed(() => {
  if (!filteredSeries.value?.length) return []
  return [...filteredSeries.value].sort((a, b) => {
    const aVal = typeof a.annualized_return_pct === 'number' ? a.annualized_return_pct : -Infinity
    const bVal = typeof b.annualized_return_pct === 'number' ? b.annualized_return_pct : -Infinity
    return bVal - aVal
  })
})

const tableYears = computed(() => {
  const yearSet = new Set()
  filteredSeries.value.forEach((series) => {
    series.points?.forEach((point) => {
      if (typeof point.year === 'number') {
        yearSet.add(point.year)
      }
    })
  })
  return Array.from(yearSet).sort((a, b) => a - b)
})

const colorMap = computed(() => {
  if (!analysis.value?.series) return {}
  const map = {}
  analysis.value.series.forEach((series, index) => {
    const labelLower = (series.label || '').toLowerCase()
    const isBitcoin =
      labelLower.includes('비트코인') ||
      labelLower.includes('bitcoin') ||
      labelLower.includes('btc')
    map[series.id] = isBitcoin ? '#FFD700' : lineColors[index % lineColors.length]
  })
  return map
})

const fxRate = computed(() => analysis.value?.fx_rate || 1300)
const analysisLogs = computed(() => (analysis.value?.logs?.length ? analysis.value.logs : progressLogs.value))
const displayLogs = computed(() => progressLogs.value)
const priceTableData = computed(() => yearlyPriceMap.value)

const dataSourcesText = computed(() => {
const sourceMap = {
  'Yahoo Finance': { url: 'https://finance.yahoo.com', label: 'Yahoo Finance' },
  'Stooq': { url: 'https://stooq.com', label: 'Stooq' },
  'pykrx': { url: 'https://github.com/sharebook-kr/pykrx', label: 'pykrx' },
  'Upbit': { url: 'https://upbit.com', label: 'Upbit' },
  'ECOS': { url: 'https://ecos.bok.or.kr', label: 'ECOS' },
  'FRED': { url: 'https://fred.stlouisfed.org', label: 'FRED' },
  'KB부동산': { url: 'https://kbland.kr/', label: 'KB부동산' },
  'KB부동산 (정적)': { url: 'https://kbland.kr/', label: 'KB부동산' },
  'KB부동산 (Agent)': { url: 'https://kbland.kr/', label: 'KB부동산' }
}

  const addSource = (value) => {
    if (!value) return
    const normalized = String(value).trim()
    if (normalized) {
      sources.add(normalized)
    }
  }

  const addEntrySources = (entry) => {
    if (!entry || typeof entry !== 'object') return
    addSource(entry.source || entry.data_source)
    const altMap = entry.alt_sources || entry.altSources
    if (altMap && typeof altMap === 'object') {
      Object.values(altMap).forEach(addSource)
    }
  }

  const sources = new Set()

  if (Array.isArray(analysis.value?.yearly_prices) && analysis.value.yearly_prices.length) {
    analysis.value.yearly_prices.forEach(addEntrySources)
  } else if (Array.isArray(analysis.value?.chart_data_table) && analysis.value.chart_data_table.length) {
    analysis.value.chart_data_table.forEach(addEntrySources)
  }

  Object.values(yearlyPriceMap.value || {}).forEach(addEntrySources)

  if (!sources.size) {
    return '데이터 출처 정보 없음'
  }

  const links = Array.from(sources).map((source) => {
    const info = sourceMap[source]
    if (!info) return `<span>${source}</span>`
    return `<a href="${info.url}" target="_blank" rel="noopener noreferrer" class="text-slate-700 underline decoration-dotted underline-offset-2 hover:text-slate-900">${info.label}</a>`
  })

  return links.join(' / ')
})

function normalizeAssetToken(label) {
  return (label || '').toString().trim().toLowerCase()
}

function hasCustomAsset(label, ticker, list = customAssets.value) {
  const targetLabel = normalizeAssetToken(label)
  const targetTicker = normalizeAssetToken(ticker)
  return list.some((asset) => {
    const labelMatch = targetLabel && normalizeAssetToken(asset.label) === targetLabel
    const tickerMatch = targetTicker && normalizeAssetToken(asset.ticker) === targetTicker
    return labelMatch || tickerMatch
  })
}

function buildDisplayLabel(label, ticker) {
  if (!label) return ''
  if (ticker) {
    const lowerTicker = ticker.toLowerCase()
    const lowerLabel = label.toLowerCase()
    if (lowerTicker !== lowerLabel && !lowerLabel.includes(lowerTicker)) {
      return `${label} (${ticker})`
    }
  }
  return label
}

async function appendResolvedAsset(rawName, { silent = false, targetList = null } = {}) {
  console.log('[DEBUG] appendResolvedAsset called with:', rawName, 'silent:', silent)
  const trimmed = (rawName || '').trim()
  if (!trimmed) return false
  const listTarget = Array.isArray(targetList) ? targetList : customAssets.value
  if (hasCustomAsset(trimmed, null, listTarget)) {
    console.log('[DEBUG] Asset already exists:', trimmed)
    if (!silent) customAssetError.value = `'${trimmed}'은(는) 이미 추가되었습니다.`
    return false
  }

  let resolved = null
  try {
    console.log('[DEBUG] Calling resolveCustomAsset for:', trimmed)
    resolved = await resolveCustomAsset(trimmed)
    console.log('[DEBUG] resolveCustomAsset response:', resolved)
  } catch (error) {
    console.log('[DEBUG] resolveCustomAsset error:', error.message, 'silent:', silent)
    if (!silent) {
      customAssetError.value = error.message || '종목 정보를 가져오지 못했습니다.'
      setTimeout(() => {
        if (customAssetError.value === (error.message || '종목 정보를 가져오지 못했습니다.')) {
          customAssetError.value = ''
        }
      }, 5000)
      throw error
    }
    // Silent mode: continue with resolved = null
  }

  const baseLabel = resolved?.label?.trim() || trimmed
  const ticker = resolved?.ticker?.trim() || resolved?.id?.trim()
  console.log('[DEBUG] baseLabel:', baseLabel, 'ticker:', ticker)
  if (hasCustomAsset(baseLabel, ticker, listTarget)) {
    console.log('[DEBUG] Asset already exists (after resolve):', baseLabel, ticker)
    return false
  }
  const display = buildDisplayLabel(baseLabel, ticker)
  const entry = { label: baseLabel, display, ticker }
  console.log('[DEBUG] Created entry:', entry)
  if (targetList) {
    targetList.push(entry)
    console.log('[DEBUG] Pushed to targetList, new length:', targetList.length)
  } else {
    customAssets.value = [...customAssets.value, entry]
    console.log('[DEBUG] Updated customAssets.value, new length:', customAssets.value.length)
  }
  if (!silent) customAssetError.value = ''
  return true
}

async function loadResolvedAssets(resolvedAssets = []) {
  console.log('[DEBUG] loadResolvedAssets called with:', resolvedAssets)
  const requestId = ++customAssetLoadId
  customAssetResolving.value = true
  customAssetError.value = ''
  customAssets.value = []

  try {
    const assets = resolvedAssets.map(asset => {
      const baseLabel = asset.label || asset.id || ''
      const ticker = asset.ticker || asset.id || ''
      return {
        label: baseLabel,
        ticker: ticker,
        display: buildDisplayLabel(baseLabel, ticker)
      }
    }).filter(asset => asset.label)

    if (requestId === customAssetLoadId) {
      console.log('[DEBUG] Setting customAssets.value to resolved assets:', assets)
      customAssets.value = assets
    }
  } finally {
    if (requestId === customAssetLoadId) {
      customAssetResolving.value = false
    }
  }
}

async function loadCustomAssetsFromList(assetNames = []) {
  console.log('[DEBUG] loadCustomAssetsFromList called with:', assetNames)
  const requestId = ++customAssetLoadId
  customAssetResolving.value = true
  customAssetError.value = ''
  customAssets.value = []
  const pendingAssets = []
  try {
    for (const name of assetNames) {
      console.log('[DEBUG] Processing asset:', name)
      if (requestId !== customAssetLoadId) {
        console.log('[DEBUG] Request cancelled (requestId mismatch)')
        return
      }
      try {
        await appendResolvedAsset(name, { silent: true, targetList: pendingAssets })
        console.log('[DEBUG] Asset resolved successfully:', name, 'pendingAssets:', pendingAssets.length)
        if (requestId !== customAssetLoadId) {
          return
        }
      } catch (error) {
        console.log('[DEBUG] Error resolving asset:', name, error)
        if (requestId !== customAssetLoadId) {
          return
        }
        pendingAssets.push({ label: name, display: name })
      }
    }
    if (requestId === customAssetLoadId) {
      console.log('[DEBUG] Setting customAssets.value to pendingAssets:', pendingAssets)
      customAssets.value = pendingAssets
    }
  } finally {
    if (requestId === customAssetLoadId) {
      customAssetResolving.value = false
    }
  }
}

async function applyQuickCompare(key, options = {}) {
  console.log('[DEBUG] applyQuickCompare called with key:', key, 'options:', options)
  errorMessage.value = ''
  const { autoRun = true } = options
  const group = quickCompareGroups.value.find((item) => item.key === key)
  console.log('[DEBUG] Found group:', group)

  if (!group) {
    console.error('Quick compare group not found for key:', key)
    errorMessage.value = '선택한 그룹 정보를 찾을 수 없습니다.'
    return
  }

  selectedQuickCompareGroup.value = key
  selectedContextKey.value = resolveContextKeyForGroup(group)
  quickCompareLoadingKey.value = key

  console.log('[DEBUG] About to load assets:', group.assets, 'resolved_assets:', group.resolved_assets)
  try {
    // Use resolved_assets if available for faster loading
    if (group.resolved_assets && group.resolved_assets.length > 0) {
      console.log('[DEBUG] Using pre-resolved assets')
      await loadResolvedAssets(group.resolved_assets)
    } else {
      console.log('[DEBUG] Resolving assets dynamically')
      await loadCustomAssetsFromList(group.assets || [])
    }
    console.log('[DEBUG] Assets loaded, customAssets.value:', customAssets.value)

    if (autoRun) {
      // Ensure loading state is clear before starting new request if needed
      // But respect existing loading state if it's just a queue
      prompt.value = buildPromptFromInputs()
      requestAgentAnalysis()
    }
  } catch (err) {
    console.error('Error in applyQuickCompare:', err)
    errorMessage.value = '빠른 비교를 실행하는 중 오류가 발생했습니다.'
  } finally {
    if (quickCompareLoadingKey.value === key) {
      quickCompareLoadingKey.value = ''
    }
  }
}

function mapQuickCompareGroups(entries = []) {
  return entries
    .map((item, index) => {
      const rawAssets = Array.isArray(item?.assets)
        ? item.assets
        : Array.isArray(item?.asset_list)
          ? item.asset_list
          : []
      const assets = rawAssets
        .map((asset) => (typeof asset === 'string' ? asset.trim() : ''))
        .filter(Boolean)
      if (!assets.length) return null
      const key = (item?.key || '').trim() || `group-${item?.id ?? index}`
      const label = (item?.label || '').trim() || `그룹 ${index + 1}`
      const contextKey =
        (item?.context_key || item?.contextKey || QUICK_COMPARE_CONTEXT_MAP[key] || '').trim()

      // Include resolved_assets if available
      const resolvedAssets = Array.isArray(item?.resolved_assets)
        ? item.resolved_assets
        : []

      return {
        id: item?.id ?? index,
        key,
        label,
        assets,
        resolved_assets: resolvedAssets,
        contextKey,
        sortOrder: Number.isFinite(item?.sort_order)
          ? Number(item.sort_order)
          : Number.isFinite(item?.sortOrder)
            ? Number(item.sortOrder)
            : index,
        isActive: item?.is_active !== false
      }
    })
    .filter(Boolean)
    .sort((a, b) => {
      if (a.sortOrder !== b.sortOrder) return a.sortOrder - b.sortOrder
      return (a.id ?? 0) - (b.id ?? 0)
    })
}

function applyQuickCompareGroupFallback() {
  quickCompareGroups.value = mapQuickCompareGroups(defaultFinanceQuickCompareGroups)
}

function resolveContextKeyForGroup(group) {
  if (!group) return 'safe_assets'
  const explicit = (group.contextKey || group.context_key || '').trim()
  if (explicit) return explicit
  return QUICK_COMPARE_CONTEXT_MAP[group.key] || 'safe_assets'
}

async function ensureQuickCompareSelection({ reapply = false } = {}) {
  if (!quickCompareGroups.value.length) {
    selectedQuickCompareGroup.value = ''
    selectedContextKey.value = 'safe_assets'
    return
  }

  const hasCurrent =
    !!selectedQuickCompareGroup.value &&
    quickCompareGroups.value.some((group) => group.key === selectedQuickCompareGroup.value)
  if (hasCurrent && !reapply) {
    return
  }

  const preferredGroup =
    quickCompareGroups.value.find((group) => group.key === 'frequent') ||
    quickCompareGroups.value.find((group) => group.key === 'dividend_favorites') ||
    quickCompareGroups.value[0]

  if (!preferredGroup) {
    selectedQuickCompareGroup.value = ''
    selectedContextKey.value = 'safe_assets'
    return
  }

  const shouldApply = reapply || !quickCompareInitialized
  if (shouldApply) {
    quickCompareInitialized = true
    await applyQuickCompare(preferredGroup.key, { autoRun: false })
  } else {
    selectedQuickCompareGroup.value = preferredGroup.key
    selectedContextKey.value = resolveContextKeyForGroup(preferredGroup)
  }
}

async function loadQuickCompareGroups() {
  quickCompareGroupsLoading.value = true
  const previousKey = selectedQuickCompareGroup.value
  try {
    const groups = await fetchFinanceQuickCompareGroups({})
    const mapped = mapQuickCompareGroups(Array.isArray(groups) ? groups : [])
    if (mapped.length) {
      quickCompareGroups.value = mapped
    } else {
      applyQuickCompareGroupFallback()
    }
  } catch (error) {
    console.warn('Failed to load quick compare groups', error)
    applyQuickCompareGroupFallback()
  } finally {
    quickCompareGroupsLoading.value = false
  }

  const stillExists =
    !!previousKey && quickCompareGroups.value.some((group) => group.key === previousKey)
  await ensureQuickCompareSelection({ reapply: !stillExists })
}

function clearAllCustomAssets() {
  customAssetLoadId += 1
  customAssetResolving.value = false
  customAssets.value = []
  customAssetError.value = ''
  selectedQuickCompareGroup.value = ''
  selectedContextKey.value = 'safe_assets'
  quickCompareLoadingKey.value = ''
}

async function handleAssetEnter(event) {
  if (event.isComposing) return
  await addAsset()
}

async function addAsset() {
  const raw = (newAssetInput.value || '').trim()
  if (!raw || customAssetResolving.value || loading.value) return

  customAssetResolving.value = true
  customAssetError.value = ''
  try {
    const added = await appendResolvedAsset(raw)
    if (added) {
      newAssetInput.value = ''
      selectedQuickCompareGroup.value = ''
      selectedContextKey.value = 'safe_assets'
    }
  } finally {
    customAssetResolving.value = false
  }
}

function removeAsset(index) {
  customAssets.value = customAssets.value.filter((_, i) => i !== index)
  customAssetError.value = ''
  selectedQuickCompareGroup.value = ''
  selectedContextKey.value = 'safe_assets'
}

watch(
  () => progressLogs.value.length,
  () => {
    const lastLog = progressLogs.value[progressLogs.value.length - 1]
    if (lastLog) {
      handleProgressLog(lastLog)
    }
  }
)

function formatMultiple(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '0.0'
  const absValue = Math.abs(value)
  let decimals = 1
  if (absValue < 1) decimals = 2
  if (absValue < 0.1) decimals = 3
  if (absValue < 0.01) decimals = 4
  return value.toFixed(decimals)
}

function formatFxRate(rate) {
  if (!Number.isFinite(rate)) return '1,300'
  return Math.round(rate).toLocaleString()
}

function getLegendLabel(series) {
  if (!series) return ''
  const customAsset = findMatchingCustomAsset(series)
  if (customAsset) {
    const friendly = stripTickerSuffix(
      customAsset.label || customAsset.display || '',
      customAsset.ticker || series.ticker || series.id
    )
    if (friendly) return friendly
  }
  return stripTickerSuffix(series.label || '', series.ticker || series.id)
}

function findMatchingCustomAsset(series) {
  if (!series) return null
  const tokens = new Set()
  const labelToken = normalizeAssetToken(series.label)
  const aliasToken = normalizeAssetToken(normalizeLabelAlias(series.label || ''))
  const tickerToken = normalizeAssetToken(series.ticker || series.id)
  ;[labelToken, aliasToken, tickerToken].forEach((token) => {
    if (token) tokens.add(token)
  })

  if (!tokens.size) return null

  return (
    customAssets.value.find((asset) => {
      const assetTokens = [
        normalizeAssetToken(asset.label),
        normalizeAssetToken(normalizeLabelAlias(asset.label || '')),
        normalizeAssetToken(asset.ticker)
      ].filter(Boolean)
      return assetTokens.some((token) => tokens.has(token))
    }) || null
  )
}

function stripTickerSuffix(label, tickerCandidate) {
  const text = (label || '').trim()
  if (!text) return ''

  const ticker = (tickerCandidate || '').trim()
  if (ticker) {
    const escapedTicker = ticker.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const tickerPattern = new RegExp(`\\s*\\(${escapedTicker}\\)\\s*$`, 'i')
    if (tickerPattern.test(text)) {
      const cleaned = text.replace(tickerPattern, '').trim()
      if (cleaned) return cleaned
    }
  }

  const trailingParenMatch = text.match(/\(([^)]*)\)\s*$/)
  if (trailingParenMatch) {
    const candidate = trailingParenMatch[1].trim()
    if (/^[A-Z0-9.\-]+$/.test(candidate) || /^\d{4,6}$/.test(candidate)) {
      const cleaned = text.replace(/\s*\([^)]*\)\s*$/, '').trim()
      if (cleaned) return cleaned
    }
  }

  return text
}

const priceFormatter = new Intl.NumberFormat('en-US', {
  notation: 'compact',
  maximumFractionDigits: 2
})

function getAssetUrl(series) {
  if (!series) return null
  const ticker = series.ticker || series.id
  if (!ticker) return null
  
  const symbol = ticker.toUpperCase()
  const entry = findPriceEntry(series)
  const source = String(entry?.source || series.source || '')
  const category = entry?.category || series.category || ''
  const labelLower = (series.label || '').toLowerCase()

  if (source.includes('KB부동산') || labelLower.includes('아파트')) {
    return 'https://kbland.kr/'
  }
  
  if (source === 'pykrx' || symbol.endsWith('.KS') || symbol.endsWith('.KQ') || category === '국내 주식') {
    const code = symbol.split('.')[0]
    return `https://finance.naver.com/item/main.naver?code=${code}`
  }
  
  if (source === 'Upbit') {
     return `https://upbit.com/exchange?code=CRIX.UPBIT.${symbol}`
  }
  
  if (source === 'FRED') {
    return `https://fred.stlouisfed.org/series/${symbol}`
  }
  
  return `https://finance.yahoo.com/quote/${symbol}`
}

function formatPriceCell(series, year) {
  const priceEntry = findPriceEntry(series)
  if (!priceEntry) {
    return { text: priceTableLoading.value ? '...' : '-', url: null }
  }

  if (priceEntry.status === 'failed') {
    return { text: '조회되지 않음', url: null }
  }

  const { rawValue, unit } = resolvePriceByMode(priceEntry, year)
  if (!Number.isFinite(rawValue)) {
    return { text: '-', url: null }
  }

  const displayValue = convertValue(rawValue, unit)
  const symbol = getUnitSymbol(priceDisplayMode.value)
  const formatted = priceFormatter.format(displayValue)
  const valueText = symbol ? `${symbol}${formatted}` : formatted
  const isLatestYear = year === currentYear || year === analysis.value?.end_year
  const text = isLatestYear ? `${valueText} (오늘)` : valueText
  const url = generateNaverFinanceUrl(series, year)
  return { text, url }
}

function findPriceEntry(series) {
  if (!series) return null
  const candidates = new Set()
  if (series.id) {
    candidates.add(series.id)
    candidates.add(series.id.toLowerCase())
  }
  if (series.label) {
    candidates.add(series.label)
    const normalized = normalizeLabelAlias(series.label)
    if (normalized) {
      candidates.add(normalized)
    }
  }
  for (const key of candidates) {
    if (key && yearlyPriceMap.value[key]) {
      return yearlyPriceMap.value[key]
    }
  }
  return null
}

function normalizeLabelAlias(label) {
  return label.replace(/\([^)]*\)/g, '').trim().toLowerCase()
}

function resolvePriceByMode(priceEntry, year) {
  const mode = priceDisplayMode.value === 'krw' ? 'krw' : 'usd'
  const altMap = priceEntry.altPrices?.[mode]
  if (altMap) {
    const altValue = Number(altMap[year])
    if (Number.isFinite(altValue)) {
      return { rawValue: altValue, unit: mode }
    }
  }
  const baseValue = Number(priceEntry.prices?.[year])
  if (Number.isFinite(baseValue)) {
    return { rawValue: baseValue, unit: priceEntry.unit || '' }
  }
  return { rawValue: null, unit: priceEntry.unit || '' }
}

function extractStockCode(series) {
  if (!series?.label) return null
  const match = series.label.match(/\((\d{6})\)/)
  return match ? match[1] : null
}

function generateNaverFinanceUrl(series, year) {
  if (selectedContextKey.value !== 'kr_equity') return null
  const stockCode = extractStockCode(series)
  if (!stockCode) return null
  return `https://finance.naver.com/item/sise_day.naver?code=${stockCode}`
}

function convertValue(value, unit, targetMode = priceDisplayMode.value) {
  const sourceUnit = (unit || '').toLowerCase()
  const normalizedTarget = targetMode === 'krw' ? 'krw' : 'usd'
  if (!Number.isFinite(value)) return value
  if (normalizedTarget === 'krw' && sourceUnit !== 'krw') {
    return value * (fxRate.value || 1300)
  }
  if (normalizedTarget === 'usd' && sourceUnit === 'krw') {
    return value / (fxRate.value || 1300)
  }
  return value
}

function isKoreanEquitySeries(series) {
  if (!series) return false
  const entry = findPriceEntry(series)
  const ticker = (series.ticker || series.id || '').toUpperCase()
  const source = (entry?.source || entry?.data_source || series.source || '').toString().toLowerCase()
  if (source.includes('pykrx')) return true
  if (/\.K[QS]$/.test(ticker)) return true

  const categoryCandidates = [
    series.category,
    entry?.category,
    getSeriesMetaValue(series, 'category'),
    getSeriesMetaValue(series, 'asset_class'),
    getSeriesMetaValue(series, 'asset_category')
  ]

  if (categoryCandidates.some((value) => {
    if (!value) return false
    const lower = value.toString().toLowerCase()
    return lower.includes('국내') || lower.includes('korea') || lower.includes('kospi') || lower.includes('kosdaq')
  })) {
    return true
  }

  const regionCandidates = [
    getSeriesMetaValue(series, 'region'),
    getSeriesMetaValue(series, 'country'),
    entry?.region
  ]

  return regionCandidates.some((value) => {
    if (!value) return false
    return value.toString().toLowerCase().includes('korea')
  })
}

function getSeriesDisplayCurrency(series) {
  return isKoreanEquitySeries(series) ? 'krw' : 'usd'
}

function getCurrencySymbolForMode(mode) {
  return mode === 'krw' ? '₩' : '$'
}

function resolvePriceValueForCurrency(series, point, year, targetCurrency) {
  const normalizedTarget = targetCurrency === 'krw' ? 'krw' : 'usd'
  const entry = findPriceEntry(series)
  if (entry) {
    const altMap = entry.altPrices?.[normalizedTarget]
    if (altMap && Number.isFinite(Number(altMap[year]))) {
      return { value: Number(altMap[year]), unit: normalizedTarget }
    }
    const baseValue = Number(entry.prices?.[year])
    if (Number.isFinite(baseValue)) {
      const converted = convertValue(baseValue, entry.unit || series.unit || '', normalizedTarget)
      return { value: converted, unit: normalizedTarget }
    }
  }

  if (point) {
    const rawValue = Number(point.raw_value ?? point.rawValue)
    if (Number.isFinite(rawValue)) {
      const converted = convertValue(rawValue, series.unit || '', normalizedTarget)
      return { value: converted, unit: normalizedTarget }
    }
    const fallback = Number(point.multiple ?? point.value)
    if (Number.isFinite(fallback)) {
      return { value: fallback, unit: null }
    }
  }

  return { value: null, unit: normalizedTarget }
}

function getUnitSymbol(unit) {
  if (!unit) return ''
  const lowered = unit.toLowerCase()
  if (lowered === 'usd' || lowered === '$') return '$'
  if (lowered === 'krw' || lowered === '₩') return '₩'
  return ''
}

function formatKoreanWonVerbose(amount) {
  if (!Number.isFinite(amount) || amount <= 0) return '0원'
  let remainder = Math.floor(amount)
  const units = [
    { value: 1000000000000, label: '조' },
    { value: 100000000, label: '억' },
    { value: 10000, label: '만' }
  ]
  const parts = []
  units.forEach(({ value, label }) => {
    if (remainder >= value) {
      const unitValue = Math.floor(remainder / value)
      parts.push(`${unitValue.toLocaleString()}${label}`)
      remainder %= value
    }
  })
  if (remainder > 0 || !parts.length) {
    parts.push(remainder.toLocaleString())
  }
  return `${parts.join(' ')} 원`
}

const bitcoinPerformanceStats = computed(() => {
  if (!analysis.value || !filteredSeries.value.length) return null
  const bitcoinSeries = filteredSeries.value.find((series) => isBitcoinLabel(series.label))
  if (!bitcoinSeries || !bitcoinSeries.points?.length) return null

  const points = bitcoinSeries.points
  const preferredStartYear = chartStartYear.value
  const startPoint = preferredStartYear
    ? points.find((point) => point.year === preferredStartYear) || points[0]
    : points[0]
  const latestPoint = points[points.length - 1]
  if (!startPoint || !latestPoint) return null

  const displayStartYear = preferredStartYear || startPoint.year
  const entry = findPriceEntry(bitcoinSeries)
  let priceText = ''
  if (entry) {
    const { rawValue, unit } = resolvePriceByMode(entry, latestPoint.year)
    if (Number.isFinite(rawValue)) {
      const converted = convertValue(rawValue, unit)
      const symbol = priceDisplayMode.value === 'krw' ? '₩' : '$'
      priceText = `${symbol}${priceFormatter.format(converted)}`
    }
  }

  const baseMultiple = Number(startPoint.multiple)
  const endMultiple = Number(latestPoint.multiple)
  let multipleFromStart = bitcoinSeries.multiple_from_start
  if (Number.isFinite(baseMultiple) && baseMultiple > 0 && Number.isFinite(endMultiple)) {
    multipleFromStart = endMultiple / baseMultiple
  }

  let annualizedReturnPct = bitcoinSeries.annualized_return_pct
  const spanYears = Number.isFinite(displayStartYear)
    ? Math.max(1, latestPoint.year - displayStartYear)
    : null
  if (spanYears && Number.isFinite(multipleFromStart) && multipleFromStart > 0) {
    annualizedReturnPct = (Math.pow(multipleFromStart, 1 / spanYears) - 1) * 100
  }

  return {
    startYear: displayStartYear,
    endYear: latestPoint.year,
    annualizedReturnPct,
    multipleFromStart,
    priceText
  }
})

const bitcoinPerformanceText = computed(() => {
  const stats = bitcoinPerformanceStats.value
  if (!stats) return ''
  const segments = []
  if (Number.isFinite(stats.annualizedReturnPct)) {
    segments.push(`연평균 ${formatPercent(stats.annualizedReturnPct)}`)
  }
  if (Number.isFinite(stats.multipleFromStart)) {
    segments.push(`${formatMultiple(stats.multipleFromStart)}배`)
  }
  if (stats.priceText) {
    segments.push(`현재 ${stats.priceText}`)
  }
  if (!segments.length) return ''
  return `비트코인 (${stats.startYear}년 → ${stats.endYear}년) · ${segments.join(' · ')}`
})

const bitcoinHeroSummary = computed(() => {
  const stats = bitcoinPerformanceStats.value
  if (!stats || !analysis.value) return null
  const startYear = stats.startYear
  const endYear = stats.endYear || analysis.value.end_year
  if (!startYear || !endYear) return null

  const multiple = Number(stats.multipleFromStart)
  const cagr = Number(stats.annualizedReturnPct ?? stats.annualized_return_pct)
  const investmentWon = Number(investmentAmount.value) * 10000
  const finalWon = Number.isFinite(multiple) ? investmentWon * multiple : null

  return {
    startYear,
    endYear,
    duration: Math.max(1, endYear - startYear),
    multipleText: Number.isFinite(multiple) ? `${formatMultiple(multiple)}배` : '',
    cagrText: Number.isFinite(cagr) ? formatPercent(cagr) : '',
    investmentText: `${formattedInvestmentAmountNumber.value}만원`,
    finalText: Number.isFinite(finalWon) ? formatKoreanWonVerbose(finalWon) : ''
  }
})

function getReturnForYear(series, year) {
  if (!series?.points) return '-'
  const point = series.points.find((p) => p.year === year)
  if (!point) return '-'

  if (analysisResultType.value === 'price') {
    const displayCurrency = getSeriesDisplayCurrency(series)
    const { value } = resolvePriceValueForCurrency(series, point, year, displayCurrency)
    if (!Number.isFinite(value)) return '-'
    const symbol = getCurrencySymbolForMode(displayCurrency)
    return `${symbol}${priceFormatter.format(value)}`
  }

  const value = Number(point.value)
  if (!Number.isFinite(value)) return '-'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(1)}%`
}

function getReturnCellClass(series, year) {
  if (analysisResultType.value === 'price') return 'text-slate-600'
  const point = series.points?.find((p) => p.year === year)
  const value = Number(point?.value)
  if (!Number.isFinite(value)) return 'text-slate-600'
  if (value <= 0) return 'text-rose-600 font-semibold'
  if (value >= 15) return 'text-emerald-600 font-semibold'
  return 'text-slate-600'
}

function toggleSeries(id) {
  const next = new Set(hiddenSeries.value)
  if (next.has(id)) {
    next.delete(id)
  } else {
    next.add(id)
  }
  hiddenSeries.value = next
}

function isBitcoinLegend(series) {
  return isBitcoinLabel(series?.label)
}

function isBitcoinLabel(label) {
  if (!label) return false
  const lower = label.toLowerCase()
  return lower.includes('비트코인') || lower.includes('bitcoin') || lower.includes('btc')
}

function shouldApplyTax(series) {
  if (!series) return false
  if (isBitcoinLabel(series.label)) return false
  const category = (series.category || '').toLowerCase()
  const unit = (series.unit || '').toLowerCase()
  const label = (series.label || '').toLowerCase()
  const id = (series.id || '').toLowerCase()
  const isUsEquity =
    category.includes('미국') ||
    label.includes('미국') ||
    id.endsWith('.us')
  return isUsEquity && unit === 'usd'
}

function startLoadingStageTracking() {
  stopLoadingStageTracking()
  priceDataProgressBumps = 0
  if (!LOADING_STAGES.length) return
  loadingStageIndex.value = 0
  loadingProgress.value = LOADING_STAGES[0].minProgress

  LOADING_STAGES.slice(1).forEach((stage) => {
    if (!Number.isFinite(stage.fallbackDelayMs)) return
    const timer = setTimeout(() => {
      setLoadingStage(stage.key)
    }, stage.fallbackDelayMs)
    stageFallbackTimers.set(stage.key, timer)
  })

  loadingProgressInterval = setInterval(() => {
    const stage = currentLoadingStage.value
    if (!stage) return
    if (loadingProgress.value >= stage.maxProgress) return
    const increment = stage.autoIncrement ?? 1
    loadingProgress.value = Math.min(stage.maxProgress, loadingProgress.value + increment)
  }, 1000)
}

function stopLoadingStageTracking() {
  stageFallbackTimers.forEach((timer) => clearTimeout(timer))
  stageFallbackTimers.clear()
  if (loadingProgressInterval) {
    clearInterval(loadingProgressInterval)
    loadingProgressInterval = null
  }
}

function setLoadingStage(stageKey, { immediate = false } = {}) {
  const targetIndex = LOADING_STAGES.findIndex((stage) => stage.key === stageKey)
  if (targetIndex === -1) return
  if (targetIndex < loadingStageIndex.value) return
  loadingStageIndex.value = targetIndex
  const stage = LOADING_STAGES[targetIndex]
  const targetProgress = immediate ? stage.maxProgress : stage.minProgress
  if (loadingProgress.value < targetProgress) {
    loadingProgress.value = targetProgress
  }
  if (stageFallbackTimers.has(stageKey)) {
    clearTimeout(stageFallbackTimers.get(stageKey))
    stageFallbackTimers.delete(stageKey)
  }
}

function bumpPriceStageProgress() {
  const stage = LOADING_STAGES.find((entry) => entry.key === DATA_STAGE_KEY)
  if (!stage) return
  priceDataProgressBumps += 1
  const range = Math.max(0, stage.maxProgress - stage.minProgress)
  const offset = Math.min(range, priceDataProgressBumps * 4)
  const nextValue = stage.minProgress + offset
  if (nextValue > loadingProgress.value) {
    loadingProgress.value = nextValue
  }
}

function isDataFetchCompletionLog(message) {
  const normalized = message.toLowerCase()
  if (message.includes('✓')) return true
  if (normalized.includes('cache hit') || normalized.includes('캐시됨')) return true
  if (normalized.includes('수집 완료') || normalized.includes('데이터 포인트')) return true
  return false
}

function handleProgressLog(message) {
  if (!message) return
  const normalized = message.toLowerCase()

  const matchedStage = LOADING_STAGES.find((stage) => {
    if (!Array.isArray(stage.matchers) || !stage.matchers.length) return false
    return stage.matchers.some((token) => token && normalized.includes(token.toLowerCase()))
  })

  if (matchedStage) {
    setLoadingStage(matchedStage.key)
  }

  if (normalized.includes('[데이터 수집]')) {
    setLoadingStage(DATA_STAGE_KEY)
    if (isDataFetchCompletionLog(message)) {
      bumpPriceStageProgress()
    }
  }

  if (normalized.includes('[수익률 계산]')) {
    setLoadingStage('calc')
  }

  if (normalized.includes('[분석 생성]')) {
    setLoadingStage('summary')
  }

  if (message.includes('✓ 분석 완료')) {
    completeLoadingStageTracking()
  } else if (normalized.includes('요청이 취소되었습니다')) {
    stopLoadingStageTracking()
  } else if (normalized.includes('오류')) {
    stopLoadingStageTracking()
  }
}

function completeLoadingStageTracking() {
  const summaryStage = LOADING_STAGES[LOADING_STAGES.length - 1]
  if (summaryStage) {
    setLoadingStage(summaryStage.key, { immediate: true })
  }
  loadingProgress.value = 100
  stopLoadingStageTracking()
}

function getLoadingMessage() {
  return currentLoadingStage.value?.description || '데이터를 가져오는 중입니다.'
}

function resetPrompt() {
  prompt.value = ''
  selectedContextKey.value = 'safe_assets'
  hiddenSeries.value = new Set()
  yearlyPriceMap.value = {}
  priceTableError.value = ''
  priceTableLoading.value = false
  priceRequestId += 1
  if (abortController) {
    abortController.abort()
    abortController = null
  }
  loading.value = false
}

function cancelRequest() {
  if (abortController) {
    abortController.abort()
    abortController = null
    loading.value = false
    stopLoadingStageTracking()
    appendProgressLogs('요청이 취소되었습니다.')
  }
  priceRequestId += 1
  yearlyPriceMap.value = {}
  priceTableError.value = ''
  priceTableLoading.value = false
}

function cacheKeyForDividends(value) {
  return value ? 'true' : 'false'
}

function clearDividendCache() {
  cancelDividendPrefetch()
  dividendResultCache['true'] = null
  dividendResultCache['false'] = null
  dividendDataReady['true'] = false
  dividendDataReady['false'] = false
  pendingDividendTarget.value = null
}

function cancelDividendPrefetch() {
  if (dividendPrefetchController) {
    dividendPrefetchController.abort()
    dividendPrefetchController = null
    dividendPrefetchTarget = null
  }
}

function applyAnalysisResult(result, { shouldCache = false, preserveHidden = false } = {}) {
  if (!result) return
  pendingDividendTarget.value = null
  const previousHidden = preserveHidden ? new Set(hiddenSeries.value) : null
  const nextAvailableIds = new Set((result?.series || []).map((series) => series.id))
  analysis.value = result
  analysisResultType.value = result.calculation_method || 'cagr'
  analysisSummary.value = result.analysis_summary || ''
  const resolvedInclude = Object.prototype.hasOwnProperty.call(result, 'include_dividends')
    ? !!result.include_dividends
    : includeDividends.value
  includeDividends.value = resolvedInclude
  dividendDataReady[cacheKeyForDividends(resolvedInclude)] = true
  displayStartYear.value = result.start_year
  sliderMinYear.value = result.start_year
  hiddenSeries.value = previousHidden
    ? new Set([...previousHidden].filter((id) => nextAvailableIds.has(id)))
    : new Set()

  if (result.chart_data_table) {
    processYearlyPrices(result.chart_data_table)
  } else if (result.yearly_prices) {
    processYearlyPrices(result.yearly_prices)
  } else {
    yearlyPriceMap.value = {}
    priceTableError.value = ''
    priceTableLoading.value = false
  }

  if (shouldCache) {
    const cacheKey = cacheKeyForDividends(resolvedInclude)
    dividendResultCache[cacheKey] = result
  }
}

function handleDividendToggle() {
  if (loading.value || !analysis.value) return
  const nextValue = !includeDividends.value
  const cacheKey = cacheKeyForDividends(nextValue)
  const cachedResult = dividendResultCache[cacheKey]
  if (!cachedResult) {
    pendingDividendTarget.value = nextValue
    prefetchDividendVariant(nextValue)
    return
  }

  pendingDividendTarget.value = null
  includeDividends.value = nextValue
  applyAnalysisResult(cachedResult, { preserveHidden: true })
  prefetchDividendVariant(!nextValue)
}

async function prefetchDividendVariant(targetInclude) {
  const requestContext = lastAnalysisRequest.value
  if (!requestContext) return
  const cacheKey = cacheKeyForDividends(targetInclude)
  if (dividendResultCache[cacheKey]) {
    dividendDataReady[cacheKey] = true
    return
  }

  if (dividendPrefetchController && dividendPrefetchTarget === targetInclude) {
    return
  }

  if (dividendPrefetchController) {
    dividendPrefetchController.abort()
  }

  dividendPrefetchController = new AbortController()
  dividendPrefetchTarget = targetInclude
  dividendDataReady[cacheKey] = false
  let shouldWarmOpposite = false

  try {
    const result = await fetchHistoricalReturns({
      ...requestContext,
      includeDividends: targetInclude,
      signal: dividendPrefetchController.signal
    })
    if (result?.ok) {
      dividendResultCache[cacheKey] = result
      dividendDataReady[cacheKey] = true
      if (pendingDividendTarget.value === targetInclude) {
        includeDividends.value = targetInclude
        applyAnalysisResult(result, { preserveHidden: true })
        pendingDividendTarget.value = null
        shouldWarmOpposite = true
      }
    }
  } catch (error) {
    if (error.name !== 'AbortError') {
      console.error('Dividend prefetch failed', error)
    }
    if (pendingDividendTarget.value === targetInclude) {
      pendingDividendTarget.value = null
    }
  } finally {
    dividendPrefetchController = null
    dividendPrefetchTarget = null
    if (shouldWarmOpposite) {
      prefetchDividendVariant(!targetInclude)
    }
  }
}

async function runAnalysis(options = {}) {
  const { preserveCache = false } = options
  if (abortController) {
    abortController.abort()
  }

  if (preserveCache) {
    cancelDividendPrefetch()
  } else {
    clearDividendCache()
  }

  analysis.value = null
  displayStartYear.value = null
  sliderMinYear.value = null
  hiddenSeries.value = new Set()
  priceDisplayMode.value = showWonMode.value ? 'krw' : 'usd'
  yearlyPriceMap.value = {}
  priceTableError.value = ''
  priceTableLoading.value = false
  priceRequestId += 1

  const requestContext = {
    prompt: prompt.value,
    contextKey: selectedContextKey.value,
    customAssets: customAssets.value.map((asset) => asset.ticker || asset.label)
  }
  lastAnalysisRequest.value = requestContext
  prefetchDividendVariant(!includeDividends.value)

  abortController = new AbortController()
  loading.value = true
  errorMessage.value = ''
  loadingProgress.value = 0
  showLogs.value = true
  startLoadingStageTracking()

  if (progressLogs.value.length > 0) {
    appendProgressLogs('', '='.repeat(50), '')
  }
  appendProgressLogs('분석 요청 중...')

  try {
    const payload = {
      ...requestContext,
      includeDividends: includeDividends.value,
      signal: abortController.signal,
      onLog: (message) => {
        appendProgressLogs(message)
      }
    }

    const result = await fetchHistoricalReturnsStream(payload)
    applyAnalysisResult(result, { shouldCache: true })
    prefetchDividendVariant(!includeDividends.value)
    completeLoadingStageTracking()

    appendProgressLogs('', '✓ 분석 완료')
  } catch (error) {
    stopLoadingStageTracking()
    if (error.name === 'AbortError') {
      errorMessage.value = '요청이 취소되었습니다.'
      appendProgressLogs('요청이 취소되었습니다.')
    } else {
      errorMessage.value = error.message || '분석 중 오류가 발생했습니다.'
      appendProgressLogs(`오류: ${error.message}`)
      cancelDividendPrefetch()
    }
  } finally {
    loading.value = false
    abortController = null
  }
}

function processYearlyPrices(pricesData) {
  const map = {}
  if (Array.isArray(pricesData)) {
    pricesData.forEach((entry) => {
      const priceMap = {}
      if (Array.isArray(entry.prices)) {
        entry.prices.forEach((pricePoint) => {
          const year = Number(pricePoint.year)
          const value = Number(pricePoint.value)
          if (Number.isFinite(year) && Number.isFinite(value)) {
            priceMap[year] = value
          }
        })
      }
      if (Array.isArray(entry.values)) {
        entry.values.forEach((point) => {
          const year = Number(point.year)
          const value = Number(point.value)
          if (Number.isFinite(year) && Number.isFinite(value)) {
            priceMap[year] = value
          }
        })
      }

      const altPrices = {}
      if (entry.alt_prices && typeof entry.alt_prices === 'object') {
        Object.entries(entry.alt_prices).forEach(([unitKey, priceList]) => {
          const normalizedUnit = String(unitKey || '').toLowerCase()
          if (!normalizedUnit) return
          const altMap = {}
          if (Array.isArray(priceList)) {
            priceList.forEach((pricePoint) => {
              const year = Number(pricePoint.year)
              const value = Number(pricePoint.value)
              if (Number.isFinite(year) && Number.isFinite(value)) {
                altMap[year] = value
              }
            })
          }
          if (Object.keys(altMap).length) {
            altPrices[normalizedUnit] = altMap
          }
        })
      }

      const record = {
        unit: (entry.unit || '').toLowerCase(),
        label: entry.label || '',
        category: entry.category || '',
        source: entry.source || '',
        prices: priceMap,
        altPrices,
        altSources: entry.alt_sources || {},
        status: entry.status || 'unknown',
        errorMessage: entry.error_message || null,
      }

      const aliases = new Set()
      ;[entry.id, entry.requested_id].forEach((alias) => {
        if (alias) aliases.add(alias)
      })
      if (Array.isArray(entry.aliases)) {
        entry.aliases.forEach((alias) => {
          if (alias) aliases.add(alias)
        })
      }

      aliases.forEach((alias) => {
        if (!alias) return
        map[alias] = record
        map[String(alias).toLowerCase()] = record
      })
    })
  }
  yearlyPriceMap.value = map
  priceTableLoading.value = false
}

</script>
