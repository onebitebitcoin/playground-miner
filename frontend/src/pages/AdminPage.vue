<template>
  <div class="min-h-screen bg-gray-50 p-4">
    <div class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">관리자 패널</h1>
        <p class="text-gray-600">시스템 설정을 관리하고 데이터를 모니터링하세요.</p>
      </div>

      <!-- Access notice (no longer blocks content) -->
      <div v-if="!isAdmin" class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center mb-4">
        <p class="text-yellow-800">관리자 모드가 아닙니다. 일부 변경 기능은 비활성화됩니다.</p>
      </div>

      <!-- Admin Content (always visible; write actions gated below) -->
      <div>
        <!-- Admin Tabs -->
        <div class="mb-6">
          <div class="border-b border-gray-200">
            <nav class="-mb-px flex space-x-8" aria-label="Tabs">
              <button
                @click="activeTab = 'mnemonics'"
                :class="[
                  activeTab === 'mnemonics'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm'
                ]"
              >
                니모닉 관리
              </button>
              <button
                @click="activeTab = 'routing'"
                :class="[
                  activeTab === 'routing'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm'
                ]"
              >
                라우팅 관리
              </button>
            </nav>
          </div>
        </div>

        <!-- Mnemonics Tab Content -->
        <div v-if="activeTab === 'mnemonics'" class="grid lg:grid-cols-2 gap-8">
          <!-- Mnemonic Pool Management -->
          <div class="space-y-6">
            <div class="bg-white rounded-lg shadow-md p-6">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">니모닉 풀 관리</h3>

              <!-- Auto Generate Pool -->
              <div class="bg-blue-50 p-4 rounded-lg mb-4">
                <h4 class="font-medium text-blue-800 mb-3">자동 생성 풀</h4>
                <div class="space-y-3">
                  <div class="flex gap-2">
                    <input v-model="mnemonicCount"
                           type="number"
                           min="1"
                           max="50"
                           placeholder="생성할 개수"
                           class="flex-1 px-3 py-2 border border-blue-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
                    <button @click="addMnemonicPool"
                            :disabled="loading || !mnemonicCount || mnemonicCount < 1"
                            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
                      {{ loading ? '생성 중...' : '풀 추가' }}
                    </button>
                  </div>
                  <p class="text-sm text-blue-600">자동으로 생성된 니모닉을 풀에 추가합니다</p>
                </div>
              </div>

              <!-- Manual Mnemonic Add -->
              <div class="bg-green-50 p-4 rounded-lg">
                <h4 class="font-medium text-green-800 mb-3">개별 니모닉 추가</h4>
                <div class="space-y-3">
                  <!-- Individual word inputs -->
                  <div class="grid grid-cols-3 gap-2">
                    <div v-for="i in 12" :key="i" class="relative">
                      <label :for="`admin-word-${i}`" class="block text-xs font-medium text-green-600 mb-1">
                        {{ i }}
                      </label>
                      <input
                        :id="`admin-word-${i}`"
                        v-model="adminMnemonicWords[i-1]"
                        @input="updateAdminManualMnemonic"
                        @paste="handleAdminPaste($event, i-1)"
                        type="text"
                        :placeholder="`단어 ${i}`"
                        class="w-full px-2 py-2 text-sm border border-green-200 rounded focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none"
                        :class="{ 'border-red-300': manualPoolError }"
                      />
                    </div>
                  </div>

                  <!-- Alternative textarea input -->
                  <div class="border-t border-green-200 pt-3">
                    <label class="block text-sm font-medium text-green-700 mb-2">
                      또는 한번에 입력:
                    </label>
                    <textarea v-model="manualPoolMnemonicText"
                              @input="updateAdminFromTextarea"
                              placeholder="12개의 영어 단어를 공백으로 구분하여 입력"
                              class="w-full h-16 px-3 py-2 text-sm border border-green-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none resize-none"
                              :class="{ 'border-red-300': manualPoolError }"></textarea>
                  </div>

                  <div v-if="manualPoolError" class="text-red-600 text-sm">
                    {{ manualPoolError }}
                  </div>

                  <button @click="addManualMnemonicToPool"
                          :disabled="loading || !isValidAdminMnemonicInput"
                          class="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed">
                    {{ loading ? '추가 중...' : '풀에 추가' }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Mnemonic Pool Status -->
          <div class="space-y-6">
            <div class="bg-white rounded-lg shadow-md p-6">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">풀 상태</h3>

              <div class="bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
                <div v-if="adminMnemonics.length === 0" class="text-gray-500 text-center py-8">
                  저장된 니모닉이 없습니다
                </div>
                <div v-else class="space-y-2">
                  <div v-for="mnemonic in adminMnemonics" :key="mnemonic.id"
                       class="flex justify-between items-center p-3 bg-white rounded border">
                    <div class="flex-1">
                      <div class="flex items-center gap-2">
                        <span class="text-sm font-medium text-gray-900">{{ mnemonic.username }}</span>
                        <span v-if="mnemonic.is_assigned"
                              class="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                          할당됨
                        </span>
                        <span v-else
                              class="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                          대기중
                        </span>
                      </div>
                      <span class="text-sm text-gray-500">{{ formatDate(mnemonic.created_at) }}</span>
                    </div>
                    <button @click="showMnemonicInAdmin(mnemonic.mnemonic)"
                            class="text-sm text-blue-600 hover:text-blue-800">
                      보기
                    </button>
                  </div>
                </div>
              </div>

              <!-- Pool Statistics -->
              <div class="bg-yellow-50 p-4 rounded-lg mt-4">
                <h4 class="font-medium text-yellow-800 mb-2">통계</h4>
                <div class="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span class="text-yellow-700">전체 니모닉:</span>
                    <span class="font-medium ml-1">{{ adminMnemonics.length }}</span>
                  </div>
                  <div>
                    <span class="text-yellow-700">사용 가능:</span>
                    <span class="font-medium ml-1">{{ availableMnemonicsCount }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Routing Tab Content (left-side tabs) -->
        <div v-if="activeTab === 'routing'">
          <div class="bg-white rounded-lg shadow-md">
            <div class="grid grid-cols-1 md:grid-cols-4">
              <div class="border-r border-gray-200 p-4 space-y-2">
                <button @click="activeRoutingTab = 'nodes'" :class="[activeRoutingTab === 'nodes' ? 'bg-blue-50 text-blue-700 border border-blue-200' : 'hover:bg-gray-50 text-gray-700 border border-transparent','w-full text-left px-3 py-2 rounded']">서비스 노드 관리</button>
                <button @click="activeRoutingTab = 'routes'" :class="[activeRoutingTab === 'routes' ? 'bg-blue-50 text-blue-700 border border-blue-200' : 'hover:bg-gray-50 text-gray-700 border border-transparent','w-full text-left px-3 py-2 rounded']">경로 관리</button>
                <button @click="activeRoutingTab = 'final'" :class="[activeRoutingTab === 'final' ? 'bg-blue-50 text-blue-700 border border-blue-200' : 'hover:bg-gray-50 text-gray-700 border border-transparent','w-full text-left px-3 py-2 rounded']">최종 경로</button>
              </div>
              <div class="md:col-span-3 p-6">
                <div v-if="routingUpdateLoading" class="bg-blue-50 p-4 rounded-lg mb-4"><p class="text-blue-800">데이터를 로딩하고 있습니다...</p></div>
                <div v-if="activeRoutingTab === 'nodes'">
                  <h3 class="text-lg font-semibold text-gray-900 mb-4">서비스 노드 관리</h3>
                  <div v-if="serviceNodes.length === 0" class="text-center py-8 text-gray-500">서비스 노드가 없습니다. 데이터를 다시 로드해보세요.</div>
                  <div v-else class="space-y-4">
                    <div v-for="node in serviceNodes" :key="node.id" class="border border-gray-200 rounded-lg p-4">
                      <div class="flex items-center justify-between mb-3">
                        <h4 class="font-medium text-gray-900">{{ node.display_name }}</h4>
                        <div class="flex items-center gap-2"><span :class="[node.is_enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800', 'text-xs px-2 py-1 rounded']">{{ node.is_enabled ? '활성' : '비활성' }}</span></div>
                      </div>
                      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                        <div><label class="block text-sm font-medium text-gray-700 mb-1">표시명</label><input v-model="node.display_name" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent" /></div>
                        <div><label class="block text-sm font-medium text-gray-700 mb-1">KYC 상태</label><div class="flex items-center gap-2 mt-2"><label class="flex items-center"><input v-model="node.is_kyc" type="checkbox" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" /><span class="ml-2 text-sm text-gray-700">KYC 필요</span></label></div></div>
                        <div><label class="block text-sm font-medium text-gray-700 mb-1">수탁 유형</label><div class="flex items-center gap-2 mt-2"><label class="flex items-center"><input v-model="node.is_custodial" type="checkbox" class="rounded border-gray-300 text-red-600 focus:ring-red-500" /><span class="ml-2 text-sm text-gray-700">수탁형</span></label></div></div>
                        <div><label class="block text-sm font-medium text-gray-700 mb-1">활성 상태</label><div class="flex items-center gap-2 mt-2"><label class="flex items-center"><input v-model="node.is_enabled" type="checkbox" class="rounded border-gray-300 text-green-600 focus:ring-green-500" /><span class="ml-2 text-sm text-gray-700">활성화</span></label></div></div>
                        <div><label class="block text-sm font-medium text-gray-700 mb-1">작업</label><button @click="updateServiceNode(node)" :disabled="!isAdmin || routingUpdateLoading" class="w-full px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm">{{ routingUpdateLoading ? '업데이트 중...' : '업데이트' }}</button></div>
                      </div>
                      <div class="mt-4"><label class="block text-sm font-medium text-gray-700 mb-1">설명</label><input v-model="node.description" type="text" placeholder="서비스 설명" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent" /></div>
                    </div>
                  </div>
                </div>
                <div v-else-if="activeRoutingTab === 'routes'">
                  <h3 class="text-lg font-semibold text-gray-900 mb-4">경로 관리</h3>
                  <div class="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg mb-6 border border-blue-200">
                    <h4 class="font-semibold text-blue-900 mb-4 flex items-center"><svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/></svg>새 경로 생성</h4>
                    <!-- 그룹 탭: 거래소별 빠른 필터 -->
                    <div class="mb-3">
                      <nav class="flex flex-wrap gap-2 text-sm" aria-label="Node groups">
                        <button @click="routeSelectGroup = 'all'" :class="groupTabClass('all')">전체</button>
                        <button @click="routeSelectGroup = 'upbit'" :class="groupTabClass('upbit')">업비트</button>
                        <button @click="routeSelectGroup = 'bithumb'" :class="groupTabClass('bithumb')">빗썸</button>
                        <button @click="routeSelectGroup = 'binance'" :class="groupTabClass('binance')">바이낸스</button>
                        <button @click="routeSelectGroup = 'okx'" :class="groupTabClass('okx')">OKX</button>
                      </nav>
                    </div>
                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-3">1. 출발지 선택</label>
                        <div class="grid grid-cols-2 gap-2 max-h-56 sm:max-h-72 overflow-y-auto overscroll-contain border rounded p-2 pr-2 bg-white" style="scrollbar-gutter: stable;">
                          <div v-for="node in filteredByGroup(serviceNodes)" :key="`source-${node.id}`" @click="newRoute.sourceId = node.id" :class="['p-2 border rounded cursor-pointer text-sm', newRoute.sourceId === node.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-blue-300']">{{ node.display_name }}</div>
                        </div>
                      </div>
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-3">2. 목적지 선택</label>
                        <div class="grid grid-cols-2 gap-2 h-60 sm:h-72 overflow-y-auto overscroll-contain border rounded p-2 pr-2 bg-white" style="scrollbar-gutter: stable;">
                          <div v-for="node in filteredDestNodes" :key="`dest-${node.id}`" @click="newRoute.sourceId !== node.id ? newRoute.destinationId = node.id : null" :class="['p-2 border rounded cursor-pointer text-sm', newRoute.destinationId === node.id ? 'border-green-500 bg-green-50' : (newRoute.sourceId === node.id ? 'border-gray-200 opacity-60 cursor-not-allowed' : 'border-gray-200 hover:border-green-300')]">{{ node.display_name }}</div>
                        </div>
                      </div>
                      <div><label class="block text-sm font-medium text-gray-700 mb-2">경로 유형</label><select v-model="newRoute.routeType" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"><option disabled value="">선택하세요</option><option value="trading">💱 거래수수료</option><option value="withdrawal_lightning">⚡ 라이트닝 출금</option><option value="withdrawal_onchain">🔗 온체인 출금</option></select></div>
                      <div><label class="block text-sm font-medium text-gray-700 mb-2">생성</label><button @click="createRoute" :disabled="!isAdmin || routingUpdateLoading || !isValidNewRoute" class="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium">{{ routingUpdateLoading ? '추가 중...' : '경로 생성' }}</button></div>
                      <div><label class="block text-sm font-medium text-gray-700 mb-2">비율 수수료 (%)</label><input v-model="newRoute.feeRate" type="number" step="0.0001" min="0" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" /></div>
                      <div><label class="block text-sm font-medium text-gray-700 mb-2">고정 수수료 (BTC)</label><input v-model="newRoute.feeFixed" type="number" step="0.00000001" min="0" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" /></div>
                      <div class="md:col-span-2"><input v-model="newRoute.description" type="text" placeholder="경로 설명 (선택사항)" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" /></div>
                    </div>
                  </div>
                  <div class="mt-8">
                    <!-- Filters -->
                    <div class="mb-4 bg-gray-50 border border-gray-200 p-3 rounded">
                      <div class="grid md:grid-cols-2 gap-3">
                        <div>
                          <label class="block text-sm font-medium text-gray-700 mb-1">출발지 필터</label>
                          <select v-model="routeFilterSources" multiple class="w-full min-h-[2.5rem] px-2 py-1 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none">
                            <option v-for="n in serviceNodes" :key="`srcopt-${n.id}`" :value="n.id">{{ n.display_name }}</option>
                          </select>
                        </div>
                        <div>
                          <label class="block text-sm font-medium text-gray-700 mb-1">목적지 필터</label>
                          <select v-model="routeFilterDestinations" multiple class="w-full min-h-[2.5rem] px-2 py-1 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none">
                            <option v-for="n in serviceNodes" :key="`dstop-${n.id}`" :value="n.id">{{ n.display_name }}</option>
                          </select>
                        </div>
                      </div>
                      <div class="mt-2 text-xs text-gray-600">
                        선택하지 않으면 전체 표시됩니다.
                        <button @click="clearRouteFilters" class="ml-2 px-2 py-0.5 rounded bg-gray-200 hover:bg-gray-300">필터 초기화</button>
                      </div>
                    </div>

                    <!-- Snapshot controls -->
                    <div class="mb-4 bg-white border border-gray-200 rounded-lg p-4">
                      <div class="flex flex-wrap items-center justify-between gap-3">
                        <div class="text-sm text-gray-700">
                          <div class="font-medium">라우팅 스냅샷</div>
                          <div class="text-gray-500">
                            <template v-if="snapshotInfo.has_snapshot">
                              마지막 저장: <span class="font-medium">{{ snapshotInfo.updated_at }}</span>
                              <span class="ml-2 text-xs text-gray-400">(노드 {{ snapshotInfo.counts?.nodes || 0 }}, 경로 {{ snapshotInfo.counts?.routes || 0 }})</span>
                            </template>
                            <template v-else>
                              저장된 스냅샷이 없습니다
                            </template>
                          </div>
                        </div>
                      <div class="flex items-center gap-2">
                        <button @click="saveSnapshot" :disabled="snapshotLoading || !isAdmin" class="px-3 py-1 bg-gray-800 text-white rounded hover:bg-gray-900 disabled:opacity-50 text-xs sm:text-sm">현재 상태 저장</button>
                        <button @click="resetFromSnapshot" :disabled="snapshotLoading || !isAdmin || !snapshotInfo.has_snapshot" class="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 text-xs sm:text-sm">스냅샷으로 초기화</button>
                      </div>
                    </div>
                    <div v-if="snapshotError" class="mt-2 text-sm text-red-600">{{ snapshotError }}</div>
                  </div>

                    <h5 class="text-lg font-medium text-gray-900 mb-4 flex items-center"><svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-1.447-.894L15 4m0 13V4m-6 3l6-3"/></svg>등록된 경로 ({{ filteredRoutes.length }}개)</h5>
                    <div v-if="filteredRoutes.length === 0" class="text-center py-12 text-gray-500 bg-gray-50 rounded-lg"><svg class="w-12 h-12 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-1.447-.894L15 4m0 13V4m-6 3l6-3"/></svg><p class="text-lg font-medium">조건에 맞는 경로가 없습니다</p><p class="text-sm">필터를 조정하거나 초기화하세요</p></div>
                    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      <div v-for="route in filteredRoutes" :key="`${route.source.service}-${route.destination.service}-${route.route_type}`" class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                        <!-- Header -->
                        <div class="flex items-center justify-between mb-3">
                          <div class="flex items-center space-x-2">
                            <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm font-medium">{{ route.source.display_name }}</span>
                            <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                            <span class="px-2 py-1 bg-green-100 text-green-800 rounded text-sm font-medium">{{ route.destination.display_name }}</span>
                          </div>
                          <button v-if="isAdmin" @click="deleteRoute(route.id)" :disabled="routingUpdateLoading" class="text-red-600 hover:text-red-800 p-1 rounded hover:bg-red-50 transition-colors" title="삭제">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                          </button>
                        </div>

                        <!-- Badges -->
                        <div class="mb-3">
                          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">{{ getRouteTypeDisplay(route.route_type) }}</span>
                          <span :class="[route.is_enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800', 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ml-2']">{{ route.is_enabled ? '✓ 활성' : '✗ 비활성' }}</span>
                        </div>

                        <!-- Edit form -->
                        <div v-if="isAdmin" class="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                          <div>
                            <label class="block text-xs font-medium text-gray-600 mb-1">유형</label>
                            <select v-model="route.edit_route_type" class="w-full px-2 py-1 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none">
                              <option value="trading">거래 수수료</option>
                              <option value="withdrawal_lightning">라이트닝 출금</option>
                              <option value="withdrawal_onchain">온체인 출금</option>
                            </select>
                          </div>
                          <div>
                            <label class="block text-xs font-medium text-gray-600 mb-1">비율 수수료(%)</label>
                            <input v-model.number="route.edit_fee_rate" type="number" step="0.0001" min="0" class="w-full px-2 py-1 border border-gray-300 rounded-md" />
                          </div>
                          <div>
                            <label class="block text-xs font-medium text-gray-600 mb-1">고정 수수료(BTC)</label>
                            <input v-model.number="route.edit_fee_fixed" type="number" step="0.00000001" min="0" class="w-full px-2 py-1 border border-gray-300 rounded-md" />
                          </div>
                          <div class="md:col-span-3 flex justify-end">
                            <button @click="updateExistingRoute(route)" :disabled="routingUpdateLoading" class="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50">{{ routingUpdateLoading ? '저장 중...' : '저장' }}</button>
                          </div>
                        </div>

                        <!-- Read-only fee display for non-admin -->
                        <div v-else class="space-y-2 text-sm">
                          <div v-if="route.fee_rate !== null" class="flex justify-between"><span class="text-gray-600">비율 수수료:</span><span class="font-medium text-blue-600">{{ route.fee_rate }}%</span></div>
                          <div v-if="route.fee_fixed !== null" class="flex justify-between"><span class="text-gray-600">고정 수수료:</span><span class="font-medium text-orange-600">{{ route.fee_fixed }} BTC</span></div>
                          <div v-if="!route.fee_rate && !route.fee_fixed" class="flex justify-between"><span class="text-gray-600">수수료:</span><span class="font-medium text-green-600">무료</span></div>
                        </div>

                        <div v-if="route.description" class="flex justify-between border-t pt-2 mt-2 text-sm"><span class="text-gray-600">설명:</span><span class="font-medium text-gray-800 text-right max-w-xs truncate">{{ route.description }}</span></div>
                      </div>
                    </div>
                    <div v-if="routingUpdateSuccess" class="p-3 bg-green-50 border border-green-200 rounded-lg mt-4"><div class="flex items-center"><svg class="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" /></svg><p class="text-green-700">라우팅 설정이 성공적으로 업데이트되었습니다!</p></div></div>
                    <div v-if="routingUpdateError" class="p-3 bg-red-50 border border-red-200 rounded-lg mt-2"><div class="flex items-center"><svg class="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" /></svg><p class="text-red-700">{{ routingUpdateError }}</p></div></div>
                  </div>
                </div>
                <!-- Final combined paths -->
                <div v-else>
                    <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-gray-900">최종 경로(조합) <span class="text-sm text-gray-500">({{ sortedOptimalPaths.length }}개)</span></h3>
                    <div class="flex items-center gap-3">
                      <div class="flex items-center gap-1">
                        <label class="text-sm text-gray-700">송금 금액</label>
                        <input v-model.number="sendAmountInput" type="number" min="0" step="1" placeholder="예: 100"
                               class="w-28 px-2 py-1 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
                        <select v-model="sendUnit" class="px-2 py-1 border border-gray-300 rounded bg-white text-sm">
                          <option value="1">원</option>
                          <option value="10000">만원</option>
                          <option value="100000000">억원</option>
                        </select>
                      </div>
                      <label class="text-sm text-gray-700">BTC 가격(KRW)</label>
                      <span class="text-sm font-semibold text-gray-900">{{ btcPriceKrw ? formatKRW(btcPriceKrw) : '불러오는 중...' }}</span>
                      <button @click="fetchBtcPriceKrw" class="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded">가격 새로고침</button>
                      <button @click="loadOptimalPaths" :disabled="optimalLoading" class="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50">{{ optimalLoading ? '계산 중...' : '다시 계산' }}</button>
                    </div>
                  </div>
                  <div v-if="optimalError" class="p-3 bg-red-50 border border-red-200 rounded text-red-700 mb-3">{{ optimalError }}</div>
                  <div v-if="optimalPaths.length === 0 && !optimalLoading" class="text-gray-500 text-sm">경로가 없습니다. 상단에서 경로를 추가한 뒤 다시 계산하세요.</div>
                  <div class="space-y-4" v-else>
                    <div v-for="(path, idx) in sortedOptimalPaths" :key="path.path_signature || idx" class="border border-gray-200 rounded p-4">
                    <div class="flex items-center justify-between mb-2">
                      <div class="font-medium text-gray-900">경로 #{{ idx + 1 }}</div>
                      <div class="text-sm text-gray-600">
                        총 비율 수수료: <span class="font-semibold">{{ computePathFees(path.routes).rate.toFixed(4) }}%</span>
                        • 총 고정 수수료: <span class="font-semibold">{{ computePathFees(path.routes).fixed.toFixed(8) }} BTC</span>
                        <template v-if="btcPriceKrw && computePathFees(path.routes).fixed">
                          (≈ {{ formatKRW(computePathFees(path.routes).fixed * btcPriceKrw) }})
                        </template>
                        <template v-if="sendAmountKRW > 0 && btcPriceKrw">
                          • 총 예상 수수료: <span class="font-semibold text-blue-700">{{ formatKRW(computeTotalFeeKRW(path)) }}</span>
                        </template>
                      </div>
                    </div>
                    <div class="flex flex-wrap items-center text-sm">
                      <template v-for="(r, i) in path.routes" :key="i">
                        <span class="px-2 py-1 bg-blue-50 text-blue-800 rounded">{{ r.source.display_name }}</span>
                        <svg class="w-4 h-4 mx-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                        <span v-if="i === path.routes.length - 1" class="px-2 py-1 bg-green-50 text-green-800 rounded">{{ r.destination.display_name }}</span>
                      </template>
                    </div>
                    <div class="mt-2 grid grid-cols-1 gap-2 text-xs text-gray-600">
                      <div v-for="(r, i) in path.routes" :key="'d'+i" class="flex justify-between bg-gray-50 px-2 py-1 rounded">
                        <span>{{ r.source.display_name }} → {{ r.destination.display_name }} ({{ getRouteTypeDisplay(r.route_type) }})</span>
                        <span>
                          <template v-if="r.fee_rate !== null">{{ r.fee_rate }}%</template>
                          <template v-if="r.fee_fixed !== null">{{ r.fee_rate !== null ? ' + ' : ''}}{{ r.fee_fixed }} BTC</template>
                          <template v-if="r.fee_rate === null && r.fee_fixed === null">무료</template>
                        </span>
                      </div>
                    </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Success Message -->
      <div v-if="successMessage" class="fixed bottom-4 right-4 bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg">
        {{ successMessage }}
      </div>

      <!-- Error Message -->
      <div v-if="errorMessage" class="fixed bottom-4 right-4 bg-red-600 text-white px-4 py-2 rounded-lg shadow-lg">
        {{ errorMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import {
  apiRequestMnemonic,
  apiGenerateMnemonic,
  apiSaveMnemonic,
  apiGetAdminMnemonics,
  apiGetServiceNodes,
  apiUpdateServiceNode,
  apiGetRoutes,
  apiCreateRoute,
  apiDeleteRoute,
  apiGetOptimalPaths,
  apiGetRoutingSnapshotInfo,
  apiSaveRoutingSnapshot,
  apiResetRoutingFromSnapshot
} from '../api'

// State
const loading = ref(false)
const successMessage = ref('')
const errorMessage = ref('')
const activeTab = ref('mnemonics')
const activeRoutingTab = ref('nodes')

// Mnemonic management state
const mnemonicCount = ref(10)
const manualPoolMnemonicText = ref('')
const adminMnemonicWords = ref(Array(12).fill(''))
const manualPoolError = ref('')
const adminMnemonics = ref([])

// (fee management removed)

// Routing management state
const serviceNodes = ref([])
const routes = ref([])
const routingUpdateLoading = ref(false)
const routingUpdateSuccess = ref(false)
const routingUpdateError = ref('')
// removed forceRerenderKey
const newRoute = ref({
  sourceId: '',
  destinationId: '',
  routeType: '',
  feeRate: null,
  feeFixed: null,
  description: ''
})

// Final path (optimal) state
const optimalPaths = ref([])
const optimalLoading = ref(false)
const optimalError = ref('')
const btcPriceKrw = ref(0) // KRW per 1 BTC
// Snapshot state
const snapshotInfo = ref({ has_snapshot: false, updated_at: '', counts: { nodes: 0, routes: 0 } })
const snapshotLoading = ref(false)
const snapshotError = ref('')
// User-entered remittance amount (KRW)
const sendAmountInput = ref('')
const sendUnit = ref('10000') // 기본 만원 단위

// Creation UI group filter
const routeSelectGroup = ref('all') // 'all' | 'upbit' | 'bithumb' | 'binance' | 'okx'

// Route filters
const routeFilterSources = ref([]) // array<number>
const routeFilterDestinations = ref([]) // array<number>

// Computed
const isAdmin = computed(() => {
  const nickname = localStorage.getItem('nickname')
  const adminStatus = localStorage.getItem('isAdmin')
  return nickname === 'admin' && adminStatus === 'true'
})

const availableMnemonicsCount = computed(() => {
  return adminMnemonics.value.filter(m => !m.is_assigned).length
})

const isValidAdminMnemonicInput = computed(() => {
  const words = adminMnemonicWords.value.filter(w => w.trim().length > 0)
  return words.length === 12 || (manualPoolMnemonicText.value.trim().split(/\s+/).length === 12)
})

const isValidNewRoute = computed(() => {
  return newRoute.value.sourceId && newRoute.value.destinationId && newRoute.value.routeType &&
         (newRoute.value.feeRate !== null && newRoute.value.feeRate !== '' ||
          newRoute.value.feeFixed !== null && newRoute.value.feeFixed !== '')
})

const filteredRoutes = computed(() => {
  const srcSet = new Set(routeFilterSources.value || [])
  const dstSet = new Set(routeFilterDestinations.value || [])
  return (routes.value || []).filter(r => {
    const srcOk = srcSet.size === 0 || srcSet.has(r.source.id)
    const dstOk = dstSet.size === 0 || dstSet.has(r.destination.id)
    return srcOk && dstOk
  })
})

// (admin debug view removed)

// Utility functions
const getCurrentUsername = () => {
  return localStorage.getItem('nickname') || 'anonymous'
}

// Ensure admin endpoints always receive 'admin' to satisfy backend check
const getAdminUsername = () => {
  return isAdmin.value ? 'admin' : getCurrentUsername()
}

// (admin debug view removed)

const validateMnemonic = (mnemonic) => {
  const words = mnemonic.trim().split(/\s+/)
  if (words.length !== 12) {
    return '니모닉은 정확히 12개의 단어로 구성되어야 합니다'
  }

  for (const word of words) {
    if (!/^[a-z]+$/.test(word)) {
      return '모든 단어는 영어 소문자여야 합니다'
    }
  }

  return null
}

const showSuccessMessage = (message) => {
  successMessage.value = message
  setTimeout(() => {
    successMessage.value = ''
  }, 3000)
}

const showErrorMessage = (message) => {
  errorMessage.value = message
  setTimeout(() => {
    errorMessage.value = ''
  }, 3000)
}

const formatDate = (dateString) => {
  try {
    return new Date(dateString).toLocaleString('ko-KR')
  } catch {
    return dateString
  }
}

// Helper functions for route creation interface
const getNodeDisplayName = (nodeId) => {
  if (!nodeId) return ''
  const node = serviceNodes.value.find(n => n.id === nodeId)
  return node ? node.display_name : ''
}

const getRouteTypeDisplay = (routeType) => {
  const types = {
    'trading': '💱 거래수수료',
    'withdrawal_lightning': '⚡ 라이트닝 출금',
    'withdrawal_onchain': '🔗 온체인 출금'
  }
  return types[routeType] || routeType
}

// Compute aggregate fee for a path
const computePathFees = (pathRoutes) => {
  let totalRate = 0
  let totalFixed = 0
  for (const r of pathRoutes || []) {
    if (r.fee_rate !== null && r.fee_rate !== undefined) totalRate += Number(r.fee_rate) || 0
    if (r.fee_fixed !== null && r.fee_fixed !== undefined) totalFixed += Number(r.fee_fixed) || 0
  }
  return { rate: totalRate, fixed: totalFixed }
}

const formatKRW = (n) => {
  try { return Number(n).toLocaleString('ko-KR') + '원' } catch { return n + '원' }
}

// Helpers for creation UI grouping and destination filtering
const groupTabClass = (name) => {
  return [
    'px-3 py-1 rounded border',
    routeSelectGroup.value === name ? 'bg-white border-blue-300 text-blue-700' : 'bg-white/60 border-gray-200 hover:bg-white'
  ]
}

const filteredByGroup = (nodes) => {
  if (routeSelectGroup.value === 'all') return nodes
  return nodes.filter(n => {
    switch (routeSelectGroup.value) {
      case 'upbit': return n.service?.startsWith('upbit')
      case 'bithumb': return n.service?.startsWith('bithumb')
      case 'binance': return n.service?.startsWith('binance')
      case 'okx': return n.service?.startsWith('okx')
      default: return true
    }
  })
}

const selectedSource = computed(() => serviceNodes.value.find(n => n.id === newRoute.value.sourceId) || null)
const disallowedDestForUser = new Set(['binance','binance_usdt','binance_btc','okx','okx_usdt','okx_btc'])
const filteredDestNodes = computed(() => {
  let nodes = filteredByGroup(serviceNodes.value)
  if (selectedSource.value) {
    const srcSvc = selectedSource.value.service
    if (srcSvc === 'user') {
      nodes = nodes.filter(n => !disallowedDestForUser.has(n.service))
    }
    if (srcSvc === 'upbit_usdt') {
      nodes = nodes.filter(n => n.service !== 'upbit_btc')
    }
    if (srcSvc === 'bithumb_usdt') {
      nodes = nodes.filter(n => n.service !== 'bithumb_btc')
    }
  }
  // Exclude selecting the same node as destination
  return nodes.filter(n => n.id !== newRoute.value.sourceId)
})

// Route creation presets and helpers
const clearRoute = () => {
  newRoute.value = {
    sourceId: '',
    destinationId: '',
    routeType: '',
    feeRate: null,
    feeFixed: null,
    description: ''
  }
}

const applyPreset = (presetType) => {
  clearRoute()

  const exchangeNodes = serviceNodes.value.filter(n => ['binance', 'okx', 'upbit', 'bithumb'].includes(n.service))
  const lightningNodes = serviceNodes.value.filter(n => ['coinos', 'strike', 'walletofsatoshi'].includes(n.service))
  const walletNode = serviceNodes.value.find(n => n.service === 'personal_wallet')

  switch (presetType) {
    case 'exchange-lightning':
      if (exchangeNodes.length > 0 && lightningNodes.length > 0) {
        newRoute.value.sourceId = exchangeNodes[0].id
        newRoute.value.destinationId = lightningNodes[0].id
        newRoute.value.routeType = 'withdrawal_lightning'
        newRoute.value.feeFixed = 0.00001
        newRoute.value.description = '거래소에서 라이트닝 서비스로 출금'
      }
      break

    case 'lightning-wallet':
      if (lightningNodes.length > 0 && walletNode) {
        newRoute.value.sourceId = lightningNodes[0].id
        newRoute.value.destinationId = walletNode.id
        newRoute.value.routeType = 'withdrawal_onchain'
        newRoute.value.description = '라이트닝 서비스에서 개인지갑으로 출금'
      }
      break

    case 'exchange-onchain':
      if (exchangeNodes.length > 0 && walletNode) {
        newRoute.value.sourceId = exchangeNodes[0].id
        newRoute.value.destinationId = walletNode.id
        newRoute.value.routeType = 'withdrawal_onchain'
        newRoute.value.feeFixed = 0.0005
        newRoute.value.description = '거래소에서 개인지갑으로 직접 출금'
      }
      break
  }
}

// Mnemonic management functions
const updateAdminManualMnemonic = () => {
  const words = adminMnemonicWords.value.filter(w => w.trim().length > 0)
  manualPoolMnemonicText.value = adminMnemonicWords.value.join(' ').trim()
}

const updateAdminFromTextarea = () => {
  const words = manualPoolMnemonicText.value.trim().split(/\s+/).filter(w => w.length > 0)

  for (let i = 0; i < 12; i++) {
    adminMnemonicWords.value[i] = words[i] || ''
  }
}

const handleAdminPaste = (event, startIndex) => {
  event.preventDefault()
  const pastedText = (event.clipboardData || window.clipboardData).getData('text')
  const words = pastedText.trim().split(/\s+/).filter(w => w.length > 0)

  for (let i = 0; i < 12; i++) {
    adminMnemonicWords.value[i] = words[i] || ''
  }

  updateAdminManualMnemonic()
}

const addMnemonicPool = async () => {
  if (!mnemonicCount.value || mnemonicCount.value < 1) return

  loading.value = true
  let addedCount = 0

  try {
    for (let i = 0; i < mnemonicCount.value; i++) {
      const username = `pool_${Date.now()}_${i}`
      const response = await apiGenerateMnemonic()

      if (response.success && response.mnemonic) {
        const saveResponse = await apiSaveMnemonic(response.mnemonic, username)
        if (saveResponse.success) {
          addedCount++
        }
      }
    }

    if (addedCount > 0) {
      showSuccessMessage(`${addedCount}개의 니모닉이 풀에 추가되었습니다`)
      await loadAdminData()
    } else {
      showErrorMessage('니모닉 추가에 실패했습니다')
    }
  } catch (error) {
    showErrorMessage('네트워크 오류가 발생했습니다')
  } finally {
    loading.value = false
  }
}

const addManualMnemonicToPool = async () => {
  manualPoolError.value = ''

  const finalMnemonic = manualPoolMnemonicText.value.trim() || adminMnemonicWords.value.join(' ').trim()
  const error = validateMnemonic(finalMnemonic)
  if (error) {
    manualPoolError.value = error
    return
  }

  loading.value = true
  try {
    const username = `manual_${Date.now()}`
    const response = await apiSaveMnemonic(finalMnemonic, username)

    if (response.success) {
      showSuccessMessage('니모닉이 풀에 추가되었습니다')

      // Clear all inputs
      manualPoolMnemonicText.value = ''
      adminMnemonicWords.value = Array(12).fill('')

      await loadAdminData()
    } else {
      manualPoolError.value = response.error || '니모닉 저장에 실패했습니다'
    }
  } catch (error) {
    manualPoolError.value = '네트워크 오류가 발생했습니다'
  } finally {
    loading.value = false
  }
}

const showMnemonicInAdmin = (mnemonic) => {
  alert(`니모닉: ${mnemonic}`)
}



// (fee management removed)

// Routing management functions
const loadServiceNodes = async () => {
  try {
    const username = getCurrentUsername()
    console.log('Loading service nodes for user:', username)
    const response = await apiGetServiceNodes(username)
    console.log('Service nodes response:', response)
    if (response.success) {
      serviceNodes.value = Array.isArray(response.nodes) ? [...response.nodes] : []
    } else {
      routingUpdateError.value = response.error || '서비스 노드 데이터 로드에 실패했습니다'
    }
  } catch (error) {
    routingUpdateError.value = '네트워크 오류'
  }
}

const loadRoutes = async () => {
  try {
    const username = getCurrentUsername()
    const response = await apiGetRoutes(username)
    if (response.success) {
      routes.value = (response.routes || []).map(r => ({
        ...r,
        edit_route_type: r.route_type,
        edit_fee_rate: r.fee_rate,
        edit_fee_fixed: r.fee_fixed,
      }))
    } else {
      routingUpdateError.value = response.error || '경로 데이터 로드에 실패했습니다'
    }
  } catch (error) {
    routingUpdateError.value = '네트워크 오류'
  }
}

const updateServiceNode = async (node) => {
  routingUpdateLoading.value = true
  routingUpdateSuccess.value = false
  routingUpdateError.value = ''

  try {
    const username = getCurrentUsername()
    const response = await apiUpdateServiceNode(
      username,
      node.service,
      node.display_name,
      node.is_kyc,
      node.is_custodial,
      node.is_enabled,
      node.description,
      node.website_url || ''
    )

    if (response.success) {
      routingUpdateSuccess.value = true
      // Update the local node data
      const index = serviceNodes.value.findIndex(n => n.service === node.service)
      if (index !== -1) {
        serviceNodes.value[index] = response.node
      }

      // Clear success message after 3 seconds
      setTimeout(() => {
        routingUpdateSuccess.value = false
      }, 3000)
    } else {
      routingUpdateError.value = response.error || '서비스 노드 업데이트에 실패했습니다'
    }
  } catch (error) {
    routingUpdateError.value = '네트워크 오류'
  } finally {
    routingUpdateLoading.value = false
  }
}

const createRoute = async () => {
  routingUpdateLoading.value = true
  routingUpdateSuccess.value = false
  routingUpdateError.value = ''

  try {
    const username = getCurrentUsername()
    const response = await apiCreateRoute(
      username,
      parseInt(newRoute.value.sourceId),
      parseInt(newRoute.value.destinationId),
      newRoute.value.routeType,
      newRoute.value.feeRate ? parseFloat(newRoute.value.feeRate) : null,
      newRoute.value.feeFixed ? parseFloat(newRoute.value.feeFixed) : null,
      true, // is_enabled
      newRoute.value.description
    )

    if (response.success) {
      routingUpdateSuccess.value = true

      // Add the new route to the list
      routes.value.push({
        ...response.route,
        edit_route_type: response.route.route_type,
        edit_fee_rate: response.route.fee_rate,
        edit_fee_fixed: response.route.fee_fixed,
      })

      // Reset form
      newRoute.value = {
        sourceId: '',
        destinationId: '',
        routeType: '',
        feeRate: null,
        feeFixed: null,
        description: ''
      }

      // Clear success message after 3 seconds
      setTimeout(() => {
        routingUpdateSuccess.value = false
      }, 3000)
    } else {
      routingUpdateError.value = response.error || '경로 생성에 실패했습니다'
    }
  } catch (error) {
    routingUpdateError.value = '네트워크 오류'
  } finally {
    routingUpdateLoading.value = false
  }
}

const deleteRoute = async (routeId) => {
  if (!confirm('이 경로를 삭제하시겠습니까?')) return

  routingUpdateLoading.value = true
  routingUpdateSuccess.value = false
  routingUpdateError.value = ''

  try {
    const username = getCurrentUsername()
    const response = await apiDeleteRoute(username, routeId)

    if (response.success) {
      routingUpdateSuccess.value = true

      // Remove the route from the list
      routes.value = routes.value.filter(r => r.id !== routeId)

      // Clear success message after 3 seconds
      setTimeout(() => {
        routingUpdateSuccess.value = false
      }, 3000)
    } else {
      routingUpdateError.value = response.error || '경로 삭제에 실패했습니다'
    }
  } catch (error) {
    routingUpdateError.value = '네트워크 오류'
  } finally {
    routingUpdateLoading.value = false
  }
}

const updateExistingRoute = async (route) => {
  routingUpdateLoading.value = true
  routingUpdateSuccess.value = false
  routingUpdateError.value = ''
  try {
    const username = getCurrentUsername()
    const newType = route.edit_route_type || route.route_type
    const newFeeRate = route.edit_fee_rate !== undefined && route.edit_fee_rate !== null && route.edit_fee_rate !== ''
      ? Number(route.edit_fee_rate)
      : null
    const newFeeFixed = route.edit_fee_fixed !== undefined && route.edit_fee_fixed !== null && route.edit_fee_fixed !== ''
      ? Number(route.edit_fee_fixed)
      : null

    // Create or update the (source, dest, newType)
    const resp = await apiCreateRoute(
      username,
      route.source.id,
      route.destination.id,
      newType,
      newFeeRate,
      newFeeFixed,
      route.is_enabled,
      route.description || ''
    )

    if (!resp.success) {
      routingUpdateError.value = resp.error || '경로 업데이트에 실패했습니다'
      return
    }

    const updated = resp.route
    // If the type changed, delete the old one
    if (newType !== route.route_type) {
      await apiDeleteRoute(username, route.id)
      // Replace element in routes array
      routes.value = routes.value.map(r => r.id === route.id ? {
        ...updated,
        edit_route_type: updated.route_type,
        edit_fee_rate: updated.fee_rate,
        edit_fee_fixed: updated.fee_fixed,
      } : r)
    } else {
      // Same key; just patch fields
      routes.value = routes.value.map(r => r.id === route.id ? {
        ...updated,
        edit_route_type: updated.route_type,
        edit_fee_rate: updated.fee_rate,
        edit_fee_fixed: updated.fee_fixed,
      } : r)
    }

    routingUpdateSuccess.value = true
    setTimeout(() => (routingUpdateSuccess.value = false), 2000)
  } catch (e) {
    routingUpdateError.value = '네트워크 오류'
  } finally {
    routingUpdateLoading.value = false
  }
}

// Load optimal paths (combine registered routes)
const loadOptimalPaths = async () => {
  optimalLoading.value = true
  optimalError.value = ''
  try {
    const res = await apiGetOptimalPaths(500)
    if (res.success) {
      optimalPaths.value = res.paths || []
    } else {
      optimalError.value = res.error || '최적 경로 계산에 실패했습니다'
    }
  } catch (e) {
    optimalError.value = '네트워크 오류'
  } finally {
    optimalLoading.value = false
  }
}

// Snapshot handlers
const loadSnapshotInfo = async () => {
  snapshotLoading.value = true
  snapshotError.value = ''
  try {
    const res = await apiGetRoutingSnapshotInfo()
    if (res.success) snapshotInfo.value = res.info
    else snapshotError.value = res.error || '스냅샷 정보를 불러오지 못했습니다'
  } catch (_) {
    snapshotError.value = '네트워크 오류'
  } finally {
    snapshotLoading.value = false
  }
}

// getAdminUsername is defined earlier; reuse it

const saveSnapshot = async () => {
  if (!isAdmin.value) { showErrorMessage('관리자만 가능합니다'); return }
  snapshotLoading.value = true
  snapshotError.value = ''
  try {
    const res = await apiSaveRoutingSnapshot(getAdminUsername())
    if (res.success) { await loadSnapshotInfo(); showSuccessMessage('현재 상태를 스냅샷으로 저장했습니다') }
    else showErrorMessage(res.error || '스냅샷 저장 실패')
  } finally { snapshotLoading.value = false }
}

const resetFromSnapshot = async () => {
  if (!isAdmin.value) { showErrorMessage('관리자만 가능합니다'); return }
  if (!confirm('저장된 스냅샷으로 경로/노드를 초기화합니다. 진행하시겠습니까?')) return
  snapshotLoading.value = true
  snapshotError.value = ''
  try {
    const res = await apiResetRoutingFromSnapshot(getAdminUsername())
    if (res.success) {
      await loadServiceNodes();
      await loadRoutes();
      await loadOptimalPaths();
      await loadSnapshotInfo();
      showSuccessMessage('스냅샷으로 초기화되었습니다')
    } else {
      showErrorMessage(res.error || '초기화 실패')
    }
  } finally { snapshotLoading.value = false }
}

// Fetch BTC price (KRW) via public API
const fetchBtcPriceKrw = async () => {
  try {
    const resp = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=krw')
    const data = await resp.json()
    const price = data?.bitcoin?.krw
    if (typeof price === 'number' && price > 0) {
      btcPriceKrw.value = price
    }
  } catch (e) {
    console.error('Failed to fetch BTC price (KRW):', e)
  }
}

// Filters helpers
const clearRouteFilters = () => {
  routeFilterSources.value = []
  routeFilterDestinations.value = []
}

// Load initial data (mnemonics for admin)
const loadData = async () => {
  loading.value = true
  try {
    if (isAdmin.value) {
      const username = getCurrentUsername()
      // Mnemonics for admin only
      try {
        const res = await apiGetAdminMnemonics(username)
        if (res.success) adminMnemonics.value = res.mnemonics
      } catch (_) {}
    }
  } finally {
    loading.value = false
  }
}

// Load admin data on mount if admin
onMounted(async () => {
  console.log('AdminPage mounted, isAdmin:', isAdmin.value)
  await loadData()
  // Preload BTC price for final path KRW display
  await fetchBtcPriceKrw()
  // Ensure routing data loads on first enter
  if (activeTab.value === 'routing') {
    routingUpdateLoading.value = true
    try {
      await loadServiceNodes()
      await loadRoutes()
      await loadSnapshotInfo()
    } finally {
      routingUpdateLoading.value = false
    }
  }
})

// Load routing data when routing tab becomes active (immediate)
watch(() => activeTab.value, async (newTab) => {
  if (newTab === 'routing') {
    routingUpdateLoading.value = true
    try {
      // Refresh BTC price when entering routing tab
      await fetchBtcPriceKrw()
      await loadServiceNodes()
      await loadRoutes()
      await loadSnapshotInfo()
      await loadOptimalPaths()
    } finally {
      routingUpdateLoading.value = false
    }
  }
}, { immediate: true })

// Computed helpers for final path fee calculation
const sendAmountKRW = computed(() => {
  const a = Number(sendAmountInput.value || 0)
  const u = Number(sendUnit.value || 1)
  if (!isFinite(a) || !isFinite(u)) return 0
  return a * u
})

const computeTotalFeeKRW = (path) => {
  if (!path || !Array.isArray(path.routes)) return 0
  const { rate, fixed } = computePathFees(path.routes)
  const rateFee = (sendAmountKRW.value || 0) * (Number(rate) || 0) / 100
  const fixedFee = (Number(fixed) || 0) * (btcPriceKrw.value || 0)
  // 소수점 버림 처리
  return Math.max(0, Math.floor(rateFee + fixedFee))
}

const sortedOptimalPaths = computed(() => {
  const arr = [...(optimalPaths.value || [])]
  if ((sendAmountKRW.value || 0) > 0 && (btcPriceKrw.value || 0) > 0) {
    arr.sort((a, b) => computeTotalFeeKRW(a) - computeTotalFeeKRW(b))
  }
  return arr
})
</script>
