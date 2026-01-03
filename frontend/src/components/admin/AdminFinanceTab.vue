<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-white rounded-lg shadow p-6">
        <div class="text-sm text-gray-600 mb-1">총 쿼리 수</div>
        <div class="text-2xl font-bold text-gray-900">{{ financeStats.total_queries || 0 }}</div>
      </div>
      <div class="bg-white rounded-lg shadow p-6">
        <div class="text-sm text-gray-600 mb-1">성공률</div>
        <div class="text-2xl font-bold text-green-600">{{ financeStats.success_rate || 0 }}%</div>
      </div>
      <div class="bg-white rounded-lg shadow p-6">
        <div class="text-sm text-gray-600 mb-1">평균 처리시간</div>
        <div class="text-2xl font-bold text-blue-600">{{ financeStats.avg_processing_time_ms || 0 }}ms</div>
      </div>
      <div class="bg-white rounded-lg shadow p-6">
        <div class="text-sm text-gray-600 mb-1">최근 24시간</div>
        <div class="text-2xl font-bold text-purple-600">{{ financeStats.queries_last_24h || 0 }}</div>
      </div>
    </div>

    <div class="bg-white rounded-lg shadow overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900">재무 프롬프트 템플릿</h3>
        <p class="text-sm text-gray-500 mt-1">
          Finance 페이지에서 사용하는 단일 프롬프트와 변수 구성을 확인할 수 있습니다.
        </p>
      </div>
      <div class="p-6 space-y-5">
        <div>
          <p class="text-sm font-medium text-gray-700 mb-2">실제 요청</p>
          <div class="bg-slate-900/5 border border-slate-200 rounded-xl p-4 font-mono text-sm text-slate-800">
            {{ investmentPromptTemplate }}
          </div>
        </div>
        <div>
          <p class="text-sm font-medium text-gray-700 mb-2">변수 설명</p>
          <ul class="space-y-2">
            <li
              v-for="variable in investmentPromptVariables"
              :key="variable.key"
              class="flex items-start gap-2 text-sm text-gray-700"
            >
              <span class="px-2 py-0.5 bg-slate-100 text-slate-700 rounded font-mono text-xs">
                {{ variable.key }}
              </span>
              <span>{{ variable.description }}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <div class="bg-white rounded-lg shadow overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900">Agent 프롬프트 관리</h3>
      </div>

      <div v-if="agentPromptsLoading" class="text-center py-12 text-gray-500">
        로딩 중...
      </div>

      <div v-else-if="!agentPrompts.length" class="text-center py-12 text-gray-500">
        Agent 프롬프트가 없습니다.
        <button
          @click="initializeAgentPrompts"
          class="block mx-auto mt-4 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
        >
          기본 프롬프트 초기화
        </button>
      </div>

      <div v-else class="divide-y divide-gray-200">
        <div v-for="agent in agentPrompts" :key="agent.id" class="p-6">
          <div class="flex items-start justify-between mb-4 gap-3 flex-wrap">
            <div>
              <h4 class="text-lg font-semibold text-gray-900">{{ agent.name }}</h4>
              <p class="text-sm text-gray-600 mt-1">{{ agent.description }}</p>
              <div class="flex items-center gap-3 mt-2">
                <span class="text-xs text-gray-500">타입: {{ agent.agent_type }}</span>
                <span class="text-xs text-gray-500">버전: v{{ agent.version }}</span>
                <span :class="agent.is_active ? 'text-green-600' : 'text-red-600'" class="text-xs font-semibold">
                  {{ agent.is_active ? '활성' : '비활성' }}
                </span>
              </div>
            </div>
            <div class="flex gap-2">
              <button
                @click="toggleAgentPromptEdit(agent.agent_type)"
                class="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                :disabled="!isAdmin"
              >
                {{ editingAgentType === agent.agent_type ? '취소' : '수정' }}
              </button>
              <button
                @click="deleteAgentPromptEntry(agent.agent_type)"
                class="px-3 py-1 text-sm border border-red-200 text-red-600 rounded-lg hover:bg-red-50 transition-colors disabled:opacity-50"
                :disabled="agentPromptDeleting === agent.agent_type || !isAdmin"
              >
                {{ agentPromptDeleting === agent.agent_type ? '삭제 중...' : '삭제' }}
              </button>
            </div>
          </div>

          <div v-if="editingAgentType === agent.agent_type" class="space-y-4 mt-4 border-t pt-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">이름</label>
              <input
                v-model="editingAgentData.name"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">설명</label>
              <input
                v-model="editingAgentData.description"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">시스템 프롬프트</label>
              <textarea
                v-model="editingAgentData.system_prompt"
                rows="10"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
              ></textarea>
            </div>
            <div class="flex items-center">
              <input
                v-model="editingAgentData.is_active"
                type="checkbox"
                id="agent-active"
                class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label for="agent-active" class="ml-2 text-sm text-gray-700">활성화</label>
            </div>
            <div class="flex gap-2">
              <button
                @click="saveAgentPrompt(agent.agent_type)"
                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                저장
              </button>
              <button
                @click="editingAgentType = null"
                class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                취소
              </button>
            </div>
          </div>

          <div v-else class="mt-4">
            <div class="bg-gray-50 rounded-lg p-4">
              <pre class="text-xs text-gray-700 whitespace-pre-wrap font-mono">{{ agent.system_prompt }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="bg-white rounded-lg shadow overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900">캐시된 종목 관리</h3>
        <p class="text-sm text-gray-500 mt-1">DB에 저장된 종목 가격 데이터 (2009년부터 현재까지)</p>
      </div>

      <div class="px-6 py-5">
        <div v-if="cachedAssetsLoading && !cachedAssetsInitialLoad" class="text-center py-6 text-gray-500">
          로딩 중...
        </div>
        <div v-else class="space-y-4">
          <div class="flex flex-col gap-3">
            <div class="flex flex-col gap-3 md:flex-row md:items-end">
              <div class="flex-1">
                <label class="block text-sm font-medium text-gray-700 mb-1">종목명/티커 검색</label>
                <input
                  v-model="cachedAssetsSearchInput"
                  type="text"
                  placeholder="예: 비트코인 또는 BTC"
                  class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  @keyup.enter="applyCachedAssetsSearch"
                />
              </div>
              <div class="flex-1">
                <label class="block text-sm font-medium text-gray-700 mb-1">Canonical ID 필터</label>
                <select
                  v-model="selectedCanonicalId"
                  @change="applyCanonicalIdFilter"
                  class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="">전체 보기</option>
                  <option v-for="canonicalId in canonicalIds" :key="canonicalId.canonical_id" :value="canonicalId.canonical_id">
                    {{ canonicalId.canonical_id }} - {{ canonicalId.label }}
                  </option>
                </select>
              </div>
              <div class="flex gap-2">
                <button
                  @click="applyCachedAssetsSearch"
                  class="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors whitespace-nowrap"
                >
                  검색
                </button>
                <button
                  @click="resetCachedAssetsSearch"
                  class="px-4 py-2 text-sm border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 whitespace-nowrap"
                  :disabled="!cachedAssetsSearchInput && !cachedAssetsSearchTerm && !selectedCanonicalId"
                >
                  초기화
                </button>
              </div>
            </div>
            <div class="text-sm text-gray-500 text-right">
              페이지 {{ cachedAssetsCurrentPage }} / {{ cachedAssetsTotalPages }}
            </div>
          </div>

          <div v-if="cachedAssets.length" class="relative overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">종목명</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Canonical ID</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">카테고리</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">데이터 기간</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">데이터 포인트</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">소스</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">최종 업데이트</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">작업</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="cache in cachedAssets" :key="cache.id" class="hover:bg-gray-50">
                  <td class="px-4 py-3 text-sm text-gray-900">{{ cache.label }}</td>
                  <td class="px-4 py-3 text-sm font-mono text-gray-600">{{ cache.asset_id }}</td>
                  <td class="px-4 py-3 text-sm text-gray-600">{{ cache.category || '-' }}</td>
                  <td class="px-4 py-3 text-sm text-gray-600">{{ cache.start_year }} - {{ cache.end_year }}</td>
                  <td class="px-4 py-3 text-sm text-gray-600">{{ Object.keys(cache.yearly_prices || {}).length }}년</td>
                  <td class="px-4 py-3 text-sm text-gray-600">{{ cache.source || '-' }}</td>
                  <td class="px-4 py-3 text-sm text-gray-500">{{ formatDateTime(cache.last_updated) }}</td>
                  <td class="px-4 py-3 text-sm">
                    <button
                      @click="deleteCachedAsset(cache)"
                      class="px-2 py-1 text-xs border border-red-200 text-red-600 rounded hover:bg-red-50 transition-colors disabled:opacity-50"
                      :disabled="deletingCacheId === cache.id || !isAdmin"
                    >
                      {{ deletingCacheId === cache.id ? '삭제 중...' : '삭제' }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
            <div
              v-if="cachedAssetsLoading && cachedAssetsInitialLoad"
              class="absolute inset-0 bg-white/50 backdrop-blur-[1px] flex items-center justify-center text-gray-600 text-sm font-medium transition-opacity duration-200"
            >
              <div class="bg-white px-4 py-2 rounded-lg shadow-sm border border-gray-200">
                새 페이지 데이터를 불러오는 중...
              </div>
            </div>
            <div
              class="mt-4 flex flex-col gap-3 text-sm text-gray-500 md:flex-row md:items-center md:justify-between"
            >
              <div>
                총 {{ cachedAssetsTotal }}개 종목 캐시됨
                <template v-if="cachedAssetsSearchTerm">
                  (검색어: "{{ cachedAssetsSearchTerm }}")
                </template>
              </div>
              <div class="flex items-center gap-2 text-gray-700">
                <button
                  @click="prevCachedAssetsPage"
                  class="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                  :disabled="cachedAssetsOffset === 0"
                >
                  이전
                </button>
                <span class="text-sm text-gray-600">{{ cachedAssetsCurrentPage }} / {{ cachedAssetsTotalPages }}</span>
                <button
                  @click="nextCachedAssetsPage"
                  class="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                  :disabled="cachedAssetsOffset + cachedAssetsLimit >= cachedAssetsTotal"
                >
                  다음
                </button>
              </div>
            </div>
          </div>

          <div
            v-else
            class="text-center py-6 text-gray-500 border border-dashed border-gray-200 rounded-lg"
          >
            <p>캐시된 종목이 없습니다.</p>
            <p v-if="cachedAssetsSearchTerm" class="mt-1 text-sm text-gray-400">다른 검색어로 다시 시도해 보세요.</p>
          </div>
        </div>
      </div>
    </div>

    <div class="bg-white rounded-lg shadow overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900">비교 종목 그룹 관리</h3>
        <p class="text-sm text-gray-500 mt-1">Finance 페이지의 빠른 비교 버튼 구성을 수정합니다.</p>
      </div>

      <div class="px-6 py-5 space-y-4">
        <div v-if="quickCompareGroupsLoading" class="text-center py-6 text-gray-500">
          로딩 중...
        </div>
        <div v-else-if="!quickCompareGroups.length" class="text-center py-6 text-gray-500">
          등록된 비교 종목 그룹이 없습니다. 아래에서 추가하세요.
        </div>
        <div v-else class="space-y-4">
          <div
            v-for="group in quickCompareGroups"
            :key="group.id || group.key"
            class="border border-gray-200 rounded-lg p-4 space-y-3"
          >
            <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <div>
                <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide">{{ group.key }}</p>
                <p class="text-base font-semibold text-gray-900">{{ group.label }}</p>
                <div class="flex flex-wrap gap-3 text-xs text-gray-500">
                  <span :class="group.isActive ? 'text-green-600' : 'text-red-600'">
                    {{ group.isActive ? '사용 중' : '비활성' }}
                  </span>
                </div>
              </div>
              <div class="flex gap-2">
                <button
                  @click="editQuickCompareGroup(group)"
                  class="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                  :disabled="!isAdmin"
                >
                  수정
                </button>
                <button
                  @click="deleteFinanceQuickCompareGroup(group)"
                  class="px-3 py-1 text-sm border border-red-200 text-red-600 rounded-lg hover:bg-red-50 transition-colors disabled:opacity-50"
                  :disabled="deletingQuickCompareGroupId === group.id || !isAdmin"
                >
                  {{ deletingQuickCompareGroupId === group.id ? '삭제 중...' : '삭제' }}
                </button>
              </div>
            </div>
            <div class="flex flex-wrap gap-2 bg-gray-50 rounded-lg p-3 border border-gray-200">
              <template v-if="group.resolved_assets && group.resolved_assets.length > 0">
                <div
                  v-for="(asset, idx) in group.resolved_assets"
                  :key="`${asset.ticker || asset.id}-${idx}`"
                  class="inline-flex items-center gap-2 bg-white border border-gray-200 rounded-full px-3 py-1 text-xs"
                >
                  <span class="text-gray-700">{{ asset.label }}</span>
                  <span v-if="asset.ticker && asset.ticker !== asset.label" class="text-gray-400">({{ asset.ticker }})</span>
                  <span v-if="asset.has_cache" class="inline-flex items-center bg-green-100 text-green-700 px-2 py-0.5 rounded-full text-xs font-medium">
                    캐시 있음
                  </span>
                </div>
              </template>
              <template v-else>
                <span class="text-xs text-gray-600">{{ group.assets.join(', ') }}</span>
              </template>
            </div>
          </div>
        </div>
      </div>

      <div class="border-t border-gray-100 bg-gray-50 px-6 py-5 space-y-4">
        <h4 class="text-base font-semibold text-gray-900">
          {{ editingQuickCompareGroupId ? '비교 종목 그룹 수정' : '새 비교 종목 그룹 추가' }}
        </h4>
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Key</label>
            <input
              v-model="quickCompareGroupForm.key"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="예: us_bigtech"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">라벨</label>
            <input
              v-model="quickCompareGroupForm.label"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="예: 미국 빅테크"
            />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">종목 목록</label>
          <div class="flex flex-wrap gap-2 items-center mb-2 p-3 border border-gray-200 rounded-lg min-h-[60px]">
            <div
              v-for="(asset, index) in quickCompareGroupForm.assets"
              :key="`${asset.label}-${asset.ticker || index}`"
              class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm flex items-center gap-2 border border-blue-300"
            >
              <span>{{ asset.display || asset.label }}</span>
              <button @click="removeAssetFromForm(index)" class="text-blue-600 hover:text-blue-800 font-bold">×</button>
            </div>

            <div class="relative flex-1 min-w-[200px]">
              <input
                v-model="newAssetInputForm"
                @keydown.enter.prevent="handleAssetEnterForm"
                type="text"
                placeholder="종목명 입력 (Enter)"
                :disabled="customAssetResolvingForm"
                class="w-full px-3 py-1 text-sm border border-gray-300 rounded-full focus:outline-none focus:border-blue-500 disabled:opacity-50"
              />
              <button
                @click="addAssetToForm"
                :disabled="customAssetResolvingForm"
                class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-blue-500 transition-colors disabled:opacity-40"
              >
                <span v-if="!customAssetResolvingForm">+</span>
                <svg v-else class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke-width="4"></circle>
                  <path class="opacity-75" stroke-width="4" d="M4 12a8 8 0 018-8"></path>
                </svg>
              </button>
            </div>
          </div>
          <p v-if="customAssetErrorForm" class="text-xs text-red-600 mt-1">{{ customAssetErrorForm }}</p>
          <p v-else class="text-xs text-gray-500 mt-1">종목명을 입력하고 Enter를 누르거나 + 버튼을 클릭하세요</p>
        </div>
        <div class="flex items-center gap-2">
          <input
            v-model="quickCompareGroupForm.isActive"
            type="checkbox"
            id="quick-compare-active"
            class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <label for="quick-compare-active" class="text-sm text-gray-700">사용</label>
        </div>
        <div class="flex justify-end">
          <button
            @click="saveFinanceQuickCompareGroup"
            class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
            :disabled="quickCompareGroupSaving || !isAdmin"
          >
            {{ quickCompareGroupSaving ? '저장 중...' : editingQuickCompareGroupId ? '그룹 업데이트' : '그룹 추가' }}
          </button>
        </div>
      </div>
    </div>

    <div class="bg-white rounded-lg shadow overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900">재무 쿼리 로그</h3>
      </div>

      <div v-if="financeLogsLoading && !hasLoadedFinanceLogs" class="text-center py-12 text-gray-500">
        로딩 중...
      </div>

      <div v-else-if="!financeLogs.length" class="text-center py-12 text-gray-500">
        로그가 없습니다.
      </div>

      <div v-else class="relative overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">시간</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">사용자</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">프롬프트</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">컨텍스트</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">자산 수</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">처리시간</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">상태</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="log in financeLogs" :key="log.id" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ formatDateTime(log.created_at) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                {{ log.user_identifier }}
              </td>
              <td class="px-6 py-4 text-sm text-gray-900 max-w-xs">
                <div class="space-y-2">
                  <div class="flex items-start gap-2">
                    <span class="truncate block" :title="log.prompt">
                      {{ log.prompt || '-' }}
                    </span>
                    <span
                      v-if="log.is_prefetch"
                      class="inline-flex items-center px-2 py-0.5 text-[11px] font-medium rounded-full border border-blue-100 bg-blue-50 text-blue-600"
                    >
                      Prefetch
                    </span>
                    <button
                      v-if="log.prompt"
                      class="text-gray-400 hover:text-gray-600 flex-shrink-0"
                      @click="toggleLogPrompt(log.id)"
                      :aria-expanded="expandedLogPromptId === log.id"
                      title="전체 프롬프트 보기"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M13 16h-1v-4h-1m1-4h.01M12 2a10 10 0 100 20 10 10 0 000-20z"
                        />
                      </svg>
                    </button>
                  </div>
                  <div
                    v-if="expandedLogPromptId === log.id"
                    class="text-xs text-gray-700 bg-slate-50 border border-slate-200 rounded p-3 whitespace-pre-wrap"
                  >
                    <p class="font-medium text-gray-900 mb-2">Full Prompt</p>
                    <p>{{ log.prompt }}</p>
                    <div v-if="Array.isArray(log.quick_requests) && log.quick_requests.length" class="mt-2">
                      <p class="font-medium text-gray-900 mb-1">Quick 요청</p>
                      <ul class="list-disc list-inside space-y-0.5">
                        <li v-for="(item, idx) in log.quick_requests" :key="idx">{{ item }}</li>
                      </ul>
                    </div>
                    <div v-if="log.error_message" class="mt-2 text-red-600">
                      <p class="font-medium mb-1">오류</p>
                      <p>{{ log.error_message }}</p>
                    </div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                {{ log.context_key || '-' }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-center">
                {{ log.assets_count }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                {{ log.processing_time_ms ? log.processing_time_ms + 'ms' : '-' }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span
                  v-if="log.success"
                  class="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800"
                >
                  성공
                </span>
                <span
                  v-else
                  class="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800"
                  :title="log.error_message"
                >
                  실패
                </span>
              </td>
            </tr>
          </tbody>
        </table>
        <div
          v-if="cachedAssetsLoading && cachedAssetsInitialLoad"
          class="absolute inset-0 bg-white/50 backdrop-blur-[1px] flex items-center justify-center text-gray-600 text-sm font-medium transition-opacity duration-200"
        >
          <div class="bg-white px-4 py-2 rounded-lg shadow-sm border border-gray-200">
            새 페이지 데이터를 불러오는 중...
          </div>
        </div>
      </div>

      <div
        v-if="financeLogs.length"
        class="px-6 py-4 border-t border-gray-200 flex items-center justify-between"
      >
        <div class="text-sm text-gray-600">
          {{ financeLogsOffset + 1 }} -
          {{ Math.min(financeLogsOffset + financeLogsLimit, financeLogsTotal) }} / {{ financeLogsTotal }}
        </div>
        <div class="flex gap-2">
          <button
            @click="prevFinanceLogsPage"
            :disabled="financeLogsOffset === 0"
            class="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            이전
          </button>
          <button
            @click="nextFinanceLogsPage"
            :disabled="financeLogsOffset + financeLogsLimit >= financeLogsTotal"
            class="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            다음
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'

const props = defineProps({
  isAdmin: { type: Boolean, default: false },
  showSuccess: { type: Function, required: true },
  showError: { type: Function, required: true }
})

const investmentPromptTemplate =
  '{{투자기간}}년 전에 비트코인에 {{투자금}}만원을 투자했다면 지금 얼마인지 알려주고, 비트코인과 비교 종목({{비교자산}})을 비교해줘.'
const investmentPromptVariables = [
  {
    key: '{{투자기간}}',
    description: '사용자가 Finance 화면에서 입력한 투자 시점 (1~30년 사이에서 선택)'
  },
  {
    key: '{{투자금}}',
    description: '입력한 투자 금액(만원 단위, 1~100,000 범위에서 제한)'
  },
  {
    key: '{{비교자산}}',
    description: '사용자가 선택하거나 추가한 비교 종목 목록 (없으면 대표 자산군으로 대체)'
  }
]

const financeLogs = ref([])
const financeLogsLoading = ref(false)
const financeLogsOffset = ref(0)
const financeLogsLimit = ref(10)
const financeLogsTotal = ref(0)
const hasLoadedFinanceLogs = ref(false)
const expandedLogPromptId = ref(null)
const financeStats = ref({
  total_queries: 0,
  successful_queries: 0,
  failed_queries: 0,
  success_rate: 0,
  avg_processing_time_ms: 0,
  queries_last_24h: 0,
  top_users: [],
  top_contexts: []
})

const agentPrompts = ref([])
const agentPromptsLoading = ref(false)
const editingAgentType = ref(null)
const editingAgentData = ref({
  name: '',
  description: '',
  system_prompt: '',
  is_active: true
})
const agentPromptDeleting = ref('')

const quickCompareGroups = ref([])
const quickCompareGroupsLoading = ref(false)
const editingQuickCompareGroupId = ref(null)
const quickCompareGroupSaving = ref(false)
const deletingQuickCompareGroupId = ref(null)
const quickCompareGroupForm = ref({
  key: '',
  label: '',
  assets: [],
  isActive: true
})
const newAssetInputForm = ref('')
const customAssetResolvingForm = ref(false)
const customAssetErrorForm = ref('')

const cachedAssets = ref([])
const cachedAssetsLoading = ref(false)
const cachedAssetsInitialLoad = ref(false)
const cachedAssetsOffset = ref(0)
const cachedAssetsLimit = ref(10)
const cachedAssetsTotal = ref(0)
const cachedAssetsSearchInput = ref('')
const cachedAssetsSearchTerm = ref('')
const deletingCacheId = ref(null)
const canonicalIds = ref([])
const canonicalIdsLoading = ref(false)
const selectedCanonicalId = ref('')

const cachedAssetsCurrentPage = computed(() => {
  if (!cachedAssetsLimit.value) return 1
  return Math.floor(cachedAssetsOffset.value / cachedAssetsLimit.value) + 1
})

const cachedAssetsTotalPages = computed(() => {
  if (!cachedAssetsLimit.value) return 1
  const pages = Math.ceil(cachedAssetsTotal.value / cachedAssetsLimit.value)
  return pages > 0 ? pages : 1
})

const fetchIfAdmin = async () => {
  if (!props.isAdmin) return
  await Promise.all([
    loadFinanceLogs(),
    loadFinanceStats(),
    loadAgentPrompts(),
    loadFinanceQuickCompareGroups(),
    loadCachedAssets(),
    loadCanonicalIds()
  ])
}

const loadFinanceLogs = async () => {
  if (!props.isAdmin) {
    financeLogs.value = []
    financeLogsTotal.value = 0
    hasLoadedFinanceLogs.value = true
    return
  }

  financeLogsLoading.value = true
  try {
    const username = localStorage.getItem('nickname')
    if (!username || localStorage.getItem('isAdmin') !== 'true') {
      throw new Error('관리자 인증 정보가 유효하지 않습니다')
    }

    const params = new URLSearchParams({
      limit: financeLogsLimit.value.toString(),
      offset: financeLogsOffset.value.toString(),
      username
    })
    const response = await fetch(`${import.meta.env.VITE_API_BASE || ''}/api/finance/admin/logs?${params}`, {
      credentials: 'include'
    })
    const data = await response.json()

    if (data.ok) {
      financeLogs.value = (data.logs || []).map((log) => ({
        ...log,
        is_prefetch: Boolean(log.is_prefetch)
      }))
      financeLogsTotal.value = data.total || 0
    } else {
      props.showError(data.error || '로그를 불러올 수 없습니다')
    }
  } catch (error) {
    props.showError(error?.message || '로그 로딩 중 오류가 발생했습니다')
  } finally {
    financeLogsLoading.value = false
    hasLoadedFinanceLogs.value = true
  }
}

const loadFinanceStats = async () => {
  if (!props.isAdmin) return

  try {
    const username = localStorage.getItem('nickname')
    if (!username || localStorage.getItem('isAdmin') !== 'true') {
      throw new Error('관리자 인증 정보가 유효하지 않습니다')
    }

    const params = new URLSearchParams({ username })
    const response = await fetch(`${import.meta.env.VITE_API_BASE || ''}/api/finance/admin/stats?${params}`, {
      credentials: 'include'
    })
    const data = await response.json()

    if (data.ok) {
      financeStats.value = data.stats || financeStats.value
    } else if (data.error) {
      props.showError(data.error)
    }
  } catch (error) {
    console.error('Failed to load finance stats:', error)
  }
}

const formatDateTime = (isoString) => {
  if (!isoString) return '-'
  const date = new Date(isoString)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

const toggleLogPrompt = (logId) => {
  expandedLogPromptId.value = expandedLogPromptId.value === logId ? null : logId
}

const prevFinanceLogsPage = () => {
  if (financeLogsOffset.value > 0) {
    financeLogsOffset.value = Math.max(0, financeLogsOffset.value - financeLogsLimit.value)
    loadFinanceLogs()
  }
}

const nextFinanceLogsPage = () => {
  if (financeLogsOffset.value + financeLogsLimit.value < financeLogsTotal.value) {
    financeLogsOffset.value += financeLogsLimit.value
    loadFinanceLogs()
  }
}

const prevCachedAssetsPage = () => {
  if (cachedAssetsOffset.value <= 0) return
  cachedAssetsOffset.value = Math.max(0, cachedAssetsOffset.value - cachedAssetsLimit.value)
  loadCachedAssets()
}

const nextCachedAssetsPage = () => {
  if (cachedAssetsOffset.value + cachedAssetsLimit.value >= cachedAssetsTotal.value) return
  cachedAssetsOffset.value += cachedAssetsLimit.value
  loadCachedAssets()
}

const applyCachedAssetsSearch = () => {
  const trimmed = cachedAssetsSearchInput.value.trim()
  cachedAssetsSearchInput.value = trimmed
  cachedAssetsSearchTerm.value = trimmed
  cachedAssetsOffset.value = 0
  loadCachedAssets()
}

const applyCanonicalIdFilter = () => {
  cachedAssetsOffset.value = 0
  loadCachedAssets()
}

const resetCachedAssetsSearch = () => {
  if (!cachedAssetsSearchInput.value && !cachedAssetsSearchTerm.value && !selectedCanonicalId.value) return
  cachedAssetsSearchInput.value = ''
  cachedAssetsSearchTerm.value = ''
  selectedCanonicalId.value = ''
  cachedAssetsOffset.value = 0
  loadCachedAssets()
}

const loadAgentPrompts = async () => {
  if (!props.isAdmin) return
  agentPromptsLoading.value = true
  try {
    const { fetchAgentPrompts } = await import('../../services/financeService')
    const data = await fetchAgentPrompts({})
    agentPrompts.value = data.prompts || []
  } catch (error) {
    props.showError(error.message || 'Agent 프롬프트를 불러올 수 없습니다')
  } finally {
    agentPromptsLoading.value = false
  }
}

const toggleAgentPromptEdit = (agentType) => {
  if (editingAgentType.value === agentType) {
    editingAgentType.value = null
    editingAgentData.value = {
      name: '',
      description: '',
      system_prompt: '',
      is_active: true
    }
  } else {
    const agent = agentPrompts.value.find((a) => a.agent_type === agentType)
    if (agent) {
      editingAgentType.value = agentType
      editingAgentData.value = {
        name: agent.name,
        description: agent.description,
        system_prompt: agent.system_prompt,
        is_active: agent.is_active
      }
    }
  }
}

const saveAgentPrompt = async (agentType) => {
  try {
    const { updateAgentPrompt } = await import('../../services/financeService')
    await updateAgentPrompt({
      agentType,
      name: editingAgentData.value.name,
      description: editingAgentData.value.description,
      systemPrompt: editingAgentData.value.system_prompt,
      isActive: editingAgentData.value.is_active
    })
    props.showSuccess('Agent 프롬프트가 업데이트되었습니다')
    editingAgentType.value = null
    await loadAgentPrompts()
  } catch (error) {
    props.showError(error.message || 'Agent 프롬프트 업데이트에 실패했습니다')
  }
}

const initializeAgentPrompts = async () => {
  try {
    const { initializeAgentPrompts } = await import('../../services/financeService')
    await initializeAgentPrompts({})
    props.showSuccess('기본 Agent 프롬프트가 초기화되었습니다')
    await loadAgentPrompts()
  } catch (error) {
    props.showError(error.message || 'Agent 프롬프트 초기화에 실패했습니다')
  }
}

const deleteAgentPromptEntry = async (agentType) => {
  if (!props.isAdmin) return
  if (!confirm('선택한 Agent 프롬프트를 삭제하시겠습니까?')) return
  agentPromptDeleting.value = agentType
  try {
    const { deleteAgentPrompt } = await import('../../services/financeService')
    await deleteAgentPrompt({ agentType })
    props.showSuccess('Agent 프롬프트가 삭제되었습니다')
    if (editingAgentType.value === agentType) {
      editingAgentType.value = null
    }
    await loadAgentPrompts()
  } catch (error) {
    props.showError(error.message || 'Agent 프롬프트 삭제에 실패했습니다')
  } finally {
    agentPromptDeleting.value = ''
  }
}

const normalizeQuickCompareGroup = (entry, index) => {
  const rawAssets = Array.isArray(entry?.assets)
    ? entry.assets
    : Array.isArray(entry?.asset_list)
      ? entry.asset_list
      : []
  const assets = rawAssets.map((asset) => (typeof asset === 'string' ? asset.trim() : '')).filter(Boolean)
  return {
    id: entry?.id ?? index,
    key: entry?.key || `group-${index + 1}`,
    label: entry?.label || `그룹 ${index + 1}`,
    assets,
    sortOrder: Number.isFinite(entry?.sort_order)
      ? Number(entry.sort_order)
      : Number.isFinite(entry?.sortOrder)
        ? Number(entry.sortOrder)
        : index,
    isActive: entry?.is_active !== false
  }
}

const parseAssetsInput = (text = '') =>
  (text || '')
    .split(/[\n,]/)
    .map((value) => value.trim())
    .filter(Boolean)

const loadFinanceQuickCompareGroups = async () => {
  if (!props.isAdmin) return
  quickCompareGroupsLoading.value = true
  try {
    const { fetchAdminFinanceQuickCompareGroups } = await import('../../services/financeService')
    const data = await fetchAdminFinanceQuickCompareGroups({})
    const mapped = (data || [])
      .map((entry, index) => normalizeQuickCompareGroup(entry, index))
      .sort((a, b) => {
        if (a.sortOrder !== b.sortOrder) return a.sortOrder - b.sortOrder
        return (a.id ?? 0) - (b.id ?? 0)
      })
    quickCompareGroups.value = mapped
    const editingExists = mapped.some((group) => group.id === editingQuickCompareGroupId.value)
    if (!editingExists) {
      resetQuickCompareGroupForm()
    }
  } catch (error) {
    props.showError(error.message || '비교 종목 그룹을 불러올 수 없습니다')
  } finally {
    quickCompareGroupsLoading.value = false
  }
}

const editQuickCompareGroup = (group) => {
  if (!group) return
  editingQuickCompareGroupId.value = group.id ?? null

  // Use resolved_assets if available, otherwise fall back to assets
  const resolvedAssets = group.resolved_assets || []
  const assets = resolvedAssets.length > 0
    ? resolvedAssets.map(asset => ({
        label: asset.label,
        ticker: asset.ticker || asset.id,
        display: buildDisplayLabel(asset.label, asset.ticker || asset.id)
      }))
    : (group.assets || []).map(name => ({
        label: name,
        ticker: '',
        display: name
      }))

  quickCompareGroupForm.value = {
    key: group.key || '',
    label: group.label || '',
    assets: assets,
    isActive: group.isActive !== false
  }
}

const resetQuickCompareGroupForm = () => {
  editingQuickCompareGroupId.value = null
  quickCompareGroupForm.value = {
    key: '',
    label: '',
    assets: [],
    isActive: true
  }
  newAssetInputForm.value = ''
  customAssetResolvingForm.value = false
  customAssetErrorForm.value = ''
}

const buildDisplayLabel = (label, ticker) => {
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

const saveFinanceQuickCompareGroup = async () => {
  if (!props.isAdmin) return
  const assetNames = quickCompareGroupForm.value.assets.map(asset => asset.ticker || asset.label)
  const payload = {
    key: (quickCompareGroupForm.value.key || '').trim(),
    label: (quickCompareGroupForm.value.label || '').trim(),
    assets: assetNames,
    is_active: Boolean(quickCompareGroupForm.value.isActive)
  }

  if (!payload.key || !payload.label) {
    props.showError('Key와 라벨을 모두 입력하세요')
    return
  }
  if (!payload.assets.length) {
    props.showError('최소 1개 이상의 비교 종목을 입력하세요')
    return
  }

  quickCompareGroupSaving.value = true
  try {
    const services = await import('../../services/financeService')
    if (editingQuickCompareGroupId.value) {
      await services.updateAdminFinanceQuickCompareGroup(editingQuickCompareGroupId.value, payload)
      props.showSuccess('비교 종목 그룹이 업데이트되었습니다')
    } else {
      await services.createAdminFinanceQuickCompareGroup(payload)
      props.showSuccess('비교 종목 그룹이 추가되었습니다')
    }
    resetQuickCompareGroupForm()
    await loadFinanceQuickCompareGroups()
  } catch (error) {
    props.showError(error.message || '비교 종목 그룹을 저장하지 못했습니다')
  } finally {
    quickCompareGroupSaving.value = false
  }
}

async function handleAssetEnterForm(event) {
  if (event.isComposing) return
  await addAssetToForm()
}

async function addAssetToForm() {
  const raw = (newAssetInputForm.value || '').trim()
  if (!raw || customAssetResolvingForm.value) return

  customAssetResolvingForm.value = true
  customAssetErrorForm.value = ''
  try {
    const { resolveCustomAsset } = await import('../../services/financeService')
    const resolved = await resolveCustomAsset(raw)

    const baseLabel = resolved?.label?.trim() || raw
    const ticker = resolved?.ticker?.trim() || resolved?.id?.trim() || ''

    // Check if asset already exists
    const exists = quickCompareGroupForm.value.assets.some(asset => {
      const labelMatch = asset.label.toLowerCase() === baseLabel.toLowerCase()
      const tickerMatch = ticker && asset.ticker && asset.ticker.toLowerCase() === ticker.toLowerCase()
      return labelMatch || tickerMatch
    })

    if (exists) {
      customAssetErrorForm.value = `'${baseLabel}'은(는) 이미 추가되었습니다.`
      setTimeout(() => {
        if (customAssetErrorForm.value.includes(baseLabel)) {
          customAssetErrorForm.value = ''
        }
      }, 3000)
      return
    }

    const display = buildDisplayLabel(baseLabel, ticker)
    quickCompareGroupForm.value.assets.push({ label: baseLabel, ticker, display })
    newAssetInputForm.value = ''
    customAssetErrorForm.value = ''
  } catch (error) {
    customAssetErrorForm.value = error.message || '종목 정보를 가져오지 못했습니다.'
    setTimeout(() => {
      customAssetErrorForm.value = ''
    }, 5000)
  } finally {
    customAssetResolvingForm.value = false
  }
}

function removeAssetFromForm(index) {
  quickCompareGroupForm.value.assets = quickCompareGroupForm.value.assets.filter((_, i) => i !== index)
}

const deleteFinanceQuickCompareGroup = async (group) => {
  if (!props.isAdmin || !group?.id) return
  if (!confirm('선택한 비교 종목 그룹을 삭제하시겠습니까?')) return
  deletingQuickCompareGroupId.value = group.id
  try {
    const { deleteAdminFinanceQuickCompareGroup } = await import('../../services/financeService')
    await deleteAdminFinanceQuickCompareGroup(group.id)
    props.showSuccess('비교 종목 그룹이 삭제되었습니다')
    if (editingQuickCompareGroupId.value === group.id) {
      resetQuickCompareGroupForm()
    }
    await loadFinanceQuickCompareGroups()
  } catch (error) {
    props.showError(error.message || '비교 종목 그룹 삭제에 실패했습니다')
  } finally {
    deletingQuickCompareGroupId.value = null
  }
}

const loadCachedAssets = async () => {
  if (!props.isAdmin) {
    cachedAssets.value = []
    cachedAssetsTotal.value = 0
    cachedAssetsOffset.value = 0
    cachedAssetsInitialLoad.value = true
    return
  }

  cachedAssetsLoading.value = true
  try {
    const { fetchAdminPriceCache } = await import('../../services/financeService')
    const data = await fetchAdminPriceCache({
      offset: cachedAssetsOffset.value,
      limit: cachedAssetsLimit.value,
      search: cachedAssetsSearchTerm.value,
      canonical_id: selectedCanonicalId.value
    })
    const total = data.total || 0
    if (total > 0 && cachedAssetsOffset.value >= total) {
      const lastPageOffset = Math.floor((total - 1) / cachedAssetsLimit.value) * cachedAssetsLimit.value
      if (lastPageOffset !== cachedAssetsOffset.value) {
        cachedAssetsOffset.value = lastPageOffset
        await loadCachedAssets()
        return
      }
    }

    if (total === 0 && cachedAssetsOffset.value !== 0) {
      cachedAssetsOffset.value = 0
    }

    cachedAssets.value = data.cached_assets || []
    cachedAssetsTotal.value = total
  } catch (error) {
    props.showError(error.message || '캐시된 종목 목록을 불러올 수 없습니다')
  } finally {
    cachedAssetsLoading.value = false
    cachedAssetsInitialLoad.value = true
  }
}

const loadCanonicalIds = async () => {
  if (!props.isAdmin) {
    canonicalIds.value = []
    return
  }

  canonicalIdsLoading.value = true
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE || ''}/api/finance/admin/canonical-ids`, {
      credentials: 'include'
    })
    const data = await response.json()

    if (data.ok) {
      canonicalIds.value = data.canonical_ids || []
    } else {
      props.showError(data.error || 'Canonical ID 목록을 불러올 수 없습니다')
    }
  } catch (error) {
    console.error('Failed to load canonical IDs:', error)
  } finally {
    canonicalIdsLoading.value = false
  }
}

const deleteCachedAsset = async (cache) => {
  if (!props.isAdmin || !cache?.id) return
  if (!confirm(`${cache.label} (${cache.asset_id})의 캐시를 삭제하시겠습니까?`)) return
  deletingCacheId.value = cache.id
  try {
    const { deleteAdminPriceCache } = await import('../../services/financeService')
    await deleteAdminPriceCache(cache.id)
    props.showSuccess('캐시가 삭제되었습니다')
    await loadCachedAssets()
  } catch (error) {
    props.showError(error.message || '캐시 삭제에 실패했습니다')
  } finally {
    deletingCacheId.value = null
  }
}

onMounted(fetchIfAdmin)

watch(
  () => props.isAdmin,
  (value) => {
    if (value) {
      fetchIfAdmin()
    } else {
      financeLogs.value = []
      financeStats.value = {
        total_queries: 0,
        successful_queries: 0,
        failed_queries: 0,
        success_rate: 0,
        avg_processing_time_ms: 0,
        queries_last_24h: 0,
        top_users: [],
        top_contexts: []
      }
      agentPrompts.value = []
      quickCompareGroups.value = []
      cachedAssets.value = []
      cachedAssetsTotal.value = 0
      cachedAssetsOffset.value = 0
      cachedAssetsSearchInput.value = ''
      cachedAssetsSearchTerm.value = ''
    }
  }
)
</script>
