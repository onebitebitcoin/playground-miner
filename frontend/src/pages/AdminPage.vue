<template>
  <div class="min-h-screen bg-gray-50 px-3 py-4 sm:px-6">
    <div class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="mb-6 md:mb-8">
        <h1 class="text-2xl md:text-3xl font-bold text-gray-900 mb-2">관리자 페이지</h1>
        <p class="text-sm md:text-base text-gray-600">시스템 설정을 관리하고 데이터를 모니터링하세요.</p>
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
            <nav class="-mb-px flex space-x-4 md:space-x-8 overflow-x-auto" aria-label="Tabs">
              <button
                @click="activeTab = 'mining'"
                :class="[
                  activeTab === 'mining'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-xs md:text-sm'
                ]"
              >
                비트코인 채굴
              </button>
              <button
                @click="activeTab = 'mnemonics'"
                :class="[
                  activeTab === 'mnemonics'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-xs md:text-sm'
                ]"
              >
                지갑
              </button>
              <button
                @click="activeTab = 'routing'"
                :class="[
                  activeTab === 'routing'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-xs md:text-sm'
                ]"
              >
                수수료 계산
              </button>
              <button
                @click="activeTab = 'sidebar'"
                :class="[
                  activeTab === 'sidebar'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-xs md:text-sm'
                ]"
              >
                설정
              </button>
            </nav>
          </div>
        </div>

        <!-- Mnemonics Tab Content -->
        <div v-if="activeTab === 'mnemonics'" class="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-8">
          <!-- Mnemonic Pool Management -->
          <div class="space-y-4 md:space-y-6">
            <div class="bg-white rounded-lg shadow-md p-4 md:p-6 h-auto md:h-[700px] flex flex-col">
              <h3 class="text-base md:text-lg font-semibold text-gray-900 mb-4">니모닉 풀 관리</h3>

              <!-- Manual Mnemonic Add -->
              <div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <div class="flex items-center justify-between mb-3">
                  <h4 class="font-medium text-gray-800">개별 니모닉 추가</h4>
                  <div class="flex items-center gap-1">
                    <button @click="generateAndFillAdminMnemonic"
                            class="p-2 rounded text-gray-700 hover:text-gray-900"
                            title="자동 생성">
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v12" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 12h12" />
                      </svg>
                      <span class="sr-only">자동 생성</span>
                    </button>
                    <button @click="clearAdminManualMnemonic"
                            class="p-2 rounded text-gray-700 hover:text-gray-900"
                            title="지우기">
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V5a2 2 0 00-2-2H9a2 2 0 00-2 2v2m-3 0h14" />
                      </svg>
                      <span class="sr-only">지우기</span>
                    </button>
                  </div>
                </div>
                <div class="space-y-3">
                  <!-- Individual word inputs -->
                  <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    <div v-for="i in 12" :key="i" class="relative">
                      <label :for="`admin-word-${i}`" class="block text-xs font-medium text-gray-600 mb-1">
                        {{ i }}
                      </label>
                      <input
                        :id="`admin-word-${i}`"
                        v-model="adminMnemonicWords[i-1]"
                        @input="handleWordInput(i-1, $event)"
                        @keydown="handleKeyDown(i-1, $event)"
                        @paste="handleAdminPaste($event, i-1)"
                        @blur="handleBlur"
                        type="text"
                        :placeholder="`단어 ${i}`"
                        autocomplete="off"
                        class="w-full px-2 py-2 text-xs sm:text-sm border border-gray-200 rounded focus:ring-2 focus:ring-gray-500 focus:border-gray-500 outline-none"
                        :class="{ 'border-red-300': manualPoolError || (adminMnemonicUnknown && adminMnemonicUnknown.length && adminMnemonicUnknown.includes((adminMnemonicWords[i-1]||'').trim().toLowerCase())) }"
                      />

                      <!-- Autocomplete dropdown -->
                      <div
                        v-if="autocompleteIndex === i-1 && autocompleteSuggestions.length > 0"
                        class="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-48 overflow-y-auto"
                      >
                        <div
                          v-for="(suggestion, idx) in autocompleteSuggestions"
                          :key="suggestion"
                          @click="selectSuggestion(i-1, suggestion)"
                          class="px-3 py-2 cursor-pointer text-sm hover:bg-blue-50 transition-colors"
                          :class="{ 'bg-blue-100': idx === autocompleteSelectedIndex }"
                        >
                          {{ suggestion }}
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Alternative textarea input -->
                  <div class="border-t border-gray-200 pt-3">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                      또는 한번에 입력:
                    </label>
                    <textarea v-model="manualPoolMnemonicText"
                              @input="updateAdminFromTextarea"
                              placeholder="12/15/18/21/24개의 영어 단어를 공백으로 구분하여 입력"
                              class="w-full h-16 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-gray-500 outline-none resize-none"
                              :class="{ 'border-red-300': manualPoolError }"></textarea>
                    <div class="mt-2 space-y-2">
                      <button @click="checkAdminMnemonic"
                              :disabled="adminMnemonicChecking"
                              class="w-full px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900 disabled:opacity-50 disabled:cursor-not-allowed">
                        {{ adminMnemonicChecking ? '검사 중...' : '유효성 검사' }}
                      </button>
                      <div v-if="adminMnemonicValidity !== null" :class="adminMnemonicValidity ? 'text-green-700' : 'text-red-600'" class="text-sm">
                        {{ adminMnemonicValidity ? '유효한 BIP39 니모닉' : '유효하지 않은 니모닉' }}
                        <span v-if="adminMnemonicWordCount"> ({{ adminMnemonicWordCount }}단어)</span>
                        <span v-if="!adminMnemonicValidity && adminMnemonicUnknown && adminMnemonicUnknown.length" class="ml-2 text-xs text-red-600">[{{ adminMnemonicUnknown.join(', ') }}]</span>
                        <span v-if="!adminMnemonicValidity && (!adminMnemonicUnknown || adminMnemonicUnknown.length === 0) && adminMnemonicErrorCode === 'checksum_failed'" class="ml-2 text-xs text-red-600">(체크섬 불일치)</span>
                      </div>
                    </div>
                  </div>

                  <div v-if="manualPoolError" class="text-red-600 text-sm">
                    {{ manualPoolError }}
                  </div>

                  <button @click="addManualMnemonicToPool"
                          :disabled="loading || !isValidAdminMnemonicInput"
                          class="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed">
                    {{ loading ? '추가 중...' : '니모닉 풀 추가' }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          

          <!-- Mnemonic Pool Status -->
          <div class="space-y-6">
            <div class="bg-white rounded-lg shadow-md p-4 md:p-6 h-[700px] flex flex-col">
              <div class="flex items-center justify-between mb-1">
                <h3 class="text-base md:text-lg font-semibold text-gray-900">풀 상태</h3>
                <div class="flex items-center gap-2">
                  <button @click="loadAllMnemonicBalances"
                          :disabled="balancesLoading || adminMnemonics.length === 0"
                          class="p-2 rounded text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                          title="잔액 업데이트">
                    <template v-if="balancesLoading">
                      <div class="w-4 h-4 md:w-5 md:h-5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
                    </template>
                    <template v-else>
                      <svg class="w-4 h-4 md:w-5 md:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </template>
                    <span class="sr-only">잔액 업데이트</span>
                  </button>
                </div>
              </div>
              <div class="text-xs md:text-sm text-gray-600 mb-3 flex-shrink-0">
                전체 니모닉 {{ adminMnemonics.length }} · 사용 가능 {{ availableMnemonicsCount }}
              </div>

              <div class="bg-gray-50 p-2 md:p-4 rounded-lg overflow-y-auto flex-1 min-h-0">
                <div v-if="adminMnemonics.length === 0" class="text-gray-500 text-center py-8 text-sm">
                  저장된 니모닉이 없습니다
                </div>
                <div v-else class="space-y-2">
                  <div v-for="mnemonic in adminMnemonics" :key="mnemonic.id"
                       class="flex flex-col sm:flex-row sm:items-start sm:justify-between p-2 md:p-3 bg-white rounded border gap-2 sm:gap-3">
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2 flex-wrap mb-1">
                        <span class="text-xs text-gray-500">ID {{ mnemonic.id }}</span>
                        <span v-if="mnemonic.is_assigned" class="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded">{{ mnemonic.assigned_to || '미상' }}</span>
                        <span v-else class="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">대기중</span>
                      </div>
                      <span class="text-xs text-gray-500 block mb-1">{{ formatDate(mnemonic.created_at) }}</span>
                      <div class="text-xs md:text-sm text-gray-700 flex flex-wrap items-center gap-1">
                        <span v-if="mnemonic._loading_balance" class="text-blue-600">조회중...</span>
                        <span v-else-if="mnemonic._balance_error" class="flex items-center gap-1 text-red-600">
                          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span class="font-medium">조회 실패</span>
                          <span class="text-xs text-red-500" :title="mnemonic._balance_error_detail">({{ mnemonic._balance_error }})</span>
                        </span>
                        <span v-else class="flex flex-wrap items-center gap-1">
                          <span class="font-medium">{{ Number(mnemonic.balance_sats || 0).toLocaleString() }} sats</span>
                          <span class="text-gray-500 text-xs">({{ formatBtc(mnemonic.balance_sats) }})</span>
                        </span>
                      </div>


                    </div>
                    <div class="shrink-0 flex sm:flex-col items-center sm:items-end gap-1">
                      <div class="flex items-center gap-1">
                        <button @click="fetchOnchain(mnemonic)"
                                :disabled="mnemonic._loading_balance"
                                class="p-1.5 md:p-2 rounded text-blue-600 hover:text-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                title="잔액 새로고침">
                          <svg v-if="mnemonic._loading_balance" class="w-4 h-4 md:w-5 md:h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          <svg v-else class="w-4 h-4 md:w-5 md:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                        </button>
                        <button v-if="mnemonic.is_assigned" @click="unassignMnemonic(mnemonic)"
                                class="p-1.5 md:p-2 rounded text-amber-700 hover:text-amber-800"
                                title="할당 해제">
                          <svg class="w-4 h-4 md:w-5 md:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12h6m0 0l-3 3m3-3l-3-3M9 7a4 4 0 110 8 4 4 0 010-8z" />
                          </svg>
                        </button>
                      <button @click="showMnemonicInAdmin(mnemonic)"
                              class="p-1.5 md:p-2 rounded text-gray-700 hover:text-gray-900"
                              title="보기">
                          <svg class="w-4 h-4 md:w-5 md:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.477 0 8.268 2.943 9.542 7-1.274 4.057-5.065 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                          </svg>
                        </button>
                        <button @click="deleteMnemonic(mnemonic)"
                                class="p-1.5 md:p-2 rounded text-red-600 hover:text-red-700"
                                title="삭제">
                          <svg class="w-4 h-4 md:w-5 md:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m-3 0h14"></path>
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>


            </div>
          </div>
          <div class="lg:col-span-2">
            <div class="bg-white rounded-lg shadow-md p-4 md:p-6">
              <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
                <div>
                  <h3 class="text-base md:text-lg font-semibold text-gray-900">킹스톤 지갑 목록</h3>
                  <p class="text-sm text-gray-500">생성된 지갑과 PIN을 확인하고 관리하세요.</p>
                </div>
                <button
                  @click="refreshKingstoneWallets"
                  :disabled="kingstoneWalletsLoading"
                  class="inline-flex items-center gap-2 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg disabled:opacity-50 disabled:cursor-wait"
                >
                  <svg v-if="!kingstoneWalletsLoading" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                  </svg>
                  <span>새로고침</span>
                </button>
              </div>

              <div v-if="kingstoneWalletsLoading" class="py-10 text-center text-gray-500">
                <div class="w-6 h-6 border-2 border-gray-300 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
                로딩 중...
              </div>
              <div v-else-if="kingstoneWalletsError" class="p-4 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                {{ kingstoneWalletsError }}
              </div>
              <div v-else-if="kingstoneWallets.length === 0" class="p-6 bg-gray-50 border border-dashed border-gray-200 rounded text-center text-sm text-gray-600">
                등록된 지갑이 없습니다.
              </div>
              <div v-else class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200 text-sm">
                  <thead class="bg-gray-50 text-xs uppercase tracking-wide text-gray-500">
                    <tr>
                      <th scope="col" class="px-4 py-3 text-left font-semibold">지갑 이름</th>
                      <th scope="col" class="px-4 py-3 text-left font-semibold">생성자</th>
                      <th scope="col" class="px-4 py-3 text-left font-semibold">생성일</th>
                      <th scope="col" class="px-4 py-3 text-left font-semibold">핀번호</th>
                      <th scope="col" class="px-4 py-3 text-right font-semibold">작업</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-gray-100">
                    <tr v-for="wallet in kingstoneWallets" :key="wallet.wallet_id" class="hover:bg-gray-50 transition-colors">
                      <td class="px-4 py-3 font-medium text-gray-900">{{ wallet.wallet_name }}</td>
                      <td class="px-4 py-3 text-gray-700">{{ wallet.username }}</td>
                      <td class="px-4 py-3 text-gray-600 whitespace-nowrap">{{ formatDate(wallet.created_at) }}</td>
                      <td class="px-4 py-3 text-gray-900 font-mono">
                        {{ wallet.pin || '미저장' }}
                      </td>
                      <td class="px-4 py-3 text-right">
                        <button
                          @click="deleteKingstoneWallet(wallet)"
                          :disabled="!isAdmin || isKingstoneWalletDeleting(wallet.wallet_id)"
                          class="inline-flex items-center justify-center w-9 h-9 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed"
                          title="지갑 삭제"
                        >
                          <svg v-if="!isKingstoneWalletDeleting(wallet.wallet_id)" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V5a2 2 0 00-2-2H9a2 2 0 00-2 2v2m-3 0h14" />
                          </svg>
                          <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                          </svg>
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <!-- Routing Tab Content (left-side tabs) -->
        <div v-if="activeTab === 'routing'">
          <div class="bg-white rounded-lg shadow-md">
            <!-- Mobile horizontal tabs -->
            <div class="md:hidden border-b border-gray-200 p-2">
              <div class="flex space-x-1 overflow-x-auto">
                <button @click="activeRoutingTab = 'nodes'" :class="[activeRoutingTab === 'nodes' ? 'bg-blue-50 text-blue-700 border-blue-500' : 'text-gray-700 border-transparent hover:bg-gray-50','px-3 py-2 rounded border-b-2 whitespace-nowrap text-sm font-medium']">서비스 노드 관리</button>
                <button @click="activeRoutingTab = 'routes'" :class="[activeRoutingTab === 'routes' ? 'bg-blue-50 text-blue-700 border-blue-500' : 'text-gray-700 border-transparent hover:bg-gray-50','px-3 py-2 rounded border-b-2 whitespace-nowrap text-sm font-medium']">경로 관리</button>
                <button @click="activeRoutingTab = 'final'" :class="[activeRoutingTab === 'final' ? 'bg-blue-50 text-blue-700 border-blue-500' : 'text-gray-700 border-transparent hover:bg-gray-50','px-3 py-2 rounded border-b-2 whitespace-nowrap text-sm font-medium']">최종 경로</button>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-4">
              <!-- Desktop left sidebar -->
              <div class="hidden md:block border-r border-gray-200 p-4 space-y-2">
                <button @click="activeRoutingTab = 'nodes'" :class="[activeRoutingTab === 'nodes' ? 'bg-blue-50 text-blue-700 border border-blue-200' : 'hover:bg-gray-50 text-gray-700 border border-transparent','w-full text-left px-3 py-2 rounded']">서비스 노드 관리</button>
                <button @click="activeRoutingTab = 'routes'" :class="[activeRoutingTab === 'routes' ? 'bg-blue-50 text-blue-700 border border-blue-200' : 'hover:bg-gray-50 text-gray-700 border border-transparent','w-full text-left px-3 py-2 rounded']">경로 관리</button>
                <button @click="activeRoutingTab = 'final'" :class="[activeRoutingTab === 'final' ? 'bg-blue-50 text-blue-700 border border-blue-200' : 'hover:bg-gray-50 text-gray-700 border border-transparent','w-full text-left px-3 py-2 rounded']">최종 경로</button>
              </div>
              <div class="md:col-span-3 p-4 md:p-6">
                <div v-if="routingUpdateLoading" class="bg-blue-50 p-4 rounded-lg mb-4"><p class="text-blue-800">데이터를 로딩하고 있습니다...</p></div>
                <div v-if="activeRoutingTab === 'nodes'">
                  <h3 class="text-lg font-semibold text-gray-900 mb-4">서비스 노드 관리</h3>
                  <div class="space-y-4">
                    <div class="border border-dashed border-blue-200 rounded-lg p-4 bg-blue-50/40">
                      <div class="flex items-center justify-between mb-3">
                        <div>
                          <h4 class="font-medium text-gray-900">새 서비스 노드 추가</h4>
                          <p class="text-sm text-gray-500 mt-1">거래소/서비스 노드를 직접 등록할 수 있습니다. 생성 즉시 DB에 저장됩니다.</p>
                        </div>
                        <span class="text-xs font-semibold px-2 py-1 rounded bg-blue-100 text-blue-800">신규 등록</span>
                      </div>
                      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label class="block text-sm font-medium text-gray-700 mb-1">서비스 코드</label>
                          <input
                            v-model="newServiceNode.service"
                            type="text"
                            placeholder="예: upbit_krw"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          />
                          <p class="mt-1 text-xs text-gray-500">소문자/숫자/밑줄만 사용 (예: binance_btc)</p>
                        </div>
                        <div>
                          <label class="block text-sm font-medium text-gray-700 mb-1">표시명</label>
                          <input
                            v-model="newServiceNode.display_name"
                            type="text"
                            placeholder="예: 바이낸스 BTC"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          />
                        </div>
                        <div>
                          <label class="block text-sm font-medium text-gray-700 mb-1">노드 유형</label>
                          <select
                            v-model="newServiceNode.node_type"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                          >
                            <option v-for="type in nodeTypeOptions" :key="`new-type-${type.value}`" :value="type.value">
                              {{ type.label }}
                            </option>
                          </select>
                        </div>
                        <div>
                          <label class="block text-sm font-medium text-gray-700 mb-1">웹사이트 주소</label>
                          <input
                            v-model="newServiceNode.website_url"
                            type="text"
                            placeholder="https://"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          />
                        </div>
                        <div class="md:col-span-2">
                          <label class="block text-sm font-medium text-gray-700 mb-1">설명</label>
                          <textarea
                            v-model="newServiceNode.description"
                            rows="2"
                            placeholder="노드 설명을 입력하세요"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          ></textarea>
                        </div>
                      </div>
                      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                        <label class="flex items-center gap-2 text-sm text-gray-700">
                          <input v-model="newServiceNode.is_kyc" type="checkbox" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                          KYC 필요
                        </label>
                        <label class="flex items-center gap-2 text-sm text-gray-700">
                          <input v-model="newServiceNode.is_custodial" type="checkbox" class="rounded border-gray-300 text-red-600 focus:ring-red-500" />
                          수탁형 서비스
                        </label>
                        <label class="flex items-center gap-2 text-sm text-gray-700">
                          <input v-model="newServiceNode.is_enabled" type="checkbox" class="rounded border-gray-300 text-green-600 focus:ring-green-500" />
                          즉시 활성화
                        </label>
                      </div>
                      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mt-4 gap-3">
                        <p class="text-sm text-gray-600">
                          서비스 코드는 고유해야 하며 생성 후 경로에서 바로 사용할 수 있습니다.
                        </p>
                        <button
                          @click="createServiceNode"
                          :disabled="!isAdmin || routingUpdateLoading || !canCreateServiceNode"
                          class="w-full sm:w-auto px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                        >
                          {{ routingUpdateLoading ? '등록 중...' : '서비스 노드 생성' }}
                        </button>
                      </div>
                      <div v-if="newServiceNodeError && isNewServiceNodeDirty" class="mt-2 text-sm text-red-600">
                        {{ newServiceNodeError }}
                      </div>
                    </div>

                    <template v-if="serviceNodes.length === 0">
                      <div class="text-center py-8 text-gray-500 bg-white border border-dashed border-gray-200 rounded-lg">
                        등록된 서비스 노드가 없습니다. 새로운 노드를 추가하세요.
                      </div>
                    </template>
                    <template v-else>
                      <div class="space-y-4">
                        <div v-for="node in serviceNodes" :key="node.id" class="border border-gray-200 rounded-lg p-4">
                        <div class="flex items-center justify-between mb-3">
                          <h4 class="font-medium text-gray-900">{{ node.display_name }}</h4>
                          <div class="flex items-center gap-2"><span :class="[node.is_enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800', 'text-xs px-2 py-1 rounded']">{{ node.is_enabled ? '활성' : '비활성' }}</span></div>
                        </div>
                        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                          <div><label class="block text-sm font-medium text-gray-700 mb-1">표시명</label><input v-model="node.display_name" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent" /></div>
                          <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">노드 유형</label>
                            <select v-model="node.node_type" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white">
                              <option v-for="type in nodeTypeOptions" :key="`node-type-${node.service}-${type.value}`" :value="type.value">{{ type.label }}</option>
                            </select>
                          </div>
                          <div><label class="block text-sm font-medium text-gray-700 mb-1">KYC 상태</label><div class="flex items-center gap-2 mt-2"><label class="flex items-center"><input v-model="node.is_kyc" type="checkbox" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" /><span class="ml-2 text-sm text-gray-700">KYC 필요</span></label></div></div>
                        <div><label class="block text-sm font-medium text-gray-700 mb-1">수탁 유형</label><div class="flex items-center gap-2 mt-2"><label class="flex items-center"><input v-model="node.is_custodial" type="checkbox" class="rounded border-gray-300 text-red-600 focus:ring-red-500" /><span class="ml-2 text-sm text-gray-700">수탁형</span></label></div></div>
                        <div><label class="block text-sm font-medium text-gray-700 mb-1">활성 상태</label><div class="flex items-center gap-2 mt-2"><label class="flex items-center"><input v-model="node.is_enabled" type="checkbox" class="rounded border-gray-300 text-green-600 focus:ring-green-500" /><span class="ml-2 text-sm text-gray-700">활성화</span></label></div></div>
                        <div><label class="block text-sm font-medium text-gray-700 mb-1">작업</label><button @click="updateServiceNode(node)" :disabled="!isAdmin || routingUpdateLoading" class="w-full px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm">{{ routingUpdateLoading ? '업데이트 중...' : '업데이트' }}</button></div>
                      </div>
                        <div class="mt-4"><label class="block text-sm font-medium text-gray-700 mb-1">설명</label><input v-model="node.description" type="text" placeholder="서비스 설명" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent" /></div>
                      </div>
                    </div>
                    </template>
                  </div>
                </div>
                <div v-else-if="activeRoutingTab === 'routes'">
                  <h3 class="text-lg font-semibold text-gray-900 mb-4">경로 관리</h3>
                  <div class="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg mb-6 border border-blue-200">
                    <h4 class="font-semibold text-blue-900 mb-4 flex items-center"><svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/></svg>새 경로 생성</h4>
                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-3">1. 출발지 선택</label>
                        <div class="grid grid-cols-2 gap-2 max-h-56 sm:max-h-72 overflow-y-auto overscroll-contain border rounded p-2 pr-2 bg-white" style="scrollbar-gutter: stable;">
                          <div v-for="node in serviceNodes" :key="`source-${node.id}`" @click="newRoute.sourceId = node.id" :class="['p-2 border rounded cursor-pointer text-sm', newRoute.sourceId === node.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-blue-300']">{{ node.display_name }}</div>
                        </div>
                      </div>
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-3">2. 목적지 선택</label>
                        <div class="grid grid-cols-2 gap-2 h-60 sm:h-72 overflow-y-auto overscroll-contain border rounded p-2 pr-2 bg-white" style="scrollbar-gutter: stable;">
                          <div v-for="node in filteredDestNodes" :key="`dest-${node.id}`" @click="newRoute.sourceId !== node.id ? newRoute.destinationId = node.id : null" :class="['p-2 border rounded cursor-pointer text-sm', newRoute.destinationId === node.id ? 'border-green-500 bg-green-50' : (newRoute.sourceId === node.id ? 'border-gray-200 opacity-60 cursor-not-allowed' : 'border-gray-200 hover:border-green-300')]">{{ node.display_name }}</div>
                        </div>
                      </div>
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">경로 유형</label>
                        <div class="grid gap-2">
                          <label
                            v-for="option in routeTypeOptions"
                            :key="option.value"
                            class="block cursor-pointer"
                          >
                            <input
                              class="sr-only"
                              type="radio"
                              name="new-route-type"
                              :value="option.value"
                              v-model="newRoute.routeType"
                            />
                            <div
                              :class="[
                                newRoute.routeType === option.value
                                  ? 'border-blue-500 bg-blue-50 shadow-sm'
                                  : 'border-gray-200 bg-white hover:border-blue-300',
                                'flex items-start gap-3 rounded-lg border px-3 py-2 transition-colors'
                              ]"
                            >
                              <div class="flex flex-col">
                                <span class="text-sm font-medium text-gray-900">{{ option.label }}</span>
                                <span class="text-xs text-gray-500">{{ option.description }}</span>
                              </div>
                            </div>
                          </label>
                        </div>
                      </div>
                      <div><label class="block text-sm font-medium text-gray-700 mb-2">생성</label><button @click="createRoute" :disabled="!isAdmin || routingUpdateLoading || !isValidNewRoute" class="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium">{{ routingUpdateLoading ? '추가 중...' : '경로 생성' }}</button></div>
                      <div><label class="block text-sm font-medium text-gray-700 mb-2">비율 수수료 (%)</label><input v-model="newRoute.feeRate" type="number" step="0.0001" min="0" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" /></div>
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">고정 수수료</label>
                        <div class="space-y-3">
                          <input v-model="newRoute.feeFixed" type="number" step="0.00000001" min="0" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
                          <div class="flex flex-wrap gap-2">
                            <label
                              v-for="option in feeCurrencyOptions"
                              :key="`new-fee-currency-${option.value}`"
                              class="cursor-pointer"
                            >
                              <input type="radio" class="sr-only" :value="option.value" v-model="newRoute.feeFixedCurrency" />
                              <span
                                :class="[
                                  newRoute.feeFixedCurrency === option.value
                                    ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                                    : 'bg-white text-gray-700 border-gray-300 hover:border-blue-300',
                                  'px-3 py-1 rounded-full border text-sm font-medium inline-flex items-center gap-1 transition-colors'
                                ]"
                              >
                                {{ option.label }}
                              </span>
                            </label>
                          </div>
                        </div>
                      </div>
                      <div class="md:col-span-2 lg:col-span-3">
                        <div class="bg-gray-50 border border-gray-200 rounded-lg p-3">
                          <label class="inline-flex items-center gap-2 text-sm text-gray-700">
                            <input type="checkbox" v-model="newRoute.isEvent" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                            이벤트 경로
                          </label>
                          <div v-if="newRoute.isEvent" class="mt-3 grid sm:grid-cols-2 gap-3">
                            <div>
                              <label class="block text-xs font-medium text-gray-600 mb-1">이벤트 제목</label>
                              <input v-model="newRoute.eventTitle" type="text" placeholder="예: 수수료 50% 할인" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
                            </div>
                            <div class="sm:col-span-2">
                              <label class="block text-xs font-medium text-gray-600 mb-1">이벤트 설명</label>
                              <textarea v-model="newRoute.eventDescription" rows="2" placeholder="이벤트 내용 및 조건을 입력하세요" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"></textarea>
                            </div>
                          </div>
                        </div>
                      </div>
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
                        <div class="mb-3 flex flex-wrap items-center gap-2">
                          <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            {{ getRouteTypeLabel(route.route_type) }}
                          </span>
                          <span :class="[route.is_enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800', 'inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium']">
                            <svg v-if="route.is_enabled" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                            <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                            <span>{{ route.is_enabled ? '활성' : '비활성' }}</span>
                          </span>
                        </div>

                        <!-- Edit form -->
                        <div v-if="isAdmin" class="space-y-3 text-sm">
                          <div>
                            <label class="block text-xs font-medium text-gray-600 mb-1">유형</label>
                            <select v-model="route.edit_route_type" class="w-full px-2 py-1 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none">
                              <option value="trading">거래 수수료</option>
                              <option value="withdrawal_lightning">라이트닝 출금</option>
                              <option value="withdrawal_onchain">온체인 출금</option>
                            </select>
                          </div>
                          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                            <div>
                              <label class="block text-xs font-medium text-gray-600 mb-1">비율 수수료(%)</label>
                              <input v-model.number="route.edit_fee_rate" type="number" step="0.0001" min="0" class="w-full px-2 py-1 border border-gray-300 rounded-md" />
                            </div>
                            <div>
                              <label class="block text-xs font-medium text-gray-600 mb-1">고정 수수료</label>
                              <div class="space-y-2">
                                <input v-model.number="route.edit_fee_fixed" type="number" step="0.00000001" min="0" class="w-full px-2 py-1 border border-gray-300 rounded-md" />
                                <div class="flex flex-wrap gap-1.5">
                                  <label
                                    v-for="option in feeCurrencyOptions"
                                    :key="`edit-fee-currency-${route.id}-${option.value}`"
                                    class="cursor-pointer"
                                  >
                                    <input type="radio" class="sr-only" :value="option.value" v-model="route.edit_fee_fixed_currency" />
                                    <span
                                      :class="[
                                        route.edit_fee_fixed_currency === option.value
                                          ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                                          : 'bg-white text-gray-700 border-gray-300 hover:border-blue-300',
                                        'px-2.5 py-0.5 rounded-full border text-xs font-medium inline-flex items-center gap-1 transition-colors'
                                      ]"
                                    >
                                      {{ option.label }}
                                    </span>
                                  </label>
                                </div>
                              </div>
                            </div>
                          </div>
                          <div class="bg-gray-50 border border-gray-200 rounded-md p-3">
                            <div class="flex items-center justify-between">
                              <span class="text-xs font-medium text-gray-700">이벤트</span>
                              <label class="inline-flex items-center gap-2 text-xs text-gray-700">
                                <input type="checkbox" v-model="route.edit_is_event" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                                이벤트 경로
                              </label>
                            </div>
                            <div v-if="route.edit_is_event" class="mt-2 grid md:grid-cols-2 gap-2">
                              <div>
                                <label class="block text-[11px] font-medium text-gray-600 mb-1">제목</label>
                                <input v-model="route.edit_event_title" type="text" placeholder="예: 라이트닝 50% 할인" class="w-full px-2 py-1 border border-gray-300 rounded-md text-sm" />
                              </div>
                              <div class="md:col-span-2">
                                <label class="block text-[11px] font-medium text-gray-600 mb-1">설명</label>
                                <textarea v-model="route.edit_event_description" rows="2" placeholder="이벤트 세부 정보를 입력하세요" class="w-full px-2 py-1 border border-gray-300 rounded-md text-sm"></textarea>
                              </div>
                            </div>
                          </div>
                          <div class="flex justify-end">
                            <button @click="updateExistingRoute(route)" :disabled="routingUpdateLoading" class="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50">{{ routingUpdateLoading ? '저장 중...' : '저장' }}</button>
                          </div>
                        </div>

                        <!-- Read-only fee display for non-admin -->
                        <div v-else class="space-y-2 text-sm">
                          <div v-if="route.fee_rate !== null" class="flex justify-between"><span class="text-gray-600">비율 수수료:</span><span class="font-medium text-blue-600">{{ route.fee_rate }}%</span></div>
                          <div v-if="route.fee_fixed !== null" class="flex justify-between">
                            <span class="text-gray-600">고정 수수료:</span>
                            <span class="font-medium text-orange-600">
                              {{ formatFixedAmount(route.fee_fixed, route.fee_fixed_currency) }} {{ normalizeFeeCurrency(route.fee_fixed_currency) }}
                            </span>
                          </div>
                          <div v-if="!route.fee_rate && !route.fee_fixed" class="flex justify-between"><span class="text-gray-600">수수료:</span><span class="font-medium text-green-600">무료</span></div>
                        </div>

                        <div v-if="route.description" class="flex justify-between border-t pt-2 mt-2 text-sm"><span class="text-gray-600">설명:</span><span class="font-medium text-gray-800 text-right max-w-xs truncate">{{ route.description }}</span></div>
                        <div v-if="route.is_event" class="mt-2 border border-amber-200 bg-amber-50 rounded-lg p-3 text-xs text-amber-900">
                          <div class="flex items-center gap-2 font-semibold text-amber-800 mb-1">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {{ route.event_title || '이벤트 진행중' }}
                          </div>
                          <p class="whitespace-pre-line">{{ route.event_description || '이벤트 상세정보가 없습니다.' }}</p>
                        </div>
                      </div>
                    </div>
                    <div v-if="routingUpdateSuccess" class="p-3 bg-green-50 border border-green-200 rounded-lg mt-4"><div class="flex items-center"><svg class="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" /></svg><p class="text-green-700">라우팅 설정이 성공적으로 업데이트되었습니다!</p></div></div>
                    <div v-if="routingUpdateError" class="p-3 bg-red-50 border border-red-200 rounded-lg mt-2"><div class="flex items-center"><svg class="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" /></svg><p class="text-red-700">{{ routingUpdateError }}</p></div></div>
                  </div>
                </div>
                <!-- Final combined paths -->
                <div v-else>
                    <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between mb-4">
                    <h3 class="text-lg font-semibold text-gray-900">
                      최종 경로(조합)
                      <span class="text-sm text-gray-500">({{ sortedOptimalPaths.length }}개)</span>
                    </h3>
                    <div class="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:justify-end">
                      <div class="flex flex-col sm:flex-row sm:items-center sm:gap-2 w-full sm:w-auto">
                        <label class="text-sm text-gray-700">송금 금액</label>
                        <div class="flex items-center gap-2 w-full sm:w-auto">
                          <input
                            v-model.number="sendAmountInput"
                            type="number"
                            min="0"
                            step="1"
                            placeholder="예: 100"
                            class="w-full sm:w-24 md:w-28 px-2 py-1 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                          />
                          <select
                            v-model="sendUnit"
                            class="w-full sm:w-auto px-2 py-1 border border-gray-300 rounded bg-white text-sm"
                          >
                            <option value="1">원</option>
                            <option value="10000">만원</option>
                            <option value="100000000">억원</option>
                          </select>
                        </div>
                      </div>
                      <div class="flex flex-col sm:flex-row sm:items-center sm:gap-3 text-sm text-gray-700">
                        <label class="inline-flex items-center gap-2">
                          <input type="checkbox" v-model="optimalFilterExcludeLightning" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                          라이트닝 경로 제외
                        </label>
                        <label class="inline-flex items-center gap-2">
                          <input type="checkbox" v-model="optimalFilterExcludeKycWithdrawal" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                          KYC 출금 제외
                        </label>
                      </div>
                      <div class="flex items-center justify-between sm:justify-start gap-2 text-sm w-full sm:w-auto">
                        <span class="text-gray-700">BTC 가격(KRW, 업비트 기준)</span>
                        <span class="font-semibold text-gray-900">{{ btcPriceKrw ? formatKRW(btcPriceKrw) : '불러오는 중...' }}</span>
                      </div>
                      <div class="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
                        <button
                          @click="fetchBtcPriceKrw(true)"
                          class="w-full sm:w-auto px-2 py-2 text-xs sm:text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded"
                        >
                          가격 새로고침
                        </button>
                        <button
                          @click="loadOptimalPaths"
                          :disabled="optimalLoading"
                          class="w-full sm:w-auto px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                        >
                          {{ optimalLoading ? '계산 중...' : '다시 계산' }}
                        </button>
                      </div>
                    </div>
                  </div>
                  <div v-if="optimalError" class="p-3 bg-red-50 border border-red-200 rounded text-red-700 mb-3">{{ optimalError }}</div>
                  <div v-if="sortedOptimalPaths.length === 0 && !optimalLoading" class="text-gray-500 text-sm">경로가 없습니다. 상단에서 경로를 추가하거나 필터를 조정한 뒤 다시 계산하세요.</div>
                  <div class="space-y-4" v-else>
                    <div
                      v-for="(path, idx) in sortedOptimalPaths"
                      :key="path.path_signature || idx"
                      class="border border-gray-200 rounded p-4"
                    >
                    <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between mb-2">
                      <div class="font-medium text-gray-900">경로 #{{ idx + 1 }}</div>
                      <div class="text-sm text-gray-600">
                        <template v-for="pathFees in [computePathFees(path.routes)]" :key="`optimal-fees-${idx}`">
                          총 비율 수수료: <span class="font-semibold">{{ pathFees.rate.toFixed(4) }}%</span>
                          • 총 고정 수수료: <span class="font-semibold">{{ formatFixedFeeSummary(pathFees.fixedByCurrency) }}</span>
                          <template v-if="computeFixedFeeKRW(pathFees.fixedByCurrency)">
                            (≈ {{ formatKRW(computeFixedFeeKRW(pathFees.fixedByCurrency)) }})
                          </template>
                        </template>
                        <template v-if="sendAmountKRW > 0">
                          • 총 예상 수수료: <span class="font-semibold text-blue-700">{{ formatKRW(computeTotalFeeKRW(path)) }}</span>
                        </template>
                      </div>
                    </div>
                    <div class="flex flex-wrap items-center gap-1 text-sm">
                      <template v-for="(r, i) in path.routes" :key="i">
                        <span class="px-2 py-1 bg-blue-50 text-blue-800 rounded">{{ r.source.display_name }}</span>
                        <svg class="w-4 h-4 mx-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                        <span v-if="i === path.routes.length - 1" class="px-2 py-1 bg-green-50 text-green-800 rounded">{{ r.destination.display_name }}</span>
                      </template>
                    </div>
                    <div class="mt-2 grid grid-cols-1 gap-2 text-xs text-gray-600">
                      <div v-for="(r, i) in path.routes" :key="'d'+i" class="flex justify-between bg-gray-50 px-2 py-1 rounded">
                        <span>{{ r.source.display_name }} → {{ r.destination.display_name }} ({{ getRouteTypeLabel(r.route_type) }})</span>
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
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Mining Tab Content -->
        <div v-if="activeTab === 'mining'">
          <div class="bg-white rounded-lg shadow-md p-6 max-w-xl">
            <h3 class="text-lg font-semibold text-gray-900 mb-2">채굴 데이터 초기화</h3>
            <p class="text-sm text-gray-600 mb-4">모든 블록 데이터를 삭제합니다. 관리자만 실행할 수 있습니다.</p>
            <div class="space-y-3">
              <input v-model="adminResetPassword" type="password" placeholder="관리자 비밀번호 입력"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-gray-900" />
              <div class="flex gap-2">
                <button @click="confirmAdminReset" :disabled="!isAdmin || adminResetLoading"
                        class="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50">
                  {{ adminResetLoading ? '초기화 중...' : '초기화' }}
                </button>
                <span v-if="!isAdmin" class="text-sm text-gray-500 self-center">관리자 모드가 아닙니다</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Settings Tab Content -->
        <div v-if="activeTab === 'sidebar'">
          <div class="bg-white rounded-lg shadow-md p-6 max-w-xl">
            <h3 class="text-lg font-semibold text-gray-900 mb-2">사이드바 메뉴 설정</h3>
            <p class="text-sm text-gray-600 mb-4">사용자에게 보여질 사이드바 메뉴를 설정합니다.</p>

            <div v-if="sidebarConfigLoading" class="text-center py-8 text-gray-500">
              로딩 중...
            </div>

            <div v-else class="space-y-4">
              <!-- Mining Toggle -->
              <div class="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div>
                  <h4 class="font-medium text-gray-900">비트코인 채굴</h4>
                  <p class="text-sm text-gray-500">채굴 페이지 메뉴 표시</p>
                </div>
                <button
                  @click="toggleSidebarItem('show_mining')"
                  :class="[
                    sidebarConfig.show_mining
                      ? 'bg-blue-600'
                      : 'bg-gray-300',
                    'relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
                  ]"
                  :disabled="!isAdmin"
                >
                  <span
                    :class="[
                      sidebarConfig.show_mining ? 'translate-x-6' : 'translate-x-1',
                      'inline-block h-4 w-4 transform rounded-full bg-white transition-transform'
                    ]"
                  />
                </button>
              </div>

              <!-- UTXO Toggle -->
              <div class="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div>
                  <h4 class="font-medium text-gray-900">UTXO</h4>
                  <p class="text-sm text-gray-500">UTXO 페이지 메뉴 표시</p>
                </div>
                <button
                  @click="toggleSidebarItem('show_utxo')"
                  :class="[
                    sidebarConfig.show_utxo
                      ? 'bg-blue-600'
                      : 'bg-gray-300',
                    'relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
                  ]"
                  :disabled="!isAdmin"
                >
                  <span
                    :class="[
                      sidebarConfig.show_utxo ? 'translate-x-6' : 'translate-x-1',
                      'inline-block h-4 w-4 transform rounded-full bg-white transition-transform'
                    ]"
                  />
                </button>
              </div>

              <!-- Wallet Toggle -->
              <div class="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div>
                  <h4 class="font-medium text-gray-900">지갑</h4>
                  <p class="text-sm text-gray-500">지갑 페이지 메뉴 표시</p>
                </div>
                <button
                  @click="toggleSidebarItem('show_wallet')"
                  :class="[
                    sidebarConfig.show_wallet
                      ? 'bg-blue-600'
                      : 'bg-gray-300',
                    'relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
                  ]"
                  :disabled="!isAdmin"
                >
                  <span
                    :class="[
                      sidebarConfig.show_wallet ? 'translate-x-6' : 'translate-x-1',
                      'inline-block h-4 w-4 transform rounded-full bg-white transition-transform'
                    ]"
                  />
                </button>
              </div>

              <!-- Fee Calculator Toggle -->
              <div class="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div>
                  <h4 class="font-medium text-gray-900">수수료 계산</h4>
                  <p class="text-sm text-gray-500">수수료 계산 페이지 메뉴 표시</p>
                </div>
                <button
                  @click="toggleSidebarItem('show_fee')"
                  :class="[
                    sidebarConfig.show_fee
                      ? 'bg-blue-600'
                      : 'bg-gray-300',
                    'relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
                  ]"
                  :disabled="!isAdmin"
                >
                  <span
                    :class="[
                      sidebarConfig.show_fee ? 'translate-x-6' : 'translate-x-1',
                      'inline-block h-4 w-4 transform rounded-full bg-white transition-transform'
                    ]"
                  />
                </button>
              </div>
            </div>
          </div>

          <!-- Wallet Page Settings Section -->
          <div class="bg-white rounded-lg shadow-md p-6 max-w-xl mt-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-2">비밀번호 설정</h3>
            <p class="text-sm text-gray-600 mb-4">페이지 접근 관련 비밀번호를 관리합니다.</p>

            <div class="space-y-4">
              <!-- Wallet Page Card -->
              <div class="p-4 border border-gray-200 rounded-lg">
                <div class="flex items-center justify-between mb-3">
                  <h4 class="font-medium text-gray-900">지갑 페이지</h4>
                </div>
                <div class="space-y-3">
                  <div class="text-sm text-gray-600">
                    현재 비밀번호: <span class="font-mono text-gray-800">{{ (currentWalletPassword && currentWalletPassword.length) ? currentWalletPassword : '설정되지 않음' }}</span>
                  </div>
                  <div class="flex flex-col sm:flex-row gap-2">
                    <input
                      v-model="walletPasswordInput"
                      type="password"
                      class="flex-1 px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-gray-300 focus:border-gray-500 outline-none"
                      placeholder="새 비밀번호 (빈칸 입력 시 해제)"
                    />
                    <button
                      @click="saveWalletPassword"
                      :disabled="savingWalletPassword || !isAdmin"
                      class="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {{ savingWalletPassword ? '저장 중...' : '저장' }}
                    </button>
                  </div>
                  <div v-if="!isAdmin" class="text-xs text-yellow-700 bg-yellow-50 border border-yellow-200 rounded p-2">
                    관리자 권한이 아닙니다. 설정은 비활성화됩니다.
                  </div>
                  <div v-if="walletPasswordMessage" class="text-sm" :class="walletPasswordMessage.includes('성공') ? 'text-green-700' : 'text-red-600'">
                    {{ walletPasswordMessage }}
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

      <!-- Mnemonic Display Modal -->
      <div v-if="showMnemonicModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2 md:p-4" @click="showMnemonicModal = false">
        <div class="bg-white rounded-lg p-4 md:p-6 max-w-lg w-full max-h-[90vh] md:max-h-[80vh] overflow-y-auto" @click.stop>
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-lg md:text-xl font-semibold text-gray-900">자세히 보기</h2>
            <button @click="showMnemonicModal = false" class="text-gray-400 hover:text-gray-600">
              <svg class="w-5 h-5 md:w-6 md:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>

          <!-- Mnemonic Words Section -->
          <div class="mb-4 md:mb-6">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-base md:text-lg font-medium text-gray-900">시드 문구</h3>
              <div class="flex items-center gap-1 md:gap-2">
                <button @click="toggleMnemonicQr" class="p-1.5 md:p-2 rounded text-gray-700 hover:text-gray-900" title="QR 코드 토글">
                  <svg class="w-4 h-4 md:w-5 md:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"></path>
                  </svg>
                  <span class="sr-only">QR 코드</span>
                </button>
                <button @click="copyMnemonicToClipboard" class="p-1.5 md:p-2 rounded text-gray-700 hover:text-gray-900" title="시드 문구 복사">
                  <svg class="w-4 h-4 md:w-5 md:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <rect x="9" y="7" width="11" height="13" rx="2" ry="2"></rect>
                    <rect x="4" y="4" width="11" height="13" rx="2" ry="2"></rect>
                  </svg>
                  <span class="sr-only">시드 문구 복사</span>
                </button>
              </div>
            </div>

            <!-- Mnemonic QR Code -->
            <div v-if="showMnemonicQr" class="text-center mb-4">
              <div ref="mnemonicQrContainer" class="flex justify-center">
                <!-- QR code will be inserted here -->
              </div>
            </div>

            <div class="bg-gray-50 p-3 md:p-4 rounded-lg">
              <div class="grid grid-cols-2 sm:grid-cols-3 gap-1.5 md:gap-2 mb-4">
                <div v-for="(word, index) in currentDisplayMnemonic.split(' ')" :key="index"
                     class="flex items-center space-x-1 md:space-x-2 p-1.5 md:p-2 bg-white rounded border">
                  <span class="text-xs text-gray-500 font-medium w-3 md:w-4">{{ index + 1 }}</span>
                  <span class="text-xs md:text-sm font-mono">{{ word }}</span>
                </div>
              </div>

              <!-- Full text display -->
              <div class="border-t pt-3 md:pt-4">
                <p class="text-xs md:text-sm text-gray-700 font-mono break-all">{{ currentDisplayMnemonic }}</p>
              </div>
            </div>
          </div>

          <!-- zpub Section -->
          <div class="mb-6">
            <div class="flex items-center justify-between mb-2">
              <h3 class="text-lg font-medium text-gray-900">zpub</h3>
              <div class="flex items-center gap-2">
                <button @click="toggleZpubQr" class="p-2 rounded text-gray-700 hover:text-gray-900" :disabled="!modalZpub" title="QR 코드 토글">
                  <svg class="w-5 h-5" :class="{ 'opacity-50': !modalZpub }" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"></path>
                  </svg>
                  <span class="sr-only">QR 코드</span>
                </button>
                <button @click="copyZpubInModal" class="p-2 rounded text-gray-700 hover:text-gray-900" title="zpub 복사">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <rect x="9" y="7" width="11" height="13" rx="2" ry="2"></rect>
                    <rect x="4" y="4" width="11" height="13" rx="2" ry="2"></rect>
                  </svg>
                  <span class="sr-only">zpub 복사</span>
                </button>
              </div>
            </div>

            <!-- Zpub QR Code -->
            <div v-if="showZpubQr" class="text-center mb-4">
              <div ref="zpubQrContainer" class="flex justify-center">
                <!-- QR code will be inserted here -->
              </div>
            </div>

            <div class="bg-gray-50 p-4 rounded-lg">
              <p class="text-sm text-gray-700 font-mono break-all whitespace-normal">{{ modalZpub || '—' }}</p>
            </div>
          </div>

          <!-- Master Fingerprint Section -->
          <div class="mb-6">
            <div class="flex items-center justify-between mb-2">
              <h3 class="text-lg font-medium text-gray-900">마스터 핑거프린트 (MFP)</h3>
              <button @click="copyMfpToClipboard" class="p-2 rounded text-gray-700 hover:text-gray-900" :disabled="!modalMasterFingerprint" title="MFP 복사">
                <svg class="w-5 h-5" :class="{ 'opacity-50': !modalMasterFingerprint }" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <rect x="9" y="7" width="11" height="13" rx="2" ry="2"></rect>
                  <rect x="4" y="4" width="11" height="13" rx="2" ry="2"></rect>
                </svg>
                <span class="sr-only">MFP 복사</span>
              </button>
            </div>
            <div class="bg-gray-50 p-4 rounded-lg">
              <p class="text-sm text-gray-700 font-mono">{{ modalMasterFingerprint || '—' }}</p>
            </div>
          </div>

          <!-- Addresses Section -->
          <div class="mb-6">
            <div class="flex items-center justify-between mb-2">
              <h3 class="text-lg font-medium text-gray-900">주소</h3>
              <button @click="refreshAddressesInModal" class="p-2 rounded text-gray-700 hover:text-gray-900" title="주소 새로고침">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span class="sr-only">주소 새로고침</span>
              </button>
            </div>
            <div class="bg-gray-50 p-2 rounded-lg">
              <div v-if="modalAddresses.length === 0" class="text-sm text-gray-500 px-2 py-3">표시할 주소가 없습니다</div>
              <div v-else class="space-y-1">
                <div v-for="(addr, idx) in modalAddresses.slice(0, 10)" :key="idx" class="flex items-center justify-between bg-white rounded border px-2 py-1">
                  <span class="text-sm font-mono text-gray-800 break-all pr-2">{{ addr }}</span>
                  <button @click="copyAddressString(addr)" class="p-2 rounded text-gray-700 hover:text-gray-900" title="주소 복사">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <rect x="9" y="7" width="11" height="13" rx="2" ry="2"></rect>
                      <rect x="4" y="4" width="11" height="13" rx="2" ry="2"></rect>
                    </svg>
                    <span class="sr-only">주소 복사</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="flex flex-wrap items-center justify-end gap-2">
            <button @click="showMnemonicModal = false"
                    class="px-3 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 text-sm">
              닫기
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import * as bip39 from 'bip39'
import {
  apiRequestMnemonic,
  apiGenerateMnemonic,
  apiSaveMnemonic,
  apiGetAdminMnemonics,
  apiValidateMnemonic,
  apiDeleteMnemonic,
  apiGetMnemonicZpub,
  apiGetMnemonicAddress,
  apiGetOnchainBalanceById,
  apiSetMnemonicBalance,
  apiUnassignMnemonic,
  apiSetWalletPassword,
  apiGetWalletPassword,
  apiGetServiceNodes,
  apiUpdateServiceNode,
  apiGetRoutes,
  apiCreateRoute,
  apiDeleteRoute,
  apiGetOptimalPaths,
  apiGetRoutingSnapshotInfo,
  apiSaveRoutingSnapshot,
  apiResetRoutingFromSnapshot,
  apiGetSidebarConfig,
  apiUpdateSidebarConfig,
  apiGetKingstoneAdminWallets,
  apiAdminDeleteKingstoneWallet
} from '../api'
import { useNotification } from '../composables/useNotification'
import { copyToClipboard } from '../composables/useClipboard'
import { generateQRCode } from '../composables/useQRCode'
import { formatBtc, formatDate, formatKrw } from '../utils/formatters'
import { validateMnemonic, parseMnemonicWords } from '../utils/validation'
import { getUpbitBtcPriceKrw } from '../utils/btcPriceProvider'
import { getBtcPriceUsdt } from '../utils/btcUsdtPriceProvider'

// Composables
const { successMessage, errorMessage, showSuccess, showError } = useNotification()

// State
const loading = ref(false)
const activeTab = ref('mnemonics')
const activeRoutingTab = ref('nodes')

// Admin mining reset state
const adminResetPassword = ref('')
const adminResetLoading = ref(false)

// Sidebar config state
const sidebarConfig = ref({
  show_mining: true,
  show_utxo: true,
  show_wallet: true,
  show_fee: true
})
const sidebarConfigLoading = ref(false)

// Mnemonic management state
const manualPoolMnemonicText = ref('')
const adminMnemonicWords = ref(Array(12).fill(''))

// Kingstone wallet admin state
const kingstoneWallets = ref([])
const kingstoneWalletsLoading = ref(false)
const kingstoneWalletsError = ref('')
const kingstoneWalletDeleting = ref({})

// BIP39 autocomplete state
const bip39Wordlist = bip39.wordlists.english
const autocompleteIndex = ref(-1)
const autocompleteSuggestions = ref([])
const autocompleteSelectedIndex = ref(0)
const manualPoolError = ref('')
const adminMnemonics = ref([])
const adminMnemonicValidity = ref(null)
const adminMnemonicWordCount = ref(0)
const adminMnemonicChecking = ref(false)
const adminMnemonicUnknown = ref([])
const adminMnemonicErrorCode = ref('')
const balancesLoading = ref(false)
// Wallet password state
const walletPasswordInput = ref('')
const savingWalletPassword = ref(false)
const walletPasswordMessage = ref('')
const currentWalletPassword = ref('')

// Modal state for mnemonic display
const showMnemonicModal = ref(false)
const currentDisplayMnemonic = ref('')
const currentDisplayId = ref(null)
const modalZpub = ref('')
const modalMasterFingerprint = ref('')
const modalAddress = ref('')
const modalAddresses = ref([])
const modalAddressStartIndex = ref(0)
const mnemonicQrContainer = ref(null)
const zpubQrContainer = ref(null)
const showMnemonicQr = ref(false)
const showZpubQr = ref(false)

// (fee management removed)

// Load current wallet password on mount
const loadCurrentWalletPassword = async () => {
  try {
    const res = await apiGetWalletPassword()
    if (res.success) currentWalletPassword.value = res.password || ''
  } catch (_) {}
}

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
  feeFixedCurrency: 'BTC',
  description: '',
  isEvent: false,
  eventTitle: '',
  eventDescription: ''
})
const routeTypeOptions = [
  {
    value: 'trading',
    label: '거래 수수료',
    description: '거래소 내부·간 전환',
  },
  {
    value: 'withdrawal_lightning',
    label: '라이트닝 출금',
    description: '라이트닝 네트워크 출금',
  },
  {
    value: 'withdrawal_onchain',
    label: '온체인 출금',
    description: '블록체인 전송',
  }
]
const feeCurrencyOptions = [
  { value: 'BTC', label: 'BTC' },
  { value: 'USDT', label: 'USDT' },
]
const routeTypeOptionMap = routeTypeOptions.reduce((acc, option) => {
  acc[option.value] = option
  return acc
}, {})
const nodeTypeOptions = [
  { value: 'exchange', label: '거래소' },
  { value: 'service', label: '서비스' },
  { value: 'wallet', label: '지갑' },
  { value: 'user', label: '사용자' }
]
const validNodeTypeValues = new Set(nodeTypeOptions.map(opt => opt.value))
const inferNodeTypeFromService = (service = '') => {
  if (!service) return 'service'
  if (service === 'user') return 'user'
  if (service === 'personal_wallet') return 'wallet'
  if (/^(upbit|bithumb|binance|okx)/.test(service)) return 'exchange'
  return 'service'
}
const normalizeNodeTypeValue = (value, service = '') => {
  if (value && validNodeTypeValues.has(value)) return value
  return inferNodeTypeFromService(service)
}
const withDefaultNodeType = (node) => {
  if (!node || typeof node !== 'object') return node
  return {
    ...node,
    node_type: normalizeNodeTypeValue(node.node_type, node.service)
  }
}

const getEmptyServiceNodeForm = () => ({
  service: '',
  display_name: '',
  node_type: 'service',
  is_kyc: false,
  is_custodial: true,
  is_enabled: true,
  description: '',
  website_url: ''
})
const newServiceNode = ref(getEmptyServiceNodeForm())
const resetNewServiceNode = () => {
  newServiceNode.value = getEmptyServiceNodeForm()
}

// Final path (optimal) state
const optimalPaths = ref([])
const optimalLoading = ref(false)
const optimalError = ref('')
const btcPriceKrw = ref(0) // KRW per 1 BTC
const btcPriceUsdt = ref(0) // USDT per 1 BTC
const usdtPriceKrw = computed(() => {
  const btcKrw = btcPriceKrw.value
  const btcUsdt = btcPriceUsdt.value
  if (!btcKrw || !btcUsdt) return 0
  if (!Number.isFinite(btcUsdt) || btcUsdt === 0) return 0
  return btcKrw / btcUsdt
})
// Snapshot state
const snapshotInfo = ref({ has_snapshot: false, updated_at: '', counts: { nodes: 0, routes: 0 } })
const snapshotLoading = ref(false)
const snapshotError = ref('')
// User-entered remittance amount (KRW)
const sendAmountInput = ref('')
const sendUnit = ref('10000') // 기본 만원 단위

// Route filters
const routeFilterSources = ref([]) // array<number>
const routeFilterDestinations = ref([]) // array<number>
const optimalFilterExcludeLightning = ref(false)
const optimalFilterExcludeKycWithdrawal = ref(false)

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

// Computed
const isAdmin = computed(() => {
  const nickname = localStorage.getItem('nickname')
  const adminStatus = localStorage.getItem('isAdmin')
  return nickname === 'admin' && adminStatus === 'true'
})

const availableMnemonicsCount = computed(() => {
  return adminMnemonics.value.filter(m => !m.is_assigned).length
})

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
  if ((serviceNodes.value || []).some(n => n.service === code)) return '이미 존재하는 서비스 코드입니다'
  const displayName = (newServiceNode.value.display_name || '').trim()
  if (!displayName) return '표시명을 입력하세요'
  return ''
})
const canCreateServiceNode = computed(() => !newServiceNodeError.value)

const getAdminUsername = () => {
  const nickname = localStorage.getItem('nickname')
  const adminStatus = localStorage.getItem('isAdmin')
  return nickname === 'admin' && adminStatus === 'true' ? 'admin' : ''
}

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

// Alias for backward compatibility
const showSuccessMessage = showSuccess
const showErrorMessage = showError

// On-chain helpers (per mnemonic)
const fetchOnchain = async (mnemonic) => {
  const index = adminMnemonics.value.findIndex(m => m.id === mnemonic.id)
  if (index === -1) return

  try {
    // Set loading state and clear previous errors
    adminMnemonics.value[index]._loading_balance = true
    adminMnemonics.value[index]._balance_error = null
    adminMnemonics.value[index]._balance_error_detail = null

    const res = await apiGetOnchainBalanceById(mnemonic.id, { count: 20, bothChains: true })
    if (res.success) {
      // 자동 반영: 온체인 잔액을 풀 잔액에 바로 반영
      const total = res.total_sats || 0

      // Update the array item directly for Vue 3 reactivity
      adminMnemonics.value[index].balance_sats = total
      adminMnemonics.value[index]._onchain_total = total

      // 서버에도 즉시 업데이트(관리자일 때만)
      const adminUser = getAdminUsername()
      if (adminUser) {
        try {
          await apiSetMnemonicBalance(adminUser, mnemonic.id, total)
        } catch (err) {
          console.error('Failed to save balance to server:', err)
        }
      }
    } else {
      // Set error state on the mnemonic object based on error type
      const errorMsg = res.error || '온체인 조회 실패'
      let errorType = 'API 오류'

      if (res.error_type === 'rate_limit') {
        errorType = 'API 제한'
      } else if (res.error_type === 'timeout') {
        errorType = '시간 초과'
      } else if (res.error_type === 'service_unavailable') {
        errorType = '서비스 불가'
      } else if (res.error_type === 'network') {
        errorType = '네트워크 오류'
      }

      adminMnemonics.value[index]._balance_error = errorType
      adminMnemonics.value[index]._balance_error_detail = errorMsg
      showErrorMessage(errorMsg)
    }
  } catch (err) {
    // Unexpected errors that weren't caught by API layer
    console.error('Unexpected error fetching onchain balance:', err)

    adminMnemonics.value[index]._balance_error = '예기치 않은 오류'
    adminMnemonics.value[index]._balance_error_detail = err.message || '잔액 조회 중 예기치 않은 오류가 발생했습니다'
    showErrorMessage('잔액 조회 중 예기치 않은 오류가 발생했습니다')
  } finally {
    adminMnemonics.value[index]._loading_balance = false
  }
}

// applyOnchainToPool는 더 이상 필요하지 않으나, 참조 제거로 미사용 처리됨

const copyZpub = async (mnemonic) => {
  try {
    const res = await apiGetMnemonicZpub(getAdminUsername(), mnemonic.id, 0)
    if (res.success && res.zpub) {
      mnemonic._zpub = res.zpub
      try {
        await navigator.clipboard.writeText(res.zpub)
        showSuccessMessage('zpub 이 복사되었습니다')
      } catch (_) {
        showSuccessMessage('zpub 생성 완료 (클립보드 권한 없음)')
      }
    } else {
      showErrorMessage(res.error || 'zpub 조회 실패')
    }
  } catch (_) {
    showErrorMessage('요청 실패')
  }
}

const copyReceiveAddress = async (mnemonic) => {
  try {
    const res = await apiGetMnemonicAddress(getAdminUsername(), mnemonic.id, { index: 0, account: 0, change: 0 })
    if (res.success && res.address) {
      mnemonic._address = res.address
      try {
        await navigator.clipboard.writeText(res.address)
        showSuccessMessage('주소가 복사되었습니다')
      } catch (_) {
        showSuccessMessage('주소 생성 완료 (클립보드 권한 없음)')
      }
    } else {
      showErrorMessage(res.error || '주소 생성 실패')
    }
  } catch (_) {
    showErrorMessage('요청 실패')
  }
}

const unassignMnemonic = async (mnemonic) => {
  try {
    const res = await apiUnassignMnemonic(getAdminUsername(), mnemonic.id)
    if (res.success) {
      mnemonic.is_assigned = false
      mnemonic.assigned_to = ''
      showSuccessMessage('할당이 해제되었습니다')
    } else {
      showErrorMessage(res.error || '할당 해제 실패')
    }
  } catch (_) {
    showErrorMessage('네트워크 오류')
  }
}

const deleteMnemonic = async (mnemonic) => {
  if (!confirm('이 니모닉을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) return
  try {
    const res = await apiDeleteMnemonic(getAdminUsername(), mnemonic.id)
    if (res.success) {
      adminMnemonics.value = adminMnemonics.value.filter(m => m.id !== mnemonic.id)
      showSuccessMessage('니모닉이 삭제되었습니다')
    } else {
      showErrorMessage(res.error || '삭제 실패')
    }
  } catch (_) {
    showErrorMessage('요청 실패')
  }
}

const copyPoolMnemonic = async (mnemonic) => {
  try {
    if (!mnemonic?.mnemonic) { showErrorMessage('니모닉이 비어 있습니다'); return }
    await navigator.clipboard.writeText(mnemonic.mnemonic)
    showSuccessMessage('니모닉이 클립보드에 복사되었습니다')
  } catch (_) {
    // Fallback: create a temporary textarea to copy
    try {
      const ta = document.createElement('textarea')
      ta.value = mnemonic.mnemonic
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
      showSuccessMessage('니모닉이 클립보드에 복사되었습니다')
    } catch (_) {
      showErrorMessage('복사 실패')
    }
  }
}

// Helper functions for route creation interface
const getNodeDisplayName = (nodeId) => {
  if (!nodeId) return ''
  const node = serviceNodes.value.find(n => n.id === nodeId)
  return node ? node.display_name : ''
}

const getRouteTypeLabel = (routeType) => routeTypeOptionMap[routeType]?.label || routeType
const supportedFeeCurrencies = new Set(feeCurrencyOptions.map(opt => opt.value))
const normalizeFeeCurrency = (currency = 'BTC') => {
  const upper = (currency || 'BTC').toString().toUpperCase()
  return supportedFeeCurrencies.has(upper) ? upper : 'BTC'
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

// Compute aggregate fee for a path
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
  try { return Number(n).toLocaleString('ko-KR') + '원' } catch { return n + '원' }
}

const selectedSource = computed(() => serviceNodes.value.find(n => n.id === newRoute.value.sourceId) || null)
const disallowedDestForUser = new Set(['binance','binance_usdt','binance_btc','okx','okx_usdt','okx_btc'])
const filteredDestNodes = computed(() => {
  let nodes = serviceNodes.value
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
    feeFixedCurrency: 'BTC',
    description: '',
    isEvent: false,
    eventTitle: '',
    eventDescription: ''
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
// BIP39 autocomplete functions
const handleWordInput = (index, event) => {
  const input = event.target.value.toLowerCase().trim()

  if (input.length === 0) {
    autocompleteIndex.value = -1
    autocompleteSuggestions.value = []
    return
  }

  // Filter words that start with the input
  const suggestions = bip39Wordlist.filter(word => word.startsWith(input))

  if (suggestions.length > 0) {
    autocompleteIndex.value = index
    autocompleteSuggestions.value = suggestions.slice(0, 8) // Limit to 8 suggestions
    autocompleteSelectedIndex.value = 0
  } else {
    autocompleteIndex.value = -1
    autocompleteSuggestions.value = []
  }

  updateAdminManualMnemonic()
}

const selectSuggestion = (index, word) => {
  adminMnemonicWords.value[index] = word
  autocompleteIndex.value = -1
  autocompleteSuggestions.value = []
  autocompleteSelectedIndex.value = 0
  updateAdminManualMnemonic()

  // Focus next input
  nextTick(() => {
    const nextIndex = index + 1
    if (nextIndex < 12) {
      const nextInput = document.getElementById(`admin-word-${nextIndex + 1}`)
      if (nextInput) nextInput.focus()
    }
  })
}

const handleKeyDown = (index, event) => {
  if (autocompleteIndex.value !== index || autocompleteSuggestions.value.length === 0) {
    return
  }

  switch (event.key) {
    case 'ArrowDown':
      event.preventDefault()
      autocompleteSelectedIndex.value = Math.min(
        autocompleteSelectedIndex.value + 1,
        autocompleteSuggestions.value.length - 1
      )
      break
    case 'ArrowUp':
      event.preventDefault()
      autocompleteSelectedIndex.value = Math.max(autocompleteSelectedIndex.value - 1, 0)
      break
    case 'Enter':
      event.preventDefault()
      selectSuggestion(index, autocompleteSuggestions.value[autocompleteSelectedIndex.value])
      break
    case 'Escape':
      event.preventDefault()
      autocompleteIndex.value = -1
      autocompleteSuggestions.value = []
      break
    case 'Tab':
      if (autocompleteSuggestions.value.length > 0) {
        event.preventDefault()
        selectSuggestion(index, autocompleteSuggestions.value[autocompleteSelectedIndex.value])
      }
      break
  }
}

const closeAutocomplete = () => {
  autocompleteIndex.value = -1
  autocompleteSuggestions.value = []
  autocompleteSelectedIndex.value = 0
}

const handleBlur = () => {
  setTimeout(() => closeAutocomplete(), 200)
}

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

  // If multiple words are pasted, fill from index 0
  if (words.length > 1) {
    for (let i = 0; i < 12; i++) {
      adminMnemonicWords.value[i] = words[i] || ''
    }
  } else {
    // If single word is pasted, put it at the current field
    if (words.length === 1) {
      adminMnemonicWords.value[startIndex] = words[0]
    }
  }

  updateAdminManualMnemonic()
}

// Removed addMnemonicPool (auto pool create)

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

      // Clear input fields immediately
      clearAdminManualMnemonic()

      // Reload the full list
      await loadData()

      // Auto-load balance for the newly added mnemonic
      const newMnemonic = adminMnemonics.value.find(m => m.id === response.id)
      if (newMnemonic) {
        try {
          // Set loading state immediately for UI feedback
          newMnemonic._loading_balance = true

          await fetchOnchain(newMnemonic)

          showSuccess('잔액 조회 완료')
        } catch (error) {
          console.error(`Failed to load balance for new manual mnemonic ${newMnemonic.id}:`, error)
          showError('잔액 조회 실패')
        }
      } else {
        console.warn('새로 추가된 니모닉을 찾을 수 없습니다. ID:', response.id)
      }
    } else {
      manualPoolError.value = response.error || '니모닉 저장에 실패했습니다'
    }
  } catch (error) {
    manualPoolError.value = '네트워크 오류가 발생했습니다'
  } finally {
    loading.value = false
  }
}

// Auto-generate a mnemonic and fill the manual inputs
const generateAndFillAdminMnemonic = async () => {
  try {
    const response = await apiGenerateMnemonic()
    if (response.success && response.mnemonic) {
      const words = (response.mnemonic || '').trim().split(/\s+/)
      // Fill 12 inputs
      for (let i = 0; i < 12; i++) {
        adminMnemonicWords.value[i] = words[i] || ''
      }
      manualPoolMnemonicText.value = words.slice(0, 12).join(' ')
      // Reset validation state
      adminMnemonicValidity.value = null
      adminMnemonicWordCount.value = 0
      adminMnemonicUnknown.value = []
      adminMnemonicErrorCode.value = ''
      manualPoolError.value = ''
    } else {
      showErrorMessage(response.error || '니모닉 생성에 실패했습니다')
    }
  } catch (e) {
    showErrorMessage('네트워크 오류가 발생했습니다')
  }
}

const clearAdminManualMnemonic = () => {
  manualPoolMnemonicText.value = ''
  adminMnemonicWords.value = Array(12).fill('')
  adminMnemonicValidity.value = null
  adminMnemonicWordCount.value = 0
  adminMnemonicUnknown.value = []
  adminMnemonicErrorCode.value = ''
  manualPoolError.value = ''
}

const checkAdminMnemonic = async () => {
  const text = (manualPoolMnemonicText.value || adminMnemonicWords.value.join(' ')).trim()
  if (!text) { adminMnemonicValidity.value = null; adminMnemonicWordCount.value = 0; showErrorMessage('니모닉을 입력하세요'); return }
  adminMnemonicChecking.value = true
  try {
  const res = await apiValidateMnemonic(text)
  if (res.success) {
    adminMnemonicValidity.value = !!res.valid
    adminMnemonicWordCount.value = res.word_count || 0
    adminMnemonicErrorCode.value = res.error || ''
    if (!res.valid) {
      let msg = '유효하지 않은 니모닉입니다'
      if (res.error === 'invalid_word_count') msg = '단어 개수가 올바르지 않습니다 (12/15/18/21/24)'
      else if (res.error === 'checksum_failed') msg = '체크섬이 일치하지 않습니다'
      const unknown = (res.unknown_words || [])
      if (unknown.length) {
        msg += `: [${unknown.join(', ')}]`
      }
      adminMnemonicUnknown.value = unknown
      manualPoolError.value = msg
      showErrorMessage(msg)
    } else {
      adminMnemonicUnknown.value = []
      adminMnemonicErrorCode.value = ''
      manualPoolError.value = ''
      showSuccessMessage('유효성 검사에 문제가 없습니다')
      }
  } else {
    adminMnemonicUnknown.value = res.unknown_words || []
    const msg = adminMnemonicUnknown.value.length ? `유효하지 않은 단어: [${adminMnemonicUnknown.value.join(', ')}]` : (res.error || '검증 실패')
    manualPoolError.value = msg
    showErrorMessage(msg)
  }
  } finally {
    adminMnemonicChecking.value = false
  }
}

const showMnemonicInAdmin = async (m) => {
  // m is the mnemonic object from the list
  currentDisplayMnemonic.value = m.mnemonic
  currentDisplayId.value = m.id
  modalZpub.value = ''
  modalMasterFingerprint.value = ''
  modalAddress.value = ''
  modalAddressStartIndex.value = 0
  modalAddresses.value = []
  showMnemonicQr.value = false
  showZpubQr.value = false
  showMnemonicModal.value = true
  // Preload zpub and first 10 addresses
  try {
    const res = await apiGetMnemonicZpub(getAdminUsername(), currentDisplayId.value, 0)
    if (res.success && res.zpub) {
      modalZpub.value = res.zpub
      modalMasterFingerprint.value = res.master_fingerprint || ''
    }
  } catch (_) {}
  try { await loadAddressesInModal() } catch (_) {}
}

const toggleMnemonicQr = async () => {
  showMnemonicQr.value = !showMnemonicQr.value
  if (showMnemonicQr.value) {
    await nextTick()
    if (mnemonicQrContainer.value) {
      await generateQRCode(mnemonicQrContainer.value, currentDisplayMnemonic.value)
    }
  }
}

const toggleZpubQr = async () => {
  if (!modalZpub.value) return
  showZpubQr.value = !showZpubQr.value
  if (showZpubQr.value) {
    await nextTick()
    if (zpubQrContainer.value) {
      await generateQRCode(zpubQrContainer.value, modalZpub.value)
    }
  }
}

const copyMnemonicToClipboard = async () => {
  await copyToClipboard(
    currentDisplayMnemonic.value,
    () => showSuccess('니모닉이 클립보드에 복사되었습니다'),
    showError
  )
}

const copyZpubInModal = async () => {
  if (modalZpub.value) {
    await copyToClipboard(modalZpub.value, () => showSuccess('zpub이 복사되었습니다'), showError)
    return
  }

  if (!currentDisplayId.value) {
    showError('잘못된 상태')
    return
  }

  try {
    const res = await apiGetMnemonicZpub(getAdminUsername(), currentDisplayId.value, 0)
    if (res.success && res.zpub) {
      modalZpub.value = res.zpub
      modalMasterFingerprint.value = res.master_fingerprint || ''
      await copyToClipboard(res.zpub, () => showSuccess('zpub이 복사되었습니다'), showError)
    } else {
      showError(res.error || 'zpub 조회 실패')
    }
  } catch {
    showError('요청 실패')
  }
}

const copyMfpToClipboard = async () => {
  await copyToClipboard(
    modalMasterFingerprint.value,
    () => showSuccess('MFP가 클립보드에 복사되었습니다'),
    showError
  )
}

const loadAddressesInModal = async () => {
  const id = currentDisplayId.value
  if (!id) return
  try {
    const username = getAdminUsername()
    const start = Number(modalAddressStartIndex.value || 0)
    const reqs = Array.from({ length: 10 }, (_, i) => apiGetMnemonicAddress(username, id, { index: start + i, account: 0, change: 0 }))
    const results = await Promise.allSettled(reqs)
    const addrs = []
    for (const r of results) {
      if (r.status === 'fulfilled' && r.value?.success && r.value.address) addrs.push(r.value.address)
    }
    modalAddresses.value = addrs
  } catch (_) { /* ignore */ }
}

const refreshAddressesInModal = async () => {
  modalAddressStartIndex.value = Number(modalAddressStartIndex.value || 0) + 10
  await loadAddressesInModal()
}

const copyAddressString = async (addr) => {
  try {
    await navigator.clipboard.writeText(addr)
    showSuccessMessage('주소가 복사되었습니다')
  } catch (_) {
    showErrorMessage('클립보드 복사 실패')
  }
}

const copyAddressInModal = async () => {
  try {
    if (!currentDisplayId.value) { showErrorMessage('잘못된 상태'); return }
    const res = await apiGetMnemonicAddress(getAdminUsername(), currentDisplayId.value, { index: 0, account: 0, change: 0 })
    if (res.success && res.address) {
      modalAddress.value = res.address
      try { await navigator.clipboard.writeText(res.address); showSuccessMessage('주소가 복사되었습니다') }
      catch (_) { showSuccessMessage('주소 생성 완료 (클립보드 권한 없음)') }
    } else {
      showErrorMessage(res.error || '주소 생성 실패')
    }
  } catch (_) { showErrorMessage('요청 실패') }
}

// Wallet password setters
const saveWalletPassword = async () => {
  walletPasswordMessage.value = ''
  savingWalletPassword.value = true
  try {
    const passwordToSet = walletPasswordInput.value || ''
    const res = await apiSetWalletPassword(passwordToSet)
    if (res.success) {
      walletPasswordMessage.value = res.wallet_password_set ? '비밀번호 설정 성공' : '비밀번호 해제 성공'
      currentWalletPassword.value = passwordToSet
      walletPasswordInput.value = ''
    } else {
      walletPasswordMessage.value = res.error || '설정 실패'
    }
  } catch (_) {
    walletPasswordMessage.value = '요청 실패'
  } finally {
    savingWalletPassword.value = false
  }
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
      serviceNodes.value = Array.isArray(response.nodes) ? response.nodes.map(withDefaultNodeType) : []
    } else {
      routingUpdateError.value = response.error || '서비스 노드 데이터 로드에 실패했습니다'
    }
  } catch (error) {
    routingUpdateError.value = '네트워크 오류'
  }
}

const createServiceNode = async () => {
  if (!isAdmin.value) {
    showErrorMessage('관리자만 서비스 노드를 추가할 수 있습니다')
    return
  }
  if (!canCreateServiceNode.value) {
    if (isNewServiceNodeDirty.value) {
      showErrorMessage(newServiceNodeError.value || '입력값을 확인하세요')
    }
    return
  }

  routingUpdateLoading.value = true
  routingUpdateSuccess.value = false
  routingUpdateError.value = ''

  try {
    const username = getCurrentUsername()
    const response = await apiUpdateServiceNode(
      username,
      normalizedNewServiceCode.value,
      (newServiceNode.value.display_name || '').trim(),
      normalizeNodeTypeValue(newServiceNode.value.node_type, normalizedNewServiceCode.value),
      Boolean(newServiceNode.value.is_kyc),
      Boolean(newServiceNode.value.is_custodial),
      Boolean(newServiceNode.value.is_enabled),
      newServiceNode.value.description,
      newServiceNode.value.website_url || ''
    )

    if (response.success) {
      routingUpdateSuccess.value = true
      await loadServiceNodes()
      resetNewServiceNode()
      setTimeout(() => {
        routingUpdateSuccess.value = false
      }, 3000)
    } else {
      routingUpdateError.value = response.error || '서비스 노드 생성에 실패했습니다'
    }
  } catch (error) {
    routingUpdateError.value = '네트워크 오류'
  } finally {
    routingUpdateLoading.value = false
  }
}

const loadRoutes = async () => {
  try {
    const username = getCurrentUsername()
    const response = await apiGetRoutes(username)
    if (response.success) {
      routes.value = (response.routes || []).map(r => {
        const normalizedCurrency = normalizeFeeCurrency(r.fee_fixed_currency)
        return {
          ...r,
          fee_fixed_currency: normalizedCurrency,
          edit_route_type: r.route_type,
          edit_fee_rate: r.fee_rate,
          edit_fee_fixed: r.fee_fixed,
          edit_fee_fixed_currency: normalizedCurrency,
          edit_is_event: r.is_event,
          edit_event_title: r.event_title,
          edit_event_description: r.event_description,
        }
      })
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
      normalizeNodeTypeValue(node.node_type, node.service),
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
        serviceNodes.value[index] = withDefaultNodeType(response.node)
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
    const selectedCurrency = (newRoute.value.feeFixedCurrency || 'BTC').toUpperCase()
    const response = await apiCreateRoute(
      username,
      parseInt(newRoute.value.sourceId),
      parseInt(newRoute.value.destinationId),
      newRoute.value.routeType,
      newRoute.value.feeRate ? parseFloat(newRoute.value.feeRate) : null,
      newRoute.value.feeFixed ? parseFloat(newRoute.value.feeFixed) : null,
      selectedCurrency,
      true, // is_enabled
      newRoute.value.description,
      Boolean(newRoute.value.isEvent),
      newRoute.value.eventTitle || '',
      newRoute.value.eventDescription || ''
    )

    if (response.success) {
      routingUpdateSuccess.value = true

      // Add the new route to the list
      const normalizedCurrency = normalizeFeeCurrency(response.route.fee_fixed_currency)
      routes.value.push({
        ...response.route,
        fee_fixed_currency: normalizedCurrency,
        edit_route_type: response.route.route_type,
        edit_fee_rate: response.route.fee_rate,
        edit_fee_fixed: response.route.fee_fixed,
        edit_fee_fixed_currency: normalizedCurrency,
        edit_is_event: response.route.is_event,
        edit_event_title: response.route.event_title,
        edit_event_description: response.route.event_description,
      })

      // Reset form
      newRoute.value = {
        sourceId: '',
        destinationId: '',
        routeType: '',
        feeRate: null,
        feeFixed: null,
        feeFixedCurrency: 'BTC',
        description: '',
        isEvent: false,
        eventTitle: '',
        eventDescription: ''
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
    const newFeeFixedCurrency = (route.edit_fee_fixed_currency || route.fee_fixed_currency || 'BTC').toUpperCase()

    // Create or update the (source, dest, newType)
    const resp = await apiCreateRoute(
      username,
      route.source.id,
      route.destination.id,
      newType,
      newFeeRate,
      newFeeFixed,
      newFeeFixedCurrency,
      route.is_enabled,
      route.description || '',
      Boolean(route.edit_is_event),
      route.edit_event_title || '',
      route.edit_event_description || ''
    )

    if (!resp.success) {
      routingUpdateError.value = resp.error || '경로 업데이트에 실패했습니다'
      return
    }

    const updated = resp.route
    const normalizedCurrency = normalizeFeeCurrency(updated.fee_fixed_currency)
    // If the type changed, delete the old one
    if (newType !== route.route_type) {
      await apiDeleteRoute(username, route.id)
      // Replace element in routes array
      routes.value = routes.value.map(r => r.id === route.id ? {
        ...updated,
        fee_fixed_currency: normalizedCurrency,
        edit_route_type: updated.route_type,
        edit_fee_rate: updated.fee_rate,
        edit_fee_fixed: updated.fee_fixed,
        edit_fee_fixed_currency: normalizedCurrency,
        edit_is_event: updated.is_event,
        edit_event_title: updated.event_title,
        edit_event_description: updated.event_description,
      } : r)
    } else {
      // Same key; just patch fields
      routes.value = routes.value.map(r => r.id === route.id ? {
        ...updated,
        fee_fixed_currency: normalizedCurrency,
        edit_route_type: updated.route_type,
        edit_fee_rate: updated.fee_rate,
        edit_fee_fixed: updated.fee_fixed,
        edit_fee_fixed_currency: normalizedCurrency,
        edit_is_event: updated.is_event,
        edit_event_title: updated.event_title,
        edit_event_description: updated.event_description,
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

// Fetch BTC price (KRW) via Upbit API with caching
const fetchBtcPriceKrw = async (force = false) => {
  try {
    const [priceKrw, priceUsdt] = await Promise.all([
      getUpbitBtcPriceKrw(force),
      getBtcPriceUsdt(force).catch(err => {
        console.error('Failed to fetch BTC price (USDT):', err)
        return btcPriceUsdt.value
      })
    ])
    btcPriceKrw.value = priceKrw
    if (priceUsdt) {
      btcPriceUsdt.value = priceUsdt
    }
  } catch (e) {
    console.error('Failed to fetch BTC price (KRW) from Upbit:', e)
  }
}

// Filters helpers
const clearRouteFilters = () => {
  routeFilterSources.value = []
  routeFilterDestinations.value = []
}

// Kingstone wallet helpers
const isKingstoneWalletDeleting = (walletId) => {
  return Boolean(kingstoneWalletDeleting.value[walletId])
}

const setKingstoneWalletDeleting = (walletId, flag) => {
  kingstoneWalletDeleting.value = {
    ...kingstoneWalletDeleting.value,
    [walletId]: flag
  }
}

const loadKingstoneWallets = async () => {
  if (!isAdmin.value) {
    kingstoneWallets.value = []
    kingstoneWalletsError.value = '관리자 권한이 필요합니다'
    return
  }

  kingstoneWalletsLoading.value = true
  kingstoneWalletsError.value = ''
  try {
    const res = await apiGetKingstoneAdminWallets('admin')
    if (res.success) {
      kingstoneWallets.value = (res.wallets || []).map((wallet) => ({
        ...wallet,
        pin: wallet.pin || '',
      }))
    } else {
      kingstoneWalletsError.value = res.error || '지갑 목록을 불러오지 못했습니다'
      kingstoneWallets.value = []
    }
  } catch (error) {
    console.error('Failed to load Kingstone wallets:', error)
    kingstoneWalletsError.value = '지갑 목록을 불러오지 못했습니다'
    kingstoneWallets.value = []
  } finally {
    kingstoneWalletsLoading.value = false
  }
}

const refreshKingstoneWallets = async () => {
  await loadKingstoneWallets()
}

const deleteKingstoneWallet = async (wallet) => {
  if (!isAdmin.value) return
  if (!wallet?.wallet_id) return
  if (!confirm('이 지갑을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) return

  const walletId = wallet.wallet_id
  setKingstoneWalletDeleting(walletId, true)
  try {
    const res = await apiAdminDeleteKingstoneWallet('admin', walletId)
    if (res.success) {
      kingstoneWallets.value = kingstoneWallets.value.filter(w => w.wallet_id !== walletId)
      showSuccessMessage('지갑이 삭제되었습니다')
    } else {
      showErrorMessage(res.error || '지갑 삭제에 실패했습니다')
    }
  } catch (error) {
    console.error('Failed to delete Kingstone wallet:', error)
    showErrorMessage('지갑 삭제 요청 중 오류가 발생했습니다')
  } finally {
    setKingstoneWalletDeleting(walletId, false)
  }
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
        if (res.success) {
          adminMnemonics.value = res.mnemonics
          // Note: Don't auto-load all balances here for better performance
          // Users can use the refresh-all button or individual refresh buttons
        }
      } catch (_) {}

      await loadKingstoneWallets()
    }
  } finally {
    loading.value = false
  }
}

// Load balances for all mnemonics in the pool
const loadAllMnemonicBalances = async () => {
  if (!adminMnemonics.value || adminMnemonics.value.length === 0) return

  balancesLoading.value = true
  try {
    // mark all as loading
    try { (adminMnemonics.value || []).forEach(m => m._loading_balance = true) } catch (_) {}
    // Load balances in parallel for better performance, but limit concurrent requests
    const batchSize = 5 // Limit to 5 concurrent requests to avoid overwhelming the server
    for (let i = 0; i < adminMnemonics.value.length; i += batchSize) {
      const batch = adminMnemonics.value.slice(i, i + batchSize)
      const balancePromises = batch.map(async (mnemonic) => {
        try {
          await fetchOnchain(mnemonic)
        } catch (error) {
          console.error(`Failed to load balance for mnemonic ${mnemonic.id}:`, error)
        }
      })
      await Promise.all(balancePromises)
    }
  } finally {
    balancesLoading.value = false
  }
}

// Load admin data on mount if admin
onMounted(async () => {
  console.log('AdminPage mounted, isAdmin:', isAdmin.value)
  await loadData()
  await loadSidebarConfig()
  await loadCurrentWalletPassword()
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

watch(() => activeTab.value, async (newTab, oldTab) => {
  if (newTab === 'mnemonics' && oldTab !== 'mnemonics' && isAdmin.value) {
    await loadKingstoneWallets()
  }
})

// Sidebar config functions
const loadSidebarConfig = async () => {
  sidebarConfigLoading.value = true
  try {
    const result = await apiGetSidebarConfig()
    if (result.success && result.config) {
      sidebarConfig.value = result.config
    }
  } catch (error) {
    console.error('Failed to load sidebar config:', error)
  } finally {
    sidebarConfigLoading.value = false
  }
}

const toggleSidebarItem = async (key) => {
  if (!isAdmin.value) return

  const updates = {
    [key]: !sidebarConfig.value[key]
  }

  try {
    const result = await apiUpdateSidebarConfig(getCurrentUsername(), updates)
    if (result.success && result.config) {
      sidebarConfig.value = result.config
      showSuccess('사이드바 설정이 업데이트되었습니다')
      // Trigger event to update App.vue sidebar
      window.dispatchEvent(new CustomEvent('sidebarConfigUpdated'))
    } else {
      showError(result.error || '설정 업데이트 실패')
    }
  } catch (error) {
    showError('설정 업데이트 중 오류 발생')
    console.error('Failed to update sidebar config:', error)
  }
}

// Admin: confirm chain reset
const confirmAdminReset = async () => {
  if (!isAdmin.value) { showErrorMessage('관리자만 가능합니다'); return }
  if (!adminResetPassword.value) { showErrorMessage('비밀번호를 입력하세요'); return }
  adminResetLoading.value = true
  try {
    const res = await fetch((import.meta.env.VITE_API_BASE || '') + '/api/init_reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ token: adminResetPassword.value })
    })
    let data = null
    try { data = await res.json() } catch (_) {}
    if (res.ok && data?.ok) {
      showSuccessMessage('초기화가 완료되었습니다')
    } else {
      showErrorMessage(data?.error || '초기화 실패')
    }
  } catch (_) {
    showErrorMessage('네트워크 오류')
  } finally {
    adminResetLoading.value = false
  }
}

// Computed helpers for final path fee calculation
const sendAmountKRW = computed(() => {
  const a = Number(sendAmountInput.value || 0)
  const u = Number(sendUnit.value || 1)
  if (!isFinite(a) || !isFinite(u)) return 0
  return a * u
})

const computeTotalFeeKRW = (path) => {
  if (!path || !Array.isArray(path.routes)) return 0
  const { rate, fixedByCurrency } = computePathFees(path.routes)
  const rateFee = (sendAmountKRW.value || 0) * (Number(rate) || 0) / 100
  const fixedFee = computeFixedFeeKRW(fixedByCurrency)
  // 소수점 버림 처리
  return Math.max(0, Math.floor(rateFee + fixedFee))
}

const filteredOptimalPaths = computed(() => {
  return (optimalPaths.value || []).filter(path => {
    if (!Array.isArray(path.routes)) return true
    return !path.routes.some(route => shouldExcludeRouteByOptimalFilters(route))
  })
})

const sortedOptimalPaths = computed(() => {
  const arr = [...filteredOptimalPaths.value]
  if ((sendAmountKRW.value || 0) > 0) {
    arr.sort((a, b) => computeTotalFeeKRW(a) - computeTotalFeeKRW(b))
  }
  return arr
})
</script>
