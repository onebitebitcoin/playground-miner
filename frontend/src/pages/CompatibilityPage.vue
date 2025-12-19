<template>
  <div class="space-y-6">
<section class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 space-y-6">
      <div class="flex flex-col gap-3">
        <div class="flex items-start justify-between gap-4">
          <div class="flex-1">
            <p class="text-sm font-semibold text-slate-500 uppercase tracking-wider">비트코인의 사주는?</p>
            <h2 class="text-xl font-bold text-slate-900 mt-1">금(金)이 주력인 디지털 금, 수·화가 극단을 이루는 에너지</h2>
          </div>
        </div>
      </div>
      <div class="grid gap-6 lg:grid-cols-2 items-center">
        <div class="space-y-4">
          <div class="rounded-2xl bg-slate-50 p-5 space-y-3 min-h-[220px]">
            <div v-if="selectedBitcoinHighlight" class="space-y-3">
              <div class="flex items-center gap-3">
                <span class="text-3xl">{{ selectedBitcoinHighlight.icon }}</span>
                <div>
                  <p class="text-lg font-bold text-slate-900">{{ selectedBitcoinHighlight.label }}</p>
                  <p class="text-sm text-slate-500">{{ selectedBitcoinHighlight.value }}</p>
                </div>
                <span class="ml-auto text-lg font-black text-slate-900">{{ selectedBitcoinHighlight.ratio }}%</span>
              </div>
              <div class="w-full bg-slate-200 rounded-full h-2">
                <div
                  class="h-2 rounded-full transition-all duration-300"
                  :class="selectedBitcoinHighlight.colorClass"
                  :style="{ width: `${selectedBitcoinHighlight.ratio}%` }"
                ></div>
              </div>
              <p class="text-sm text-slate-600 leading-relaxed">
                {{ selectedBitcoinHighlight.description }}
              </p>
            </div>
            <div v-else class="text-sm text-slate-500">표시할 앵커가 없습니다.</div>
          </div>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="trait in bitcoinHighlights"
              :key="trait.elementKey"
              type="button"
              class="px-3 py-1.5 rounded-full border text-xs font-semibold transition-all"
              :class="{
                'bg-slate-900 text-white border-slate-900 shadow-sm': trait.elementKey === selectedBitcoinHighlightKey,
                'bg-white text-slate-600 border-slate-200 hover:border-slate-400': trait.elementKey !== selectedBitcoinHighlightKey
              }"
              @click="handleBitcoinHighlightSelect(trait.elementKey)"
            >
              {{ trait.label }}
            </button>
          </div>
        </div>
        <div class="rounded-2xl bg-white p-4 flex items-center justify-center">
          <svg
            v-if="bitcoinRadarChart.markers.length"
            :viewBox="`0 0 ${bitcoinRadarChart.size} ${bitcoinRadarChart.size}`"
            :width="bitcoinRadarChart.size"
            :height="bitcoinRadarChart.size"
            class="max-w-full"
          >
            <circle
              :cx="bitcoinRadarChart.center"
              :cy="bitcoinRadarChart.center"
              :r="bitcoinRadarChart.maxRadius"
              class="fill-slate-50 stroke-slate-200"
            ></circle>
            <line
              v-for="(axis, index) in bitcoinRadarChart.axes"
              :key="`axis-${index}`"
              :x1="bitcoinRadarChart.center"
              :y1="bitcoinRadarChart.center"
              :x2="axis.x2"
              :y2="axis.y2"
              class="stroke-slate-200"
              stroke-width="1"
            ></line>
            <polygon
              :points="bitcoinRadarChart.polygonPoints"
              class="fill-indigo-400/20 stroke-indigo-500 radar-polygon"
              stroke-width="2"
            ></polygon>
            <circle
              v-for="marker in bitcoinRadarChart.markers"
              :key="marker.key"
              :cx="marker.x"
              :cy="marker.y"
              :r="marker.active ? 8 : 6"
              :class="marker.active ? 'fill-indigo-500' : 'fill-white stroke-indigo-400'"
              :stroke-width="marker.active ? 3 : 2"
              @click="handleBitcoinHighlightSelect(marker.key)"
              class="cursor-pointer transition-all duration-200 radar-point"
            ></circle>
            <text
              v-for="marker in bitcoinRadarChart.markers"
              :key="`percent-${marker.key}`"
              :x="marker.x"
              :y="marker.y - 14"
              class="text-[11px] fill-indigo-500 font-bold pointer-events-none"
              text-anchor="middle"
            >
              {{ marker.ratio }}%
            </text>
            <text
              v-for="axis in bitcoinRadarChart.axes"
              :key="`label-${axis.key}`"
              :x="axis.labelX"
              :y="axis.labelY"
              class="text-sm fill-slate-700 font-bold"
              text-anchor="middle"
              dominant-baseline="middle"
            >
              {{ axis.label }}
            </text>
          </svg>
          <p v-else class="text-sm text-slate-500">표시할 데이터가 없습니다.</p>
        </div>
      </div>
    </section>

    <section class="space-y-6">
      <div class="grid gap-6 lg:grid-cols-2">
        <div class="preset-card-container bg-white rounded-2xl shadow-sm p-4 sm:p-6 space-y-5">
          <div>
            <h3 class="text-base font-semibold text-slate-900">나의 사주 입력</h3>
            <div class="mt-3 space-y-3 text-xs">
              <div class="flex flex-wrap items-center gap-2">
                <span class="text-slate-500 font-semibold uppercase tracking-wide">빠른 설정</span>
                <span v-if="quickPresetLoading" class="text-slate-400">불러오는 중...</span>
                <span v-else-if="!quickPresetOptions.length" class="text-slate-400">등록된 빠른 설정이 없습니다.</span>
                <span v-else class="text-slate-500">사용자를 선택하여 직접 입력을 하거나 다른 사람을 선택하세요</span>
              </div>
              <div v-if="!quickPresetLoading && quickPresetOptions.length" class="relative">
                <div class="flex gap-3 overflow-x-auto pb-6 pt-3 -mx-1 px-1 -mt-3 scroll-container" style="overflow-y: visible; scroll-behavior: smooth;">
                <button
                  v-for="preset in quickPresetOptions"
                  :key="preset.id"
                  type="button"
                  class="preset-card yugioh-card flex-shrink-0"
                  :class="{ 'preset-card-selected': selectedPresetId === preset.id }"
                  @click="applyQuickPreset(preset)"
                >
                  <div class="card-inner">
                    <div class="card-border"></div>
                    <div class="card-content">
                      <div class="card-header">
                        <div class="card-name">{{ preset.label }}</div>
                      </div>
                      <div class="card-image">
                        <img
                          v-if="preset.imageUrl"
                          :src="preset.imageUrl"
                          :alt="preset.label"
                          class="card-image-actual"
                        />
                        <div v-else class="card-image-placeholder">👤</div>
                      </div>
                      <div class="card-info">
                        <div v-if="preset.birthdate" class="card-birthdate">{{ formatCardDate(preset.birthdate) }}</div>
                        <div v-if="selectedPresetId === preset.id" class="card-selected-badge">
                          <svg class="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
                            <path
                              fill-rule="evenodd"
                              d="M16.707 5.293a1 1 0 010 1.414l-7.01 7.01a1 1 0 01-1.414 0l-3.01-3.01A1 1 0 116.293 9.293L8.99 11.99l6.303-6.303a1 1 0 011.414 0z"
                              clip-rule="evenodd"
                            />
                          </svg>
                          <span>선택됨</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </button>
              </div>
              <!-- 스크롤 힌트 -->
              <div class="scroll-hint">
                <svg class="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                </svg>
              </div>
            </div>
            </div>
            <div class="grid gap-4 sm:grid-cols-2 mt-3">
              <label class="space-y-1 text-sm text-slate-600">
                <span class="font-medium text-slate-900">이름</span>
                <input
                  v-model="userName"
                  type="text"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0"
                  placeholder="이름을 입력하세요"
                />
              </label>
              <label class="space-y-1" for="gender">
                <span class="text-xs font-semibold text-slate-500">성별 (선택)</span>
                <select
                  id="gender"
                  v-model="gender"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0 bg-white"
                >
                  <option value="">선택 안 함</option>
                  <option value="male">남성</option>
                  <option value="female">여성</option>
                </select>
              </label>
            </div>
          </div>
          <div class="grid gap-4 sm:grid-cols-2">
            <label class="space-y-1" for="birth-date">
              <span class="text-xs font-semibold text-slate-500">생년월일 *</span>
              <input
                id="birth-date"
                v-model="birthdate"
                type="date"
                class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0"
                required
              />
            </label>
            <div class="space-y-2">
              <label class="space-y-1" for="birth-time">
                <span class="text-xs font-semibold text-slate-500">태어난 시간 (선택)</span>
                <input
                  id="birth-time"
                  v-model="birthtime"
                  type="time"
                  :disabled="timeUnknown"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0 disabled:bg-slate-50"
                />
              </label>
              <label class="inline-flex items-center gap-2 text-xs text-slate-500">
                <input type="checkbox" v-model="timeUnknown" class="rounded border-slate-300 text-slate-900" />
                시간을 모르겠어요
              </label>
            </div>
          </div>
        </div>
        <div class="preset-card-container bg-white rounded-2xl shadow-sm p-4 sm:p-6 space-y-5 relative">
          <!-- Overlay when not enabled -->
          <div
            v-if="!targetProfileEnabled"
            class="absolute inset-0 bg-slate-900/30 backdrop-blur-md rounded-2xl flex items-center justify-center z-10 cursor-pointer"
            @click="targetProfileEnabled = true"
          >
            <div class="flex flex-col items-center gap-3">
              <button
                class="w-16 h-16 rounded-full bg-slate-900 text-white flex items-center justify-center hover:bg-slate-800 transition-colors shadow-lg"
                @click="targetProfileEnabled = true"
              >
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 4v16m8-8H4" />
                </svg>
              </button>
              <p class="text-sm font-semibold text-slate-900">비교 대상 추가하기</p>
            </div>
          </div>

          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h3 class="text-base font-semibold text-slate-900">비교 대상 사주</h3>
            </div>
          </div>
          <div class="space-y-4">
            <div class="text-xs space-y-3">
              <div class="flex flex-wrap items-center gap-2">
                <span class="text-slate-500 font-semibold uppercase tracking-wide">비교 대상 빠른 설정</span>
                <span v-if="quickPresetLoading" class="text-slate-400">불러오는 중...</span>
                <span v-else-if="!quickPresetOptions.length" class="text-slate-400">등록된 빠른 설정이 없습니다.</span>
                <span v-else class="text-slate-500">사용자를 선택하여 직접 입력을 하거나 다른 사람을 선택하세요</span>
              </div>
              <div v-if="!quickPresetLoading && quickPresetOptions.length" class="flex gap-3 overflow-x-auto pb-6 pt-3 -mx-1 px-1 -mt-3" style="overflow-y: visible;">
                <button
                  v-for="preset in quickPresetOptions"
                  :key="`target-${preset.id}`"
                  type="button"
                  class="preset-card yugioh-card flex-shrink-0"
                  :class="{ 'preset-card-selected': selectedTargetPresetId === preset.id }"
                  @click="applyTargetQuickPreset(preset)"
                >
                  <div class="card-inner">
                    <div class="card-border"></div>
                    <div class="card-content">
                      <div class="card-header">
                        <div class="card-name">{{ preset.label }}</div>
                      </div>
                      <div class="card-image">
                        <img
                          v-if="preset.imageUrl"
                          :src="preset.imageUrl"
                          :alt="preset.label"
                          class="card-image-actual"
                        />
                        <div v-else class="card-image-placeholder">👥</div>
                      </div>
                      <div class="card-info">
                        <div v-if="preset.birthdate" class="card-birthdate">{{ formatCardDate(preset.birthdate) }}</div>
                        <div v-if="selectedTargetPresetId === preset.id" class="card-selected-badge">
                          <svg class="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
                            <path
                              fill-rule="evenodd"
                              d="M16.707 5.293a1 1 0 010 1.414l-7.01 7.01a1 1 0 01-1.414 0l-3.01-3.01A1 1 0 116.293 9.293L8.99 11.99l6.303-6.303a1 1 0 011.414 0z"
                              clip-rule="evenodd"
                            />
                          </svg>
                          <span>선택됨</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </button>
              </div>
            </div>
            <div class="grid gap-4 sm:grid-cols-2">
              <label class="space-y-1 text-sm text-slate-600">
                <span class="font-medium text-slate-900">비교 대상 이름</span>
                <input
                  v-model="targetName"
                  type="text"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0"
                  placeholder="비교 대상 이름을 입력하세요"
                />
              </label>
              <label class="space-y-1" for="target-gender">
                <span class="text-xs font-semibold text-slate-500">성별 (선택)</span>
                <select
                  id="target-gender"
                  v-model="targetGender"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0 bg-white"
                >
                  <option value="">선택 안 함</option>
                  <option value="male">남성</option>
                  <option value="female">여성</option>
                </select>
              </label>
            </div>
            <div class="grid gap-4 sm:grid-cols-2">
              <label class="space-y-1" for="target-birth-date">
                <span class="text-xs font-semibold text-slate-500">비교 대상 생년월일 *</span>
                <input
                  id="target-birth-date"
                  v-model="targetBirthdate"
                  type="date"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0"
                  required
                />
              </label>
              <div class="space-y-2">
                <label class="space-y-1" for="target-birth-time">
                  <span class="text-xs font-semibold text-slate-500">태어난 시간 (선택)</span>
                  <input
                    id="target-birth-time"
                    v-model="targetBirthtime"
                    type="time"
                    :disabled="targetTimeUnknown"
                    class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0 disabled:bg-slate-50"
                  />
                </label>
                <label class="inline-flex items-center gap-2 text-xs text-slate-500">
                  <input type="checkbox" v-model="targetTimeUnknown" class="rounded border-slate-300 text-slate-900" />
                  시간을 모르겠어요
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Card Preview Section -->
      <div v-if="birthdate || targetBirthdate" class="flex flex-col gap-4">
        <div class="flex items-center justify-center gap-4">
          <!-- User Card -->
          <div v-if="birthdate" class="yugioh-card" :class="{ 'card-selected': birthdate }">
            <div class="card-inner">
              <div class="card-border"></div>
              <div class="card-content">
                <div class="card-header">
                  <div class="card-name">{{ userName || DEFAULT_USER_NAME }}</div>
                </div>
                <div class="card-image">
                  <img
                    v-if="userImageUrl"
                    :src="userImageUrl"
                    :alt="userName || DEFAULT_USER_NAME"
                    class="card-image-actual"
                  />
                  <div v-else class="card-image-placeholder">👤</div>
                </div>
                <div class="card-info">
                  <div class="card-birthdate">{{ formatCardDate(birthdate) }}</div>
                  <div v-if="!timeUnknown && birthtime" class="card-time">{{ birthtime }}</div>
                  <div v-if="gender" class="card-gender">{{ gender === 'male' ? '남성' : '여성' }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Plus Icon - show when both cards exist -->
          <div v-if="birthdate && targetBirthdate" class="plus-icon">
            <svg class="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 4v16m8-8H4" />
            </svg>
          </div>

          <!-- Target Card -->
          <div v-if="targetBirthdate" class="yugioh-card" :class="{ 'card-selected': targetBirthdate }">
            <div class="card-inner">
              <div class="card-border"></div>
              <div class="card-content">
                <div class="card-header">
                  <div class="card-name">{{ targetName || DEFAULT_TARGET_NAME }}</div>
                </div>
                <div class="card-image">
                  <img
                    v-if="targetImageUrl"
                    :src="targetImageUrl"
                    :alt="targetName || DEFAULT_TARGET_NAME"
                    class="card-image-actual"
                  />
                  <div v-else class="card-image-placeholder">👥</div>
                </div>
                <div class="card-info">
                  <div class="card-birthdate">{{ formatCardDate(targetBirthdate) }}</div>
                  <div v-if="!targetTimeUnknown && targetBirthtime" class="card-time">{{ targetBirthtime }}</div>
                  <div v-if="targetGender" class="card-gender">{{ targetGender === 'male' ? '남성' : '여성' }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="flex flex-col gap-2">
        <button
          class="w-full flex items-center justify-center gap-2 rounded-2xl bg-slate-900 text-white py-3 text-sm font-semibold disabled:opacity-80 transition-all shadow-md hover:shadow-lg disabled:shadow-none"
          :disabled="loading"
          @click="handleCompatibility"
        >
          <svg v-if="!loading" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
          <span>{{ loading ? '분석 중...' : analyzeButtonLabel }}</span>
        </button>
        <div v-if="loading" class="w-full bg-slate-100 rounded-full h-3 overflow-hidden shadow-inner mt-1 relative">
          <div
            class="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 transition-all duration-500 ease-out relative"
            :style="{ width: `${Math.max(4, loadingProgressRatio * 100)}%` }"
          >
            <div class="absolute inset-0 w-full h-full bg-white/30 animate-shimmer"></div>
          </div>
        </div>
        <div v-if="loading" class="w-full rounded-2xl border border-slate-200 bg-white/90 p-4 space-y-3">
          <div class="text-xs font-semibold text-slate-600 flex items-center gap-2">
            <span>진행 단계</span>
            <span class="text-slate-400">({{ loadingStepStats.completed }}/{{ loadingStepStats.total }})</span>
          </div>
          <ol class="space-y-2 text-xs text-slate-600">
            <li v-for="step in loadingSteps" :key="step.key" class="flex flex-col gap-1">
              <div class="flex items-center gap-2">
                <div
                  class="w-6 h-6 inline-flex items-center justify-center rounded-full text-[10px] font-bold border"
                  :class="{
                    'bg-emerald-100 text-emerald-600 border-emerald-200': step.status === 'done',
                    'bg-indigo-50 text-indigo-600 border-indigo-200': step.status === 'running',
                    'bg-slate-100 text-slate-400 border-slate-200': step.status === 'pending',
                    'bg-rose-100 text-rose-600 border-rose-200': step.status === 'error'
                  }"
                >
                  <svg
                    v-if="step.status === 'running'"
                    class="w-3.5 h-3.5 animate-spin text-indigo-600"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                  >
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke-width="4" stroke="currentColor" />
                    <path class="opacity-75" d="M4 12a8 8 0 018-8" stroke-width="4" stroke-linecap="round" stroke="currentColor" />
                  </svg>
                  <span v-else>
                    {{ step.status === 'done' ? '✔' : step.status === 'error' ? '!' : '•' }}
                  </span>
                </div>
                <span class="font-medium text-slate-800">{{ step.label }}</span>
              </div>
              <p v-if="step.detail" class="pl-7 text-[11px] text-slate-500 leading-snug">
                {{ step.detail }}
              </p>
            </li>
          </ol>
        </div>
        <p v-if="errorMessage" class="text-xs text-rose-500">{{ errorMessage }}</p>
      </div>
      <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 space-y-6">
        <div>
          <h3 class="text-base font-semibold text-slate-900">사주 분석 결과</h3>
          <span 
            v-if="userVsBitcoinResult?.agentProvider" 
            class="text-xs text-slate-400 cursor-pointer hover:text-slate-600 hover:underline"
            @click="openPromptDebug"
            title="프롬프트 보기"
          >
            (Powered by {{ userVsBitcoinResult.agentProvider }})
          </span>
        </div>
        <div v-if="!userVsBitcoinResult && !targetVsBitcoinResult && !userVsTargetResult" class="text-center py-12">
          <p class="text-sm text-slate-500">{{ analyzeButtonLabel }}를 눌러 궁합을 확인하세요.</p>
        </div>

        <!-- 1. 사용자 vs 비트코인 -->
        <div v-if="userVsBitcoinResult" class="border-t border-slate-200 pt-6 space-y-4">
          <h4 class="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
            <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-orange-500 text-white text-xs font-bold">1</span>
            <span>{{ userVsBitcoinResult.personName }} × 비트코인 궁합</span>
          </h4>

          <div class="rounded-2xl border border-slate-200 bg-white p-5">
            <div class="flex gap-8 items-start flex-wrap md:flex-nowrap">
              <div class="flex-shrink-0">
                <div class="w-28 h-28 sm:w-32 sm:h-32 rounded-2xl overflow-hidden border-2 border-slate-200 bg-slate-100 flex items-center justify-center shadow-sm">
                  <img v-if="userVsBitcoinResult.personImageUrl" :src="userVsBitcoinResult.personImageUrl" :alt="userVsBitcoinResult.personName" class="w-full h-full object-cover" />
                  <span v-else class="text-4xl">👤</span>
                </div>
              </div>
              <div class="flex-1 space-y-2">
                <p class="text-lg font-bold text-slate-900">{{ userVsBitcoinResult.personName }}</p>
                <ul class="text-base text-slate-700 space-y-1.5 leading-relaxed select-text">
                  <li v-for="fact in userVsBitcoinResult.profileFacts" :key="fact">{{ fact }}</li>
                </ul>
                <div
                  v-if="userVsBitcoinResult.personStory"
                  class="text-base text-slate-700 leading-relaxed mt-3 select-text"
                >
                  {{ userVsBitcoinResult.personStory }}
                </div>
              </div>
              <div v-if="userProfileRadar" class="profile-radar hidden md:flex items-center justify-center">
                <svg
                  :viewBox="`0 0 ${userProfileRadar.size} ${userProfileRadar.size}`"
                  :width="userProfileRadar.size"
                  :height="userProfileRadar.size"
                  class="profile-radar-svg"
                >
                  <circle
                    :cx="userProfileRadar.center"
                    :cy="userProfileRadar.center"
                    :r="userProfileRadar.maxRadius"
                    class="fill-slate-50 stroke-slate-200"
                  ></circle>
                  <line
                    v-for="axis in userProfileRadar.axes"
                    :key="`user-axis-${axis.key}`"
                    :x1="userProfileRadar.center"
                    :y1="userProfileRadar.center"
                    :x2="axis.x2"
                    :y2="axis.y2"
                    class="stroke-slate-200"
                    stroke-width="1"
                  ></line>
                  <polygon
                    :points="userProfileRadar.polygonPoints"
                    class="fill-blue-100/40 stroke-blue-500 radar-polygon"
                    stroke-width="2"
                  ></polygon>
                  <circle
                    v-for="marker in userProfileRadar.markers"
                    :key="`user-marker-${marker.key}`"
                    :cx="marker.x"
                    :cy="marker.y"
                    r="5"
                    class="fill-blue-500"
                  ></circle>
                  <text
                    v-for="marker in userProfileRadar.markers"
                    :key="`user-percent-${marker.key}`"
                    :x="marker.x"
                    :y="marker.y - 10"
                    class="text-[10px] fill-blue-600 font-semibold pointer-events-none"
                    text-anchor="middle"
                  >
                    {{ marker.ratio }}%
                  </text>
                  <text
                    v-for="axis in userProfileRadar.axes"
                    :key="`user-label-${axis.key}`"
                    :x="axis.labelX"
                    :y="axis.labelY"
                    class="text-xs fill-slate-700 font-bold"
                    text-anchor="middle"
                    dominant-baseline="middle"
                  >
                    {{ axis.label }}
                  </text>
                </svg>
              </div>
            </div>
          </div>

          <div
            v-if="userVsBitcoinResult"
            class="rounded-2xl border border-amber-200 bg-amber-50/70 p-4 space-y-3 highlight-panel"
          >
            <div class="text-[11px] font-semibold text-amber-700 uppercase tracking-wide flex items-center gap-2">
              <span class="inline-flex w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
              핵심 하이라이트
            </div>
            <div
              v-if="userVsBitcoinResult.highlightLoading"
              class="flex items-center gap-2 text-xs text-amber-700"
            >
              <svg class="w-4 h-4 animate-spin text-amber-500" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" d="M4 12a8 8 0 018-8" stroke="currentColor" stroke-width="4" stroke-linecap="round" />
              </svg>
              <span>하이라이트 생성 중입니다...</span>
            </div>
            <div
              v-else-if="userVsBitcoinResult.highlightedNarrative"
              class="prose prose-slate prose-sm max-w-none markdown-highlight select-text"
            >
              <div v-html="renderMarkdown(userVsBitcoinResult.highlightedNarrative)"></div>
            </div>
            <p v-else class="text-xs text-amber-800 bg-white/70 rounded-lg px-3 py-2">
              하이라이트를 불러오지 못했습니다.
            </p>
          </div>
        </div>

        <!-- 2. 비교대상 vs 비트코인 -->
        <div v-if="targetVsBitcoinResult" class="border-t border-slate-200 pt-6 space-y-4">
          <h4 class="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
            <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-orange-500 text-white text-xs font-bold">2</span>
            <span>{{ targetVsBitcoinResult.personName }} × 비트코인 궁합</span>
          </h4>

          <div class="rounded-2xl border border-slate-200 bg-white p-5">
            <div class="flex gap-8 items-start flex-wrap md:flex-nowrap">
              <div class="flex-shrink-0">
                <div class="w-28 h-28 sm:w-32 sm:h-32 rounded-2xl overflow-hidden border-2 border-slate-200 bg-slate-100 flex items-center justify-center shadow-sm">
                  <img v-if="targetVsBitcoinResult.personImageUrl" :src="targetVsBitcoinResult.personImageUrl" :alt="targetVsBitcoinResult.personName" class="w-full h-full object-cover" />
                  <span v-else class="text-4xl">👤</span>
                </div>
              </div>
              <div class="flex-1 space-y-2">
                <p class="text-lg font-bold text-slate-900">{{ targetVsBitcoinResult.personName }}</p>
                <ul class="text-base text-slate-700 space-y-1.5 leading-relaxed select-text">
                  <li v-for="fact in targetVsBitcoinResult.profileFacts" :key="fact">{{ fact }}</li>
                </ul>
                <div
                  v-if="targetVsBitcoinResult.personStory"
                  class="text-base text-slate-700 leading-relaxed mt-3 select-text"
                >
                  {{ targetVsBitcoinResult.personStory }}
                </div>
              </div>
              <div v-if="targetProfileRadar" class="profile-radar hidden md:flex items-center justify-center">
                <svg
                  :viewBox="`0 0 ${targetProfileRadar.size} ${targetProfileRadar.size}`"
                  :width="targetProfileRadar.size"
                  :height="targetProfileRadar.size"
                  class="profile-radar-svg"
                >
                  <circle
                    :cx="targetProfileRadar.center"
                    :cy="targetProfileRadar.center"
                    :r="targetProfileRadar.maxRadius"
                    class="fill-slate-50 stroke-slate-200"
                  ></circle>
                  <line
                    v-for="axis in targetProfileRadar.axes"
                    :key="`target-axis-${axis.key}`"
                    :x1="targetProfileRadar.center"
                    :y1="targetProfileRadar.center"
                    :x2="axis.x2"
                    :y2="axis.y2"
                    class="stroke-slate-200"
                    stroke-width="1"
                  ></line>
                  <polygon
                    :points="targetProfileRadar.polygonPoints"
                    class="fill-purple-100/40 stroke-purple-500 radar-polygon"
                    stroke-width="2"
                  ></polygon>
                  <circle
                    v-for="marker in targetProfileRadar.markers"
                    :key="`target-marker-${marker.key}`"
                    :cx="marker.x"
                    :cy="marker.y"
                    r="5"
                    class="fill-purple-500"
                  ></circle>
                  <text
                    v-for="marker in targetProfileRadar.markers"
                    :key="`target-percent-${marker.key}`"
                    :x="marker.x"
                    :y="marker.y - 10"
                    class="text-[10px] fill-purple-600 font-semibold pointer-events-none"
                    text-anchor="middle"
                  >
                    {{ marker.ratio }}%
                  </text>
                  <text
                    v-for="axis in targetProfileRadar.axes"
                    :key="`target-label-${axis.key}`"
                    :x="axis.labelX"
                    :y="axis.labelY"
                    class="text-xs fill-slate-700 font-bold"
                    text-anchor="middle"
                    dominant-baseline="middle"
                  >
                    {{ axis.label }}
                  </text>
                </svg>
              </div>
            </div>
          </div>

          <div
            v-if="targetVsBitcoinResult"
            class="rounded-2xl border border-amber-200 bg-amber-50/70 p-4 space-y-3 highlight-panel"
          >
            <div class="text-[11px] font-semibold text-amber-700 uppercase tracking-wide flex items-center gap-2">
              <span class="inline-flex w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
              핵심 하이라이트
            </div>
            <div
              v-if="targetVsBitcoinResult.highlightLoading"
              class="flex items-center gap-2 text-xs text-amber-700"
            >
              <svg class="w-4 h-4 animate-spin text-amber-500" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" d="M4 12a8 8 0 018-8" stroke="currentColor" stroke-width="4" stroke-linecap="round" />
              </svg>
              <span>하이라이트 생성 중입니다...</span>
            </div>
            <div
              v-else-if="targetVsBitcoinResult.highlightedNarrative"
              class="prose prose-slate prose-sm max-w-none markdown-highlight select-text"
            >
              <div v-html="renderMarkdown(targetVsBitcoinResult.highlightedNarrative)"></div>
            </div>
            <p v-else class="text-xs text-amber-800 bg-white/70 rounded-lg px-3 py-2">
              하이라이트를 불러오지 못했습니다.
            </p>
          </div>

        </div>

        <!-- 3. 사용자 vs 비교대상 -->
        <div v-if="userVsTargetResult" class="border-t border-slate-200 pt-6 space-y-4">
          <h4 class="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
            <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-purple-500 text-white text-xs font-bold">3</span>
            <span>{{ userVsTargetResult.personName }} × {{ userVsTargetResult.targetPersonName }} × 비트코인 궁합</span>
          </h4>

          <div class="grid gap-4 md:grid-cols-2">
            <div class="rounded-2xl border border-slate-200 bg-white p-4">
              <div class="flex gap-5 items-start mb-3 flex-wrap">
                <div class="flex-shrink-0">
                  <div class="w-20 h-20 rounded-xl overflow-hidden border-2 border-slate-200 bg-slate-100 flex items-center justify-center shadow-sm">
                    <img v-if="userVsTargetResult.personImageUrl" :src="userVsTargetResult.personImageUrl" :alt="userVsTargetResult.personName" class="w-full h-full object-cover" />
                    <span v-else class="text-2xl">👤</span>
                  </div>
                </div>
                <div class="flex-1">
                  <p class="text-base font-bold text-slate-900 mb-1">{{ userVsTargetResult.personName }}</p>
                  <ul class="text-base text-slate-700 space-y-1.5 select-text">
                    <li v-for="fact in userVsTargetResult.personFacts" :key="fact">{{ fact }}</li>
                  </ul>
                  <div
                    v-if="userVsTargetResult.personStory"
                    class="text-base text-slate-700 leading-relaxed mt-2 select-text"
                  >
                    {{ userVsTargetResult.personStory }}
                  </div>
                </div>
                <div v-if="teamUserProfileRadar" class="profile-radar mt-3 md:mt-0 flex items-center justify-center">
                  <svg
                    :viewBox="`0 0 ${teamUserProfileRadar.size} ${teamUserProfileRadar.size}`"
                    :width="teamUserProfileRadar.size"
                    :height="teamUserProfileRadar.size"
                    class="profile-radar-svg"
                  >
                    <circle
                      :cx="teamUserProfileRadar.center"
                      :cy="teamUserProfileRadar.center"
                      :r="teamUserProfileRadar.maxRadius"
                      class="fill-slate-50 stroke-slate-200"
                    ></circle>
                    <line
                      v-for="axis in teamUserProfileRadar.axes"
                      :key="`team-user-axis-${axis.key}`"
                      :x1="teamUserProfileRadar.center"
                      :y1="teamUserProfileRadar.center"
                      :x2="axis.x2"
                      :y2="axis.y2"
                      class="stroke-slate-200"
                      stroke-width="1"
                    ></line>
                    <polygon
                      :points="teamUserProfileRadar.polygonPoints"
                      class="fill-green-100/40 stroke-green-500 radar-polygon"
                      stroke-width="2"
                    ></polygon>
                    <circle
                      v-for="marker in teamUserProfileRadar.markers"
                      :key="`team-user-marker-${marker.key}`"
                      :cx="marker.x"
                      :cy="marker.y"
                      r="4.5"
                      class="fill-green-500"
                    ></circle>
                    <text
                      v-for="marker in teamUserProfileRadar.markers"
                      :key="`team-user-percent-${marker.key}`"
                      :x="marker.x"
                      :y="marker.y - 8"
                      class="text-[9px] fill-green-600 font-semibold pointer-events-none"
                      text-anchor="middle"
                    >
                      {{ marker.ratio }}%
                    </text>
                    <text
                      v-for="axis in teamUserProfileRadar.axes"
                      :key="`team-user-label-${axis.key}`"
                      :x="axis.labelX"
                      :y="axis.labelY"
                      class="text-[11px] fill-slate-700 font-bold"
                      text-anchor="middle"
                      dominant-baseline="middle"
                    >
                      {{ axis.label }}
                    </text>
                  </svg>
                </div>
              </div>
            </div>

            <div class="rounded-2xl border border-slate-200 bg-white p-4">
              <div class="flex gap-5 items-start mb-3 flex-wrap">
                <div class="flex-shrink-0">
                  <div class="w-20 h-20 rounded-xl overflow-hidden border-2 border-slate-200 bg-slate-100 flex items-center justify-center shadow-sm">
                    <img v-if="userVsTargetResult.targetPersonImageUrl" :src="userVsTargetResult.targetPersonImageUrl" :alt="userVsTargetResult.targetPersonName" class="w-full h-full object-cover" />
                    <span v-else class="text-2xl">👤</span>
                  </div>
                </div>
                <div class="flex-1">
                  <p class="text-base font-bold text-slate-900 mb-1">{{ userVsTargetResult.targetPersonName }}</p>
                  <ul class="text-base text-slate-700 space-y-1.5 select-text">
                    <li v-for="fact in userVsTargetResult.targetFacts" :key="fact">{{ fact }}</li>
                  </ul>
                  <div
                    v-if="userVsTargetResult.targetStory"
                    class="text-base text-slate-700 leading-relaxed mt-2 select-text"
                  >
                    {{ userVsTargetResult.targetStory }}
                  </div>
                </div>
                <div v-if="teamTargetProfileRadar" class="profile-radar mt-3 md:mt-0 flex items-center justify-center">
                  <svg
                    :viewBox="`0 0 ${teamTargetProfileRadar.size} ${teamTargetProfileRadar.size}`"
                    :width="teamTargetProfileRadar.size"
                    :height="teamTargetProfileRadar.size"
                    class="profile-radar-svg"
                  >
                    <circle
                      :cx="teamTargetProfileRadar.center"
                      :cy="teamTargetProfileRadar.center"
                      :r="teamTargetProfileRadar.maxRadius"
                      class="fill-slate-50 stroke-slate-200"
                    ></circle>
                    <line
                      v-for="axis in teamTargetProfileRadar.axes"
                      :key="`team-target-axis-${axis.key}`"
                      :x1="teamTargetProfileRadar.center"
                      :y1="teamTargetProfileRadar.center"
                      :x2="axis.x2"
                      :y2="axis.y2"
                      class="stroke-slate-200"
                      stroke-width="1"
                    ></line>
                    <polygon
                      :points="teamTargetProfileRadar.polygonPoints"
                      class="fill-amber-100/40 stroke-amber-500 radar-polygon"
                      stroke-width="2"
                    ></polygon>
                    <circle
                      v-for="marker in teamTargetProfileRadar.markers"
                      :key="`team-target-marker-${marker.key}`"
                      :cx="marker.x"
                      :cy="marker.y"
                      r="4.5"
                      class="fill-amber-500"
                    ></circle>
                    <text
                      v-for="marker in teamTargetProfileRadar.markers"
                      :key="`team-target-percent-${marker.key}`"
                      :x="marker.x"
                      :y="marker.y - 8"
                      class="text-[9px] fill-amber-600 font-semibold pointer-events-none"
                      text-anchor="middle"
                    >
                      {{ marker.ratio }}%
                    </text>
                    <text
                      v-for="axis in teamTargetProfileRadar.axes"
                      :key="`team-target-label-${axis.key}`"
                      :x="axis.labelX"
                      :y="axis.labelY"
                      class="text-[11px] fill-slate-700 font-bold"
                      text-anchor="middle"
                      dominant-baseline="middle"
                    >
                      {{ axis.label }}
                    </text>
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <div
            v-if="userVsTargetResult"
            class="rounded-2xl border border-amber-200 bg-amber-50/70 p-4 space-y-3 highlight-panel"
          >
            <div class="text-[11px] font-semibold text-amber-700 uppercase tracking-wide flex items-center gap-2">
              <span class="inline-flex w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
              핵심 하이라이트
            </div>
            <div
              v-if="userVsTargetResult.highlightLoading"
              class="flex items-center gap-2 text-xs text-amber-700"
            >
              <svg class="w-4 h-4 animate-spin text-amber-500" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" d="M4 12a8 8 0 018-8" stroke="currentColor" stroke-width="4" stroke-linecap="round" />
              </svg>
              <span>하이라이트 생성 중입니다...</span>
            </div>
            <div
              v-else-if="userVsTargetResult.highlightedNarrative"
              class="prose prose-slate prose-sm max-w-none markdown-highlight select-text"
            >
              <div v-html="renderMarkdown(userVsTargetResult.highlightedNarrative)"></div>
            </div>
            <p v-else class="text-xs text-amber-800 bg-white/70 rounded-lg px-3 py-2">
              하이라이트를 불러오지 못했습니다.
            </p>
          </div>

        </div>

        <div v-if="pairCompatibilityResult" class="border-t border-slate-200 pt-6 space-y-4">
          <div class="rounded-2xl border border-purple-200 bg-purple-50/60 p-5 space-y-3">
            <div class="flex items-center gap-2">
              <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-purple-600 text-white text-xs font-bold">◎</span>
              <p class="text-base font-bold text-purple-900">두 사람 궁합 리포트</p>
              <span
                v-if="pairCompatibilityResult.agentProvider"
                class="ml-auto text-xs text-purple-600"
              >
                ({{ pairCompatibilityResult.agentProvider }})
              </span>
            </div>
            <div class="rounded-2xl border border-amber-200 bg-white/70 p-4 space-y-3 highlight-panel">
              <div class="text-[11px] font-semibold text-amber-700 uppercase tracking-wide flex items-center gap-2">
                <span class="inline-flex w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
                핵심 하이라이트
              </div>
              <div
                v-if="pairCompatibilityResult.highlightLoading"
                class="flex items-center gap-2 text-xs text-amber-700"
              >
                <svg class="w-4 h-4 animate-spin text-amber-500" viewBox="0 0 24 24" fill="none">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" d="M4 12a8 8 0 018-8" stroke="currentColor" stroke-width="4" stroke-linecap="round" />
                </svg>
                <span>하이라이트 생성 중입니다...</span>
              </div>
              <div
                v-else-if="pairCompatibilityResult.highlightedNarrative"
                class="prose prose-slate prose-sm max-w-none markdown-highlight select-text"
                v-html="renderMarkdown(pairCompatibilityResult.highlightedNarrative)"
              ></div>
              <p v-else class="text-xs text-amber-800 bg-white/70 rounded-lg px-3 py-2">
                하이라이트를 불러오지 못했습니다.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>

  <!-- Prompt Debug Modal -->
  <div v-if="showDebugModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" @click.self="showDebugModal = false">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden">
      <div class="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
        <h3 class="font-bold text-slate-900">Agent Prompt Debug</h3>
        <button @click="showDebugModal = false" class="text-slate-400 hover:text-slate-600">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <div class="flex-1 overflow-y-auto p-6 space-y-6">
        <div v-for="(prompt, idx) in debugPrompts" :key="idx" class="space-y-2">
          <h4 class="font-semibold text-slate-800 text-lg sticky top-0 bg-white py-2 border-b border-slate-100">
            {{ prompt.title }}
          </h4>
          <div class="bg-slate-900 rounded-xl p-4 overflow-x-auto">
            <pre class="text-xs text-slate-300 font-mono whitespace-pre-wrap leading-relaxed">{{ prompt.content }}</pre>
          </div>
        </div>
        <div v-if="debugPrompts.length === 0" class="text-center text-slate-500 py-12">
          저장된 프롬프트가 없습니다.
        </div>
      </div>
      <div class="p-4 border-t border-slate-200 bg-slate-50 flex justify-end">
        <button @click="showDebugModal = false" class="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800">
          닫기
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watchEffect } from 'vue'
import { fetchCompatibilityQuickPresets, fetchCompatibilityReportTemplates, runCompatibilityAgent, saveCompatibilityAnalysis } from '@/services/compatibilityService'

const BITCOIN_HIGHLIGHTS = [
  {
    label: '목(木)',
    elementKey: 'wood',
    value: '성장과 개발 생태계',
    description: '새로운 확장 제안과 구축자 생태계를 키우는 힘. 라이트닝·탭루트 같은 실험을 밀어 올리고, 지속적인 코드 리뷰·테스트 문화가 뿌리처럼 비트코인을 지탱한다.',
    icon: '🌱',
    ratio: 10,
    colorClass: 'bg-green-500'
  },
  {
    label: '화(火)',
    elementKey: 'fire',
    value: '관심, 서사, 과열 모멘텀',
    description: '가격 급등락과 서사가 촉발하는 열기. 밈과 미디어, 정치 발언이 불꽃처럼 튀며, 한 번 붙은 불길이 글로벌 유동성을 빨아들여 단기간 폭증을 만든다.',
    icon: '🔥',
    ratio: 20,
    colorClass: 'bg-red-500'
  },
  {
    label: '토(土)',
    elementKey: 'earth',
    value: '완충, 신뢰 인프라, 거버넌스',
    description: '채굴자·노드·풀 운영자가 만든 방호벽. 전 세계에 흩어진 노드가 규칙을 검증하고, 채굴 난이도·반감기 구조가 충격을 흡수하는 버팀목이 된다.',
    icon: '🏔️',
    ratio: 10,
    colorClass: 'bg-yellow-600'
  },
  {
    label: '금(金)',
    elementKey: 'metal',
    value: '규칙, 고정 공급, 불변성',
    description: '비트코인의 핵심 본체. 2,100만 개 고정 공급과 검증 가능한 합의 규칙이 디지털 금의 품격을 부여하고, 누구도 임의 발행·검열을 할 수 없도록 만든다.',
    icon: '🥇',
    ratio: 35,
    colorClass: 'bg-amber-500'
  },
  {
    label: '수(水)',
    elementKey: 'water',
    value: '유동성, 글로벌 자본 흐름',
    description: '거대한 자본·거래소·파생상품 시장이 만들어내는 파도. 상승장에서는 폭발적 흡인력을, 조정기에는 급랭을 유발하며 온체인 자금 이동이 실시간으로 흐른다.',
    icon: '💧',
    ratio: 25,
    colorClass: 'bg-blue-500'
  }
]

const REPORT_TEMPLATE_DEFAULTS = {
  user_vs_bitcoin: `{{SUBJECT_NAME}}의 사주와 비트코인 궁합을 분석하세요.{{SUBJECT_EXTRA}}

**작성 지침 (반드시 준수):**

1. **분량**: 800~1000자. 시스템 프롬프트의 요구(비트코인 커리어·재물·인간관계·전략)를 빠짐없이 반영하고, 문단 사이 공백 없이 촘촘히 작성하세요.
2. **문체**: 모든 문장은 ‘~입니다’ 체로 작성하고, 각 항목의 핵심 문장은 **제목: 내용** 형태의 문장으로 시작하세요.

3. **출력 템플릿(순서 고정, 마크다운 엄수)**:
   - ## 프로필 브리핑
     - 일간: …
     - 오행 앵커: …
     - 직업/역할: …
   - ## 커리어 & 재물
     - 불릿 2~3개로 비트코인 커리어와 재물 흐름 서술
   - ## 인간관계
     - 협업/대인관계 리듬과 리스크를 불릿 2개로 정리
   - ## 비트코인 전략 체크리스트
     - 1. …
     - 2. …
     - 3. …

4. **근거 & 어휘**: 저장된 사주·스토리·오행 분포에서 최소 2가지 근거를 명시하고, 한자 대신 풀이형 표현을 사용하세요.

5. **금지 사항**: 인사말, 잡담, “모르겠다” 류 표현, 표 생략, 섹션 누락 금지.`,
  team_vs_bitcoin: `{{USER_NAME}}와(과) {{TARGET_NAME}}가 함께 비트코인 투자할 때의 팀 궁합을 분석하세요.{{TEAM_EXTRA}}

**작성 지침 (반드시 준수):**

1. **분량**: 700~950자. 두 사람의 사주 앵커, 투자 습관, 협업 리듬, 전략 포지셔닝을 모두 다루세요.
2. **문체**: 모든 문장을 ‘~입니다’ 체로 작성하고, 각 문단의 첫 문장은 '제목: 내용' 구조로 요약하세요.

3. **출력 템플릿(순서 고정, 마크다운 엄수)**:
   - ## 팀 특성 & 호흡
     - 사용자 이름과 비교 대상 이름을 모두 언급하는 불릿 2~3개
   - ## 커리어 & 재물 시너지
     - 불릿 2개, 각 문장에 어느 사람이 어떤 역할을 맡는지 명시
   - ## 인간관계/커뮤니케이션
     - 불릿 2개, 갈등 방지법 포함
   - ## 팀 비트코인 전략 체크리스트
     - 1. 역할 분담 규칙
     - 2. 의사결정 루틴
     - 3. 리스크 통제법

4. **근거**: 각 섹션에서 최소 한 번씩 두 사람의 사주 요약 또는 스토리에서 직접 언급한 특징을 인용하세요.

5. **금지 사항**: 인사말, 모호한 표현, 생략표, 섹션 누락 금지.`
}

const BITCOIN_CANVAS_PROFILE = {
  entityName: '비트코인',
  label: '비트코인 사주 캔버스',
  summaryHighlight: '금(金)이 주력인 디지털 금, 수·화가 극단을 이루는 에너지',
  description: '',
  highlights: BITCOIN_HIGHLIGHTS
}

const ELEMENTS = [
  { key: 'wood', label: '목(木)', summary: '확장과 성장, 트렌드 파악에 빠름' },
  { key: 'fire', label: '화(火)', summary: '추진력과 속도, 모멘텀 집중' },
  { key: 'earth', label: '토(土)', summary: '안정과 조율, 리스크 관리 탁월' },
  { key: 'metal', label: '금(金)', summary: '정교함과 구조화, 규칙 기반 판단' },
  { key: 'water', label: '수(水)', summary: '흐름과 적응, 변동성 흡수' }
]

const ELEMENT_ICON_MAP = {
  wood: '🌱',
  fire: '🔥',
  earth: '🏔️',
  metal: '🥇',
  water: '💧'
}

const ELEMENT_COLOR_CLASS_MAP = {
  wood: 'bg-green-500',
  fire: 'bg-red-500',
  earth: 'bg-yellow-600',
  metal: 'bg-amber-500',
  water: 'bg-blue-500'
}

const ZODIAC_SIGNS = ['자(쥐)', '축(소)', '인(호랑이)', '묘(토끼)', '진(용)', '사(뱀)', '오(말)', '미(양)', '신(원숭이)', '유(닭)', '술(개)', '해(돼지)']

// 비트코인 맥시멀리스트 관점의 오행 궁합
// 핵심 철학: 상극(相克)은 '갈등'이 아니라 '역할 분담'이다
// 모든 상극을 긍정적으로 재해석:
// - 화극금(火克金) = 불이 금속을 단련한다 (tempering)
// - 금극목(金克木) = 금속이 나무에게 틀과 기준을 제공한다 (foundation)
// - 목극토(木克土) = 나무가 토양을 활용한다 (utilization)
// - 토극수(土克水) = 토양이 물의 흐름을 조절한다 (channeling)
// - 수극화(水克火) = 물이 불을 진정시킨다 (cooling)
const ELEMENT_AFFINITY = {
  wood: {
    allies: ['water', 'fire'],
    neutral: ['wood', 'earth'],
    foundation: ['metal'],  // 금은 목에게 규칙과 구조를 제공 (긍정적)
    challenges: []
  },
  fire: {
    allies: ['wood', 'earth'],
    neutral: ['fire', 'metal'],
    cooling: ['water'],  // 수는 화를 진정시킴 (긍정적)
    challenges: []
  },
  earth: {
    allies: ['fire', 'metal'],
    neutral: ['earth', 'water'],
    utilization: ['wood'],  // 목이 토를 활용함 (긍정적)
    challenges: []
  },
  // 비트코인(금)의 해석
  metal: {
    allies: ['earth', 'water'],
    neutral: ['metal', 'wood'],
    tempering: ['fire'],  // 화는 금을 단련함 (긍정적)
    challenges: []  // 비트코인에게 상극은 없다
  },
  water: {
    allies: ['metal', 'wood'],
    neutral: ['water', 'fire'],
    channeling: ['earth'],  // 토는 수의 흐름을 조절함 (긍정적)
    challenges: []
  }
}

const STRATEGY_LIBRARY = {
  wood: {
    style: '성장형 장기 적립',
    focus: '매월 또는 매주 일정 금액을 꾸준히 적립하며, 시장이 하락할 때도 인내심을 갖고 저축을 이어갑니다.',
    allocation: '비트코인 장기 보유 100% (최소 4년 이상)'
  },
  fire: {
    style: '열정적 정기 저축',
    focus: '감정에 흔들리지 않고 정해진 날짜에 자동으로 적립하며, 절대 단기 변동성에 매도하지 않습니다.',
    allocation: '비트코인 장기 보유 100% (최소 4년 이상)'
  },
  earth: {
    style: '안정형 장기 축적',
    focus: '변동성이 커도 흔들리지 않고 매월 정기 적립을 유지하며, 10년 이상의 장기 관점을 유지합니다.',
    allocation: '비트코인 장기 보유 100% (최소 4년 이상)'
  },
  metal: {
    style: '규율형 정기 저축',
    focus: '정확한 날짜와 금액을 정해 기계적으로 적립하며, 시장 상황과 무관하게 원칙을 지킵니다.',
    allocation: '비트코인 장기 보유 100% (최소 4년 이상)'
  },
  water: {
    style: '유연형 꾸준한 축적',
    focus: '시장 하락 시에도 당황하지 않고 오히려 더 저렴한 가격에 축적할 기회로 여기며 정기 저축을 이어갑니다.',
    allocation: '비트코인 장기 보유 100% (최소 4년 이상)'
  }
}

const TIME_WINDOWS = [
  { key: 'dawn', label: '새벽 (23:00-05:00)', bonus: 6, title: '직감이 강해지는 새벽', description: '새벽에 태어난 사람은 직감이 강하지만, 비트코인 저축에서는 감정보다 규칙이 중요합니다. 정해진 날짜에 자동 적립하세요.' },
  { key: 'morning', label: '아침 (05:00-11:00)', bonus: 4, title: '규칙적인 아침 리듬', description: '아침 에너지는 꾸준함과 루틴을 강화합니다. 매주 또는 매월 정기 적립 일정을 아침 시간으로 정하면 좋습니다.' },
  { key: 'afternoon', label: '낮 (11:00-17:00)', bonus: 2, title: '균형 잡힌 낮의 안정감', description: '낮 시간대는 균형과 안정을 상징합니다. 시장 변동성에 흔들리지 말고 장기 관점을 유지하세요.' },
  { key: 'evening', label: '저녁 (17:00-23:00)', bonus: 5, title: '차분한 저녁의 인내', description: '저녁 에너지는 복기와 성찰에 최적화되어 있습니다. 하루를 마무리하며 비트코인 저축 목표를 다시 상기하세요.' },
  { key: 'unknown', label: '시간 미상', bonus: 0, title: '중립 시간대', description: '시간 정보를 모르는 경우에는 매월 정해진 날짜에 자동 적립하는 루틴을 만드는 것이 가장 안전합니다.' }
]

const FALLBACK_QUICK_PRESETS = [
  {
    id: 'user-self',
    label: '사용자',
    gender: '',
    birthdate: '',
    birthtime: '',
    assume_time_unknown: false,
    image_url: ''
  },
  {
    id: 'saylor',
    label: '마이클 세일러',
    birthdate: '1965-02-04',
    gender: 'male',
    image_url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Michael_Saylor_2016.jpg/640px-Michael_Saylor_2016.jpg'
  },
  {
    id: 'trump',
    label: '도널드 트럼프',
    birthdate: '1946-06-14',
    gender: 'male',
    image_url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Donald_Trump_official_portrait.jpg/640px-Donald_Trump_official_portrait.jpg'
  },
  {
    id: 'fink',
    label: '래리 핑크',
    birthdate: '1952-11-02',
    gender: 'male',
    image_url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Laurence_D._Fink.jpg/640px-Laurence_D._Fink.jpg'
  },
  {
    id: 'dimon',
    label: '제이미 다이먼',
    birthdate: '1956-03-13',
    gender: 'male',
    image_url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Jamie_Dimon_2018.jpg/640px-Jamie_Dimon_2018.jpg'
  },
  {
    id: 'vitalik',
    label: '비탈릭 부테린',
    birthdate: '1994-01-31',
    gender: 'male',
    image_url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1c/Vitalik_Buterin_TechCrunch_London_2015_%28cropped%29.jpg/640px-Vitalik_Buterin_TechCrunch_London_2015_%28cropped%29.jpg'
  }
]

const DEFAULT_USER_NAME = '사용자'
const DEFAULT_TARGET_NAME = '비교 대상'
const EMPTY_TARGET_PROFILE = {
  profileType: 'person',
  entityName: DEFAULT_TARGET_NAME,
  label: `${DEFAULT_TARGET_NAME} 사주 캔버스`,
  summaryHighlight: '생년월일을 입력하면 오행 구성이 계산됩니다.',
  description: '빠른 설정에서 인물을 선택하거나 직접 입력해 사주를 비교하세요.',
  highlights: [],
  agentPrompt: `${DEFAULT_TARGET_NAME}의 사주를 기준으로 사용자와의 오행 궁합을 비교하라.`,
  targetZodiac: '',
  targetYinYang: ''
}
const bitcoinCanvasProfile = BITCOIN_CANVAS_PROFILE

const birthdate = ref('')
const birthtime = ref('')
const gender = ref('')
const timeUnknown = ref(false)
const userName = ref(DEFAULT_USER_NAME)
const userImageUrl = ref('')
const userDescription = ref('')
const userStory = ref('')
const userSajuSummary = ref('')
const targetName = ref(DEFAULT_TARGET_NAME)
const targetBirthdate = ref('')
const targetBirthtime = ref('')
const targetGender = ref('')
const targetTimeUnknown = ref(false)
const targetImageUrl = ref('')
const targetDescription = ref('')
const targetStory = ref('')
const targetSajuSummary = ref('')
const targetProfileEnabled = ref(false)
const loading = ref(false)
const analysisStep = ref(0)
const totalSteps = ref(3)
const errorMessage = ref('')
const showDebugModal = ref(false)
const debugPrompts = ref([])
const loadingSteps = ref([])
const loadingStepStats = computed(() => {
  const total = loadingSteps.value.length
  const completed = loadingSteps.value.filter((step) => step.status === 'done').length
  return { total, completed }
})
const loadingProgressRatio = computed(() => {
  const total = loadingSteps.value.length
  if (!total) {
    return Math.min(1, analysisStep.value / Math.max(totalSteps.value, 1))
  }
  const completed = loadingSteps.value.filter((step) => step.status === 'done').length
  const running = loadingSteps.value.some((step) => step.status === 'running')
  const partial = running ? 0.35 : 0
  return Math.min(1, (completed + partial) / total)
})
const pairCompatibilityResult = ref(null)

function openPromptDebug() {
  const prompts = []
  if (userVsBitcoinResult.value?.debugPrompt) {
    prompts.push({ title: '1. 사용자 vs 비트코인', content: userVsBitcoinResult.value.debugPrompt })
  }
  if (targetVsBitcoinResult.value?.debugPrompt) {
    prompts.push({ title: '2. 비교대상 vs 비트코인', content: targetVsBitcoinResult.value.debugPrompt })
  }
  if (userVsTargetResult.value?.debugPrompt) {
    prompts.push({ title: '3. 팀 궁합 vs 비트코인', content: userVsTargetResult.value.debugPrompt })
  }
  if (pairCompatibilityResult.value?.debugPrompt) {
    prompts.push({ title: '4. 두 사람 직접 궁합', content: pairCompatibilityResult.value.debugPrompt })
  }
  debugPrompts.value = prompts
  showDebugModal.value = true
}

const userVsBitcoinResult = ref(null)
const targetVsBitcoinResult = ref(null)
const userVsTargetResult = ref(null)
const selectedTargetPresetId = ref(null)
const personTargetMeta = computed(() => buildPersonTargetMeta())
const activeTargetProfile = computed(() => personTargetMeta.value)
const quickPresetOptions = ref(
  FALLBACK_QUICK_PRESETS.map((preset, index) => normalizeQuickPreset(preset, index)).filter(Boolean)
)
const quickPresetLoading = ref(false)
const reportTemplateMap = ref({})
const selectedPresetId = ref(null)
const bitcoinHighlights = computed(() => {
  const highlights = bitcoinCanvasProfile.highlights || []
  return [...highlights].sort((a, b) => b.ratio - a.ratio)
})
const selectedBitcoinHighlightKey = ref('')
watchEffect(() => {
  const highlights = bitcoinHighlights.value
  if (!highlights.length) {
    selectedBitcoinHighlightKey.value = ''
    return
  }
  const exists = highlights.some((item) => item.elementKey === selectedBitcoinHighlightKey.value)
  if (!exists) {
    selectedBitcoinHighlightKey.value = highlights[0].elementKey
  }
})
const selectedBitcoinHighlight = computed(() => {
  const highlights = bitcoinHighlights.value
  return highlights.find((item) => item.elementKey === selectedBitcoinHighlightKey.value) || highlights[0] || null
})
function buildRadarChartData(highlights = [], { size = 320, minRadius = 40, maxRadius = 120 } = {}) {
  const ordered = ELEMENTS.map((el) => {
    const found = highlights.find((item) => item.elementKey === el.key)
    return found || { elementKey: el.key, label: el.label, ratio: 0 }
  })
  const center = size / 2
  const angleStep = (Math.PI * 2) / ordered.length
  const polygonPoints = []
  const markers = []
  const axes = []
  ordered.forEach((item, index) => {
    const angle = -Math.PI / 2 + angleStep * index
    const normalized = Math.max(0.1, Math.min(1, item.ratio / 100))
    const radius = minRadius + normalized * (maxRadius - minRadius)
    const x = center + radius * Math.cos(angle)
    const y = center + radius * Math.sin(angle)
    polygonPoints.push(`${x},${y}`)
    markers.push({
      key: item.elementKey,
      x,
      y,
      label: item.label,
      ratio: item.ratio
    })
    axes.push({
      key: item.elementKey,
      label: item.label,
      x2: center + maxRadius * Math.cos(angle),
      y2: center + maxRadius * Math.sin(angle),
      labelX: center + (maxRadius + 24) * Math.cos(angle),
      labelY: center + (maxRadius + 24) * Math.sin(angle)
    })
  })
  return {
    size,
    center,
    maxRadius,
    axes,
    polygonPoints: polygonPoints.join(' '),
    markers
  }
}
const bitcoinRadarChart = computed(() => {
  const items = bitcoinHighlights.value
  if (!items.length) {
    return {
      size: 320,
      center: 160,
      maxRadius: 120,
      axes: [],
      polygonPoints: '',
      markers: []
    }
  }
  const chart = buildRadarChartData(items, { size: 320, minRadius: 40, maxRadius: 120 })
  chart.markers = chart.markers.map((marker) => ({
    ...marker,
    active: selectedBitcoinHighlightKey.value === marker.key
  }))
  return chart
})
function handleBitcoinHighlightSelect(key) {
  if (!key) return
  selectedBitcoinHighlightKey.value = key
}
function getProfileRadarData(profile, options = {}) {
  if (!profile?.elementHighlights?.length) return null
  return buildRadarChartData(profile.elementHighlights, options)
}
const userProfileRadar = computed(() =>
  getProfileRadarData(userVsBitcoinResult.value?.profileSnapshot, { size: 280, minRadius: 50, maxRadius: 115 })
)
const targetProfileRadar = computed(() =>
  getProfileRadarData(targetVsBitcoinResult.value?.profileSnapshot, { size: 280, minRadius: 50, maxRadius: 115 })
)
const teamUserProfileRadar = computed(() =>
  getProfileRadarData(userVsTargetResult.value?.personProfile, { size: 240, minRadius: 35, maxRadius: 95 })
)
const teamTargetProfileRadar = computed(() =>
  getProfileRadarData(userVsTargetResult.value?.targetProfile, { size: 240, minRadius: 35, maxRadius: 95 })
)
const targetNameDisplay = computed(() => activeTargetProfile.value?.entityName || DEFAULT_TARGET_NAME)
const analyzeButtonLabel = computed(() => {
  if (birthdate.value && targetBirthdate.value) {
    return '궁합 분석하기'
  }
  return '사주 분석하기'
})

let currentRunId = 0
const stageDebugDetails = reactive({
  story: [],
  saju: [],
  report: []
})

function registerLoadingStep(key, label) {
  if (!key || !label) return
  const exists = loadingSteps.value.find((step) => step.key === key)
  if (!exists) {
    loadingSteps.value.push({ key, label, status: 'pending', detail: '' })
  }
}

function setLoadingStepStatus(key, status, detail = '') {
  const step = loadingSteps.value.find((item) => item.key === key)
  if (step) {
    step.status = status
    if (detail !== undefined) {
      step.detail = detail
    }
  }
}

function getHighlightTargets() {
  return [
    userVsBitcoinResult.value,
    targetVsBitcoinResult.value,
    userVsTargetResult.value,
    pairCompatibilityResult.value
  ].filter((item) => item && item.narrative)
}

function updateHighlightStageStatus() {
  const targets = getHighlightTargets()
  if (!targets.length) {
    setLoadingStepStatus('highlight_stage', 'pending', '하이라이트 대상 없음')
    return
  }
  const total = targets.length
  const completed = targets.filter((item) => !item.highlightLoading && item.highlightedNarrative).length
  const anyRunning = targets.some((item) => item.highlightLoading)
  const detail = `${completed}/${total} 완료`
  setLoadingStepStatus('highlight_stage', anyRunning ? 'running' : 'done', detail)
}

function resetStageDebugDetails() {
  stageDebugDetails.story = []
  stageDebugDetails.saju = []
  stageDebugDetails.report = []
}

function addStageDebugDetail(stage, detail = {}) {
  if (!stageDebugDetails[stage]) return
  const payload = {
    ...detail,
    timestamp: detail.timestamp || new Date().toISOString()
  }
  stageDebugDetails[stage].push(payload)
}

function prepareLoadingSteps() {
  loadingSteps.value = []
  registerLoadingStep('story_stage', '사용자 정보 가져오기')
  registerLoadingStep('saju_stage', '사주 분석')
  registerLoadingStep('report_stage', '리포트 생성')
  registerLoadingStep('highlight_stage', '하이라이트 생성')
}

function normalizeQuickPreset(preset, index = 0) {
  if (!preset) return null
  const id = preset.id || preset.pk || preset.label || `preset-${index}`
  return {
    id,
    label: preset.label || `빠른 설정 ${index + 1}`,
    birthdate: preset.birthdate || '',
    birthtime: preset.birth_time || preset.birthtime || '',
    gender: preset.gender || '',
    imageUrl: preset.image_url || preset.imageUrl || '',
    storedSaju: preset.stored_saju || preset.storedSaju || '',
    assumeTimeUnknown: preset.assume_time_unknown ?? preset.assumeTimeUnknown ?? (!!(preset.birthdate || preset.birth_time || preset.birthtime) && !preset.birth_time && !preset.birthtime)
  }
}

async function loadReportTemplates() {
  try {
    const templates = await fetchCompatibilityReportTemplates()
    const map = {}
    if (Array.isArray(templates)) {
      templates.forEach((template) => {
        map[template.key] = template.content || ''
      })
    }
    reportTemplateMap.value = map
  } catch (error) {
    console.warn('Failed to load report templates', error)
    reportTemplateMap.value = {}
  }
}

function getReportTemplateContent(key) {
  return reportTemplateMap.value[key] || REPORT_TEMPLATE_DEFAULTS[key] || ''
}

function renderReportTemplate(key, replacements = {}) {
  let content = getReportTemplateContent(key)
  if (!content) return ''

  Object.entries(replacements).forEach(([placeholder, value]) => {
    const safeValue = value ?? ''
    const escapedKey = placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const regex = new RegExp(`{{\\s*${escapedKey}\\s*}}`, 'g')
    content = content.replace(regex, safeValue)
  })

  return content.replace(/{{\s*[A-Z0-9_]+\s*}}/g, '')
}

function buildPresetProfileContext(preset, roleLabel) {
  const name = preset.label || roleLabel || DEFAULT_USER_NAME
  const lines = [
    `이름: ${name}`,
    preset.birthdate ? `생년월일: ${preset.birthdate}` : null,
    preset.birthtime ? `태어난 시간: ${preset.birthtime}` : null,
    preset.gender ? `성별: ${preset.gender === 'male' ? '남성' : '여성'}` : null
  ].filter(Boolean)

  if (preset.storedSaju) {
    lines.push('참고 기록:')
    lines.push(preset.storedSaju)
  }

  return {
    name,
    baseContext: `${roleLabel || '인물'} 기본 정보:\n${lines.join('\n')}`
  }
}

async function runPresetStoryAgent(preset, roleLabel) {
  const { name, baseContext } = buildPresetProfileContext(preset, roleLabel)
  const storyResponse = await runCompatibilityAgent({
    agentKey: 'story_extractor',
    context: baseContext,
    temperature: 0.65
  })
  if (!storyResponse?.ok) {
    throw new Error(storyResponse?.error || '스토리 에이전트 실패')
  }
  return {
    name,
    baseContext,
    story: (storyResponse.narrative || '').trim()
  }
}

async function runPresetSajuAgent({ name, baseContext, story }) {
  const sajuContext = [
    baseContext,
    '',
    '## 추출된 서사',
    story || '별도 서사가 제공되지 않았습니다.',
    '',
    '## 요청',
    `${name}의 사주적 앵커와 비트코인 투자 태도를 분석하세요.`
  ].join('\n')

  const sajuResponse = await runCompatibilityAgent({
    agentKey: 'saju_analysis',
    context: sajuContext,
    temperature: 0.45
  })
  if (!sajuResponse?.ok) {
    throw new Error(sajuResponse?.error || '사주 요약 에이전트 실패')
  }
  return (sajuResponse.narrative || '').trim()
}

function buildFallbackHighlights(text) {
  if (!text) return ''
  const normalized = text.replace(/\r\n?/g, '\n')
  const lines = normalized
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line && !/^#+\s/.test(line))
  if (!lines.length) return ''
  const keywords = ['전략', '리스크', '주의', '핵심', '시너지', '투자', '궁합', '포인트']
  const picked = []
  lines.forEach((line) => {
    if (picked.length >= 4) return
    const normalizedLine = line.replace(/^[-*]\s+/, '')
    if (keywords.some((word) => normalizedLine.includes(word))) {
      picked.push(normalizedLine)
    }
  })
  if (!picked.length) {
    picked.push(lines[0])
  }
  return picked.map((line) => `- ==${line}==`).join('\n')
}

async function highlightNarrativeText(originalText) {
  const trimmed = (originalText || '').trim()
  if (!trimmed) return ''
  const highlightGuide = [
    '## 역할',
    '당신은 사주/궁합 리포트에서 임팩트 있는 구절을 뽑아내는 전문 에디터입니다.',
    '## 목표',
    '원문에서 반드시 기억해야 할 구절만 선택해 <mark> 형광 표시로 감싸세요.',
    '## 출력 형식',
    '- 원문 전체를 그대로 출력하되, 강조할 구절만 <mark>...</mark>로 감싸세요.',
    '- 새로운 문장이나 해설을 추가하지 마세요.',
    '- 하이라이트는 2~4개 구절로 제한하세요.'
  ].join('\n')
  const context = `${highlightGuide}\n\n[원문]\n${trimmed}`
  const response = await runCompatibilityAgent({
    agentKey: 'highlight_story',
    context,
    temperature: 0.15
  })
  if (response?.ok && response?.narrative) {
    return response.narrative.trim()
  }
  return ''
}

async function applyHighlightToResult(result) {
  if (!result?.narrative) {
    if (result) {
      result.highlightLoading = false
    }
    updateHighlightStageStatus()
    return
  }
  result.highlightLoading = true
  updateHighlightStageStatus()
  try {
    const highlighted = await highlightNarrativeText(result.narrative)
    const hasMarks = typeof highlighted === 'string' && /<mark/i.test(highlighted)
    const fallback = !hasMarks ? buildFallbackHighlights(result.narrative) : ''
    if (highlighted && hasMarks) {
      result.highlightedNarrative = highlighted
    } else if (fallback) {
      result.highlightedNarrative = fallback
    }
  } catch (error) {
    console.warn('하이라이트 에이전트 실패', error)
    const fallback = buildFallbackHighlights(result.narrative)
    if (fallback) {
      result.highlightedNarrative = fallback
    }
  } finally {
    result.highlightLoading = false
    updateHighlightStageStatus()
  }
}

async function runStoryAgentForProfile(profile, { roleLabel = '사용자', baseDescription } = {}) {
  if (!profile) return { story: '', prompt: '', provider: '' }
  const lines = [
    `${roleLabel} 기본 정보:`,
    ...profile.facts.map((fact) => `- ${fact}`)
  ]
  if (baseDescription) {
    lines.push(`- 참고 메모: ${baseDescription}`)
  }
  const context = lines.join('\n')
  let response
  try {
    response = await runCompatibilityAgent({
      agentKey: 'story_extractor',
      context,
      temperature: 0.6
    })
  } catch (error) {
    error.agentPrompt = context
    throw error
  }
  if (!response?.ok || !response?.narrative) {
    const err = new Error(response?.error || `${roleLabel} 스토리 응답이 비어 있습니다`)
    err.agentPrompt = context
    throw err
  }
  return {
    story: response.narrative.trim(),
    prompt: context,
    provider: response.model || response.provider || 'llm'
  }
}

function buildPersonTargetMeta() {
  const name = (targetName.value || '').trim() || DEFAULT_TARGET_NAME
  if (!targetBirthdate.value) {
    return {
      profileType: 'person',
      entityName: name,
      label: `${name} 사주 캔버스`,
      summaryHighlight: '생년월일을 입력하면 오행 구성이 계산됩니다.',
      description: '빠른 설정에서 인물을 선택하거나 직접 입력해 사주를 비교하세요.',
      highlights: [],
      agentPrompt: `${name}의 사주를 기준으로 사용자와의 오행 궁합을 비교하라.`
    }
  }
  const [year, month, day] = targetBirthdate.value.split('-').map((v) => Number(v))
  // 정확한 천간·지지 기반 사주 계산
  const sajuData = calculateSajuElement(year, month, day)
  const element = sajuData.element
  const zodiac = calculateZodiacSign(year, month, day)
  const yinYang = calculateYinYang(year, month, day)
  const genderLabel = targetGender.value === 'male' ? '남성' : targetGender.value === 'female' ? '여성' : '성별 미상'
  const timeLabel = targetTimeUnknown.value || !targetBirthtime.value ? '시간 미상' : targetBirthtime.value
  return {
    profileType: 'person',
    entityName: name,
    label: `${name} 사주 캔버스`,
    summaryHighlight: `${zodiac} · ${yinYang}의 기운 · 주력 ${element.label}`,
    description: `${targetBirthdate.value} 출생 ${genderLabel} · ${timeLabel} 기준 분석입니다.`,
    profileNarrative: `${name}의 사주적 앵커는 ${element.label}이며 ${element.summary} 성향이 두드러집니다.`,
    highlights: buildPersonHighlights(element, zodiac, yinYang, timeLabel),
    dominantElementKey: element.key,
    agentPrompt: `${name}의 사주를 기준으로 사용자와의 궁합을 분석하라.`,
    targetZodiac: zodiac,
    targetYinYang: yinYang
  }
}

function buildPersonHighlights(element, zodiac, yinYang, timeLabel) {
  // 주력 오행을 기준으로 5가지 오행 비율 계산
  const elementIndex = ELEMENTS.findIndex(e => e.key === element.key)

  // 기본 비율 설정 (주력 오행이 가장 높고, 나머지는 균등 분배)
  const baseRatio = 15
  const mainRatio = 40
  const ratios = ELEMENTS.map((_, index) => {
    if (index === elementIndex) return mainRatio
    return baseRatio
  })

  // 총합이 100이 되도록 조정
  const total = ratios.reduce((sum, r) => sum + r, 0)
  const normalizedRatios = ratios.map(r => Math.round((r / total) * 100))

  // 반올림 오차 보정
  const currentTotal = normalizedRatios.reduce((sum, r) => sum + r, 0)
  if (currentTotal !== 100) {
    normalizedRatios[elementIndex] += (100 - currentTotal)
  }

  // 오행 5가지 highlights 생성
  const highlights = ELEMENTS.map((el, index) => ({
    label: el.label,
    elementKey: el.key,
    value: el.summary,
    description: el.summary,
    icon: ELEMENT_ICON_MAP[el.key] || '✨',
    ratio: normalizedRatios[index],
    colorClass: ELEMENT_COLOR_CLASS_MAP[el.key] || 'bg-slate-500'
  }))

  return highlights.sort((a, b) => b.ratio - a.ratio)
}

function buildSubjectProfile(payload, { fallbackName, assumeTimeUnknown } = {}) {
  if (!payload) return null
  const name = payload.userName || payload.name || fallbackName || DEFAULT_USER_NAME
  const birthdate = `${payload.year}-${String(payload.month).padStart(2, '0')}-${String(payload.day).padStart(2, '0')}`
  const timeLabel = payload.time ? payload.time : assumeTimeUnknown ? '시간 미상' : '미입력'
  const sajuData = calculateSajuElement(payload.year, payload.month, payload.day)
  const element = sajuData.element
  const zodiac = calculateZodiacSign(payload.year, payload.month, payload.day)
  const yinYang = calculateYinYang(payload.year, payload.month, payload.day)
  const genderLabel = payload.gender === 'male' ? '남성' : payload.gender === 'female' ? '여성' : (payload.gender || '미입력')
  const facts = [
    `생년월일: ${birthdate}`,
    `성별: ${genderLabel}`,
    `띠 / 음양: ${zodiac} / ${yinYang}`,
    `주력 오행: ${element.label} (${element.summary})`,
    `태어난 시간: ${timeLabel}`
  ]
  const elementHighlights = buildPersonHighlights(element, zodiac, yinYang, timeLabel)
  return {
    name,
    birthdate,
    genderLabel,
    zodiac,
    yinYang,
    element,
    elementLabel: element.label,
    elementSummary: element.summary,
    timeLabel,
    facts,
    elementHighlights
  }
}

function buildTargetContext(targetProfileMeta, targetPayload, { targetTimeUnknown } = {}) {
  const targetName = targetProfileMeta?.entityName || '비교 대상'
  if (targetPayload) {
    const profile = buildSubjectProfile(targetPayload, {
      fallbackName: targetName,
      assumeTimeUnknown: targetTimeUnknown
    })
    return {
      name: profile.name,
      title: `${profile.name} 기준선:`,
      lines: profile.facts
    }
  }

  const lines = []
  if (targetProfileMeta?.summaryHighlight) {
    lines.push(`요약: ${targetProfileMeta.summaryHighlight}`)
  }
  if (targetProfileMeta?.description) {
    lines.push(`설명: ${targetProfileMeta.description}`)
  }
  const highlightSummary = (targetProfileMeta?.highlights || [])
    .map((trait) => `${trait.label} ${trait.ratio}%`)
    .join(', ')
  if (highlightSummary) {
    lines.push(`오행 비중: ${highlightSummary}`)
  }

  return {
    name: targetName,
    title: `${targetName} 기준선:`,
    lines
  }
}

function buildAgentContextPayload({
  subjectProfile,
  targetProfileMeta,
  targetPayload,
  subjectDescription,
  targetDescription,
  subjectStory,
  targetStory,
  targetTimeUnknown
}) {
  if (!subjectProfile) return null
  const contextLines = [
    '사용자 기본 정보:',
    ...subjectProfile.facts.map((fact) => `- ${fact}`)
  ]
  if (subjectDescription) contextLines.push(`- 추가 설명: ${subjectDescription}`)
  if (subjectStory) contextLines.push(`- 서사 요약: ${subjectStory}`)

  const targetContext = buildTargetContext(targetProfileMeta, targetPayload, { targetTimeUnknown })
  contextLines.push('', targetContext.title || `${targetContext.name} 기준선:`)
  contextLines.push(...targetContext.lines.map((line) => `- ${line}`))
  if (targetDescription) contextLines.push(`- 대상 설명: ${targetDescription}`)
  if (targetStory) contextLines.push(`- 대상 서사: ${targetStory}`)

  return {
    context: contextLines.filter(Boolean).join('\n'),
    data: {
      user: {
        name: subjectProfile.name,
        birthdate: subjectProfile.birthdate,
        gender: subjectProfile.genderLabel,
        zodiac: subjectProfile.zodiac,
        yinYang: subjectProfile.yinYang,
        element: subjectProfile.elementLabel,
        elementSummary: subjectProfile.elementSummary,
        timeLabel: subjectProfile.timeLabel
      },
      targetProfile: {
        name: targetContext.name,
        summary: targetProfileMeta?.summaryHighlight || '',
        highlights: targetProfileMeta?.highlights || []
      }
    }
  }
}

function buildTeamAgentContextPayload({
  userProfile,
  targetProfile,
  bitcoinProfile,
  userDescription,
  targetDescription,
  userStory,
  targetStory
}) {
  const lines = [
    '인물 A 정보:',
    ...userProfile.facts.map((fact) => `- ${fact}`)
  ]
  if (userDescription) lines.push(`- 추가 설명: ${userDescription}`)
  if (userStory) lines.push(`- 서사: ${userStory}`)

  lines.push('', '인물 B 정보:')
  lines.push(...targetProfile.facts.map((fact) => `- ${fact}`))
  if (targetDescription) lines.push(`- 추가 설명: ${targetDescription}`)
  if (targetStory) lines.push(`- 서사: ${targetStory}`)

  lines.push('', '비트코인 기준선:')
  if (bitcoinProfile.description) lines.push(`- 설명: ${bitcoinProfile.description}`)
  const highlightSummary = (bitcoinProfile.highlights || [])
    .map((trait) => `${trait.label} ${trait.ratio}%`)
    .join(', ')
  if (highlightSummary) lines.push(`- 오행 비중: ${highlightSummary}`)

  return {
    context: lines.filter(Boolean).join('\n'),
    data: {
      members: [
        {
          name: userProfile.name,
          zodiac: userProfile.zodiac,
          yinYang: userProfile.yinYang,
          element: userProfile.elementLabel
        },
        {
          name: targetProfile.name,
          zodiac: targetProfile.zodiac,
          yinYang: targetProfile.yinYang,
          element: targetProfile.elementLabel
        }
      ]
    }
  }
}

async function loadQuickPresets() {
  quickPresetLoading.value = true
  try {
    const presets = await fetchCompatibilityQuickPresets()
    const normalized = (Array.isArray(presets) ? presets : [])
      .map((preset, index) => normalizeQuickPreset(preset, index))
      .filter(Boolean)
    if (normalized.length) {
      quickPresetOptions.value = normalized
    }
  } catch (error) {
    console.warn('Failed to load quick presets', error)
  } finally {
    quickPresetLoading.value = false
  }
}

onMounted(() => {
  loadQuickPresets()
  loadReportTemplates()
})

async function handleCompatibility() {
  if (!birthdate.value && !targetBirthdate.value) {
    errorMessage.value = '최소 하나의 생년월일을 입력해주세요.'
    return
  }
  errorMessage.value = ''
  loading.value = true
  analysisStep.value = 0
  userVsBitcoinResult.value = null
  targetVsBitcoinResult.value = null
  userVsTargetResult.value = null
  pairCompatibilityResult.value = null
  updateHighlightStageStatus()
  const runId = Date.now()
  currentRunId = runId
  resetStageDebugDetails()

  const hasUser = !!birthdate.value
  const hasTarget = !!targetBirthdate.value
  const userPayload = hasUser ? normalizePayload() : null
  const targetPayload = hasTarget ? normalizeTargetPayload() : null
  const targetProfileMeta = activeTargetProfile.value
  prepareLoadingSteps()

  const highlightTasks = []
  const storyStageTargets = []
  if (hasUser) storyStageTargets.push('사용자')
  if (hasTarget) storyStageTargets.push('비교 대상')
  const storyStageDetail = storyStageTargets.length ? `${storyStageTargets.join(' · ')} 정보 수집 중` : '분석 대상 없음'
  setLoadingStepStatus('story_stage', 'running', storyStageDetail)
  if (storyStageTargets.length) {
    await nextTick()
  }

  // 분석할 총 단계 수 결정
  totalSteps.value = 3

  const userProfile = hasUser && userPayload
    ? buildSubjectProfile(userPayload, {
        fallbackName: userPayload.userName || DEFAULT_USER_NAME,
        assumeTimeUnknown: timeUnknown.value
      })
    : null
  const targetProfile = hasTarget && targetPayload
    ? buildSubjectProfile(targetPayload, {
        fallbackName: targetPayload.userName || targetPayload.name || DEFAULT_TARGET_NAME,
        assumeTimeUnknown: targetTimeUnknown.value
      })
    : null

  const storyTasks = []
  if (hasUser && userProfile) {
    storyTasks.push({
      key: 'user',
      label: '사용자',
      profile: userProfile,
      setter: (story) => {
        userStory.value = story
      },
      baseDescription: userDescription.value
    })
  }
  if (hasTarget && targetProfile) {
    storyTasks.push({
      key: 'target',
      label: '비교 대상',
      profile: targetProfile,
      setter: (story) => {
        targetStory.value = story
      },
      baseDescription: targetDescription.value
    })
  }

  if (storyTasks.length) {
    const storyNotes = []
    let completedStories = 0
    const totalStories = storyTasks.length
    const updateStoryProgress = (extra = '') => {
      const base = `${completedStories}/${totalStories}건`
      const prefix = storyNotes.length ? `${storyNotes.join(' / ')} · ` : ''
      const suffix = extra ? ` · ${extra}` : ''
      setLoadingStepStatus('story_stage', 'running', `${prefix}${base}${suffix}`.trim())
    }
    try {
      for (const task of storyTasks) {
        updateStoryProgress(`${task.label} 처리 중`)
        let promptContext = ''
        try {
          const storyResult = await runStoryAgentForProfile(task.profile, {
            roleLabel: task.label,
            baseDescription: task.baseDescription
          })
          promptContext = storyResult.prompt
          task.setter(storyResult.story)
          storyNotes.push(`${task.profile.name}: 완료`)
          completedStories += 1
          updateStoryProgress()
          addStageDebugDetail('story', {
            label: `${task.profile.name} 서사`,
            prompt: storyResult.prompt,
            response: storyResult.story,
            provider: storyResult.provider,
            status: 'ok'
          })
        } catch (storyTaskError) {
          const context = storyTaskError?.agentPrompt || promptContext
          addStageDebugDetail('story', {
            label: `${task.profile.name} 서사`,
            prompt: context,
            error: storyTaskError?.message || '스토리 추출 실패',
            status: 'error'
          })
          throw storyTaskError
        }
      }
      const storyDetail = storyNotes.length ? `스토리 에이전트 완료 · ${storyNotes.join(' / ')}` : '스토리 에이전트 완료'
      setLoadingStepStatus('story_stage', 'done', storyDetail)
    } catch (storyError) {
      console.error('스토리 에이전트 실패:', storyError)
      setLoadingStepStatus('story_stage', 'error', storyError?.message || '스토리 추출 실패')
      setLoadingStepStatus('saju_stage', 'error', '스토리 추출 실패로 중단되었습니다.')
      setLoadingStepStatus('report_stage', 'error', '스토리 추출 실패로 중단되었습니다.')
      errorMessage.value = '스토리 에이전트 요청에 실패했습니다. 잠시 후 다시 시도해주세요.'
      loading.value = false
      analysisStep.value = 0
      return
    }
  } else {
    setLoadingStepStatus('story_stage', 'done', '분석 대상 없음')
  }

  const sajuTasks = []
  if (hasUser && userProfile) sajuTasks.push('사용자')
  if (hasTarget && targetProfile) sajuTasks.push('비교 대상')
  if (hasUser && hasTarget && userProfile && targetProfile) sajuTasks.push('팀')
  const sajuTotal = sajuTasks.length
  let sajuCompleted = 0
  const sajuResults = []

  if (sajuTotal) {
    setLoadingStepStatus('saju_stage', 'running', `${sajuTotal}건 사주 분석 중`)
  } else {
    setLoadingStepStatus('saju_stage', 'done', '사주 분석 대상 없음')
  }

  const updateSajuProgress = () => {
    if (!sajuTotal) return
    const baseCount = `${Math.min(sajuCompleted, sajuTotal)}/${sajuTotal}건`
    const progressLabel = sajuResults.length ? `${sajuResults.join(' / ')} · ${baseCount}` : baseCount
    setLoadingStepStatus('saju_stage', 'running', progressLabel)
  }

  const finalizeSajuStage = () => {
    if (!sajuTotal) {
      setLoadingStepStatus('saju_stage', 'done', '사주 분석 대상 없음')
      return
    }
    const baseCount = `${sajuCompleted}/${sajuTotal}건`
    const detail = sajuResults.length ? `${sajuResults.join(' / ')} · ${baseCount}` : `${baseCount} 완료`
    setLoadingStepStatus('saju_stage', 'done', detail)
  }

  // 비트코인 프로필 생성
  const bitcoinProfile = {
    profileType: 'bitcoin',
    entityName: '비트코인',
    label: '금(金)이 주력인 디지털 금, 수·화가 극단을 이루는 에너지',
    summaryHighlight: '',
    description: '',
    highlights: BITCOIN_HIGHLIGHTS,
    image_url: 'https://upload.wikimedia.org/wikipedia/commons/4/46/Bitcoin.svg',
    dominantElementKey: 'metal',
    agentPrompt: '비트코인의 사주를 기준으로 궁합을 분석하라.'
  }

  const bitcoinPayload = {
    year: 2009,
    month: 1,
    day: 4,
    time: null,
    userName: '비트코인',
    gender: ''
  }

  if (currentRunId !== runId) return

  // LLM 요청 생성 (조건부)
  try {
    // 1. 사용자 vs 비트코인 (사용자가 있을 때만)
    if (hasUser && userProfile) {
      analysisStep.value = 1
      const agentPayload1 = buildAgentContextPayload({
        subjectProfile: userProfile,
        targetProfileMeta: bitcoinProfile,
        targetPayload: bitcoinPayload,
        subjectDescription: userDescription.value,
        subjectStory: userStory.value
      })
      const subjectExtra = userDescription.value ? `\n\n**${userProfile.name} 정보**: ${userDescription.value}` : ''
      const combinedContext1 = [
        agentPayload1.context,
        renderReportTemplate('user_vs_bitcoin', {
          SUBJECT_NAME: userProfile.name,
          SUBJECT_EXTRA: subjectExtra
        })
      ].filter(Boolean).join('\n\n')
      let agentResponse1
      try {
        agentResponse1 = await runCompatibilityAgent({
          agentKey: 'saju_bitcoin',
          context: combinedContext1,
          data: agentPayload1.data,
          temperature: 0.55
        })
      } catch (error) {
        addStageDebugDetail('saju', {
          label: `${userProfile.name} × 비트코인`,
          prompt: combinedContext1,
          error: error?.message || '사용자 사주 분석 실패',
          status: 'error'
        })
        throw new Error(error?.message ? `사용자 사주 분석 실패: ${error.message}` : '사용자 사주 분석 실패')
      }
      if (currentRunId !== runId) return
      if (agentResponse1?.ok && agentResponse1?.narrative) {
        userVsBitcoinResult.value = {
          personName: userProfile.name,
          personImageUrl: userImageUrl.value || '',
          profileFacts: userProfile.facts,
          profileSnapshot: userProfile,
          personStory: userStory.value || '',
          narrative: agentResponse1.narrative,
          highlightedNarrative: '',
          highlightLoading: true,
          agentProvider: agentResponse1.model || agentResponse1.provider || 'llm',
          debugPrompt: combinedContext1
        }
        sajuCompleted += 1
        sajuResults.push('사용자: 완료')
        updateSajuProgress()
        addStageDebugDetail('saju', {
          label: `${userProfile.name} × 비트코인`,
          prompt: combinedContext1,
          response: agentResponse1.narrative,
          provider: agentResponse1.model || agentResponse1.provider || 'llm',
          status: 'ok'
        })
        highlightTasks.push(applyHighlightToResult(userVsBitcoinResult.value, 'user_highlight'))
      } else {
        sajuCompleted += 1
        sajuResults.push('사용자: 실패(응답 없음)')
        updateSajuProgress()
        addStageDebugDetail('saju', {
          label: `${userProfile.name} × 비트코인`,
          prompt: combinedContext1,
          error: agentResponse1?.error || '응답이 비어 있습니다',
          status: 'error'
        })
      }
    }

    // 2. 비교대상 vs 비트코인 (비교대상이 있을 때만)
    if (hasTarget && targetProfile) {
      analysisStep.value = hasUser ? 2 : 1
      const agentPayload2 = buildAgentContextPayload({
        subjectProfile: targetProfile,
        targetProfileMeta: bitcoinProfile,
        targetPayload: bitcoinPayload,
        subjectDescription: targetDescription.value,
        subjectStory: targetStory.value
      })
      const targetExtra = targetDescription.value ? `\n\n**${targetProfile.name} 정보**: ${targetDescription.value}` : ''
      const combinedContext2 = [
        agentPayload2.context,
        renderReportTemplate('user_vs_bitcoin', {
          SUBJECT_NAME: targetProfile.name,
          SUBJECT_EXTRA: targetExtra
        })
      ].filter(Boolean).join('\n\n')
      let agentResponse2
      try {
        agentResponse2 = await runCompatibilityAgent({
          agentKey: 'saju_bitcoin',
          context: combinedContext2,
          data: agentPayload2.data,
          temperature: 0.55
        })
      } catch (error) {
        addStageDebugDetail('saju', {
          label: `${targetProfile.name} × 비트코인`,
          prompt: combinedContext2,
          error: error?.message || '비교 대상 사주 분석 실패',
          status: 'error'
        })
        throw new Error(error?.message ? `비교 대상 사주 분석 실패: ${error.message}` : '비교 대상 사주 분석 실패')
      }
      if (currentRunId !== runId) return
      if (agentResponse2?.ok && agentResponse2?.narrative) {
        targetVsBitcoinResult.value = {
          personName: targetProfile.name,
          personImageUrl: targetImageUrl.value || '',
          profileFacts: targetProfile.facts,
          profileSnapshot: targetProfile,
          personStory: targetStory.value || '',
          narrative: agentResponse2.narrative,
          highlightedNarrative: '',
          highlightLoading: true,
          agentProvider: agentResponse2.model || agentResponse2.provider || 'llm',
          debugPrompt: combinedContext2
        }
        sajuCompleted += 1
        sajuResults.push('비교 대상: 완료')
        updateSajuProgress()
        addStageDebugDetail('saju', {
          label: `${targetProfile.name} × 비트코인`,
          prompt: combinedContext2,
          response: agentResponse2.narrative,
          provider: agentResponse2.model || agentResponse2.provider || 'llm',
          status: 'ok'
        })
        highlightTasks.push(applyHighlightToResult(targetVsBitcoinResult.value, 'target_highlight'))
      } else {
        sajuCompleted += 1
        sajuResults.push('비교 대상: 실패(응답 없음)')
        updateSajuProgress()
        addStageDebugDetail('saju', {
          label: `${targetProfile.name} × 비트코인`,
          prompt: combinedContext2,
          error: agentResponse2?.error || '응답이 비어 있습니다',
          status: 'error'
        })
      }
    }

    // 3. 두 사람 × 비트코인 (팀 궁합 - 둘 다 있을 때만)
    if (hasUser && hasTarget && userProfile && targetProfile) {
      analysisStep.value = 3
      const teamPayload = buildTeamAgentContextPayload({
        userProfile,
        targetProfile,
        bitcoinProfile,
        userDescription: userDescription.value,
        targetDescription: targetDescription.value,
        userStory: userStory.value,
        targetStory: targetStory.value
      })
      const teamInfo = []
      if (userDescription.value) teamInfo.push(`**${userProfile.name}**: ${userDescription.value}`)
      if (targetDescription.value) teamInfo.push(`**${targetProfile.name}**: ${targetDescription.value}`)
      const teamExtra = teamInfo.length > 0 ? `\n\n**두 사람의 정보**:\n${teamInfo.join('\n')}` : ''
      const combinedContext3 = [
        teamPayload.context,
        renderReportTemplate('team_vs_bitcoin', {
          USER_NAME: userProfile.name,
          TARGET_NAME: targetProfile.name,
          TEAM_EXTRA: teamExtra
        })
      ].filter(Boolean).join('\n\n')
      let agentResponse3
      try {
        agentResponse3 = await runCompatibilityAgent({
          agentKey: 'saju_bitcoin',
          context: combinedContext3,
          data: teamPayload.data,
          temperature: 0.5
        })
      } catch (error) {
        addStageDebugDetail('saju', {
          label: `${userProfile.name} & ${targetProfile.name} 팀`,
          prompt: combinedContext3,
          error: error?.message || '팀 궁합 분석 실패',
          status: 'error'
        })
        throw new Error(error?.message ? `팀 궁합 분석 실패: ${error.message}` : '팀 궁합 분석 실패')
      }
      if (currentRunId !== runId) return
      if (agentResponse3?.ok && agentResponse3?.narrative) {
        userVsTargetResult.value = {
          personName: userProfile.name,
          targetPersonName: targetProfile.name,
          personImageUrl: userImageUrl.value || '',
          targetPersonImageUrl: targetImageUrl.value || '',
          personFacts: userProfile.facts,
          targetFacts: targetProfile.facts,
          personStory: userStory.value || '',
          targetStory: targetStory.value || '',
          personProfile: userProfile,
          targetProfile,
          narrative: agentResponse3.narrative,
          highlightedNarrative: '',
          highlightLoading: true,
          agentProvider: agentResponse3.model || agentResponse3.provider || 'llm',
          debugPrompt: combinedContext3
        }
        sajuCompleted += 1
        sajuResults.push('팀: 완료')
        updateSajuProgress()
        addStageDebugDetail('saju', {
          label: `${userProfile.name} & ${targetProfile.name} 팀`,
          prompt: combinedContext3,
          response: agentResponse3.narrative,
          provider: agentResponse3.model || agentResponse3.provider || 'llm',
          status: 'ok'
        })
        highlightTasks.push(applyHighlightToResult(userVsTargetResult.value, 'team_highlight'))
      } else {
        sajuCompleted += 1
        sajuResults.push('팀: 실패(응답 없음)')
        updateSajuProgress()
        addStageDebugDetail('saju', {
          label: `${userProfile.name} & ${targetProfile.name} 팀`,
          prompt: combinedContext3,
          error: agentResponse3?.error || '응답이 비어 있습니다',
          status: 'error'
        })
      }
    }

    finalizeSajuStage()
  } catch (agentError) {
    console.error('궁합 에이전트 호출 실패:', agentError)
    setLoadingStepStatus('saju_stage', 'error', agentError?.message || '사주 분석 실패')
    setLoadingStepStatus('report_stage', 'error', '사주 분석이 끝나지 않아 리포트가 중단되었습니다.')
    errorMessage.value = '궁합 에이전트 요청에 실패했습니다. 잠시 후 다시 시도해주세요.'
    loading.value = false
    analysisStep.value = 0
    return
  }

  if (hasUser && hasTarget && userProfile && targetProfile && userVsBitcoinResult.value && targetVsBitcoinResult.value) {
    try {
      analysisStep.value = 4
      setLoadingStepStatus('report_stage', 'running', '직접 궁합 리포트 생성 중')
      const pairContext = buildPairCompatibilityContext({
        userProfile,
        targetProfile,
        userDescription: userDescription.value,
        targetDescription: targetDescription.value,
        userStoryText: userStory.value,
        targetStoryText: targetStory.value,
        userNarrative: userVsBitcoinResult.value.narrative,
        targetNarrative: targetVsBitcoinResult.value.narrative
      })
      let pairResponse
      try {
        pairResponse = await runCompatibilityAgent({
          agentKey: 'pair_compatibility',
          context: pairContext,
          temperature: 0.5
        })
      } catch (error) {
        addStageDebugDetail('report', {
          label: `${userProfile.name} & ${targetProfile.name}`,
          prompt: pairContext,
          error: error?.message || '직접 궁합 리포트 실패',
          status: 'error'
        })
        const enhancedError = new Error(error?.message ? `직접 궁합 리포트 실패: ${error.message}` : '직접 궁합 리포트 실패')
        enhancedError.__stageLogged = true
        throw enhancedError
      }
      if (currentRunId !== runId) return
      if (pairResponse?.ok && pairResponse?.narrative) {
        const pairResult = {
          narrative: pairResponse.narrative,
          highlightLoading: true,
          agentProvider: pairResponse.model || pairResponse.provider || 'llm',
          debugPrompt: pairContext,
          highlightedNarrative: ''
        }
        pairCompatibilityResult.value = pairResult
        highlightTasks.push(applyHighlightToResult(pairCompatibilityResult.value, 'pair_highlight'))
        setLoadingStepStatus('report_stage', 'done', '직접 궁합 리포트 완료')
        addStageDebugDetail('report', {
          label: `${userProfile.name} & ${targetProfile.name}`,
          prompt: pairContext,
          response: pairResponse.narrative,
          provider: pairResponse.model || pairResponse.provider || 'llm',
          status: 'ok'
        })
      } else {
        setLoadingStepStatus('report_stage', 'error', pairResponse?.error || '직접 궁합 리포트를 생성하지 못했습니다')
        addStageDebugDetail('report', {
          label: `${userProfile.name} & ${targetProfile.name}`,
          prompt: pairContext,
          error: pairResponse?.error || '응답이 비어 있습니다',
          status: 'error'
        })
        pairCompatibilityResult.value = null
        updateHighlightStageStatus()
      }
    } catch (pairError) {
      console.warn('두 사람 궁합 에이전트 실패', pairError)
      setLoadingStepStatus('report_stage', 'error', pairError?.message || '직접 궁합 리포트 생성 실패')
      if (!pairError?.__stageLogged) {
        addStageDebugDetail('report', {
          label: `${userProfile.name} & ${targetProfile.name}`,
          prompt: pairContext,
          error: pairError?.message || '직접 궁합 리포트 생성 실패',
          status: 'error'
        })
      }
      pairCompatibilityResult.value = null
      updateHighlightStageStatus()
    }
  } else {
    setLoadingStepStatus('report_stage', 'done', hasTarget ? '기본 리포트 정리 완료' : '추가 비교 대상 없음')
    pairCompatibilityResult.value = null
    updateHighlightStageStatus()
  }

  await Promise.allSettled(highlightTasks)
  await nextTick()
  loading.value = false
}

function normalizePayload() {
  const [year, month, day] = birthdate.value.split('-').map((v) => Number(v))
  const time = timeUnknown.value || !birthtime.value ? null : birthtime.value
  const name = userName.value?.trim() || DEFAULT_USER_NAME
  return { year, month, day, time, gender: gender.value, userName: name }
}

function normalizeTargetPayload() {
  if (!targetBirthdate.value) return null
  const [year, month, day] = targetBirthdate.value.split('-').map((v) => Number(v))
  const time = targetTimeUnknown.value || !targetBirthtime.value ? null : targetBirthtime.value
  const name = (targetName.value || '').trim() || DEFAULT_TARGET_NAME
  return { year, month, day, time, gender: targetGender.value, userName: name, name }
}

async function applyQuickPreset(preset) {
  if (!preset) return

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
  console.log('🎯 [궁합] 사용자 프리셋 선택:', preset.label)
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

  selectedPresetId.value = preset.id || preset.label
  userName.value = preset.label || DEFAULT_USER_NAME
  gender.value = preset.gender || ''
  birthdate.value = preset.birthdate || ''
  userImageUrl.value = preset.imageUrl || ''
  userDescription.value = ''
  if (preset.birthtime) {
    birthtime.value = preset.birthtime
    timeUnknown.value = false
  } else {
    birthtime.value = ''
    timeUnknown.value = !!preset.assumeTimeUnknown
  }

  // Check if stored_saju exists
  const hasStoredSaju = !!(preset.storedSaju && preset.storedSaju !== '{}')
  console.log('📦 stored_saju 존재 여부:', hasStoredSaju)

  if (hasStoredSaju) {
    console.log('📚 DB에 저장된 사주 데이터 발견')
    console.log('   - 데이터 길이:', preset.storedSaju.length, '자')
    console.log('   - 미리보기:', preset.storedSaju.substring(0, 100) + '...')
  } else {
    console.log('🔢 저장된 사주 없음 - 생년월일로 계산 예정')
    console.log('   - 생년월일:', preset.birthdate)
    console.log('   - 태어난 시간:', preset.birthtime || '미상')
  }

  userStory.value = ''
  userSajuSummary.value = ''
  try {
    console.log('🤖 Story agent 처리 시작...')
    const storyStart = Date.now()
    const storyResult = await runPresetStoryAgent(preset, '사용자')
    const storyDuration = Date.now() - storyStart
    console.log('✅ Story agent 완료 (' + storyDuration + 'ms)')
    console.log('   - 스토리 길이:', storyResult.story.length, '자')
    userStory.value = storyResult.story

    console.log('🤖 Saju agent 처리 시작...')
    const sajuStart = Date.now()
    const sajuSummary = await runPresetSajuAgent(storyResult)
    const sajuDuration = Date.now() - sajuStart
    console.log('✅ Saju agent 완료 (' + sajuDuration + 'ms)')
    console.log('   - 사주 요약 길이:', sajuSummary.length, '자')
    userSajuSummary.value = sajuSummary
    if (sajuSummary) {
      userDescription.value = sajuSummary
    } else if (storyResult.story) {
      userDescription.value = storyResult.story
    }
  } catch (error) {
    console.error('❌ Story/Saju agent 실패:', error)
  }
}

async function applyTargetQuickPreset(preset) {
  if (!preset) return

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
  console.log('🎯 [궁합] 비교 대상 프리셋 선택:', preset.label)
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

  selectedTargetPresetId.value = preset.id || preset.label
  targetName.value = preset.label || DEFAULT_TARGET_NAME
  targetGender.value = preset.gender || ''
  targetBirthdate.value = preset.birthdate || ''
  targetImageUrl.value = preset.imageUrl || ''
  targetDescription.value = ''
  if (preset.birthtime) {
    targetBirthtime.value = preset.birthtime
    targetTimeUnknown.value = false
  } else {
    targetBirthtime.value = ''
    targetTimeUnknown.value = !!preset.assumeTimeUnknown
  }

  // Check if stored_saju exists
  const hasStoredSaju = !!(preset.storedSaju && preset.storedSaju !== '{}')
  console.log('📦 stored_saju 존재 여부:', hasStoredSaju)

  if (hasStoredSaju) {
    console.log('📚 DB에 저장된 사주 데이터 발견')
    console.log('   - 데이터 길이:', preset.storedSaju.length, '자')
    console.log('   - 미리보기:', preset.storedSaju.substring(0, 100) + '...')
  } else {
    console.log('🔢 저장된 사주 없음 - 생년월일로 계산 예정')
    console.log('   - 생년월일:', preset.birthdate)
    console.log('   - 태어난 시간:', preset.birthtime || '미상')
  }

  targetStory.value = ''
  targetSajuSummary.value = ''
  try {
    console.log('🤖 Story agent 처리 시작 (비교 대상)...')
    const storyStart = Date.now()
    const storyResult = await runPresetStoryAgent(preset, '비교 대상')
    const storyDuration = Date.now() - storyStart
    console.log('✅ Story agent 완료 (' + storyDuration + 'ms)')
    console.log('   - 스토리 길이:', storyResult.story.length, '자')
    targetStory.value = storyResult.story

    console.log('🤖 Saju agent 처리 시작 (비교 대상)...')
    const sajuStart = Date.now()
    const sajuSummary = await runPresetSajuAgent(storyResult)
    const sajuDuration = Date.now() - sajuStart
    console.log('✅ Saju agent 완료 (' + sajuDuration + 'ms)')
    console.log('   - 사주 요약 길이:', sajuSummary.length, '자')
    targetSajuSummary.value = sajuSummary
    if (sajuSummary) {
      targetDescription.value = sajuSummary
    } else if (storyResult.story) {
      targetDescription.value = storyResult.story
    }
  } catch (error) {
    console.error('❌ Story/Saju agent 실패:', error)
  }
}

function resetPresetSelection() {
  selectedPresetId.value = null
  userName.value = DEFAULT_USER_NAME
  birthdate.value = ''
  birthtime.value = ''
  gender.value = ''
  timeUnknown.value = false
  userImageUrl.value = ''
  userDescription.value = ''
  userStory.value = ''
  userSajuSummary.value = ''
}

function resetTargetPresetSelection() {
  selectedTargetPresetId.value = null
  targetName.value = DEFAULT_TARGET_NAME
  targetBirthdate.value = ''
  targetBirthtime.value = ''
  targetGender.value = ''
  targetTimeUnknown.value = false
  targetImageUrl.value = ''
  targetDescription.value = ''
  targetStory.value = ''
  targetSajuSummary.value = ''
}

// ===== 천간·지지 기반 정확한 사주 계산 =====
const HEAVENLY_STEMS = [
  { key: 'gap', label: '갑(甲)', element: 'wood', yinYang: 'yang' },
  { key: 'eul', label: '을(乙)', element: 'wood', yinYang: 'yin' },
  { key: 'byeong', label: '병(丙)', element: 'fire', yinYang: 'yang' },
  { key: 'jeong', label: '정(丁)', element: 'fire', yinYang: 'yin' },
  { key: 'mu', label: '무(戊)', element: 'earth', yinYang: 'yang' },
  { key: 'gi', label: '기(己)', element: 'earth', yinYang: 'yin' },
  { key: 'gyeong', label: '경(庚)', element: 'metal', yinYang: 'yang' },
  { key: 'sin', label: '신(辛)', element: 'metal', yinYang: 'yin' },
  { key: 'im', label: '임(壬)', element: 'water', yinYang: 'yang' },
  { key: 'gye', label: '계(癸)', element: 'water', yinYang: 'yin' }
]

const EARTHLY_BRANCHES = [
  { key: 'ja', label: '자(子)', element: 'water', zodiac: '쥐', season: 'winter' },
  { key: 'chuk', label: '축(丑)', element: 'earth', zodiac: '소', season: 'winter' },
  { key: 'in', label: '인(寅)', element: 'wood', zodiac: '호랑이', season: 'spring' },
  { key: 'myo', label: '묘(卯)', element: 'wood', zodiac: '토끼', season: 'spring' },
  { key: 'jin', label: '진(辰)', element: 'earth', zodiac: '용', season: 'spring' },
  { key: 'sa', label: '사(巳)', element: 'fire', zodiac: '뱀', season: 'summer' },
  { key: 'o', label: '오(午)', element: 'fire', zodiac: '말', season: 'summer' },
  { key: 'mi', label: '미(未)', element: 'earth', zodiac: '양', season: 'summer' },
  { key: 'sin_branch', label: '신(申)', element: 'metal', zodiac: '원숭이', season: 'autumn' },
  { key: 'yu', label: '유(酉)', element: 'metal', zodiac: '닭', season: 'autumn' },
  { key: 'sul', label: '술(戌)', element: 'earth', zodiac: '개', season: 'autumn' },
  { key: 'hae', label: '해(亥)', element: 'water', zodiac: '돼지', season: 'winter' }
]

/**
 * 년주(年柱)의 천간·지지를 계산
 * 입춘(立春) 기준으로 년도 경계 조정
 */
function calculateYearPillar(year, month, day) {
  // 입춘 기준 년도 조정 (2월 4일경이 경계)
  let sajuYear = year
  if (month === 1 || (month === 2 && day <= 3)) {
    sajuYear = year - 1
  }

  // 경자년(1900년)을 기준(36번째)으로 60갑자 사이클 계산
  // 1900 = 경자년 (庚子年) = stem:6(경), branch:0(자)
  const yearIndex = (sajuYear - 1900 + 36) % 60
  const stemIndex = yearIndex % 10
  const branchIndex = yearIndex % 12

  return {
    stem: HEAVENLY_STEMS[stemIndex],
    branch: EARTHLY_BRANCHES[branchIndex],
    year: sajuYear
  }
}

/**
 * 일간(日干)의 오행을 추출
 * 비트코인 맥시멀리스트 관점: 천간이 핵심
 */
function calculateDayElement(year, month, day) {
  // 정확한 일진 계산은 복잡하므로, 년주 천간을 기본으로 사용
  // 추후 개선 가능
  const yearPillar = calculateYearPillar(year, month, day)
  return yearPillar.stem
}

/**
 * 사주 오행 구성 계산 (천간·지지 종합)
 */
function calculateSajuElement(year, month, day) {
  const yearPillar = calculateYearPillar(year, month, day)
  const dayStem = calculateDayElement(year, month, day)

  // 천간의 오행을 주력으로 사용 (맥시멀리스트 해석)
  const elementKey = dayStem.element
  const element = ELEMENTS.find(e => e.key === elementKey) || ELEMENTS[0]

  return {
    element,
    yearPillar,
    dayStem,
    pillars: {
      year: `${yearPillar.stem.label}${yearPillar.branch.label}`,
      yearStem: yearPillar.stem,
      yearBranch: yearPillar.branch
    }
  }
}

function calculateZodiacSign(year, month, day) {
  // 사주에서는 입춘(2월 4일경)을 기준으로 년도를 나눕니다
  // 양력 1월 1일 ~ 2월 3일 사이는 전년도 띠로 계산
  let zodiacYear = year
  if (month === 1 || (month === 2 && day <= 3)) {
    zodiacYear = year - 1
  }

  // 띠 계산: 자(쥐)는 (year - 4) % 12 === 0
  const zodiacIndex = (zodiacYear - 4) % 12
  return ZODIAC_SIGNS[zodiacIndex >= 0 ? zodiacIndex : zodiacIndex + 12]
}

function calculateYinYang(year, month, day) {
  // 음양도 입춘 기준으로 계산
  let zodiacYear = year
  if (month === 1 || (month === 2 && day <= 3)) {
    zodiacYear = year - 1
  }
  return zodiacYear % 2 === 0 ? '양' : '음'
}





function buildPairCompatibilityContext({
  userProfile,
  targetProfile,
  userDescription,
  targetDescription,
  userStoryText,
  targetStoryText,
  userNarrative,
  targetNarrative
}) {
  const formatPerson = (label, profile, desc, story, narrative) => {
    const lines = [
      `# ${label}: ${profile.name}`,
      ...profile.facts.map((fact) => `- ${fact}`),
      desc ? `- 사주 요약: ${desc}` : '- 사주 요약: 정보 없음',
      story ? `- 서사: ${story}` : null,
      narrative ? `- 비트코인 분석: ${narrative}` : null
    ]
    return lines.filter(Boolean).join('\n')
  }

  return [
    formatPerson('인물 A', userProfile, userDescription, userStoryText, userNarrative),
    '',
    formatPerson('인물 B', targetProfile, targetDescription, targetStoryText, targetNarrative),
    '',
    '## 요청',
    '위 정보를 기반으로 두 사람이 서로에게 미치는 영향과 협업 전략, 주의 신호를 분석하세요.',
    '',
    '## 출력 지침',
    '- 결과는 반드시 마크다운 문법을 사용하고, 각 섹션은 `##` 헤딩으로 시작하세요.',
    '- 최소 3개 섹션(관계 다이내믹, 투자 전략, 리스크 신호)을 포함하고, 필요 시 표나 불릿을 사용해 상세히 기술하세요.',
    '- 근거가 되는 사주/스토리 인용 문장은 **굵게** 표시하세요.'
  ].join('\n')
}

function formatCardDate(dateStr) {
  if (!dateStr) return ''
  const [year, month, day] = dateStr.split('-')
  return `${year}년 ${month}월 ${day}일`
}

function renderMarkdown(text) {
  if (!text) return ''
  const normalized = text.replace(/\r\n?/g, '\n')
  const lines = normalized.split('\n')
  const htmlParts = []
  let paragraphBuffer = []
  let unorderedBuffer = []
  let orderedBuffer = []
  let blockquoteBuffer = []
  let codeBuffer = []
  let tableBuffer = []
  let inCodeBlock = false
  let codeLanguage = ''

  const escapeHtml = (value = '') =>
    value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

  const formatInline = (value) => {
    if (!value) return ''
    let formatted = escapeHtml(value)
    const codePlaceholders = []
    formatted = formatted.replace(/`([^`]+)`/g, (_, code) => {
      const placeholder = `__INLINE_CODE_${codePlaceholders.length}__`
      codePlaceholders.push(`<code>${escapeHtml(code)}</code>`)
      return placeholder
    })
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    formatted = formatted.replace(/__(.+?)__/g, '<strong>$1</strong>')
    formatted = formatted.replace(/\*(?!\*)([^*]+)\*(?!\*)/g, '<em>$1</em>')
    formatted = formatted.replace(/_(?!_)([^_]+)_(?!_)/g, '<em>$1</em>')
    formatted = formatted.replace(/==([^=]+)==/g, '<mark class="md-highlight">$1</mark>')
    formatted = formatted.replace(/&lt;mark&gt;/g, '<mark class="md-highlight">')
    formatted = formatted.replace(/&lt;\/mark&gt;/g, '</mark>')
    formatted = formatted.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    codePlaceholders.forEach((snippet, index) => {
      formatted = formatted.replace(`__INLINE_CODE_${index}__`, snippet)
    })
    return formatted
  }

  const flushParagraph = () => {
    if (paragraphBuffer.length) {
      const content = formatInline(paragraphBuffer.join(' '))
      htmlParts.push(`<p>${content}</p>`)
      paragraphBuffer = []
    }
  }

  const flushUnordered = () => {
    if (unorderedBuffer.length) {
      const items = unorderedBuffer.map((item) => `<li>${formatInline(item)}</li>`).join('')
      htmlParts.push(`<ul>${items}</ul>`)
      unorderedBuffer = []
    }
  }

  const flushOrdered = () => {
    if (orderedBuffer.length) {
      const items = orderedBuffer.map((item) => `<li>${formatInline(item)}</li>`).join('')
      htmlParts.push(`<ol>${items}</ol>`)
      orderedBuffer = []
    }
  }

  const flushLists = () => {
    flushUnordered()
    flushOrdered()
  }

  const flushBlockquote = () => {
    if (!blockquoteBuffer.length) return
    const content = blockquoteBuffer.map((line) => formatInline(line)).join('<br />')
    htmlParts.push(`<blockquote>${content}</blockquote>`)
    blockquoteBuffer = []
  }

  const isTableLine = (line) => /^\s*\|.*\|\s*$/.test(line)
  const isDividerLine = (line) => /^\s*\|?(?:\s*:?-+:?\s*\|)+\s*$/.test(line)

  const parseTableCells = (line) =>
    line
      .trim()
      .replace(/^\||\|$/g, '')
      .split('|')
      .map((cell) => cell.trim())

  const flushTable = () => {
    if (!tableBuffer.length) return
    const rows = tableBuffer.map((line) => line.trim()).filter(Boolean)
    if (!rows.length) {
      tableBuffer = []
      return
    }

    if (rows.length < 2 || !isDividerLine(rows[1])) {
      rows.forEach((line) => {
        htmlParts.push(`<p>${formatInline(line)}</p>`)
      })
      tableBuffer = []
      return
    }

    const headerCells = parseTableCells(rows[0]).map((cell) => formatInline(cell))
    let alignments = []
    let dataRows = rows.slice(1)

    if (dataRows.length && isDividerLine(dataRows[0])) {
      const dividerCells = parseTableCells(dataRows[0])
      alignments = dividerCells.map((cell) => {
        const raw = cell.trim()
        if (/^:-+:$/.test(raw)) return 'center'
        if (/^:-+$/.test(raw)) return 'left'
        if (/^-+:$/.test(raw)) return 'right'
        return 'left'
      })
      dataRows = dataRows.slice(1)
    }

    const bodyRows = dataRows.map((line) => parseTableCells(line).map((cell) => formatInline(cell)))

    const buildCell = (tag, content, index) => {
      const align = alignments[index] || 'left'
      return `<${tag} style="text-align:${align}">${content}</${tag}>`
    }

    let tableHtml = '<table>'
    tableHtml += '<thead><tr>'
    headerCells.forEach((cell, idx) => {
      tableHtml += buildCell('th', cell, idx)
    })
    tableHtml += '</tr></thead>'
    if (bodyRows.length) {
      tableHtml += '<tbody>'
      bodyRows.forEach((row) => {
        tableHtml += '<tr>'
        row.forEach((cell, idx) => {
          tableHtml += buildCell('td', cell, idx)
        })
        tableHtml += '</tr>'
      })
      tableHtml += '</tbody>'
    }
    tableHtml += '</table>'
    htmlParts.push(tableHtml)
    tableBuffer = []
  }

  const flushCodeBlock = () => {
    if (!codeBuffer.length) return
    const langClass = codeLanguage ? ` class="language-${codeLanguage}"` : ''
    const codeContent = codeBuffer.join('\n')
    htmlParts.push(`<pre><code${langClass}>${escapeHtml(codeContent)}</code></pre>`)
    codeBuffer = []
    codeLanguage = ''
  }

  const specialHeadingPatterns = [
    /^프로필\s*브리핑$/i,
    /^커리어\s*&\s*재물$/i,
    /^인간관계$/i,
    /^비트코인\s*전략\s*체크리스트$/i,
    /.+와\s*비트코인의\s*궁합$/i,
    /.+×\s*비트코인\s*궁합$/i,
  ]

  for (const rawLine of lines) {
    const trimmedLine = rawLine.trim()

    if (/^```/.test(trimmedLine)) {
      if (inCodeBlock) {
        flushCodeBlock()
        inCodeBlock = false
      } else {
        flushParagraph()
        flushLists()
        flushBlockquote()
        flushTable()
        inCodeBlock = true
        codeLanguage = trimmedLine.replace(/^```/, '').trim()
        codeBuffer = []
      }
      continue
    }

    if (inCodeBlock) {
      codeBuffer.push(rawLine)
      continue
    }

    if (!trimmedLine) {
      flushParagraph()
      flushLists()
      flushBlockquote()
      flushTable()
      continue
    }

    if (/^(-{3,}|_{3,}|\*{3,})$/.test(trimmedLine)) {
      flushParagraph()
      flushLists()
      flushBlockquote()
      flushTable()
      htmlParts.push('<hr />')
      continue
    }

    if (trimmedLine.startsWith('>')) {
      flushParagraph()
      flushLists()
      flushTable()
      blockquoteBuffer.push(trimmedLine.replace(/^>\s?/, '').trimStart())
      continue
    }

    if (isTableLine(trimmedLine)) {
      flushParagraph()
      flushLists()
      flushBlockquote()
      tableBuffer.push(trimmedLine)
      continue
    } else if (tableBuffer.length) {
      flushTable()
    }

    if (/^[-*+]\s+/.test(trimmedLine)) {
      flushParagraph()
      if (orderedBuffer.length) flushOrdered()
      if (tableBuffer.length) flushTable()
      unorderedBuffer.push(trimmedLine.replace(/^[-*+]\s+/, ''))
      continue
    }

    if (/^\d+\.\s+/.test(trimmedLine)) {
      flushParagraph()
      if (unorderedBuffer.length) flushUnordered()
      if (tableBuffer.length) flushTable()
      orderedBuffer.push(trimmedLine.replace(/^\d+\.\s+/, ''))
      continue
    }

    flushLists()
    if (tableBuffer.length) {
      flushTable()
    }

    const specialHeading = specialHeadingPatterns.some((pattern) => pattern.test(trimmedLine))
    if (specialHeading) {
      flushParagraph()
      flushTable()
      const content = formatInline(trimmedLine)
      htmlParts.push(`<h3 class="highlight-heading">${content}</h3>`)
      continue
    }

    const headingMatch = trimmedLine.match(/^(#{1,3})\s+(.*)$/)
    if (headingMatch) {
      flushParagraph()
      flushTable()
      const level = headingMatch[1].length
      const content = formatInline(headingMatch[2])
      const tag = level === 1 ? 'h2' : level === 2 ? 'h3' : 'h4'
      htmlParts.push(`<${tag}>${content}</${tag}>`)
      continue
    }

    if (blockquoteBuffer.length) {
      flushBlockquote()
    }

    paragraphBuffer.push(trimmedLine)
  }

  flushParagraph()
  flushLists()
  flushBlockquote()
  if (inCodeBlock) {
    flushCodeBlock()
  }
  if (tableBuffer.length) {
    flushTable()
  }
  return htmlParts.join('')
}
</script>

<style scoped>
/* Preset Card Container - allows cards to overflow on hover */
.preset-card-container {
  overflow: visible !important;
}

/* Section wrapper to prevent clipping */
section.space-y-6 {
  overflow: visible;
}

/* Scroll container with fade effect */
.scroll-container {
  position: relative;
  -webkit-overflow-scrolling: touch;
}

.scroll-container::after {
  content: none;
}

/* Scroll hint arrow */
.scroll-hint {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 20;
  pointer-events: none;
  animation: scrollBounce 2s ease-in-out infinite;
  background: white;
  border-radius: 50%;
  padding: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.profile-radar {
  width: 280px;
  min-width: 220px;
  max-width: 320px;
  padding: 0.75rem;
  overflow: visible;
}

.profile-radar-svg {
  width: 100%;
  height: auto;
  overflow: visible;
}

@media (max-width: 640px) {
  .profile-radar {
    width: 100%;
    min-width: 0;
  }
}

.highlight-panel ul {
  margin: 0;
  padding-left: 1.25rem;
  list-style: disc;
}

.highlight-panel ol {
  margin: 0;
  padding-left: 1.25rem;
  list-style: decimal;
}

:deep(.highlight-panel h3.highlight-heading) {
  font-size: 1.125rem;
  font-weight: 700;
  color: #92400e;
  margin-top: 1.25rem;
  margin-bottom: 0.4rem;
}

:deep(.highlight-panel h3.highlight-heading:first-of-type) {
  margin-top: 0.75rem;
}

.markdown-highlight p {
  margin-bottom: 0.5rem;
}

.markdown-highlight ul,
.markdown-highlight ol {
  margin-top: 0.25rem;
  margin-bottom: 0.25rem;
}

.md-highlight {
  background: linear-gradient(120deg, rgba(254, 240, 138, 0.9) 0%, rgba(253, 232, 138, 0.95) 100%);
  color: #7c3e0a;
  padding: 0 0.2em;
  border-radius: 0.35rem;
  box-shadow: 0 0 0 1px rgba(251, 191, 36, 0.5);
}

.radar-polygon {
  stroke-dasharray: 600;
  stroke-dashoffset: 600;
  animation: radarDraw 1.2s ease-out forwards;
}

.radar-point {
  transform-origin: center;
  transition: transform 0.2s ease, fill 0.2s ease;
}

.radar-point:hover {
  transform: scale(1.15);
}

@keyframes scrollBounce {
  0%, 100% {
    transform: translateY(-50%) translateX(0);
    opacity: 0.7;
  }
  50% {
    transform: translateY(-50%) translateX(5px);
    opacity: 1;
  }
}

@keyframes radarDraw {
  to {
    stroke-dashoffset: 0;
  }
}

/* Yu-Gi-Oh Card Styles */
.yugioh-card {
  width: 180px;
  min-height: 260px;
  perspective: 1000px;
  transition: transform 0.3s ease, z-index 0s;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}

.yugioh-card:hover {
  transform: translateY(-8px) scale(1.05);
  z-index: 100;
}

.card-inner {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: inherit;
  border-radius: 12px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
  overflow: visible;
  display: flex;
  flex-direction: column;
}

.card-border {
  display: none;
}

.card-content {
  position: relative;
  display: flex;
  flex-direction: column;
  flex: 1;
  padding: 12px;
  z-index: 1;
}

.card-header {
  text-align: center;
  margin-bottom: 8px;
  flex-shrink: 0;
}

.card-name {
  font-size: 0.95rem;
  font-weight: 700;
  color: #0f172a;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-image {
  width: 100%;
  height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #cbd5e1 0%, #94a3b8 100%);
  border-radius: 6px;
  margin-bottom: 8px;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  flex-shrink: 0;
}

.card-image-placeholder {
  font-size: 3rem;
  opacity: 0.6;
}

.card-image-actual {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-info {
  background: transparent;
  border-radius: 6px;
  padding: 0;
  font-size: 0.75rem;
  text-align: center;
  border: 0;
  flex-shrink: 0;
  min-height: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: center;
}

.card-birthdate {
  font-weight: 600;
  color: #1e293b;
  font-size: 0.75rem;
}

.card-time,
.card-gender {
  font-size: 0.7rem;
  color: #64748b;
  margin-top: 2px;
}

.card-selected-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 6px;
  padding: 4px 8px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  font-size: 0.65rem;
  font-weight: 600;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(16, 185, 129, 0.3);
}

/* Preset Card Styles */
.preset-card {
  width: 180px;
  min-height: 280px;
  height: auto;
  position: relative;
  z-index: 1;
}

.preset-card:hover {
  z-index: 100;
}

.preset-card-selected {
  z-index: 2;
}

.preset-card-selected .card-inner {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  box-shadow: 0 8px 16px rgba(16, 185, 129, 0.25);
}

.card-selected {
  animation: cardGlow 2s ease-in-out infinite;
}

@keyframes cardGlow {
  0%, 100% {
    filter: drop-shadow(0 0 4px rgba(99, 102, 241, 0.3));
  }
  50% {
    filter: drop-shadow(0 0 12px rgba(99, 102, 241, 0.6));
  }
}

@keyframes shimmer {
  from { transform: translateX(-100%); }
  to { transform: translateX(100%); }
}

.animate-shimmer {
  animation: shimmer 1.5s infinite linear;
}

.plus-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.4;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.2);
  }
}


.compatibility-content ul,
.compatibility-content ol {
  margin: 0 0 1rem 1rem;
  padding-left: 1rem;
  color: #0f172a;
  font-size: 0.95rem;
  line-height: 1.6;
}

.compatibility-content li {
  margin-bottom: 0.5rem;
}

.compatibility-content code {
  background-color: #f1f5f9;
  padding: 0.1rem 0.25rem;
  border-radius: 0.25rem;
  font-size: 0.9em;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
}

</style>
