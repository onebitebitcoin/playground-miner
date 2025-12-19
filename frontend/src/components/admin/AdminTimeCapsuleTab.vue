<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-medium leading-6 text-slate-900">타임캡슐 관리</h3>
      <div class="flex gap-2">
        <button
          @click="fetchMnemonicStatus"
          class="inline-flex items-center px-3 py-2 border border-slate-300 shadow-sm text-sm leading-4 font-medium rounded-md text-slate-700 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="mnemonicState.loading"
        >
          <svg class="-ml-0.5 mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          니모닉 새로고침
        </button>
        <button
          @click="fetchTimeCapsules"
          class="inline-flex items-center px-3 py-2 border border-slate-300 shadow-sm text-sm leading-4 font-medium rounded-md text-slate-700 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          <svg class="-ml-0.5 mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          목록 새로고침
        </button>
      </div>
    </div>

    <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 space-y-4">
      <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h4 class="text-base font-semibold text-slate-900">타임캡슐 브로드캐스팅 설정</h4>
        </div>
        <button
          @click="createMnemonic"
          :disabled="!props.isAdmin || mnemonicState.hasMnemonic || generatingMnemonic"
          class="inline-flex items-center px-4 py-2 rounded-lg text-sm font-semibold text-white shadow-sm transition disabled:opacity-50 disabled:cursor-not-allowed"
          :class="generatingMnemonic ? 'bg-slate-400 cursor-progress' : 'bg-indigo-600 hover:bg-indigo-500'"
        >
          <svg v-if="generatingMnemonic" class="animate-spin -ml-0.5 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ mnemonicState.hasMnemonic ? '니모닉 보관 중' : '니모닉 생성' }}
        </button>
      </div>

      <div v-if="mnemonicState.loading" class="text-sm text-slate-500">니모닉 정보를 불러오는 중입니다...</div>
      <div v-else class="grid gap-6 lg:grid-cols-2">
        <div>
          <div v-if="mnemonicState.hasMnemonic" class="space-y-3">
            <div class="flex flex-col gap-3 md:flex-row md:items-center">
              <div class="flex-1 relative">
                <input
                  :type="showMnemonic ? 'text' : 'password'"
                  class="w-full rounded-xl border border-slate-300 px-4 py-2 text-sm font-mono"
                  :value="mnemonicState.mnemonic"
                  readonly
                />
                <div class="absolute inset-y-0 right-0 flex items-center pr-3 gap-2">
                  <button
                    type="button"
                    class="text-slate-500 hover:text-slate-900"
                    @click="showMnemonic = !showMnemonic"
                  >
                    <svg v-if="showMnemonic" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.976 9.976 0 011.563-3.029M6.22 6.22A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7-1.275 4.057-5.065 7-9.543 7-4.478 0-8.268-2.943-9.542-7z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3l18 18" />
                    </svg>
                    <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.522 5 12 5c4.478 0 8.268 2.943 9.543 7-1.275 4.057-5.065 7-9.543 7-4.478 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>
                  <button
                    type="button"
                    class="text-slate-500 hover:text-slate-900"
                    @click="copyMnemonic"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8l6 6v4" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16h7m-3 4h5a2 2 0 002-2v-5" />
                    </svg>
                  </button>
                </div>
              </div>
              <div class="text-sm text-slate-500">
                <div>다음 주소 인덱스 <span class="font-semibold text-slate-900">#{{ mnemonicState.nextAddressIndex }}</span></div>
                <div>할당된 주소 <span class="font-semibold text-slate-900">{{ mnemonicState.assignedCount }}</span>개</div>
              </div>
            </div>
          </div>
          <p v-else class="text-sm text-slate-500">
            아직 니모닉이 생성되지 않았습니다. 주소 할당 전에 반드시 니모닉을 생성하세요.
          </p>
        </div>
        <div class="space-y-4 border border-slate-200 rounded-2xl p-4">
          <div class="flex flex-col gap-1">
            <div class="flex items-center justify-between">
              <div>
                <h5 class="text-base font-semibold text-slate-900">풀노드 연결</h5>
                <p class="text-xs text-slate-500">트랜잭션 전파에 사용할 노드 IP와 포트를 지정하세요.</p>
              </div>
              <button
                type="button"
                class="text-xs text-slate-500 hover:text-slate-900"
                @click="fetchBroadcastSettings"
              >
                새로고침
              </button>
            </div>
          </div>
          <div class="space-y-3">
            <div class="space-y-2">
              <label class="text-xs font-semibold text-slate-600">풀노드 IP / 호스트</label>
              <input
                v-model="broadcastSettings.host"
                type="text"
                class="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
                placeholder="예: https://mainnet.nunchuk.io"
                :disabled="broadcastSettings.loading"
              />
            </div>
            <div>
              <label class="text-xs font-semibold text-slate-600">포트</label>
              <input
                v-model="broadcastSettings.port"
                type="number"
                class="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
                placeholder="8332"
                :disabled="broadcastSettings.loading"
              />
            </div>
            <div v-if="recommendedNodes.length" class="text-xs text-slate-500 space-y-2">
              <div class="font-semibold text-slate-600">공개 노드 빠른 선택</div>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="node in recommendedNodes"
                  :key="node.host"
                  type="button"
                  class="px-3 py-1 rounded-full border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition text-xs"
                  @click="applyRecommendedNode(node)"
                >
                  {{ node.label }}
                </button>
              </div>
              <div class="space-y-1 text-[11px] text-slate-400">
                <div v-for="node in recommendedNodes" :key="`${node.host}-desc`">
                  <span class="font-semibold text-slate-500">{{ node.label }}</span> · {{ node.description }}
                </div>
              </div>
            </div>
          </div>
          <div class="flex flex-wrap gap-3">
            <button
              type="button"
              class="inline-flex items-center px-3 py-2 rounded-lg text-sm font-semibold text-white bg-slate-900 hover:bg-slate-800 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
              @click="saveBroadcastSettings"
              :disabled="broadcastSettings.loading || broadcastSettings.saving || !props.isAdmin"
            >
              <svg v-if="broadcastSettings.saving" class="animate-spin -ml-0.5 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              설정 저장
            </button>
            <button
              type="button"
              class="inline-flex items-center px-3 py-2 rounded-lg text-sm font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
              @click="testBroadcastConnection"
              :disabled="connectionTest.running || broadcastSettings.loading || !props.isAdmin"
            >
              <svg v-if="connectionTest.running" class="animate-spin -ml-0.5 mr-2 h-4 w-4 text-slate-600" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              연결 테스트
            </button>
          </div>
          <div>
            <div
              v-if="connectionTest.lastStatus === 'success'"
              class="text-sm text-emerald-700 bg-emerald-50 border border-emerald-100 rounded-lg px-3 py-2"
            >
              <div>블록 높이 <span class="font-semibold">{{ connectionTest.blockHeight ?? '확인됨' }}</span> ({{ connectionTest.chain || 'chain 미확인' }})</div>
              <div class="text-xs text-emerald-600 mt-1">마지막 확인: {{ formatDate(connectionTest.checkedAt) }}</div>
            </div>
            <div
              v-else-if="connectionTest.lastStatus === 'error'"
              class="text-sm text-rose-600 bg-rose-50 border border-rose-100 rounded-lg px-3 py-2"
            >
              <div>{{ connectionTest.message || '연결에 실패했습니다.' }}</div>
              <div class="text-xs text-rose-500 mt-1" v-if="connectionTest.checkedAt">마지막 시도: {{ formatDate(connectionTest.checkedAt) }}</div>
            </div>
            <div v-else class="text-xs text-slate-400">아직 연결 테스트 기록이 없습니다.</div>
          </div>
        </div>
      </div>
    </div>

    <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 space-y-4">
      <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h4 class="text-base font-semibold text-slate-900">실시간 수수료율</h4>
          <p class="text-sm text-slate-500">현재 예상 네트워크 수수료를 빠르게 확인하세요.</p>
        </div>
        <button
          type="button"
          class="inline-flex items-center px-3 py-2 rounded-lg text-sm font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          @click="fetchFeeEstimates"
          :disabled="feeEstimates.loading"
        >
          <svg v-if="feeEstimates.loading" class="animate-spin -ml-0.5 mr-2 h-4 w-4 text-slate-600" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ feeEstimates.loading ? '불러오는 중...' : '새로고침' }}
        </button>
      </div>
      <div v-if="feeEstimates.error" class="text-sm text-rose-500">
        {{ feeEstimates.error }}
      </div>
      <div v-else-if="feeEstimates.loading" class="text-sm text-slate-500">
        실시간 수수료 정보를 불러오는 중입니다...
      </div>
      <div v-else class="space-y-4">
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div
            v-for="fee in feeCards"
            :key="fee.key"
            class="border border-slate-200 rounded-2xl p-4 bg-slate-50"
          >
            <div class="text-xs uppercase tracking-wide text-slate-500">{{ fee.label }}</div>
            <div class="mt-2 text-2xl font-semibold text-slate-900">{{ fee.value ?? '---' }} <span class="text-base font-normal text-slate-500">sat/vB</span></div>
            <div class="mt-1 text-xs text-slate-500">{{ fee.caption }}</div>
          </div>
        </div>
        <div class="text-xs text-slate-400 flex items-center justify-between">
          <span>업데이트: {{ feeEstimates.lastUpdated ? formatDate(feeEstimates.lastUpdated) : '데이터 없음' }}</span>
          <a
            href="https://mempool.space/"
            target="_blank"
            rel="noopener noreferrer"
            class="text-indigo-600 hover:text-indigo-500 font-medium"
          >
            mempool.space 열기 →
          </a>
        </div>
      </div>
    </div>

    <!-- Stats or Summary -->
    <div class="grid grid-cols-1 gap-5 sm:grid-cols-3">
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="px-4 py-5 sm:p-6">
          <dt class="text-sm font-medium text-slate-500 truncate">총 타임캡슐</dt>
          <dd class="mt-1 text-3xl font-semibold text-slate-900">{{ capsules.length }}</dd>
        </div>
      </div>
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="px-4 py-5 sm:p-6">
          <dt class="text-sm font-medium text-slate-500 truncate">쿠폰 사용됨</dt>
          <dd class="mt-1 text-3xl font-semibold text-emerald-600">{{ usedCouponsCount }}</dd>
        </div>
      </div>
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="px-4 py-5 sm:p-6">
          <dt class="text-sm font-medium text-slate-500 truncate">쿠폰 미사용</dt>
          <dd class="mt-1 text-3xl font-semibold text-slate-600">{{ capsules.length - usedCouponsCount }}</dd>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="flex flex-col">
      <div class="-my-2 -mx-4 overflow-x-auto sm:-mx-6 lg:-mx-8">
        <div class="inline-block min-w-full py-2 align-middle md:px-6 lg:px-8">
          <div class="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
            <table class="min-w-full divide-y divide-slate-300">
              <thead class="bg-slate-50">
                <tr>
                  <th scope="col" class="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-slate-900 sm:pl-6">생성일</th>
                  <th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">사용자 정보</th>
                  <th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">암호화된 메시지</th>
                  <th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">비트코인 주소</th>
                  <th scope="col" class="px-3 py-3.5 text-center text-sm font-semibold text-slate-900">쿠폰 사용</th>
                  <th scope="col" class="px-3 py-3.5 text-center text-sm font-semibold text-slate-900">작업</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-200 bg-white">
                <tr v-for="capsule in capsules" :key="capsule.id">
                  <td class="whitespace-nowrap py-4 pl-4 pr-3 text-sm text-slate-500 sm:pl-6">
                    {{ formatDate(capsule.created_at) }}
                  </td>
                  <td class="whitespace-nowrap px-3 py-4 text-sm text-slate-900">
                    {{ capsule.user_info || '-' }}
                  </td>
                  <td class="px-3 py-4 text-sm text-slate-500 max-w-xs truncate" :title="capsule.encrypted_message">
                    {{ capsule.encrypted_message }}
                  </td>
                  <td class="px-3 py-4 text-sm text-slate-900">
                    <div v-if="capsule.bitcoin_address" class="text-xs text-slate-800 break-all select-text">
                      {{ capsule.bitcoin_address }}
                    </div>
                    <div v-else class="text-xs text-slate-400">주소 미할당</div>
                  </td>
                  <td class="whitespace-nowrap px-3 py-4 text-sm text-center">
                    <button
                      @click="toggleCoupon(capsule)"
                      class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                      :class="[capsule.is_coupon_used ? 'bg-emerald-600' : 'bg-slate-200']"
                    >
                      <span class="sr-only">쿠폰 사용 여부</span>
                      <span
                        aria-hidden="true"
                        class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                        :class="[capsule.is_coupon_used ? 'translate-x-5' : 'translate-x-0']"
                      />
                    </button>
                  </td>
                  <td class="whitespace-nowrap px-3 py-4 text-sm text-center">
                    <div class="flex flex-wrap items-center justify-center gap-2">
                      <button
                        @click="assignAddress(capsule)"
                        class="inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs font-medium rounded text-slate-700 bg-slate-100 hover:bg-slate-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        :disabled="assigningAddressId === capsule.id || !props.isAdmin || !mnemonicState.hasMnemonic || !!capsule.bitcoin_address"
                      >
                        <svg
                          v-if="assigningAddressId === capsule.id"
                          class="animate-spin -ml-0.5 mr-1 h-4 w-4 text-slate-600"
                          fill="none"
                          viewBox="0 0 24 24"
                        >
                          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <svg v-else class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        주소 생성
                      </button>
                      <button
                        @click="confirmDelete(capsule)"
                        class="inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs font-medium rounded text-rose-700 bg-rose-100 hover:bg-rose-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-rose-500 transition-colors"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                        <span class="ml-1">삭제</span>
                      </button>
                    </div>
                  </td>
                </tr>
                <tr v-if="capsules.length === 0">
                  <td colspan="6" class="px-3 py-8 text-center text-sm text-slate-500">
                    저장된 타임캡슐이 없습니다.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="deleteConfirmModal.show" class="fixed z-10 inset-0 overflow-y-auto">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 bg-slate-500 bg-opacity-75 transition-opacity" @click="cancelDelete"></div>
        <span class="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>
        <div class="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
          <div class="sm:flex sm:items-start">
            <div class="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-rose-100 sm:mx-0 sm:h-10 sm:w-10">
              <svg class="h-6 w-6 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
              <h3 class="text-lg leading-6 font-medium text-slate-900">타임캡슐 삭제</h3>
              <div class="mt-2">
                <p class="text-sm text-slate-500">
                  이 타임캡슐을 정말 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
                </p>
                <div class="mt-2 text-xs text-slate-400 bg-slate-50 p-2 rounded">
                  <div><strong>생성일:</strong> {{ formatDate(deleteConfirmModal.capsule?.created_at) }}</div>
                  <div><strong>사용자:</strong> {{ deleteConfirmModal.capsule?.user_info || '-' }}</div>
                </div>
              </div>
            </div>
          </div>
          <div class="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
            <button
              type="button"
              @click="deleteCapsule"
              :disabled="deleteConfirmModal.deleting"
              class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-rose-600 text-base font-medium text-white hover:bg-rose-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-rose-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg v-if="deleteConfirmModal.deleting" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ deleteConfirmModal.deleting ? '삭제 중...' : '삭제' }}
            </button>
            <button
              type="button"
              @click="cancelDelete"
              :disabled="deleteConfirmModal.deleting"
              class="mt-3 w-full inline-flex justify-center rounded-md border border-slate-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              취소
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { API_BASE_URL } from '../../api'

const props = defineProps({
  isAdmin: { type: Boolean, default: false },
  showSuccess: { type: Function, default: () => {} },
  showError: { type: Function, default: () => {} },
})

const capsules = ref([])
const assigningAddressId = ref(null)
const generatingMnemonic = ref(false)
const showMnemonic = ref(false)
const mnemonicState = ref({
  loading: false,
  hasMnemonic: false,
  mnemonic: '',
  mnemonicId: null,
  assignedCount: 0,
  nextAddressIndex: 0,
})
const broadcastSettings = ref({
  loading: false,
  saving: false,
  host: '',
  port: 8332,
})
const connectionTest = ref({
  running: false,
  lastStatus: null,
  blockHeight: null,
  chain: '',
  checkedAt: null,
  message: '',
})
const feeEstimates = ref({
  loading: false,
  data: null,
  lastUpdated: null,
  error: '',
})
const recommendedNodes = ref([])
const deleteConfirmModal = ref({
  show: false,
  capsule: null,
  deleting: false,
})

const usedCouponsCount = computed(() => capsules.value.filter(c => c.is_coupon_used).length)
const feeCards = computed(() => {
  const data = feeEstimates.value.data || {}
  return [
    { key: 'fastestFee', label: '가장 빠름', caption: '1블록 목표', value: data.fastestFee },
    { key: 'halfHourFee', label: '30분 내', caption: '3블록 목표', value: data.halfHourFee },
    { key: 'hourFee', label: '1시간 내', caption: '6블록 목표', value: data.hourFee },
    { key: 'economyFee', label: '절약형', caption: '저렴하지만 느림', value: data.economyFee ?? data.minimumFee },
  ]
})

const getAdminUsername = () => {
  const nickname = localStorage.getItem('nickname')
  if (!nickname || localStorage.getItem('isAdmin') !== 'true') {
    return ''
  }
  return nickname
}

async function fetchTimeCapsules() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/time-capsule/admin/list`)
    if (response.ok) {
      capsules.value = await response.json()
    } else {
      props.showError?.('타임캡슐 목록을 불러오지 못했습니다.')
    }
  } catch (error) {
    console.error('Error fetching time capsules:', error)
    props.showError?.('타임캡슐 목록을 불러오지 못했습니다.')
  }
}

async function fetchMnemonicStatus() {
  mnemonicState.value.loading = true
  try {
    const username = getAdminUsername()
    const params = new URLSearchParams(username ? { username } : {})
    const response = await fetch(`${API_BASE_URL}/api/time-capsule/admin/mnemonic?${params}`, {
      credentials: 'include',
    })
    const data = await response.json()
    if (response.ok && data.ok !== false) {
      mnemonicState.value = {
        loading: false,
        hasMnemonic: Boolean(data.has_mnemonic),
        mnemonic: data.mnemonic || '',
        mnemonicId: data.mnemonic_id || null,
        assignedCount: data.assigned_count || 0,
        nextAddressIndex: data.next_address_index || 0,
      }
    } else {
      mnemonicState.value.loading = false
      props.showError?.(data.error || '니모닉 정보를 불러오지 못했습니다.')
    }
  } catch (error) {
    console.error('Failed to fetch mnemonic status', error)
    mnemonicState.value.loading = false
    props.showError?.('니모닉 정보를 불러오지 못했습니다.')
  }
}

async function fetchBroadcastSettings() {
  broadcastSettings.value.loading = true
  try {
    const username = getAdminUsername()
    const params = new URLSearchParams(username ? { username } : {})
    const response = await fetch(`${API_BASE_URL}/api/time-capsule/admin/broadcast-settings?${params}`, {
      credentials: 'include',
    })
    const data = await response.json()
    if (response.ok && data.ok) {
      broadcastSettings.value.host = data.settings?.fullnode_host || ''
      broadcastSettings.value.port = data.settings?.fullnode_port ?? 8332
      recommendedNodes.value = data.recommended_nodes || []
    } else {
      props.showError?.(data.error || '브로드캐스트 설정을 불러오지 못했습니다.')
    }
  } catch (error) {
    console.error('Failed to fetch broadcast settings', error)
    props.showError?.('브로드캐스트 설정을 불러오지 못했습니다.')
  } finally {
    broadcastSettings.value.loading = false
  }
}

async function saveBroadcastSettings() {
  if (!props.isAdmin) {
    props.showError?.('관리자만 설정을 변경할 수 있습니다.')
    return
  }
  const host = (broadcastSettings.value.host || '').trim()
  const port = Number(broadcastSettings.value.port)
  if (!host) {
    props.showError?.('풀노드 IP 또는 호스트를 입력하세요.')
    return
  }
  if (!Number.isFinite(port) || port <= 0 || port > 65535) {
    props.showError?.('유효한 포트 번호를 입력하세요.')
    return
  }

  broadcastSettings.value.saving = true
  try {
    const username = getAdminUsername()
    const params = new URLSearchParams(username ? { username } : {})
    const response = await fetch(`${API_BASE_URL}/api/time-capsule/admin/broadcast-settings?${params}`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fullnode_host: host, fullnode_port: port }),
    })
    const data = await response.json()
    if (response.ok && data.ok) {
      broadcastSettings.value.host = data.settings.fullnode_host || host
      broadcastSettings.value.port = data.settings.fullnode_port ?? port
      recommendedNodes.value = data.recommended_nodes || recommendedNodes.value
      props.showSuccess?.('브로드캐스트 노드 설정을 저장했습니다.')
    } else {
      props.showError?.(data.error || '브로드캐스트 설정 저장에 실패했습니다.')
    }
  } catch (error) {
    console.error('Failed to save broadcast settings', error)
    props.showError?.('브로드캐스트 설정 저장에 실패했습니다.')
  } finally {
    broadcastSettings.value.saving = false
  }
}

async function testBroadcastConnection() {
  const host = (broadcastSettings.value.host || '').trim()
  const port = Number(broadcastSettings.value.port)
  if (!host || !Number.isFinite(port)) {
    props.showError?.('풀노드 IP와 포트를 먼저 입력하세요.')
    return
  }
  connectionTest.value.running = true
  connectionTest.value.message = ''
  connectionTest.value.lastStatus = null
  try {
    const username = getAdminUsername()
    const params = new URLSearchParams(username ? { username } : {})
    const response = await fetch(`${API_BASE_URL}/api/time-capsule/admin/broadcast-test?${params}`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fullnode_host: host, fullnode_port: port }),
    })
    const data = await response.json()
    if (response.ok && data.ok) {
      connectionTest.value.lastStatus = 'success'
      connectionTest.value.blockHeight = data.block_height ?? null
      connectionTest.value.chain = data.chain || ''
      connectionTest.value.checkedAt = new Date().toISOString()
      props.showSuccess?.('풀노드 연결이 확인되었습니다.')
    } else {
      connectionTest.value.lastStatus = 'error'
      connectionTest.value.message = data.error || '연결에 실패했습니다.'
      connectionTest.value.checkedAt = new Date().toISOString()
      props.showError?.(connectionTest.value.message)
    }
  } catch (error) {
    console.error('Failed to test broadcast connection', error)
    connectionTest.value.lastStatus = 'error'
    connectionTest.value.message = '연결 테스트 중 오류가 발생했습니다.'
    connectionTest.value.checkedAt = new Date().toISOString()
    props.showError?.('연결 테스트 중 오류가 발생했습니다.')
  } finally {
    connectionTest.value.running = false
  }
}

async function fetchFeeEstimates() {
  feeEstimates.value.loading = true
  feeEstimates.value.error = ''
  try {
    const username = getAdminUsername()
    const params = new URLSearchParams(username ? { username } : {})
    const response = await fetch(`${API_BASE_URL}/api/time-capsule/admin/fee-estimates?${params}`, {
      credentials: 'include',
    })
    const data = await response.json()
    if (response.ok && data.ok) {
      feeEstimates.value.data = data.fees || {}
      feeEstimates.value.lastUpdated = new Date().toISOString()
    } else {
      feeEstimates.value.error = data.error || '수수료 정보를 불러오지 못했습니다.'
    }
  } catch (error) {
    console.error('Failed to fetch fee estimates', error)
    feeEstimates.value.error = '수수료 정보를 불러오지 못했습니다.'
  } finally {
    feeEstimates.value.loading = false
  }
}

async function createMnemonic() {
  if (!props.isAdmin) {
    props.showError?.('관리자만 니모닉을 생성할 수 있습니다.')
    return
  }
  if (mnemonicState.value.hasMnemonic) return

  const username = getAdminUsername()
  if (!username) {
    props.showError?.('관리자 인증 정보가 없습니다.')
    return
  }

  generatingMnemonic.value = true
  try {
    const params = new URLSearchParams({ username })
    const response = await fetch(`${API_BASE_URL}/api/time-capsule/admin/mnemonic?${params}`, {
      method: 'POST',
      credentials: 'include',
    })
    const data = await response.json()
    if (response.ok && data.ok !== false) {
      mnemonicState.value = {
        loading: false,
        hasMnemonic: true,
        mnemonic: data.mnemonic || '',
        mnemonicId: data.mnemonic_id || null,
        assignedCount: 0,
        nextAddressIndex: data.next_address_index || 0,
      }
      showMnemonic.value = true
      props.showSuccess?.('니모닉이 생성되었습니다. 반드시 안전하게 보관하세요.')
    } else {
      props.showError?.(data.error || '니모닉 생성에 실패했습니다.')
    }
  } catch (error) {
    console.error('Failed to create mnemonic', error)
    props.showError?.('니모닉 생성에 실패했습니다.')
  } finally {
    generatingMnemonic.value = false
  }
}

async function assignAddress(capsule) {
  if (!capsule?.id) return
  if (!props.isAdmin) {
    props.showError?.('관리자만 주소를 할당할 수 있습니다.')
    return
  }
  if (!mnemonicState.value.hasMnemonic) {
    props.showError?.('먼저 니모닉을 생성하세요.')
    return
  }
  const username = getAdminUsername()
  if (!username) {
    props.showError?.('관리자 인증 정보가 없습니다.')
    return
  }

  assigningAddressId.value = capsule.id
  try {
    const params = new URLSearchParams({ username })
    const response = await fetch(`${API_BASE_URL}/api/time-capsule/admin/assign-address/${capsule.id}?${params}`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    })
    const data = await response.json()
    if (response.ok && data.ok) {
      const updated = data.capsule || { ...capsule, bitcoin_address: data.address, address_index: data.address_index }
      const idx = capsules.value.findIndex(c => c.id === capsule.id)
      if (idx >= 0) {
        capsules.value[idx] = { ...capsules.value[idx], ...updated }
      }
      mnemonicState.value.nextAddressIndex = (mnemonicState.value.nextAddressIndex || 0) + 1
      mnemonicState.value.assignedCount = (mnemonicState.value.assignedCount || 0) + 1
      props.showSuccess?.('새 비트코인 주소를 생성했습니다.')
    } else {
      props.showError?.(data.error || '주소 할당에 실패했습니다.')
    }
  } catch (error) {
    console.error('Failed to assign address', error)
    props.showError?.('주소 할당에 실패했습니다.')
  } finally {
    assigningAddressId.value = null
  }
}

async function toggleCoupon(capsule) {
  const newValue = !capsule.is_coupon_used
  capsule.is_coupon_used = newValue

  try {
    const response = await fetch(`${API_BASE_URL}/api/time-capsule/admin/update-coupon/${capsule.id}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ is_coupon_used: newValue }),
    })
    
    if (!response.ok) {
      capsule.is_coupon_used = !newValue
      props.showError?.('상태 업데이트에 실패했습니다.')
    }
  } catch (error) {
    console.error('Error updating coupon:', error)
    capsule.is_coupon_used = !newValue
    props.showError?.('오류가 발생했습니다.')
  }
}

function formatDate(isoString) {
  if (!isoString) return '-'
  return new Date(isoString).toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function copyMnemonic() {
  if (!mnemonicState.value.mnemonic) return
  navigator.clipboard?.writeText(mnemonicState.value.mnemonic).then(() => {
    props.showSuccess?.('니모닉이 복사되었습니다.')
  }).catch(() => {
    props.showError?.('복사에 실패했습니다.')
  })
}

function confirmDelete(capsule) {
  deleteConfirmModal.value = {
    show: true,
    capsule,
    deleting: false,
  }
}

function cancelDelete() {
  if (deleteConfirmModal.value.deleting) return
  deleteConfirmModal.value = {
    show: false,
    capsule: null,
    deleting: false,
  }
}

function applyRecommendedNode(node) {
  if (!node) return
  broadcastSettings.value.host = node.host || ''
  broadcastSettings.value.port = node.port ?? 8332
}

async function deleteCapsule() {
  if (!deleteConfirmModal.value.capsule) return

  deleteConfirmModal.value.deleting = true

  try {
    const response = await fetch(`${API_BASE_URL}/api/time-capsule/admin/delete/${deleteConfirmModal.value.capsule.id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (response.ok) {
      capsules.value = capsules.value.filter(c => c.id !== deleteConfirmModal.value.capsule.id)
      deleteConfirmModal.value.deleting = false
      cancelDelete()
      props.showSuccess?.('타임캡슐을 삭제했습니다.')
    } else {
      const errorData = await response.json().catch(() => ({}))
      props.showError?.(errorData.error || '삭제에 실패했습니다.')
      deleteConfirmModal.value.deleting = false
    }
  } catch (error) {
    console.error('Error deleting time capsule:', error)
    props.showError?.('삭제 중 오류가 발생했습니다.')
    deleteConfirmModal.value.deleting = false
  }
}

onMounted(() => {
  fetchMnemonicStatus()
  fetchTimeCapsules()
  fetchBroadcastSettings()
  fetchFeeEstimates()
})
</script>
