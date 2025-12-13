<template>
  <div class="bg-white rounded-lg shadow-md">
    <div class="md:hidden border-b border-gray-200 p-3 flex gap-2 overflow-x-auto">
      <button
        @click="activeRoutingTab = 'nodes'"
        :class="[
          'px-3 py-2 rounded border text-sm font-medium whitespace-nowrap',
          activeRoutingTab === 'nodes' ? 'bg-blue-50 border-blue-500 text-blue-700' : 'border-transparent text-gray-600'
        ]"
      >
        서비스 노드
      </button>
      <button
        @click="activeRoutingTab = 'routes'"
        :class="[
          'px-3 py-2 rounded border text-sm font-medium whitespace-nowrap',
          activeRoutingTab === 'routes' ? 'bg-blue-50 border-blue-500 text-blue-700' : 'border-transparent text-gray-600'
        ]"
      >
        경로 관리
      </button>
      <button
        @click="activeRoutingTab = 'final'"
        :class="[
          'px-3 py-2 rounded border text-sm font-medium whitespace-nowrap',
          activeRoutingTab === 'final' ? 'bg-blue-50 border-blue-500 text-blue-700' : 'border-transparent text-gray-600'
        ]"
      >
        최종 경로
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-4">
      <aside class="hidden md:flex flex-col border-r border-gray-200 p-4 space-y-2">
        <button
          @click="activeRoutingTab = 'nodes'"
          :class="[
            'w-full text-left px-3 py-2 rounded border',
            activeRoutingTab === 'nodes' ? 'bg-blue-50 border-blue-500 text-blue-700' : 'border-transparent text-gray-700'
          ]"
        >
          서비스 노드
        </button>
        <button
          @click="activeRoutingTab = 'routes'"
          :class="[
            'w-full text-left px-3 py-2 rounded border',
            activeRoutingTab === 'routes' ? 'bg-blue-50 border-blue-500 text-blue-700' : 'border-transparent text-gray-700'
          ]"
        >
          경로 관리
        </button>
        <button
          @click="activeRoutingTab = 'final'"
          :class="[
            'w-full text-left px-3 py-2 rounded border',
            activeRoutingTab === 'final' ? 'bg-blue-50 border-blue-500 text-blue-700' : 'border-transparent text-gray-700'
          ]"
        >
          최종 경로
        </button>
      </aside>

      <section class="md:col-span-3 p-4 md:p-6 space-y-6">
        <div v-if="routingUpdateLoading" class="bg-blue-50 border border-blue-200 text-blue-800 text-sm px-4 py-2 rounded">
          작업을 처리 중입니다. 잠시만 기다려주세요.
        </div>

        <section v-if="activeRoutingTab === 'nodes'" class="space-y-6">
          <header>
            <h3 class="text-lg font-semibold text-gray-900">서비스 노드 관리</h3>
            <p class="text-sm text-gray-500">새 노드를 등록하고 기존 노드를 편집합니다.</p>
          </header>

          <div class="bg-gray-50 border border-gray-200 rounded-xl p-4 space-y-4">
            <div class="grid gap-4 md:grid-cols-2">
              <label class="text-sm text-gray-700 space-y-1">
                <span>서비스 코드</span>
                <input
                  v-model="newServiceNode.service"
                  type="text"
                  class="w-full rounded border px-3 py-2"
                  placeholder="예: upbit_krw"
                />
              </label>
              <label class="text-sm text-gray-700 space-y-1">
                <span>표시명</span>
                <input v-model="newServiceNode.display_name" type="text" class="w-full rounded border px-3 py-2" placeholder="노드 이름" />
              </label>
              <label class="text-sm text-gray-700 space-y-1">
                <span>노드 유형</span>
                <select v-model="newServiceNode.node_type" class="w-full rounded border px-3 py-2 bg-white">
                  <option v-for="opt in nodeTypeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
              </label>
              <label class="text-sm text-gray-700 space-y-1">
                <span>웹사이트 주소</span>
                <input v-model="newServiceNode.website_url" type="text" class="w-full rounded border px-3 py-2" placeholder="https://" />
              </label>
            </div>
            <label class="text-sm text-gray-700 space-y-1 block">
              <span>설명</span>
              <textarea v-model="newServiceNode.description" rows="2" class="w-full rounded border px-3 py-2" placeholder="노드 설명"></textarea>
            </label>
            <div class="flex flex-wrap gap-4 text-sm text-gray-700">
              <label class="inline-flex items-center gap-2">
                <input type="checkbox" v-model="newServiceNode.is_kyc" class="rounded" />
                KYC 필요
              </label>
              <label class="inline-flex items-center gap-2">
                <input type="checkbox" v-model="newServiceNode.is_custodial" class="rounded" />
                수탁형
              </label>
              <label class="inline-flex items-center gap-2">
                <input type="checkbox" v-model="newServiceNode.is_enabled" class="rounded" />
                즉시 활성화
              </label>
            </div>
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p class="text-xs text-gray-500">서비스 코드는 고유해야 합니다.</p>
              <button
                @click="createServiceNode"
                :disabled="!isAdmin || routingUpdateLoading || !canCreateServiceNode"
                class="px-4 py-2 rounded bg-blue-600 text-white disabled:opacity-50"
              >
                {{ routingUpdateLoading ? '처리 중...' : '서비스 노드 생성' }}
              </button>
            </div>
            <p v-if="newServiceNodeError && isNewServiceNodeDirty" class="text-sm text-red-600">{{ newServiceNodeError }}</p>
          </div>

          <div>
            <p v-if="serviceNodes.length === 0" class="text-sm text-gray-500">등록된 노드가 없습니다.</p>
            <div v-else class="space-y-4">
              <article
                v-for="node in serviceNodes"
                :key="node.id"
                class="border border-gray-200 rounded-lg p-4 space-y-3"
              >
                <header class="flex items-center justify-between text-sm">
                  <div class="font-semibold text-gray-900">{{ node.display_name }} ({{ node.service }})</div>
                  <span class="px-2 py-1 rounded text-xs" :class="node.is_enabled ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'">
                    {{ node.is_enabled ? '활성' : '비활성' }}
                  </span>
                </header>
                <div class="grid gap-3 md:grid-cols-2">
                  <label class="text-xs text-gray-600 space-y-1">
                    <span>표시명</span>
                    <input v-model="node.display_name" type="text" class="w-full rounded border px-2 py-1" />
                  </label>
                  <label class="text-xs text-gray-600 space-y-1">
                    <span>노드 유형</span>
                    <select v-model="node.node_type" class="w-full rounded border px-2 py-1 bg-white">
                      <option v-for="opt in nodeTypeOptions" :key="`${node.service}-${opt.value}`" :value="opt.value">{{ opt.label }}</option>
                    </select>
                  </label>
                  <label class="text-xs text-gray-600 space-y-1">
                    <span>설명</span>
                    <input v-model="node.description" type="text" class="w-full rounded border px-2 py-1" />
                  </label>
                  <label class="text-xs text-gray-600 space-y-1">
                    <span>웹사이트</span>
                    <input v-model="node.website_url" type="text" class="w-full rounded border px-2 py-1" />
                  </label>
                </div>
                <div class="flex flex-wrap gap-4 text-xs text-gray-600">
                  <label class="inline-flex items-center gap-1">
                    <input type="checkbox" v-model="node.is_kyc" class="rounded" />
                    KYC
                  </label>
                  <label class="inline-flex items-center gap-1">
                    <input type="checkbox" v-model="node.is_custodial" class="rounded" />
                    수탁형
                  </label>
                  <label class="inline-flex items-center gap-1">
                    <input type="checkbox" v-model="node.is_enabled" class="rounded" />
                    활성화
                  </label>
                </div>
                <div class="flex justify-end">
                  <button
                    @click="updateServiceNode(node)"
                    :disabled="!isAdmin || routingUpdateLoading"
                    class="px-3 py-1 rounded bg-blue-600 text-white text-sm disabled:opacity-50"
                  >
                    {{ routingUpdateLoading ? '저장 중...' : '업데이트' }}
                  </button>
                </div>
              </article>
            </div>
          </div>
        </section>

        <section v-else-if="activeRoutingTab === 'routes'" class="space-y-6">
          <header>
            <h3 class="text-lg font-semibold text-gray-900">경로 관리</h3>
            <p class="text-sm text-gray-500">새 경로를 만들고 기존 경로를 편집합니다.</p>
          </header>

          <div class="border border-gray-200 rounded-xl p-4 space-y-4">
            <div class="grid gap-4 md:grid-cols-2">
              <label class="text-sm text-gray-700 space-y-1">
                <span>출발지</span>
                <select v-model="newRoute.sourceId" class="w-full rounded border px-3 py-2 bg-white">
                  <option value="" disabled>선택하세요</option>
                  <option v-for="node in serviceNodes" :key="`source-${node.id}`" :value="node.id">{{ node.display_name }}</option>
                </select>
              </label>
              <label class="text-sm text-gray-700 space-y-1">
                <span>목적지</span>
                <select v-model="newRoute.destinationId" class="w-full rounded border px-3 py-2 bg-white">
                  <option value="" disabled>선택하세요</option>
                  <option v-for="node in filteredDestNodes" :key="`dest-${node.id}`" :value="node.id">{{ node.display_name }}</option>
                </select>
              </label>
            </div>
            <div class="grid gap-4 md:grid-cols-2">
              <fieldset class="text-sm text-gray-700 space-y-2">
                <legend class="font-medium">경로 유형</legend>
                <label v-for="option in routeTypeOptions" :key="option.value" class="flex items-center gap-2">
                  <input type="radio" class="rounded" :value="option.value" v-model="newRoute.routeType" />
                  <span>{{ option.label }}</span>
                </label>
              </fieldset>
              <div class="space-y-3 text-sm text-gray-700">
                <label class="space-y-1 block">
                  <span>비율 수수료 (%)</span>
                  <input v-model="newRoute.feeRate" type="number" min="0" step="0.0001" class="w-full rounded border px-3 py-2" />
                </label>
                <label class="space-y-1 block">
                  <span>고정 수수료</span>
                  <input v-model="newRoute.feeFixed" type="number" min="0" step="0.00000001" class="w-full rounded border px-3 py-2" />
                </label>
                <div class="flex gap-3 flex-wrap text-xs text-gray-600">
                  <label v-for="option in feeCurrencyOptions" :key="option.value" class="inline-flex items-center gap-1">
                    <input type="radio" class="rounded" :value="option.value" v-model="newRoute.feeFixedCurrency" />
                    {{ option.label }}
                  </label>
                </div>
              </div>
            </div>
            <div class="space-y-3 text-sm text-gray-700">
              <label class="inline-flex items-center gap-2">
                <input type="checkbox" v-model="newRoute.isEvent" class="rounded" />
                이벤트 경로
              </label>
              <div v-if="newRoute.isEvent" class="grid gap-3 md:grid-cols-2">
                <label class="space-y-1">
                  <span>이벤트 제목</span>
                  <input v-model="newRoute.eventTitle" type="text" class="w-full rounded border px-3 py-2" />
                </label>
                <label class="space-y-1 md:col-span-2">
                  <span>이벤트 설명</span>
                  <textarea v-model="newRoute.eventDescription" rows="2" class="w-full rounded border px-3 py-2"></textarea>
                </label>
                <label class="space-y-1 md:col-span-2">
                  <span>이벤트 URL</span>
                  <input v-model="newRoute.eventUrl" type="text" class="w-full rounded border px-3 py-2" />
                </label>
              </div>
            </div>
            <div class="flex justify-end">
              <button
                @click="createRoute"
                :disabled="!isAdmin || routingUpdateLoading || !isValidNewRoute"
                class="px-4 py-2 rounded bg-blue-600 text-white text-sm disabled:opacity-50"
              >
                {{ routingUpdateLoading ? '저장 중...' : '경로 생성' }}
              </button>
            </div>
          </div>

          <div class="border border-gray-200 rounded-xl p-4 space-y-3 text-sm text-gray-700">
            <div class="grid gap-4 md:grid-cols-2">
              <label class="space-y-1">
                <span>출발지 필터</span>
                <select v-model="routeFilterSources" multiple class="w-full rounded border px-2 py-2 h-24 bg-white">
                  <option v-for="n in serviceNodes" :key="`filter-src-${n.id}`" :value="n.id">{{ n.display_name }}</option>
                </select>
              </label>
              <label class="space-y-1">
                <span>목적지 필터</span>
                <select v-model="routeFilterDestinations" multiple class="w-full rounded border px-2 py-2 h-24 bg-white">
                  <option v-for="n in serviceNodes" :key="`filter-dst-${n.id}`" :value="n.id">{{ n.display_name }}</option>
                </select>
              </label>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-500">선택하지 않으면 전체를 표시합니다.</span>
              <button class="text-xs text-blue-700" @click="clearRouteFilters">필터 초기화</button>
            </div>
          </div>

          <div class="border border-gray-200 rounded-xl p-4 space-y-2 text-sm text-gray-700">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div class="font-medium">라우팅 스냅샷</div>
                <div class="text-gray-500">
                  <template v-if="snapshotInfo.has_snapshot">
                    마지막 저장 {{ snapshotInfo.updated_at }}
                    <span class="text-xs text-gray-400">(노드 {{ snapshotInfo.counts?.nodes || 0 }}, 경로 {{ snapshotInfo.counts?.routes || 0 }})</span>
                  </template>
                  <template v-else>저장된 스냅샷이 없습니다</template>
                </div>
              </div>
              <div class="flex gap-2">
                <button @click="saveSnapshot" :disabled="snapshotLoading || !isAdmin" class="px-3 py-1 rounded bg-gray-800 text-white text-xs disabled:opacity-50">저장</button>
                <button
                  @click="resetFromSnapshot"
                  :disabled="snapshotLoading || !isAdmin || !snapshotInfo.has_snapshot"
                  class="px-3 py-1 rounded bg-red-600 text-white text-xs disabled:opacity-50"
                >
                  복원
                </button>
              </div>
            </div>
            <p v-if="snapshotError" class="text-red-600 text-sm">{{ snapshotError }}</p>
          </div>

          <div class="space-y-4">
            <div class="flex items-center gap-2 text-sm font-medium text-gray-900">
              등록된 경로 <span class="text-blue-600">({{ filteredRoutes.length }})</span>
            </div>
            <p v-if="filteredRoutes.length === 0" class="text-sm text-gray-500">조건에 맞는 경로가 없습니다.</p>
            <div v-else class="space-y-4">
              <article v-for="route in filteredRoutes" :key="`${route.id}`" class="border border-gray-200 rounded-lg p-4 space-y-3">
                <header class="flex items-center justify-between text-sm">
                  <div class="font-semibold text-gray-900">{{ route.source.display_name }} → {{ route.destination.display_name }}</div>
                  <button
                    v-if="isAdmin"
                    @click="deleteRoute(route.id)"
                    :disabled="routingUpdateLoading"
                    class="text-red-600 text-xs disabled:opacity-50"
                  >
                    삭제
                  </button>
                </header>
                <div class="flex flex-wrap gap-2 text-xs">
                  <span class="px-2 py-1 rounded bg-gray-100 text-gray-800">{{ getRouteTypeLabel(route.route_type) }}</span>
                  <span :class="route.is_enabled ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'" class="px-2 py-1 rounded">
                    {{ route.is_enabled ? '활성' : '비활성' }}
                  </span>
                </div>
                <div v-if="isAdmin" class="space-y-2 text-xs text-gray-700">
                  <label class="space-y-1 block">
                    <span>유형</span>
                    <select v-model="route.edit_route_type" class="w-full rounded border px-2 py-1 bg-white">
                      <option value="trading">거래 수수료</option>
                      <option value="withdrawal_lightning">라이트닝 출금</option>
                      <option value="withdrawal_onchain">온체인 출금</option>
                    </select>
                  </label>
                  <div class="grid gap-2 md:grid-cols-2">
                    <label class="space-y-1 block">
                      <span>비율 수수료 (%)</span>
                      <input v-model.number="route.edit_fee_rate" type="number" class="w-full rounded border px-2 py-1" />
                    </label>
                    <label class="space-y-1 block">
                      <span>고정 수수료</span>
                      <input v-model.number="route.edit_fee_fixed" type="number" class="w-full rounded border px-2 py-1" />
                    </label>
                  </div>
                  <div class="flex flex-wrap gap-2">
                    <label v-for="option in feeCurrencyOptions" :key="`edit-${route.id}-${option.value}`" class="inline-flex items-center gap-1">
                      <input type="radio" class="rounded" :value="option.value" v-model="route.edit_fee_fixed_currency" />
                      {{ option.label }}
                    </label>
                  </div>
                  <label class="inline-flex items-center gap-2">
                    <input type="checkbox" v-model="route.edit_is_event" class="rounded" />
                    이벤트 경로
                  </label>
                  <div v-if="route.edit_is_event" class="space-y-1">
                    <input v-model="route.edit_event_title" type="text" class="w-full rounded border px-2 py-1" placeholder="이벤트 제목" />
                    <textarea v-model="route.edit_event_description" rows="2" class="w-full rounded border px-2 py-1" placeholder="이벤트 설명"></textarea>
                    <input v-model="route.edit_event_url" type="text" class="w-full rounded border px-2 py-1" placeholder="이벤트 URL" />
                  </div>
                  <div class="flex justify-end pt-1">
                    <button
                      @click="updateExistingRoute(route)"
                      :disabled="routingUpdateLoading"
                      class="px-3 py-1 rounded bg-blue-600 text-white text-xs disabled:opacity-50"
                    >
                      {{ routingUpdateLoading ? '저장 중...' : '저장' }}
                    </button>
                  </div>
                </div>
                <div v-else class="text-sm text-gray-700 space-y-1">
                  <div>비율 수수료: {{ route.fee_rate ?? '없음' }}</div>
                  <div>고정 수수료: {{ route.fee_fixed !== null ? `${formatFixedAmount(route.fee_fixed, route.fee_fixed_currency)} ${normalizeFeeCurrency(route.fee_fixed_currency)}` : '없음' }}</div>
                </div>
                <div v-if="route.description" class="text-xs text-gray-500">설명: {{ route.description }}</div>
                <div v-if="route.is_event" class="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1">
                  {{ route.event_title || '이벤트 진행중' }}
                  <div class="text-amber-900 whitespace-pre-line">{{ route.event_description || '세부 정보 없음' }}</div>
                  <a v-if="route.event_url" :href="route.event_url" target="_blank" rel="noopener" class="text-blue-700 underline">링크 열기</a>
                </div>
              </article>
            </div>
            <div v-if="routingUpdateSuccess" class="text-sm text-green-700 bg-green-50 border border-green-200 px-3 py-2 rounded">
              라우팅 설정이 성공적으로 저장되었습니다.
            </div>
            <div v-if="routingUpdateError" class="text-sm text-red-700 bg-red-50 border border-red-200 px-3 py-2 rounded">
              {{ routingUpdateError }}
            </div>
          </div>
        </section>

        <section v-else class="space-y-6">
          <header>
            <h3 class="text-lg font-semibold text-gray-900">최종 경로</h3>
            <p class="text-sm text-gray-500">필터를 조정하고 예상 수수료를 확인하세요.</p>
          </header>
          <div class="space-y-4 border border-gray-200 rounded-xl p-4 text-sm text-gray-700">
            <div class="grid gap-3 md:grid-cols-2">
              <label class="space-y-1">
                <span>송금 금액</span>
                <input v-model.number="sendAmountInput" type="number" min="0" class="w-full rounded border px-3 py-2" placeholder="예: 100" />
              </label>
              <label class="space-y-1">
                <span>단위</span>
                <select v-model="sendUnit" class="w-full rounded border px-3 py-2 bg-white">
                  <option value="1">원</option>
                  <option value="10000">만원</option>
                  <option value="100000000">억원</option>
                </select>
              </label>
            </div>
            <div class="flex flex-wrap gap-4">
              <label class="inline-flex items-center gap-2">
                <input type="checkbox" v-model="optimalFilterExcludeLightning" class="rounded" />
                라이트닝 경로 제외
              </label>
              <label class="inline-flex items-center gap-2">
                <input type="checkbox" v-model="optimalFilterExcludeKycWithdrawal" class="rounded" />
                KYC 출금 제외
              </label>
            </div>
            <div class="flex flex-wrap items-center gap-4">
              <div>BTC 가격: <span class="font-semibold">{{ btcPriceKrw ? formatKRW(btcPriceKrw) : '불러오는 중' }}</span></div>
              <button @click="fetchBtcPriceKrw(true)" class="text-xs text-blue-700">가격 새로고침</button>
              <button @click="loadOptimalPaths" :disabled="optimalLoading" class="text-xs text-blue-700 disabled:opacity-50">
                {{ optimalLoading ? '계산 중...' : '경로 다시 계산' }}
              </button>
            </div>
          </div>
          <p v-if="optimalError" class="text-sm text-red-600">{{ optimalError }}</p>
          <p v-else-if="sortedOptimalPaths.length === 0" class="text-sm text-gray-500">조건에 맞는 경로가 없습니다.</p>
          <div v-else class="space-y-4">
            <article v-for="(path, idx) in sortedOptimalPaths" :key="path.path_signature || idx" class="border border-gray-200 rounded-lg p-4 space-y-3">
              <header class="flex items-center justify-between">
                <div class="font-semibold text-gray-900">경로 #{{ idx + 1 }}</div>
                <div class="text-xs text-gray-500">{{ path.routes.length }} 단계</div>
              </header>
              <div class="text-sm text-gray-700 space-y-1">
                <div>
                  <template v-for="fees in [computePathFees(path.routes)]" :key="`fees-${idx}`">
                    비율 수수료 합계: {{ fees.rate.toFixed(4) }}%
                    · 고정 수수료: {{ formatFixedFeeSummary(fees.fixedByCurrency) }}
                    <span v-if="computeFixedFeeKRW(fees.fixedByCurrency)">
                      ({{ formatKRW(computeFixedFeeKRW(fees.fixedByCurrency)) }})
                    </span>
                  </template>
                </div>
                <div v-if="sendAmountKRW > 0" class="text-blue-700">
                  예상 총 수수료: {{ formatKRW(computeTotalFeeKRW(path)) }}
                </div>
              </div>
              <div class="flex flex-wrap gap-2 text-xs">
                <span v-for="(step, stepIdx) in path.routes" :key="`label-${idx}-${stepIdx}`" class="px-2 py-1 rounded bg-blue-50 text-blue-700">
                  {{ step.source.display_name }} → {{ step.destination.display_name }}
                </span>
              </div>
              <div class="space-y-1 text-xs text-gray-600">
                <div v-for="(step, stepIdx) in path.routes" :key="`detail-${idx}-${stepIdx}`" class="flex justify-between">
                  <span>{{ step.source.display_name }} → {{ step.destination.display_name }} ({{ getRouteTypeLabel(step.route_type) }})</span>
                  <span>
                    <template v-if="step.fee_rate !== null">{{ step.fee_rate }}%</template>
                    <template v-if="step.fee_fixed !== null">
                      {{ step.fee_rate !== null ? ' + ' : '' }}{{ formatFixedAmount(step.fee_fixed, step.fee_fixed_currency) }} {{ normalizeFeeCurrency(step.fee_fixed_currency) }}
                    </template>
                    <template v-if="step.fee_rate === null && step.fee_fixed === null">무료</template>
                  </span>
                </div>
              </div>
            </article>
          </div>
        </section>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  apiGetServiceNodes,
  apiUpdateServiceNode,
  apiGetRoutes,
  apiCreateRoute,
  apiDeleteRoute,
  apiGetOptimalPaths,
  apiGetRoutingSnapshotInfo,
  apiSaveRoutingSnapshot,
  apiResetRoutingFromSnapshot
} from '../../api'
import { getUpbitBtcPriceKrw } from '../../utils/btcPriceProvider'
import { getBtcPriceUsdt } from '../../utils/btcUsdtPriceProvider'
import { getAdminUsername, getCurrentUsername } from '../../utils/adminAuth'

const props = defineProps({
  isAdmin: { type: Boolean, default: false },
  showSuccess: { type: Function, required: true },
  showError: { type: Function, required: true }
})

const activeRoutingTab = ref('nodes')
const serviceNodes = ref([])
const routes = ref([])
const routingUpdateLoading = ref(false)
const routingUpdateSuccess = ref(false)
const routingUpdateError = ref('')
const nodeTypeOptions = [
  { value: 'exchange', label: '거래소' },
  { value: 'service', label: '서비스' },
  { value: 'wallet', label: '지갑' },
  { value: 'user', label: '사용자' }
]
const routeTypeOptions = [
  { value: 'trading', label: '거래 수수료', description: '거래소 내부/간 전환' },
  { value: 'withdrawal_lightning', label: '라이트닝 출금', description: '라이트닝 네트워크 출금' },
  { value: 'withdrawal_onchain', label: '온체인 출금', description: '블록체인 전송' }
]
const feeCurrencyOptions = [
  { value: 'BTC', label: 'BTC' },
  { value: 'USDT', label: 'USDT' }
]
const routeTypeOptionMap = routeTypeOptions.reduce((acc, option) => {
  acc[option.value] = option
  return acc
}, {})
const getRouteTypeLabel = (value) => routeTypeOptionMap[value]?.label || '기타'
const MAX_OPTIMAL_PATHS = 300

const newServiceNode = ref({
  service: '',
  display_name: '',
  node_type: 'service',
  is_kyc: false,
  is_custodial: true,
  is_enabled: true,
  description: '',
  website_url: ''
})
const newRoute = ref({
  sourceId: '',
  destinationId: '',
  routeType: '',
  feeRate: null,
  feeFixed: null,
  feeFixedCurrency: 'BTC',
  description: '',
  isEnabled: true,
  isEvent: false,
  eventTitle: '',
  eventDescription: '',
  eventUrl: ''
})
const optimalPaths = ref([])
const optimalLoading = ref(false)
const optimalError = ref('')
const btcPriceKrw = ref(0)
const btcPriceUsdt = ref(0)
const snapshotInfo = ref({ has_snapshot: false, updated_at: '', counts: { nodes: 0, routes: 0 } })
const snapshotLoading = ref(false)
const snapshotError = ref('')
const sendAmountInput = ref('')
const sendUnit = ref('10000')
const routeFilterSources = ref([])
const routeFilterDestinations = ref([])
const optimalFilterExcludeLightning = ref(false)
const optimalFilterExcludeKycWithdrawal = ref(false)

const notifySuccess = (message) => props.showSuccess(message)
const notifyError = (message) => props.showError(message)
const isAdmin = computed(() => props.isAdmin)

const validNodeTypeValues = new Set(nodeTypeOptions.map((opt) => opt.value))
const normalizeNodeTypeValue = (value, service = '') => {
  if (value && validNodeTypeValues.has(value)) return value
  if (!service) return 'service'
  if (service === 'user') return 'user'
  if (service === 'personal_wallet') return 'wallet'
  if (/^(upbit|bithumb|binance|okx)/.test(service)) return 'exchange'
  return 'service'
}
const withDefaultNodeType = (node) => {
  if (!node || typeof node !== 'object') return node
  return {
    ...node,
    node_type: normalizeNodeTypeValue(node.node_type, node.service)
  }
}

const serviceCodePattern = /^[a-z0-9_]+$/
const normalizedNewServiceCode = computed(() => (newServiceNode.value.service || '').trim().toLowerCase())
const isNewServiceNodeDirty = computed(() => {
  const node = newServiceNode.value
  return Boolean(
    (node.service || '').length ||
      (node.display_name || '').length ||
      (node.description || '').length ||
      (node.website_url || '').length ||
      node.is_kyc ||
      !node.is_custodial ||
      !node.is_enabled
  )
})
const newServiceNodeError = computed(() => {
  const code = normalizedNewServiceCode.value
  if (!code) return '서비스 코드를 입력하세요'
  if (!serviceCodePattern.test(code)) return '서비스 코드는 소문자, 숫자, 밑줄만 사용할 수 있습니다'
  if ((serviceNodes.value || []).some((n) => n.service === code)) return '이미 존재하는 서비스 코드입니다'
  const displayName = (newServiceNode.value.display_name || '').trim()
  if (!displayName) return '표시명을 입력하세요'
  return ''
})
const canCreateServiceNode = computed(() => !newServiceNodeError.value)

const isValidNewRoute = computed(() => {
  return (
    newRoute.value.sourceId &&
    newRoute.value.destinationId &&
    newRoute.value.routeType &&
    ((newRoute.value.feeRate !== null && newRoute.value.feeRate !== '') ||
      (newRoute.value.feeFixed !== null && newRoute.value.feeFixed !== ''))
  )
})

const filteredRoutes = computed(() => {
  const srcSet = new Set(routeFilterSources.value || [])
  const dstSet = new Set(routeFilterDestinations.value || [])
  return (routes.value || []).filter((r) => {
    const srcOk = srcSet.size === 0 || srcSet.has(r.source.id)
    const dstOk = dstSet.size === 0 || dstSet.has(r.destination.id)
    return srcOk && dstOk
  })
})

const selectedSource = computed(() => serviceNodes.value.find((n) => n.id === newRoute.value.sourceId) || null)

const disallowedDestForUser = new Set(['binance', 'binance_usdt', 'binance_btc', 'okx', 'okx_usdt', 'okx_btc'])
const filteredDestNodes = computed(() => {
  let nodes = serviceNodes.value
  if (selectedSource.value) {
    const srcSvc = selectedSource.value.service
    if (srcSvc === 'user') {
      nodes = nodes.filter((n) => !disallowedDestForUser.has(n.service))
    }
    if (srcSvc === 'upbit_usdt') {
      nodes = nodes.filter((n) => n.service !== 'upbit_btc')
    }
    if (srcSvc === 'bithumb_usdt') {
      nodes = nodes.filter((n) => n.service !== 'bithumb_btc')
    }
  }
  return nodes.filter((n) => n.id !== newRoute.value.sourceId)
})

const usdtPriceKrw = computed(() => {
  const btcKrw = btcPriceKrw.value
  const btcUsdt = btcPriceUsdt.value
  if (!btcKrw || !btcUsdt) return 0
  if (!Number.isFinite(btcUsdt) || btcUsdt === 0) return 0
  return btcKrw / btcUsdt
})

const sendAmountKRW = computed(() => {
  const amount = Number(sendAmountInput.value || 0)
  const unit = Number(sendUnit.value || 1)
  if (!isFinite(amount) || !isFinite(unit)) return 0
  return amount * unit
})

const normalizeFeeCurrency = (currency = 'BTC') => {
  const upper = (currency || 'BTC').toString().toUpperCase()
  return feeCurrencyOptions.some((opt) => opt.value === upper) ? upper : 'BTC'
}

const formatFixedAmount = (value, currency = 'BTC') => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '0'
  const normalized = normalizeFeeCurrency(currency)
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
  if (normalized === 'USDT') return usdtPriceKrw.value
  return btcPriceKrw.value
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

const formatKRW = (n) => {
  try {
    return Number(n).toLocaleString('ko-KR') + '원'
  } catch {
    return n + '원'
  }
}

const computeTotalFeeKRW = (path) => {
  if (!path || !Array.isArray(path.routes)) return 0
  const { rate, fixedByCurrency } = computePathFees(path.routes)
  const rateFee = ((sendAmountKRW.value || 0) * (Number(rate) || 0)) / 100
  const fixedFee = computeFixedFeeKRW(fixedByCurrency)
  return Math.max(0, Math.floor(rateFee + fixedFee))
}

const isLightningRoute = (route) => route?.route_type === 'withdrawal_lightning'
const isNonExchangeKycNode = (node) => {
  if (!node) return false
  const nodeType = normalizeNodeTypeValue(node.node_type, node.service)
  return nodeType !== 'exchange' && nodeType !== 'user' && Boolean(node.is_kyc)
}

const shouldExcludeRouteByOptimalFilters = (route) => {
  if (!route) return false
  if (optimalFilterExcludeLightning.value && isLightningRoute(route)) return true
  if (optimalFilterExcludeKycWithdrawal.value && isNonExchangeKycNode(route.destination)) return true
  return false
}

const filteredOptimalPaths = computed(() => {
  return (optimalPaths.value || []).filter((path) => {
    if (!Array.isArray(path.routes)) return true
    return !path.routes.some((route) => shouldExcludeRouteByOptimalFilters(route))
  })
})

const sortedOptimalPaths = computed(() => {
  const arr = [...filteredOptimalPaths.value]
  if ((sendAmountKRW.value || 0) > 0) {
    arr.sort((a, b) => computeTotalFeeKRW(a) - computeTotalFeeKRW(b))
  }
  return arr
})

const clearRouteFilters = () => {
  routeFilterSources.value = []
  routeFilterDestinations.value = []
}

const loadServiceNodes = async () => {
  try {
    const username = getCurrentUsername()
    const response = await apiGetServiceNodes(username)
    if (response.success) {
      serviceNodes.value = Array.isArray(response.nodes) ? response.nodes.map(withDefaultNodeType) : []
    } else {
      routingUpdateError.value = response.error || '서비스 노드 데이터 로드에 실패했습니다'
    }
  } catch {
    routingUpdateError.value = '네트워크 오류'
  }
}

const preparedRouteForEdit = (route) => ({
  ...route,
  edit_route_type: route.route_type || 'trading',
  edit_fee_rate: route.fee_rate ?? null,
  edit_fee_fixed: route.fee_fixed ?? null,
  edit_fee_fixed_currency: normalizeFeeCurrency(route.fee_fixed_currency),
  edit_is_event: Boolean(route.is_event),
  edit_event_title: route.event_title || '',
  edit_event_description: route.event_description || '',
  edit_event_url: route.event_url || ''
})

const loadRoutes = async () => {
  try {
    const username = getCurrentUsername()
    const response = await apiGetRoutes(username)
    if (response.success) {
      routes.value = Array.isArray(response.routes) ? response.routes.map(preparedRouteForEdit) : []
    } else {
      routingUpdateError.value = response.error || '경로 데이터 로드에 실패했습니다'
    }
  } catch {
    routingUpdateError.value = '네트워크 오류'
  }
}

const loadOptimalPaths = async () => {
  optimalError.value = ''
  optimalLoading.value = true
  try {
    const response = await apiGetOptimalPaths(MAX_OPTIMAL_PATHS)
    if (response.success) {
      optimalPaths.value = Array.isArray(response.paths) ? response.paths : []
    } else {
      optimalPaths.value = []
      optimalError.value = response.error || '최적 경로 계산에 실패했습니다'
    }
  } catch {
    optimalError.value = '최적 경로 계산 중 오류가 발생했습니다'
  } finally {
    optimalLoading.value = false
  }
}

const resetNewServiceNode = () => {
  newServiceNode.value = {
    service: '',
    display_name: '',
    node_type: 'service',
    is_kyc: false,
    is_custodial: true,
    is_enabled: true,
    description: '',
    website_url: ''
  }
}

const resetNewRoute = () => {
  newRoute.value = {
    sourceId: '',
    destinationId: '',
    routeType: '',
    feeRate: null,
    feeFixed: null,
    feeFixedCurrency: 'BTC',
    description: '',
    isEnabled: true,
    isEvent: false,
    eventTitle: '',
    eventDescription: '',
    eventUrl: ''
  }
}

const normalizeNumberInput = (value) => {
  if (value === null || value === undefined || value === '') return null
  const num = Number(value)
  return Number.isFinite(num) ? num : null
}

const beginRoutingAction = () => {
  routingUpdateError.value = ''
  routingUpdateSuccess.value = false
  routingUpdateLoading.value = true
}

const endRoutingAction = () => {
  routingUpdateLoading.value = false
}

const requireAdminUsername = () => {
  const username = getAdminUsername()
  if (!username) {
    throw new Error('관리자 권한이 필요합니다')
  }
  return username
}

const createServiceNode = async () => {
  if (!props.isAdmin) {
    notifyError('관리자만 서비스 노드를 추가할 수 있습니다')
    return
  }
  if (!canCreateServiceNode.value) {
    if (isNewServiceNodeDirty.value) {
      notifyError(newServiceNodeError.value || '입력값을 확인하세요')
    }
    return
  }

  beginRoutingAction()
  try {
    const username = requireAdminUsername()
    const payload = newServiceNode.value
    const response = await apiUpdateServiceNode(
      username,
      normalizedNewServiceCode.value,
      payload.display_name,
      payload.node_type,
      Boolean(payload.is_kyc),
      Boolean(payload.is_custodial),
      Boolean(payload.is_enabled),
      payload.description || '',
      payload.website_url || ''
    )
    if (!response.success) {
      throw new Error(response.error || '서비스 노드 생성에 실패했습니다')
    }
    await loadServiceNodes()
    resetNewServiceNode()
    routingUpdateSuccess.value = true
    notifySuccess('서비스 노드를 저장했습니다')
  } catch (error) {
    const message = error?.message || '서비스 노드 생성 중 오류가 발생했습니다'
    routingUpdateError.value = message
    notifyError(message)
  } finally {
    endRoutingAction()
  }
}

const updateServiceNode = async (node) => {
  if (!props.isAdmin) {
    notifyError('관리자만 서비스 노드를 수정할 수 있습니다')
    return
  }
  if (!node) return
  beginRoutingAction()
  try {
    const username = requireAdminUsername()
    const response = await apiUpdateServiceNode(
      username,
      node.service,
      node.display_name,
      normalizeNodeTypeValue(node.node_type, node.service),
      Boolean(node.is_kyc),
      Boolean(node.is_custodial),
      Boolean(node.is_enabled),
      node.description || '',
      node.website_url || ''
    )
    if (!response.success) {
      throw new Error(response.error || '서비스 노드 업데이트에 실패했습니다')
    }
    await loadServiceNodes()
    routingUpdateSuccess.value = true
    notifySuccess('서비스 노드를 저장했습니다')
  } catch (error) {
    const message = error?.message || '서비스 노드 업데이트 중 오류가 발생했습니다'
    routingUpdateError.value = message
    notifyError(message)
  } finally {
    endRoutingAction()
  }
}

const createRoute = async () => {
  if (!props.isAdmin) {
    notifyError('관리자만 경로를 추가할 수 있습니다')
    return
  }
  if (!isValidNewRoute.value) {
    notifyError('경로 정보를 모두 입력하세요')
    return
  }
  beginRoutingAction()
  try {
    const username = requireAdminUsername()
    const route = newRoute.value
    const response = await apiCreateRoute(
      username,
      route.sourceId,
      route.destinationId,
      route.routeType,
      normalizeNumberInput(route.feeRate),
      normalizeNumberInput(route.feeFixed),
      normalizeFeeCurrency(route.feeFixedCurrency),
      Boolean(route.isEnabled),
      route.description || '',
      Boolean(route.isEvent),
      route.eventTitle || '',
      route.eventDescription || '',
      route.eventUrl || ''
    )
    if (!response.success) {
      throw new Error(response.error || '경로 생성에 실패했습니다')
    }
    await Promise.all([loadRoutes(), loadOptimalPaths()])
    resetNewRoute()
    routingUpdateSuccess.value = true
    notifySuccess('경로를 저장했습니다')
  } catch (error) {
    const message = error?.message || '경로 생성 중 오류가 발생했습니다'
    routingUpdateError.value = message
    notifyError(message)
  } finally {
    endRoutingAction()
  }
}

const updateExistingRoute = async (route) => {
  if (!props.isAdmin) {
    notifyError('관리자만 경로를 수정할 수 있습니다')
    return
  }
  if (!route) return
  beginRoutingAction()
  try {
    const username = requireAdminUsername()
    const response = await apiCreateRoute(
      route.id, // Pass the route ID for update
      username,
      route.source.id,
      route.destination.id,
      route.edit_route_type || route.route_type,
      normalizeNumberInput(route.edit_fee_rate),
      normalizeNumberInput(route.edit_fee_fixed),
      normalizeFeeCurrency(route.edit_fee_fixed_currency || route.fee_fixed_currency),
      Boolean(route.is_enabled),
      route.description || '',
      Boolean(route.edit_is_event),
      route.edit_event_title || '',
      route.edit_event_description || '',
      route.edit_event_url || ''
    )
    if (!response.success) {
      throw new Error(response.error || '경로 업데이트에 실패했습니다')
    }
    await Promise.all([loadRoutes(), loadOptimalPaths()])
    routingUpdateSuccess.value = true
    notifySuccess('경로를 저장했습니다')
  } catch (error) {
    const message = error?.message || '경로 업데이트 중 오류가 발생했습니다'
    routingUpdateError.value = message
    notifyError(message)
  } finally {
    endRoutingAction()
  }
}

const deleteRoute = async (routeId) => {
  if (!props.isAdmin) {
    notifyError('관리자만 경로를 삭제할 수 있습니다')
    return
  }
  if (!routeId) return
  beginRoutingAction()
  try {
    const username = requireAdminUsername()
    const response = await apiDeleteRoute(username, routeId)
    if (!response.success) {
      throw new Error(response.error || '경로 삭제에 실패했습니다')
    }
    await Promise.all([loadRoutes(), loadOptimalPaths()])
    routingUpdateSuccess.value = true
    notifySuccess('경로를 삭제했습니다')
  } catch (error) {
    const message = error?.message || '경로 삭제 중 오류가 발생했습니다'
    routingUpdateError.value = message
    notifyError(message)
  } finally {
    endRoutingAction()
  }
}

const loadSnapshotInfo = async () => {
  try {
    const response = await apiGetRoutingSnapshotInfo()
    if (response.success && response.info) {
      snapshotInfo.value = {
        has_snapshot: Boolean(response.info.has_snapshot),
        updated_at: response.info.updated_at || '',
        counts: response.info.counts || { nodes: 0, routes: 0 }
      }
    } else if (!response.success) {
      snapshotError.value = response.error || '스냅샷 정보를 불러오지 못했습니다'
    }
  } catch {
    snapshotError.value = '스냅샷 정보를 불러오지 못했습니다'
  }
}

const saveSnapshot = async () => {
  if (!props.isAdmin) {
    notifyError('관리자만 스냅샷을 저장할 수 있습니다')
    return
  }
  snapshotError.value = ''
  snapshotLoading.value = true
  try {
    const username = requireAdminUsername()
    const response = await apiSaveRoutingSnapshot(username)
    if (!response.success) {
      throw new Error(response.error || '스냅샷 저장에 실패했습니다')
    }
    await loadSnapshotInfo()
    notifySuccess('라우팅 스냅샷을 저장했습니다')
  } catch (error) {
    const message = error?.message || '스냅샷 저장 중 오류가 발생했습니다'
    snapshotError.value = message
    notifyError(message)
  } finally {
    snapshotLoading.value = false
  }
}

const resetFromSnapshot = async () => {
  if (!props.isAdmin) {
    notifyError('관리자만 스냅샷으로 복원할 수 있습니다')
    return
  }
  if (!snapshotInfo.value.has_snapshot) {
    notifyError('사용 가능한 스냅샷이 없습니다')
    return
  }
  snapshotError.value = ''
  snapshotLoading.value = true
  try {
    const username = requireAdminUsername()
    const response = await apiResetRoutingFromSnapshot(username)
    if (!response.success) {
      throw new Error(response.error || '스냅샷 복원에 실패했습니다')
    }
    await Promise.all([loadServiceNodes(), loadRoutes(), loadOptimalPaths(), loadSnapshotInfo()])
    notifySuccess('스냅샷으로 복원했습니다')
  } catch (error) {
    const message = error?.message || '스냅샷 복원 중 오류가 발생했습니다'
    snapshotError.value = message
    notifyError(message)
  } finally {
    snapshotLoading.value = false
  }
}

const fetchBtcPriceKrw = async (force = false) => {
  try {
    const price = await getUpbitBtcPriceKrw(force)
    if (Number.isFinite(price)) {
      btcPriceKrw.value = price
    }
  } catch {}
}

const fetchBtcPriceUsdt = async (force = false) => {
  try {
    const price = await getBtcPriceUsdt(force)
    if (Number.isFinite(price)) {
      btcPriceUsdt.value = price
    }
  } catch {}
}

const loadInitialData = async () => {
  routingUpdateLoading.value = true
  try {
    await Promise.all([loadServiceNodes(), loadRoutes()])
  } finally {
    routingUpdateLoading.value = false
  }
  loadSnapshotInfo()
  loadOptimalPaths()
  fetchBtcPriceKrw()
  fetchBtcPriceUsdt()
}

onMounted(() => {
  loadInitialData()
})
</script>
