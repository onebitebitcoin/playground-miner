<template>
  <div class="space-y-6">
    <section class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 space-y-6">
      <div class="flex flex-col gap-3">
        <div class="flex items-start justify-between gap-4">
          <div class="flex-1">
            <p class="text-sm font-semibold text-slate-500 uppercase tracking-wider">비트코인의 사주는?</p>
            <h2 class="text-xl font-bold text-slate-900 mt-1">금(金)이 주력인 디지털 금, 수·화가 극단을 이루는 에너지</h2>
            <p class="text-sm text-slate-500 mt-2">
              고정 공급과 변동성, 네트워크 속성을 오행으로 환산해 구성한 비트코인의 기준선입니다.
            </p>
          </div>
        </div>
      </div>
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        <div
          v-for="trait in bitcoinHighlights"
          :key="trait.label"
          class="rounded-2xl border border-slate-200 bg-slate-50 p-4 flex flex-col gap-3"
        >
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <span class="text-2xl">{{ trait.icon }}</span>
              <p class="text-sm font-bold text-slate-900">{{ trait.label }}</p>
            </div>
            <span class="text-lg font-black text-slate-900">{{ trait.ratio }}%</span>
          </div>
          <div class="w-full bg-slate-200 rounded-full h-2">
            <div
              class="h-2 rounded-full transition-all duration-300"
              :class="trait.colorClass"
              :style="{ width: `${trait.ratio}%` }"
            ></div>
          </div>
          <p class="text-xs font-semibold text-slate-700">{{ trait.value }}</p>
          <p class="text-xs text-slate-600 leading-relaxed">{{ trait.description }}</p>
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
                        <div v-if="preset.description" class="card-description">{{ preset.description }}</div>
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
                        <div v-if="preset.description" class="card-description">{{ preset.description }}</div>
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
          <svg v-if="loading" class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
          <span>{{ loading ? loadingMessage : analyzeButtonLabel }}</span>
        </button>
        <div v-if="loading" class="w-full bg-slate-100 rounded-full h-3 overflow-hidden shadow-inner mt-1 relative">
          <div
            class="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 transition-all duration-500 ease-out relative"
            :style="{ width: `${(analysisStep / totalSteps) * 100}%` }"
          >
            <div class="absolute inset-0 w-full h-full bg-white/30 animate-shimmer"></div>
          </div>
        </div>
        <p v-if="errorMessage" class="text-xs text-rose-500">{{ errorMessage }}</p>
      </div>
      <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 space-y-6">
                  <div>
                    <h3 class="text-base font-semibold text-slate-900">궁합 리포트</h3>
                                <p class="text-sm text-slate-500 mt-1 flex items-center gap-2">
                                  <span>세 가지 관점에서 궁합을 분석합니다</span>
                                  <span 
                                    v-if="userVsBitcoinResult?.agentProvider" 
                                    class="text-xs text-slate-400 cursor-pointer hover:text-slate-600 hover:underline"
                                    @click="openPromptDebug"
                                    title="프롬프트 보기"
                                  >
                                    (Powered by {{ userVsBitcoinResult.agentProvider }})
                                  </span>
                                </p>                  </div>
        <div v-if="!userVsBitcoinResult && !targetVsBitcoinResult && !userVsTargetResult" class="text-center py-12">
          <p class="text-sm text-slate-500">{{ analyzeButtonLabel }}를 눌러 궁합을 확인하세요.</p>
        </div>

        <!-- 1. 사용자 vs 비트코인 -->
        <div v-if="userVsBitcoinResult" class="border-t border-slate-200 pt-6 space-y-4">
          <h4 class="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
            <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-orange-500 text-white text-xs font-bold">1</span>
            <span>{{ userVsBitcoinResult.personName }} × 비트코인 궁합</span>
            <span class="ml-auto text-4xl font-black text-orange-600">{{ userVsBitcoinResult.score }}점</span>
          </h4>

          <div class="rounded-2xl border border-slate-200 bg-white p-5">
            <div class="flex gap-6 items-start">
              <div class="flex-shrink-0">
                <div class="w-24 h-24 rounded-xl overflow-hidden border-2 border-slate-200 bg-slate-100 flex items-center justify-center">
                  <img v-if="userVsBitcoinResult.personImageUrl" :src="userVsBitcoinResult.personImageUrl" :alt="userVsBitcoinResult.personName" class="w-full h-full object-cover" />
                  <span v-else class="text-4xl">👤</span>
                </div>
              </div>
              <div class="flex-1 space-y-3">
                <div v-for="highlight in userVsBitcoinResult.user.highlights" :key="highlight.label" class="space-y-1">
                  <div class="flex items-center justify-between text-sm">
                    <div class="flex items-center gap-2">
                      <span class="text-base">{{ highlight.icon }}</span>
                      <span class="font-semibold text-slate-900">{{ highlight.label }}</span>
                    </div>
                    <span class="text-sm font-bold text-slate-700">{{ highlight.ratio }}%</span>
                  </div>
                  <div class="w-full bg-slate-200 rounded-full h-1.5">
                    <div class="h-1.5 rounded-full transition-all duration-500" :class="highlight.colorClass" :style="{ width: `${highlight.ratio}%` }"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="rounded-2xl border border-slate-200 p-5 bg-slate-50">
            <div class="prose prose-slate max-w-none prose-headings:text-slate-900 prose-h2:text-lg prose-h2:font-bold prose-h2:mt-6 prose-h2:mb-3 prose-h2:first:mt-0 prose-p:text-sm prose-p:text-slate-700 prose-p:leading-relaxed prose-p:mb-3 prose-strong:text-slate-900 prose-strong:font-semibold compatibility-content select-text">
              <div v-html="renderMarkdown(userVsBitcoinResult.narrative)"></div>
            </div>
          </div>

          <div class="rounded-xl border border-amber-200 p-3 bg-amber-50">
            <p class="text-xs font-semibold text-amber-900 mb-1">⚠️ 리스크 메모</p>
            <p class="text-xs text-amber-800 leading-relaxed">{{ userVsBitcoinResult.riskNote }}</p>
          </div>
        </div>

        <!-- 2. 비교대상 vs 비트코인 -->
        <div v-if="targetVsBitcoinResult" class="border-t border-slate-200 pt-6 space-y-4">
          <h4 class="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
            <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-orange-500 text-white text-xs font-bold">2</span>
            <span>{{ targetVsBitcoinResult.personName }} × 비트코인 궁합</span>
            <span class="ml-auto text-4xl font-black text-orange-600">{{ targetVsBitcoinResult.score }}점</span>
          </h4>

          <div class="rounded-2xl border border-slate-200 bg-white p-5">
            <div class="flex gap-6 items-start">
              <div class="flex-shrink-0">
                <div class="w-24 h-24 rounded-xl overflow-hidden border-2 border-slate-200 bg-slate-100 flex items-center justify-center">
                  <img v-if="targetVsBitcoinResult.personImageUrl" :src="targetVsBitcoinResult.personImageUrl" :alt="targetVsBitcoinResult.personName" class="w-full h-full object-cover" />
                  <span v-else class="text-4xl">👤</span>
                </div>
              </div>
              <div class="flex-1 space-y-3">
                <div v-for="highlight in targetVsBitcoinResult.user.highlights" :key="highlight.label" class="space-y-1">
                  <div class="flex items-center justify-between text-sm">
                    <div class="flex items-center gap-2">
                      <span class="text-base">{{ highlight.icon }}</span>
                      <span class="font-semibold text-slate-900">{{ highlight.label }}</span>
                    </div>
                    <span class="text-sm font-bold text-slate-700">{{ highlight.ratio }}%</span>
                  </div>
                  <div class="w-full bg-slate-200 rounded-full h-1.5">
                    <div class="h-1.5 rounded-full transition-all duration-500" :class="highlight.colorClass" :style="{ width: `${highlight.ratio}%` }"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="rounded-2xl border border-slate-200 p-5 bg-slate-50">
            <div class="prose prose-slate max-w-none prose-headings:text-slate-900 prose-h2:text-lg prose-h2:font-bold prose-h2:mt-6 prose-h2:mb-3 prose-h2:first:mt-0 prose-p:text-sm prose-p:text-slate-700 prose-p:leading-relaxed prose-p:mb-3 prose-strong:text-slate-900 prose-strong:font-semibold compatibility-content select-text">
              <div v-html="renderMarkdown(targetVsBitcoinResult.narrative)"></div>
            </div>
          </div>

          <div class="rounded-xl border border-amber-200 p-3 bg-amber-50">
            <p class="text-xs font-semibold text-amber-900 mb-1">⚠️ 리스크 메모</p>
            <p class="text-xs text-amber-800 leading-relaxed">{{ targetVsBitcoinResult.riskNote }}</p>
          </div>
        </div>

        <!-- 3. 사용자 vs 비교대상 -->
        <div v-if="userVsTargetResult" class="border-t border-slate-200 pt-6 space-y-4">
          <h4 class="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
            <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-purple-500 text-white text-xs font-bold">3</span>
            <span>{{ userVsTargetResult.personName }} × {{ userVsTargetResult.targetPersonName }} × 비트코인 궁합</span>
            <span class="ml-auto text-4xl font-black text-purple-600">{{ userVsTargetResult.score }}점</span>
          </h4>

          <div class="grid gap-4 md:grid-cols-2">
            <div class="rounded-2xl border border-slate-200 bg-white p-4">
              <div class="flex gap-4 items-start mb-3">
                <div class="flex-shrink-0">
                  <div class="w-16 h-16 rounded-lg overflow-hidden border-2 border-slate-200 bg-slate-100 flex items-center justify-center">
                    <img v-if="userVsTargetResult.personImageUrl" :src="userVsTargetResult.personImageUrl" :alt="userVsTargetResult.personName" class="w-full h-full object-cover" />
                    <span v-else class="text-2xl">👤</span>
                  </div>
                </div>
                <div class="flex-1">
                  <p class="text-sm font-bold text-slate-900 mb-1">{{ userVsTargetResult.personName }}</p>
                  <p class="text-xs text-slate-500">오행 구성</p>
                </div>
              </div>
              <div class="space-y-2">
                <div v-for="highlight in userVsTargetResult.user.highlights" :key="highlight.label" class="space-y-1">
                  <div class="flex items-center justify-between text-xs">
                    <div class="flex items-center gap-1">
                      <span class="text-sm">{{ highlight.icon }}</span>
                      <span class="font-semibold text-slate-900">{{ highlight.label }}</span>
                    </div>
                    <span class="text-xs font-bold text-slate-700">{{ highlight.ratio }}%</span>
                  </div>
                  <div class="w-full bg-slate-200 rounded-full h-1">
                    <div class="h-1 rounded-full transition-all duration-500" :class="highlight.colorClass" :style="{ width: `${highlight.ratio}%` }"></div>
                  </div>
                </div>
              </div>
            </div>

            <div class="rounded-2xl border border-slate-200 bg-white p-4">
              <div class="flex gap-4 items-start mb-3">
                <div class="flex-shrink-0">
                  <div class="w-16 h-16 rounded-lg overflow-hidden border-2 border-slate-200 bg-slate-100 flex items-center justify-center">
                    <img v-if="userVsTargetResult.targetPersonImageUrl" :src="userVsTargetResult.targetPersonImageUrl" :alt="userVsTargetResult.targetPersonName" class="w-full h-full object-cover" />
                    <span v-else class="text-2xl">👤</span>
                  </div>
                </div>
                <div class="flex-1">
                  <p class="text-sm font-bold text-slate-900 mb-1">{{ userVsTargetResult.targetPersonName }}</p>
                  <p class="text-xs text-slate-500">오행 구성</p>
                </div>
              </div>
              <div v-if="userVsTargetResult.target.highlights && userVsTargetResult.target.highlights.length" class="space-y-2">
                <div v-for="highlight in userVsTargetResult.target.highlights" :key="highlight.label" class="space-y-1">
                  <div class="flex items-center justify-between text-xs">
                    <div class="flex items-center gap-1">
                      <span class="text-sm">{{ highlight.icon }}</span>
                      <span class="font-semibold text-slate-900">{{ highlight.label }}</span>
                    </div>
                    <span class="text-xs font-bold text-slate-700">{{ highlight.ratio }}%</span>
                  </div>
                  <div class="w-full bg-slate-200 rounded-full h-1">
                    <div class="h-1 rounded-full transition-all duration-500" :class="highlight.colorClass" :style="{ width: `${highlight.ratio}%` }"></div>
                  </div>
                </div>
              </div>
              <div v-else class="text-xs text-slate-500">오행 정보 없음</div>
            </div>
          </div>

          <div class="rounded-2xl border border-slate-200 p-5 bg-slate-50">
            <div class="prose prose-slate max-w-none prose-headings:text-slate-900 prose-h2:text-lg prose-h2:font-bold prose-h2:mt-6 prose-h2:mb-3 prose-h2:first:mt-0 prose-p:text-sm prose-p:text-slate-700 prose-p:leading-relaxed prose-p:mb-3 prose-strong:text-slate-900 prose-strong:font-semibold compatibility-content select-text">
              <div v-html="renderMarkdown(userVsTargetResult.narrative)"></div>
            </div>
          </div>

          <div class="rounded-xl border border-purple-200 p-3 bg-purple-50">
            <p class="text-xs font-semibold text-purple-900 mb-1">⚠️ 리스크 메모</p>
            <p class="text-xs text-purple-800 leading-relaxed">{{ userVsTargetResult.riskNote }}</p>
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
import { computed, nextTick, onMounted, ref } from 'vue'
import { fetchCompatibilityQuickPresets, generateCompatibilityNarrative, saveCompatibilityAnalysis } from '@/services/compatibilityService'

const BITCOIN_HIGHLIGHTS = [
  {
    label: '목(木)',
    elementKey: 'wood',
    value: '성장과 개발 생태계',
    description: '라이트닝, 탭루트 등 점진적 진화를 이끄는 확장 에너지.',
    icon: '🌱',
    ratio: 10,
    colorClass: 'bg-green-500'
  },
  {
    label: '화(火)',
    elementKey: 'fire',
    value: '관심, 서사, 과열',
    description: '들불처럼 번지는 화. 환호와 공포가 반복되는 극단의 에너지.',
    icon: '🔥',
    ratio: 20,
    colorClass: 'bg-red-500'
  },
  {
    label: '토(土)',
    elementKey: 'earth',
    value: '완충, 신뢰 인프라',
    description: '전 세계 노드·채굴자의 분산 네트워크가 흔들림을 버텨낸다.',
    icon: '🏔️',
    ratio: 10,
    colorClass: 'bg-yellow-600'
  },
  {
    label: '금(金)',
    elementKey: 'metal',
    value: '규칙, 고정 공급, 불변성',
    description: '비트코인의 핵심 본체. 2,100만 개 고정 공급량, 변경 불가능한 규칙.',
    icon: '⚙️',
    ratio: 35,
    colorClass: 'bg-amber-500'
  },
  {
    label: '수(水)',
    elementKey: 'water',
    value: '유동성, 글로벌 자본의 흐름',
    description: '홍수·급류에 가까운 수. 상승장에서는 폭발적, 회수 국면에서는 급락.',
    icon: '💧',
    ratio: 25,
    colorClass: 'bg-blue-500'
  }
]

const BITCOIN_CANVAS_PROFILE = {
  entityName: '비트코인',
  label: '비트코인 사주 캔버스',
  summaryHighlight: '금(金)이 주력인 디지털 금, 수·화가 극단을 이루는 에너지',
  description: '고정 공급과 변동성, 네트워크 속성을 오행으로 환산해 구성한 비트코인의 기준선입니다.',
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
  metal: '⚙️',
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
    description: '나만의 정보를 직접 입력해 궁합을 계산하세요.',
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
    description: 'MicroStrategy CEO이자 비트코인 트리플 맥시.',
    image_url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Michael_Saylor_2016.jpg/640px-Michael_Saylor_2016.jpg'
  },
  {
    id: 'trump',
    label: '도널드 트럼프',
    birthdate: '1946-06-14',
    gender: 'male',
    description: '전 미 대통령으로 친비트코인 행보를 강화 중.',
    image_url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Donald_Trump_official_portrait.jpg/640px-Donald_Trump_official_portrait.jpg'
  },
  {
    id: 'fink',
    label: '래리 핑크',
    birthdate: '1952-11-02',
    gender: 'male',
    description: '블랙록 CEO, 기관 비트코인 수요를 이끄는 인물.',
    image_url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Laurence_D._Fink.jpg/640px-Laurence_D._Fink.jpg'
  },
  {
    id: 'dimon',
    label: '제이미 다이먼',
    birthdate: '1956-03-13',
    gender: 'male',
    description: 'JP모건 CEO, 비판과 도입을 오가는 상징적 인물.',
    image_url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Jamie_Dimon_2018.jpg/640px-Jamie_Dimon_2018.jpg'
  },
  {
    id: 'vitalik',
    label: '비탈릭 부테린',
    birthdate: '1994-01-31',
    gender: 'male',
    description: '이더리움 창시자이자 크립토 철학자.',
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
const targetName = ref(DEFAULT_TARGET_NAME)
const targetBirthdate = ref('')
const targetBirthtime = ref('')
const targetGender = ref('')
const targetTimeUnknown = ref(false)
const targetImageUrl = ref('')
const targetDescription = ref('')
const targetProfileEnabled = ref(false)
const loading = ref(false)
const analysisStep = ref(0)
const totalSteps = ref(3)
const errorMessage = ref('')
const showDebugModal = ref(false)
const debugPrompts = ref([])

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
  debugPrompts.value = prompts
  showDebugModal.value = true
}

const compatibilityResult = ref(null)
const userVsBitcoinResult = ref(null)
const targetVsBitcoinResult = ref(null)
const userVsTargetResult = ref(null)
const selectedTargetPresetId = ref(null)
const personTargetMeta = computed(() => buildPersonTargetMeta())
const activeTargetProfile = computed(() => personTargetMeta.value)
const scoreProgress = ref(0)
const quickPresetOptions = ref(
  FALLBACK_QUICK_PRESETS.map((preset, index) => normalizeQuickPreset(preset, index)).filter(Boolean)
)
const quickPresetLoading = ref(false)
const selectedPresetId = ref(null)
const bitcoinHighlights = computed(() => {
  const highlights = bitcoinCanvasProfile.highlights || []
  return [...highlights].sort((a, b) => b.ratio - a.ratio)
})
const targetNameDisplay = computed(() => activeTargetProfile.value?.entityName || DEFAULT_TARGET_NAME)
const analyzeButtonLabel = computed(() => {
  if (birthdate.value && targetBirthdate.value) {
    return '궁합 분석하기'
  }
  return '사주 분석하기'
})

// 새로운 loadingMessage computed 속성 추가
const loadingMessage = computed(() => {
  const user = userName.value || DEFAULT_USER_NAME
  const target = targetName.value || DEFAULT_TARGET_NAME

  if (loading.value) {
    // 두 명일 때
    if (birthdate.value && targetBirthdate.value) {
      switch (analysisStep.value) {
        case 1: return `1) ${user}의 사주 분석 중...`
        case 2: return `2) ${target}의 사주 분석 중...`
        case 3: return `3) ${user}과 ${target} 궁합 사주 분석 중...`
        default: return `사주 분석 중... (${analysisStep.value}/${totalSteps.value})` // 폴백
      }
    } 
    // 한 명일 때 (user 또는 target 중 한 명만 있을 때)
    else if (birthdate.value || targetBirthdate.value) {
      const personName = birthdate.value ? user : target
      return `${personName}의 사주 분석 중... (${analysisStep.value}/${totalSteps.value})`
    }
  }
  return '' // 로딩 중이 아니면 빈 문자열
})

let currentRunId = 0

const SCORE_CIRCLE_RADIUS = 60
const SCORE_CIRCLE_CIRCUMFERENCE = 2 * Math.PI * SCORE_CIRCLE_RADIUS

const userNarrativeHighlights = computed(() => {
  if (!compatibilityResult.value) return []
  const result = compatibilityResult.value
  const elementSentence = `당신의 사주는 ${result.element.label}을 주축으로 하고 있으며, 이는 ${result.elementSummary}를 의미합니다.`
  const targetNameText = result.target?.entityName || '비교 대상'
  const matchSentence = `당신의 ${result.element.label} 에너지와 ${targetNameText}의 오행 속성이 만났을 때, ${result.rating}의 궁합(점수 ${result.score}점)이 드러납니다.`
  return [
    {
      id: 'element-narrative',
      label: '사주 앵커',
      icon: '🌙',
      text: elementSentence
    },
    {
      id: 'compat-narrative',
      label: '궁합 진단',
      icon: '✨',
      text: matchSentence
    }
  ]
})

function normalizeQuickPreset(preset, index = 0) {
  if (!preset) return null
  const id = preset.id || preset.pk || preset.label || `preset-${index}`
  return {
    id,
    label: preset.label || `빠른 설정 ${index + 1}`,
    description: preset.description || '',
    birthdate: preset.birthdate || '',
    birthtime: preset.birth_time || preset.birthtime || '',
    gender: preset.gender || '',
    imageUrl: preset.image_url || preset.imageUrl || '',
    assumeTimeUnknown: preset.assume_time_unknown ?? preset.assumeTimeUnknown ?? (!!(preset.birthdate || preset.birth_time || preset.birthtime) && !preset.birth_time && !preset.birthtime)
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
  compatibilityResult.value = null
  scoreProgress.value = 0
  const runId = Date.now()
  currentRunId = runId

  const hasUser = !!birthdate.value
  const hasTarget = !!targetBirthdate.value
  const userPayload = hasUser ? normalizePayload() : null
  const targetPayload = hasTarget ? normalizeTargetPayload() : null
  const targetProfileMeta = activeTargetProfile.value

  // 분석할 총 단계 수 결정
  if (hasUser && hasTarget) {
    totalSteps.value = 3 // 사용자 vs 비트코인, 타겟 vs 비트코인, 두 사람 × 비트코인
  } else {
    totalSteps.value = 1 // 하나만 vs 비트코인
  }

  // 비트코인 프로필 생성
  const bitcoinProfile = {
    profileType: 'bitcoin',
    entityName: '비트코인',
    label: '금(金)이 주력인 디지털 금, 수·화가 극단을 이루는 에너지',
    summaryHighlight: '',
    description: '고정 공급과 변동성, 네트워크 속성을 오행으로 환산해 구성한 비트코인의 기준선입니다.',
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

  // 1. 사용자 vs 비트코인 (사용자가 있을 때만)
  let result1 = null
  if (hasUser) {
    result1 = buildCompatibility(userPayload, bitcoinProfile, bitcoinPayload)
    result1.personImageUrl = userImageUrl.value || ''
    result1.personName = userPayload.userName || DEFAULT_USER_NAME
  }

  // 2. 비교대상 vs 비트코인 (비교대상이 있을 때만)
  let result2 = null
  if (hasTarget) {
    result2 = buildCompatibility(targetPayload, bitcoinProfile, bitcoinPayload)
    result2.personImageUrl = targetImageUrl.value || ''
    result2.personName = targetPayload.name || DEFAULT_TARGET_NAME
  }

  // 3. 두 사람 × 비트코인 (팀 궁합 - 둘 다 있을 때만)
  let result3 = null
  let combinedPayload = null
  if (hasUser && hasTarget) {
    combinedPayload = {
      year: Math.round((userPayload.year + targetPayload.year) / 2),
      month: Math.round((userPayload.month + targetPayload.month) / 2),
      day: Math.round((userPayload.day + targetPayload.day) / 2),
      time: null,
      userName: `${userPayload.userName || DEFAULT_USER_NAME} × ${targetPayload.name || DEFAULT_TARGET_NAME}`,
      gender: ''
    }
    // 점수 계산은 '두 사람의 평균' vs '비트코인'으로 수행
    result3 = buildCompatibility(combinedPayload, bitcoinProfile, bitcoinPayload)

    // UI 표시는 '사용자' vs '대상'으로 정보를 덮어씌움
    result3.personImageUrl = userImageUrl.value || ''
    result3.personName = userPayload.userName || DEFAULT_USER_NAME
    result3.user = JSON.parse(JSON.stringify(result1.user)) // 사용자 1 정보 복사

    result3.targetPersonImageUrl = targetImageUrl.value || ''
    result3.targetPersonName = targetPayload.name || DEFAULT_TARGET_NAME
    // result2.user가 대상(Target)의 정보를 담고 있음
    result3.target = {
      ...JSON.parse(JSON.stringify(result2.user)),
      profileType: 'person',
      entityName: targetPayload.name || DEFAULT_TARGET_NAME,
      label: `${targetPayload.name || DEFAULT_TARGET_NAME} 사주 캔버스`
    }
    
    result3.isTwoPersonComparison = true
  }

  if (currentRunId !== runId) return

  // LLM 요청 생성 (조건부)
  try {
    // 1. 사용자 vs 비트코인 (사용자가 있을 때만)
    if (hasUser && result1) {
      analysisStep.value = 1
      const agentPayload1 = buildAgentContextPayload(
        userPayload,
        bitcoinPayload,
        result1,
        bitcoinProfile,
        timeUnknown.value,
        false
      )
      agentPayload1.analysisType = 'user_vs_bitcoin'
      const userInfo = userDescription.value ? `\n\n**${userPayload.userName || DEFAULT_USER_NAME} 정보**: ${userDescription.value}` : ''
      agentPayload1.customPrompt = `${userPayload.userName || DEFAULT_USER_NAME}의 사주와 비트코인 궁합을 분석하세요.${userInfo}

**작성 지침 (반드시 준수):**

1. **극도의 간결성**: 전체 응답은 150-200자 이내로 작성하세요. 핵심 한두 가지만 전달하세요.

2. **쉬운 언어**:
   - 사주 전문 용어 절대 사용 금지
   - "목(木)이 강하다" (X) → "성장 욕구가 강하다" (O)

3. **구조**: 단 2개 섹션만
   - ## 특징 (1-2문장)
   - ## 전략 (1-2문장)

4. **문장**: 매우 짧게. 한 문장은 10-15자 이내로.

5. **개인화**: 위에 제공된 인물 정보(직업, 특징)를 고려하여 맞춤형 비트코인 투자 조언을 제공하세요.

6. **제거**: 인사말, 서론, 부연 설명 모두 제거. 핵심만 1-2줄로 요약.`

      const agentResponse1 = await generateCompatibilityNarrative(agentPayload1)
      if (currentRunId !== runId) return
      if (agentResponse1?.ok && agentResponse1?.narrative) {
        result1.narrative = agentResponse1.narrative
        result1.agentProvider = agentResponse1.model || agentResponse1.provider || 'llm'
        result1.debugPrompt = agentPayload1.customPrompt
      }
    }

    // 2. 비교대상 vs 비트코인 (비교대상이 있을 때만)
    if (hasTarget && result2) {
      analysisStep.value = hasUser ? 2 : 1
      const agentPayload2 = buildAgentContextPayload(
        targetPayload,
        bitcoinPayload,
        result2,
        bitcoinProfile,
        targetTimeUnknown.value,
        false
      )
      agentPayload2.analysisType = 'target_vs_bitcoin'
      const targetInfo = targetDescription.value ? `\n\n**${targetPayload.userName || DEFAULT_TARGET_NAME} 정보**: ${targetDescription.value}` : ''
      agentPayload2.customPrompt = `${targetPayload.userName || DEFAULT_TARGET_NAME}의 사주와 비트코인 궁합을 분석하세요.${targetInfo}

**작성 지침 (반드시 준수):**

1. **극도의 간결성**: 전체 응답은 150-200자 이내로 작성하세요. 핵심 한두 가지만 전달하세요.

2. **쉬운 언어**:
   - 사주 전문 용어 절대 사용 금지
   - "금(金)이 주력이다" (X) → "규칙을 중시한다" (O)

3. **구조**: 단 2개 섹션만
   - ## 특징 (1-2문장)
   - ## 전략 (1-2문장)

4. **문장**: 매우 짧게. 한 문장은 10-15자 이내로.

5. **개인화**: 위에 제공된 인물 정보(직업, 특징)를 고려하여 맞춤형 비트코인 투자 조언을 제공하세요.

6. **제거**: 인사말, 서론, 부연 설명 모두 제거. 핵심만 1-2줄로 요약.`

      const agentResponse2 = await generateCompatibilityNarrative(agentPayload2)
      if (currentRunId !== runId) return
      if (agentResponse2?.ok && agentResponse2?.narrative) {
        result2.narrative = agentResponse2.narrative
        result2.agentProvider = agentResponse2.model || agentResponse2.provider || 'llm'
        result2.debugPrompt = agentPayload2.customPrompt
      }
    }

    // 3. 두 사람 × 비트코인 (팀 궁합 - 둘 다 있을 때만)
    if (hasUser && hasTarget && result3 && combinedPayload) {
      analysisStep.value = 3
      const agentPayload3 = buildAgentContextPayload(
        combinedPayload,
        bitcoinPayload,
        result3,
        bitcoinProfile,
        false,
        false
      )
      agentPayload3.analysisType = 'team_vs_bitcoin'
      const teamInfo = []
      if (userDescription.value) teamInfo.push(`**${userPayload.userName || DEFAULT_USER_NAME}**: ${userDescription.value}`)
      if (targetDescription.value) teamInfo.push(`**${targetPayload.userName || DEFAULT_TARGET_NAME}**: ${targetDescription.value}`)
      const teamInfoText = teamInfo.length > 0 ? `\n\n**두 사람의 정보**:\n${teamInfo.join('\n')}` : ''
      agentPayload3.customPrompt = `${userPayload.userName || DEFAULT_USER_NAME}와(과) ${targetPayload.userName || DEFAULT_TARGET_NAME}가 함께 비트코인 투자할 때의 팀 궁합을 분석하세요.${teamInfoText}

**작성 지침 (반드시 준수):**

1. **극도의 간결성**: 전체 응답은 150-200자 이내로 작성하세요. 핵심 한두 가지만 전달하세요.

2. **쉬운 언어**:
   - 사주 전문 용어 절대 사용 금지
   - 두 사람이 팀으로 협력할 때의 시너지에 집중

3. **구조**: 단 2개 섹션만
   - ## 팀 특성 (1-2문장)
   - ## 투자 전략 (1-2문장)

4. **문장**: 매우 짧게. 한 문장은 10-15자 이내로.

5. **개인화**: 위에 제공된 두 사람의 직업과 특징을 고려하여 맞춤형 팀 투자 전략을 제공하세요.

6. **제거**: 인사말, 서론, 부연 설명 모두 제거. 핵심만 1-2줄로 요약.`

      const agentResponse3 = await generateCompatibilityNarrative(agentPayload3)
      if (currentRunId !== runId) return
      if (agentResponse3?.ok && agentResponse3?.narrative) {
        result3.narrative = agentResponse3.narrative
        result3.agentProvider = agentResponse3.model || agentResponse3.provider || 'llm'
        result3.debugPrompt = agentPayload3.customPrompt
      }
    }

  } catch (agentError) {
    console.error('궁합 에이전트 호출 실패:', agentError)
    errorMessage.value = '궁합 에이전트 요청에 실패했습니다. 잠시 후 다시 시도해주세요.'
    loading.value = false
    analysisStep.value = 0
    return
  }

  userVsBitcoinResult.value = result1
  targetVsBitcoinResult.value = result2
  userVsTargetResult.value = result3

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
  return { year, month, day, time, gender: targetGender.value, name }
}

function applyQuickPreset(preset) {
  if (!preset) return
  selectedPresetId.value = preset.id || preset.label
  userName.value = preset.label || DEFAULT_USER_NAME
  gender.value = preset.gender || ''
  birthdate.value = preset.birthdate || ''
  userImageUrl.value = preset.imageUrl || ''
  userDescription.value = preset.description || ''
  if (preset.birthtime) {
    birthtime.value = preset.birthtime
    timeUnknown.value = false
  } else {
    birthtime.value = ''
    timeUnknown.value = !!preset.assumeTimeUnknown
  }
}

function applyTargetQuickPreset(preset) {
  if (!preset) return
  selectedTargetPresetId.value = preset.id || preset.label
  targetName.value = preset.label || DEFAULT_TARGET_NAME
  targetGender.value = preset.gender || ''
  targetBirthdate.value = preset.birthdate || ''
  targetImageUrl.value = preset.imageUrl || ''
  targetDescription.value = preset.description || ''
  if (preset.birthtime) {
    targetBirthtime.value = preset.birthtime
    targetTimeUnknown.value = false
  } else {
    targetBirthtime.value = ''
    targetTimeUnknown.value = !!preset.assumeTimeUnknown
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
}

function resetTargetPresetSelection() {
  selectedTargetPresetId.value = null
  targetName.value = DEFAULT_TARGET_NAME
  targetBirthdate.value = ''
  targetBirthtime.value = ''
  targetGender.value = ''
  targetTimeUnknown.value = false
  targetImageUrl.value = ''
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

function buildCompatibility(payload, targetProfileMeta, targetPayload) {
  const profileMeta = targetProfileMeta || EMPTY_TARGET_PROFILE
  // 정확한 천간·지지 기반 사주 계산
  const sajuData = calculateSajuElement(payload.year, payload.month, payload.day)
  const element = sajuData.element
  const zodiac = calculateZodiacSign(payload.year, payload.month, payload.day)
  const yinYang = calculateYinYang(payload.year, payload.month, payload.day)
  const targetElementKey = getTargetDominantElementKey(profileMeta, targetPayload)
  const affinity = ELEMENT_AFFINITY[targetElementKey] || ELEMENT_AFFINITY.metal
  const targetElementLabel = ELEMENTS.find((item) => item.key === targetElementKey)?.label || ''
  let targetZodiac = profileMeta.targetZodiac || ''
  let targetYinYang = profileMeta.targetYinYang || ''
  if (profileMeta.profileType === 'person' && targetPayload) {
    targetZodiac = calculateZodiacSign(targetPayload.year, targetPayload.month, targetPayload.day)
    targetYinYang = calculateYinYang(targetPayload.year, targetPayload.month, targetPayload.day)
  }

  // 비트코인 맥시멀리스트 점수 계산
  let score = 58 + (payload.month % 7)

  // 오행 궁합 점수 (모든 상극을 긍정적으로 재해석)
  if (affinity.allies && affinity.allies.includes(element.key)) {
    score += 18  // 상생 관계
  } else if (affinity.tempering && affinity.tempering.includes(element.key)) {
    score += 15  // 단련 관계 (화→금)
  } else if (affinity.foundation && affinity.foundation.includes(element.key)) {
    score += 16  // 기준 제공 관계 (금→목: 규칙 위에서 확장)
  } else if (affinity.cooling && affinity.cooling.includes(element.key)) {
    score += 14  // 진정 관계 (수→화)
  } else if (affinity.utilization && affinity.utilization.includes(element.key)) {
    score += 14  // 활용 관계 (목→토)
  } else if (affinity.channeling && affinity.channeling.includes(element.key)) {
    score += 14  // 조절 관계 (토→수)
  } else if (affinity.neutral && affinity.neutral.includes(element.key)) {
    score += 8   // 중립 관계
  } else if (affinity.challenges && affinity.challenges.includes(element.key)) {
    score -= 12  // 상극 관계 (이제는 없음)
  }

  const timeAdvice = deriveTimeAdvice(payload.time)
  score += timeAdvice.bonus
  score += payload.day % 2 === 0 ? 3 : -1
  score = Math.max(35, Math.min(98, Math.round(score)))

  const rating = score >= 85 ? '찰떡궁합' : score >= 70 ? '균형 잡힌 합' : score >= 55 ? '중립형 합' : '주의가 필요한 합'
  const strategy = STRATEGY_LIBRARY[element.key]

  // Generate narrative story
  const currentYear = new Date().getFullYear()
  const nextYear = currentYear + 1
  const targetContext = {
    entityName: profileMeta.entityName || '비교 대상',
    summaryHighlight: profileMeta.summaryHighlight || '',
    highlights: profileMeta.highlights || [],
    profileType: profileMeta.profileType || 'person',
    elementKey: targetElementKey,
    elementLabel: targetElementLabel,
    zodiac: targetZodiac,
    yinYang: targetYinYang,
    profileNarrative: profileMeta.profileNarrative || ''
  }
  const narrative = generateStoryNarrative(
    payload,
    element,
    zodiac,
    yinYang,
    rating,
    score,
    strategy,
    timeAdvice,
    nextYear,
    profileMeta,
    targetContext
  )

  const userHighlights = buildPersonHighlights(element, zodiac, yinYang, payload.time || '시간 미상')
  const targetHighlights = targetContext.highlights || []

  return {
    score,
    rating,
    element,
    elementSummary: element.summary,
    zodiac,
    yinYang,
    strategy,
    timeAdvice,
    narrative,
    riskNote: buildRiskNote(element.key, rating),
    agentPrompt: profileMeta.agentPrompt,
    user: {
      name: payload.userName || DEFAULT_USER_NAME,
      elementKey: element.key,
      elementLabel: element.label,
      highlights: userHighlights
    },
    target: {
      profileType: targetContext.profileType,
      entityName: targetContext.entityName,
      label: profileMeta.label,
      summary: targetContext.summaryHighlight,
      elementKey: targetElementKey,
      highlights: targetHighlights,
      zodiac: targetContext.zodiac,
      yinYang: targetContext.yinYang
    }
  }
}

const scoreCircleDashOffset = computed(() => {
  const progress = Math.max(0, Math.min(100, scoreProgress.value || 0))
  return SCORE_CIRCLE_CIRCUMFERENCE * (1 - progress / 100)
})

function generateStoryNarrative(payload, element, zodiac, yinYang, rating, score, strategy, timeAdvice, nextYear, targetProfileMeta, targetContext) {
  const genderText = payload.gender === 'male' ? '남성' : payload.gender === 'female' ? '여성' : ''
  const genderPrefix = genderText ? `${genderText}으로서, ` : ''
  const targetLabel = targetContext?.entityName || '비교 대상'
  const isPersonTarget = targetContext?.profileType === 'person'
  const targetProfileIntro = describeTargetProfile(targetProfileMeta, targetContext)
  const dominantTrait = getDominantTrait(targetProfileMeta)

  const introHeading = `## 당신과 ${targetLabel}의 ${isPersonTarget ? '시너지' : '만남'}\n\n`
  let story = introHeading
  story += `당신은 ${zodiac} 띠${genderText ? `의 ${genderText}` : ''}로, ${yinYang}의 기운을 타고났습니다. `
  story += `당신의 사주는 ${element.label}을 주축으로 하고 있으며, 이는 ${element.summary.toLowerCase()}를 의미합니다.\n\n`

  story += `${targetProfileIntro}`
  if (dominantTrait) {
    story += `그 중에서도 가장 큰 비중을 차지하는 것은 **${dominantTrait.label}**(${dominantTrait.ratio}%)이며, ${dominantTrait.description} `
  } else if (targetContext?.elementLabel) {
    story += `${targetLabel}은(는) ${targetContext.elementLabel} 기운을 중심으로 움직입니다. `
  }
  story += `당신의 ${element.label} 에너지와 ${targetLabel}의 오행 속성이 만났을 때, ${rating}의 궁합을 보입니다(궁합 점수: ${score}점). `

  if (score >= 85) {
    story += `이는 매우 조화로운 관계로, ${genderPrefix}당신은 ${targetLabel}의 본질을 직관적으로 이해하고 장기적인 관점에서 접근할 수 있는 천부적인 소질을 갖추고 있습니다.\n\n`
  } else if (score >= 70) {
    story += `이는 균형 잡힌 관계로, ${genderPrefix}당신은 ${targetLabel}과 안정적인 리듬을 만들어갈 수 있습니다. 규칙을 세우고 그것을 지키는 것이 성공의 열쇠입니다.\n\n`
  } else if (score >= 55) {
    story += `이는 중립적인 관계로, ${genderPrefix}당신은 ${targetLabel}과의 관계에서 의식적인 노력이 필요합니다. 감정보다는 데이터와 명확한 원칙에 기반한 접근이 중요합니다.\n\n`
  } else {
    story += `이는 주의가 필요한 관계로, ${genderPrefix}당신은 ${targetLabel}의 급격한 리듬에 쉽게 흔들릴 수 있습니다. 철저한 계획과 규칙이 필수적입니다.\n\n`
  }

  // Part 2: 내년의 사주에 대한 기본 내용
  story += `## ${nextYear}년, 당신의 운세\n\n`
  story += `${nextYear}년은 당신에게 ${getYearlyFortune(element, yinYang, nextYear)}의 해가 될 것입니다. `
  story += `${element.label} 에너지를 가진 당신에게 ${nextYear}년은 ${getYearElement(nextYear)}의 기운이 흐르는 해로, `
  story += `${getElementInteraction(element.key, getYearElement(nextYear))}.\n\n`

  if (timeAdvice.key !== 'unknown') {
    story += `당신은 ${timeAdvice.label}에 태어났기에, ${timeAdvice.description.slice(0, -1)}는 특성이 있습니다. `
    story += `이는 ${nextYear}년 한 해 동안 ${getTimeBasedAdvice(timeAdvice.key)}에 도움이 될 것입니다.\n\n`
  }

  // Part 3: 비트코인 저축 및 투자에 대한 서술
  if (isPersonTarget) {
    story += `## ${targetLabel}과의 관계 조언\n\n`
    story += `${targetLabel}은(는) ${targetContext.elementLabel || '특정'} 에너지에 뿌리를 두고 있습니다. `
    story += `관계를 설계할 때 ${genderPrefix}당신의 ${element.label} 에너지는 ${strategy.focus.toLowerCase()} `
    story += `리듬을 만들어 서로의 속도를 맞추는 데 도움이 됩니다.\n\n`

    story += `**${strategy.style}** 접근법을 추천합니다. `
    story += `이 방식은 감정 기복이 커질 때도 서로의 원칙을 지켜주며, ${targetLabel}과의 협업이나 동행을 보다 안정적으로 만들어줍니다.\n\n`
  } else {
    story += `## ${nextYear}년, ${targetLabel}과 함께하는 한 해\n\n`
    story += `${nextYear}년은 ${targetLabel}을 '투자'가 아닌 '저축'의 관점으로 바라보는 것이 중요합니다. `
    story += `${genderPrefix}당신의 ${element.label} 에너지는 ${strategy.focus.toLowerCase()}\n\n`

    story += `**${strategy.style}**을 추천합니다. `
    story += `이는 당신의 본성과 가장 잘 맞는 접근법입니다. `
    story += `포지션 구성은 ${strategy.allocation}을 기본으로 하되, 시장 상황과 당신의 감정 상태를 고려하여 유연하게 조정하세요.\n\n`

    story += getBitcoinYearlyAdvice(element.key, score, nextYear)

    story += `\n\n${targetLabel}은 한정된 공급량을 가진 디지털 금입니다. `
    story += `${nextYear}년 한 해 동안, 급등과 급락에 흔들리지 말고 꾸준히 저축하는 마음가짐을 유지하세요. `
    story += `당신의 ${element.label} 에너지가 그 길을 안내할 것입니다.`
  }

  return story
}

function describeTargetProfile(profileMeta, targetContext) {
  const name = profileMeta?.entityName || DEFAULT_TARGET_NAME
  const parts = []
  if (targetContext?.zodiac) parts.push(`${targetContext.zodiac}`)
  if (targetContext?.yinYang) parts.push(`${targetContext.yinYang}의 기운`)
  if (targetContext?.elementLabel) parts.push(`주력 ${targetContext.elementLabel}`)
  const summary = parts.join(' · ')
  const suffix = profileMeta?.profileNarrative ? ` ${profileMeta.profileNarrative}` : ''
  const baseSentence = `${name}은(는) ${summary || '고유한 오행'} 성향을 지닌 인물입니다.${suffix ? ` ${suffix}` : ''} `
  if (!profileMeta?.highlights?.length) {
    return `${baseSentence}사주 정보를 입력하면 더 정밀한 비교가 가능합니다.`
  }
  const ratioText = profileMeta.highlights.map((trait) => `${trait.label} ${trait.ratio}%`).join(', ')
  return `${baseSentence}특히 ${ratioText} 비중이 두드러집니다. `
}

function getTargetDominantElementKey(profileMeta, targetPayload) {
  if (profileMeta?.dominantElementKey) return profileMeta.dominantElementKey
  if (profileMeta?.profileType === 'person' && targetPayload) {
    const element = ELEMENTS[(targetPayload.year + targetPayload.month + targetPayload.day) % ELEMENTS.length]
    return element.key
  }
  const trait = getDominantTrait(profileMeta)
  return trait?.elementKey || 'metal'
}

function getDominantTrait(profileMeta) {
  if (!profileMeta?.highlights?.length) {
    return {
      label: '정보 없음',
      ratio: 0,
      description: '비교 대상을 선택하면 주력 오행이 계산됩니다.',
      elementKey: 'metal'
    }
  }
  return profileMeta.highlights.reduce((max, trait) => {
    if (!max || Number(trait.ratio) > Number(max.ratio)) return trait
    return max
  }, null)
}

function getYearlyFortune(element, yinYang, year) {
  const fortunes = ['도약', '안정', '변화', '성장', '정리']
  return fortunes[year % fortunes.length]
}

function getYearElement(year) {
  const elements = ['금(金)', '수(水)', '목(木)', '화(火)', '토(土)']
  return elements[year % elements.length]
}

function getElementInteraction(userElement, yearElement) {
  const interactions = {
    'wood': {
      '금(金)': '조심스러운 접근이 필요하지만 구조를 배울 수 있는 해',
      '수(水)': '생명력을 공급받아 성장할 수 있는 길한 해',
      '목(木)': '동료를 만나 함께 성장하는 안정된 해',
      '화(火)': '에너지를 발산하며 성과를 낼 수 있는 활발한 해',
      '토(土)': '뿌리를 내리고 기반을 다지는 의미 있는 해'
    },
    'fire': {
      '금(金)': '열정을 제어하며 균형을 찾아야 하는 해',
      '수(水)': '충돌과 조율이 반복되는 배움의 해',
      '목(木)': '새로운 연료를 얻어 타오를 수 있는 상승의 해',
      '화(火)': '강렬한 에너지가 폭발하는 주의가 필요한 해',
      '토(土)': '결과를 안정적으로 정착시키는 수확의 해'
    },
    'earth': {
      '금(金)': '품격 있는 성과를 만들어내는 생산적인 해',
      '수(水)': '유연함을 배우며 적응력을 키우는 해',
      '목(木)': '새로운 것을 받아들이되 중심을 지켜야 하는 해',
      '화(火)': '따뜻한 에너지를 받아 풍요로워지는 해',
      '토(土)': '같은 에너지끼리 만나 안정과 정체 사이에서 선택하는 해'
    },
    'metal': {
      '금(金)': '날카로움이 더해져 정교함이 극대화되는 해',
      '수(水)': '흐름을 만들어 새로운 방향으로 나아가는 해',
      '목(木)': '대립과 절삭이 일어나지만 결과물이 명확한 해',
      '화(火)': '단련의 고통을 겪지만 더 강해지는 해',
      '토(土)': '든든한 토대를 얻어 빛을 발하는 길한 해'
    },
    'water': {
      '금(金)': '새로운 원천을 만나 풍부해지는 생성의 해',
      '수(水)': '같은 흐름끼리 모여 큰 물결을 이루는 해',
      '목(木)': '에너지를 나누어주며 성장을 돕는 베풂의 해',
      '화(火)': '증발과 순환을 경험하는 변화의 해',
      '토(土)': '흐름이 막히거나 고이는 정체를 주의해야 하는 해'
    }
  }
  return interactions[userElement]?.[yearElement] || '새로운 배움의 해'
}

function getTimeBasedAdvice(timeKey) {
  const adviceMap = {
    'dawn': '직관적인 판단과 타이밍 포착',
    'morning': '규칙적인 루틴 유지와 꾸준한 실행',
    'afternoon': '균형 잡힌 의사결정과 리밸런싱',
    'evening': '철저한 복기와 검증을 통한 리스크 관리'
  }
  return adviceMap[timeKey] || '계획적인 접근'
}

function getBitcoinYearlyAdvice(elementKey, score, year) {
  const adviceMap = {
    'wood': `${year}년은 비트코인을 꾸준히 축적하기 좋은 해입니다. 당신의 목(木) 에너지는 성장과 확장을 추구하지만, 비트코인 저축에서는 인내심이 더 중요합니다. 매월 또는 매주 일정 금액을 자동 적립하고, 가격이 오르든 내리든 흔들리지 마세요. 상승장에서 '이제 팔아야 하나' 하는 유혹이 올 수 있지만, 최소 4년 이상 보유한다는 원칙을 지키세요. 비트코인은 단기 수익이 아닌 장기 자산입니다.`,
    'fire': `${year}년 비트코인 저축에서 당신의 화(火) 에너지는 양날의 검입니다. 열정적으로 시작할 수 있지만, 변동성에 쉽게 흔들릴 수 있습니다. 감정적으로 매도하지 마세요. 매주 또는 매월 정해진 날짜에 자동으로 적립되도록 설정하고, 절대 차트를 보고 충동적으로 팔지 마세요. 비트코인은 4년 주기로 움직입니다. 최소 한 사이클(4년)은 보유하겠다는 각오로 시작하세요.`,
    'earth': `${year}년은 당신의 토(土) 에너지가 빛을 발하는 해입니다. 안정과 꾸준함을 중시하는 당신에게 비트코인 정기 저축은 완벽한 전략입니다. 시장이 폭락해도 당황하지 마세요. 오히려 더 저렴한 가격에 축적할 기회입니다. 매월 정해진 금액을 기계적으로 적립하고, 10년 이상 보유한다는 마음가짐을 가지세요. 비트코인은 인내하는 자에게 보상합니다.`,
    'metal': `${year}년 비트코인 저축에서 당신의 금(金) 에너지는 큰 강점입니다. 규율과 원칙을 중시하는 당신은 감정에 흔들리지 않고 정기 적립을 이어갈 수 있습니다. 매주 또는 매월 정확히 같은 날, 같은 금액을 적립하세요. 가격이 올라도, 내려도 상관없이 기계적으로 실행하세요. 시장을 예측하려 하지 말고, 시간을 당신의 편으로 만드세요. 비트코인은 규율 있는 저축자에게 가장 큰 보상을 줍니다.`,
    'water': `${year}년 당신의 수(水) 에너지는 유연함과 적응력을 의미합니다. 비트코인 가격이 급등하거나 급락해도 흔들리지 말고, 흐름에 몸을 맡기세요. 매월 정기 적립을 설정하고, 하락장이 와도 절대 팔지 마세요. 오히려 하락은 더 많은 비트코인을 축적할 기회입니다. 변동성을 두려워하지 말고, 최소 4년 이상의 긴 호흡으로 바라보세요. 비트코인은 물처럼 흐르며 결국 제자리를 찾습니다.`
  }
  return adviceMap[elementKey] || ''
}

function deriveTimeAdvice(time) {
  if (!time) return TIME_WINDOWS.find((window) => window.key === 'unknown')
  const [hour] = time.split(':').map((v) => Number(v))
  if (hour >= 23 || hour < 5) return TIME_WINDOWS[0]
  if (hour < 11) return TIME_WINDOWS[1]
  if (hour < 17) return TIME_WINDOWS[2]
  if (hour < 23) return TIME_WINDOWS[3]
  return TIME_WINDOWS[4]
}

function generateNarrative(elementKey, rating) {
  const snippets = {
    wood: '확장 국면에서 탄력을 얻으므로 채널 상단에서도 호흡을 길게 가져갈 수 있습니다',
    fire: '모멘텀을 빠르게 탈 수 있지만 과열 구간에서는 냉정한 룰이 필요합니다',
    earth: '큰 조정에서도 버틸 수 있는 저력과 방어선을 동시에 지니고 있습니다',
    metal: '정밀한 룰과 비트코인의 구조가 닮아 안정적인 궁합을 보여줍니다',
    water: '흐름을 타며 손실을 줄이고 새로운 파동이 올 때 자연스럽게 적응합니다'
  }
  return `${rating}으로 분류되며 ${snippets[elementKey]}`
}

function buildRiskNote(elementKey, rating) {
  const base = {
    wood: '충동적으로 시장에 진입하기보다 비중 조절 규칙을 명문화하세요.',
    fire: '손절 기준을 미리 정하지 않으면 비트코인의 변동성이 감정을 자극할 수 있습니다.',
    earth: '과도한 방어는 상승 파동을 놓칠 수 있으니 분기별로 위험 한도를 재점검하세요.',
    metal: '신호가 많아질수록 과최적화 리스크가 생깁니다. 핵심 지표만 남기세요.',
    water: '많은 시나리오를 동시에 고려하다 보면 실행이 늦어질 수 있습니다. 핵심 시나리오를 2개로 제한하세요.'
  }
  return `${base[elementKey]} (${rating} 등급)`
}

function buildAgentContextPayload(payload, targetPayload, result, targetProfileMeta, isTimeUnknown, isTargetTimeUnknown) {
  if (!payload || !result) return null
  const birthdate = `${payload.year}-${String(payload.month).padStart(2, '0')}-${String(payload.day).padStart(2, '0')}`
  const timeLabel = payload.time ? payload.time : isTimeUnknown ? '시간 미상' : '미입력'
  const highlightSummary = (targetProfileMeta?.highlights || [])
    .map((trait) => `${trait.label} ${trait.ratio}%`)
    .join(', ')
  const nextYear = new Date().getFullYear() + 1
  const targetName = targetProfileMeta?.entityName || '비교 대상'
  const targetInfoLines = []
  if (targetPayload) {
    const targetBirthdate = `${targetPayload.year}-${String(targetPayload.month).padStart(2, '0')}-${String(
      targetPayload.day
    ).padStart(2, '0')}`
    const targetTimeLabel = targetPayload.time
      ? targetPayload.time
      : isTargetTimeUnknown
        ? '시간 미상'
        : '미입력'
    targetInfoLines.push(`- 이름: ${targetName}`)
    targetInfoLines.push(`- 생년월일: ${targetBirthdate}`)
    targetInfoLines.push(`- 성별: ${targetPayload.gender || '미입력'}`)
    targetInfoLines.push(
      `- 띠 / 음양: ${result.target?.zodiac || targetProfileMeta?.targetZodiac || '미계산'} / ${result.target?.yinYang || targetProfileMeta?.targetYinYang || '미계산'}`
    )
    targetInfoLines.push(`- 태어난 시간: ${targetTimeLabel}`)
  } else {
    targetInfoLines.push(`- ${targetProfileMeta?.label || `${targetName} 프로필`}`)
    if (targetProfileMeta?.summaryHighlight) targetInfoLines.push(`- 설명: ${targetProfileMeta.summaryHighlight}`)
  }
  if (highlightSummary) {
    targetInfoLines.push(`- 오행 비중: ${highlightSummary}`)
  }

  const contextLines = [
    '사용자 기본 정보:',
    `- 이름: ${payload.userName || DEFAULT_USER_NAME}`,
    `- 생년월일: ${birthdate}`,
    `- 성별: ${payload.gender || '미입력'}`,
    `- 띠 / 음양: ${result.zodiac} / ${result.yinYang}`,
    `- 주력 오행: ${result.element.label} (${result.elementSummary})`,
    `- 태어난 시간: ${timeLabel}`,
    '',
    `${targetName} 기준선:`,
    ...targetInfoLines,
    '',
    '궁합 지표:',
    `- 궁합 점수: ${result.score} (${result.rating})`,
    `- 추천 전략: ${result.strategy.style} / ${result.strategy.focus}`,
    `- 리스크 메모: ${result.riskNote}`,
    `- ${nextYear}년 대비 조언: ${result.timeAdvice?.title || result.timeAdvice?.label || '시간 정보 없음'}`
  ].filter(Boolean)

  return {
    context: contextLines.join('\n'),
    data: {
      user: {
        name: payload.userName || DEFAULT_USER_NAME,
        birthdate,
        gender: payload.gender || '',
        zodiac: result.zodiac,
        yinYang: result.yinYang,
        element: result.element.label,
        elementSummary: result.elementSummary,
        timeLabel,
        timeAdvice: result.timeAdvice?.label || '',
        score: result.score
      },
      targetProfile: {
        name: targetName,
        label: targetProfileMeta?.label || '',
        profileType: targetProfileMeta?.profileType || 'person',
        summary: targetProfileMeta?.summaryHighlight || '',
        highlights: targetProfileMeta?.highlights || [],
        zodiac: result.target?.zodiac || targetProfileMeta?.targetZodiac || '',
        yinYang: result.target?.yinYang || targetProfileMeta?.targetYinYang || ''
      },
      compatibility: {
        score: result.score,
        rating: result.rating,
        strategy: result.strategy,
        riskNote: result.riskNote,
        targetElementKey: result.target?.elementKey || ''
      }
    }
  }
}

async function copyNarrative() {
  if (!compatibilityResult.value || !compatibilityResult.value.narrative) return

  try {
    // Remove HTML tags and format for plain text
    const plainText = compatibilityResult.value.narrative
      .replace(/## /g, '\n')
      .replace(/\*\*/g, '')
      .trim()

    await navigator.clipboard.writeText(plainText)

    // Optional: Show a brief success message
    const button = event.target.closest('button')
    const originalText = button.innerHTML
    button.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg> 복사됨!'
    setTimeout(() => {
      button.innerHTML = originalText
    }, 2000)
  } catch (err) {
    console.error('복사 실패:', err)
  }
}

function formatCardDate(dateStr) {
  if (!dateStr) return ''
  const [year, month, day] = dateStr.split('-')
  return `${year}년 ${month}월 ${day}일`
}

function renderMarkdown(text) {
  if (!text) return ''
  const lines = text.split('\n')
  const htmlParts = []
  let paragraphBuffer = []
  let unorderedBuffer = []
  let orderedBuffer = []

  const formatInline = (value) => {
    if (!value) return ''
    let formatted = value
    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>')
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    formatted = formatted.replace(/\*(.+?)\*/g, '<em>$1</em>')
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

  for (const rawLine of lines) {
    const line = rawLine.trim()
    if (!line) {
      flushParagraph()
      flushLists()
      continue
    }

    if (/^[-*+]\s+/.test(line)) {
      flushParagraph()
      if (orderedBuffer.length) flushOrdered()
      unorderedBuffer.push(line.replace(/^[-*+]\s+/, ''))
      continue
    }

    if (/^\d+\.\s+/.test(line)) {
      flushParagraph()
      if (unorderedBuffer.length) flushUnordered()
      orderedBuffer.push(line.replace(/^\d+\.\s+/, ''))
      continue
    }

    flushLists()

    const headingMatch = line.match(/^(#{1,3})\s+(.*)$/)
    if (headingMatch) {
      flushParagraph()
      const level = headingMatch[1].length
      const content = formatInline(headingMatch[2])
      const tag = level === 1 ? 'h2' : level === 2 ? 'h3' : 'h4'
      htmlParts.push(`<${tag}>${content}</${tag}>`)
      continue
    }

    paragraphBuffer.push(line)
  }

  flushParagraph()
  flushLists()
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
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 60px;
  background: linear-gradient(to left, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0) 100%);
  pointer-events: none;
  z-index: 10;
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
  background: rgba(255, 255, 255, 0.9);
  border-radius: 6px;
  padding: 8px;
  font-size: 0.75rem;
  text-align: center;
  border: 1px solid #cbd5e1;
  flex-shrink: 0;
  min-height: 50px;
}

.card-birthdate {
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
  font-size: 0.7rem;
}

.card-description {
  font-size: 0.65rem;
  color: #64748b;
  margin-top: 4px;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  word-break: break-word;
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

.score-circle-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.score-circle {
  position: relative;
  width: 5.25rem;
  height: 5.25rem;
}

.score-ring {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.score-ring circle {
  fill: transparent;
  stroke-width: 10;
}

.score-ring-bg {
  stroke: #e2e8f0;
}

.score-ring-progress {
  stroke: #0f172a;
  stroke-linecap: round;
  transition: stroke-dashoffset 1s ease;
}

.score-circle-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
</style>
