<template>
  <div class="space-y-8">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-8">
      <div class="space-y-4 md:space-y-6">
        <div class="bg-white rounded-lg shadow-md p-4 md:p-6 h-auto md:h-[700px] flex flex-col">
          <h3 class="text-base md:text-lg font-semibold text-gray-900 mb-4">니모닉 풀 관리</h3>
          <div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <div class="flex items-center justify-between mb-3">
              <h4 class="font-medium text-gray-800">개별 니모닉 추가</h4>
              <div class="flex items-center gap-1">
                <button @click="generateAndFillAdminMnemonic" class="p-2 rounded text-gray-700 hover:text-gray-900" title="자동 생성">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v12" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 12h12" />
                  </svg>
                  <span class="sr-only">자동 생성</span>
                </button>
                <button @click="clearAdminManualMnemonic" class="p-2 rounded text-gray-700 hover:text-gray-900" title="지우기">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V5a2 2 0 00-2-2H9a2 2 0 00-2 2v2m-3 0h14"
                    />
                  </svg>
                  <span class="sr-only">지우기</span>
                </button>
              </div>
            </div>
            <div class="space-y-3">
              <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
                <div v-for="i in 12" :key="i" class="relative">
                  <label :for="`admin-word-${i}`" class="block text-xs font-medium text-gray-600 mb-1">
                    {{ i }}
                  </label>
                  <input
                    :id="`admin-word-${i}`"
                    v-model="adminMnemonicWords[i - 1]"
                    @input="handleWordInput(i - 1, $event)"
                    @keydown="handleKeyDown(i - 1, $event)"
                    @paste="handleAdminPaste($event, i - 1)"
                    @blur="handleBlur"
                    type="text"
                    :placeholder="`단어 ${i}`"
                    autocomplete="off"
                    class="w-full px-2 py-2 text-xs sm:text-sm border border-gray-200 rounded focus:ring-2 focus:ring-gray-500 focus:border-gray-500 outline-none"
                    :class="{
                      'border-red-300':
                        manualPoolError ||
                        (adminMnemonicUnknown &&
                          adminMnemonicUnknown.length &&
                          adminMnemonicUnknown.includes((adminMnemonicWords[i - 1] || '').trim().toLowerCase()))
                    }"
                  />
                  <div
                    v-if="autocompleteIndex === i - 1 && autocompleteSuggestions.length > 0"
                    class="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-48 overflow-y-auto"
                  >
                    <div
                      v-for="(suggestion, idx) in autocompleteSuggestions"
                      :key="suggestion"
                      @click="selectSuggestion(i - 1, suggestion)"
                      class="px-3 py-2 cursor-pointer text-sm hover:bg-blue-50 transition-colors"
                      :class="{ 'bg-blue-100': idx === autocompleteSelectedIndex }"
                    >
                      {{ suggestion }}
                    </div>
                  </div>
                </div>
              </div>

              <div class="border-t border-gray-200 pt-3">
                <label class="block text-sm font-medium text-gray-700 mb-2">또는 한번에 입력:</label>
                <textarea
                  v-model="manualPoolMnemonicText"
                  @input="updateAdminFromTextarea"
                  placeholder="12/15/18/21/24개의 영어 단어를 공백으로 구분하여 입력"
                  class="w-full h-16 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-gray-500 outline-none resize-none"
                  :class="{ 'border-red-300': manualPoolError }"
                ></textarea>
                <div class="mt-2 space-y-2">
                  <button
                    @click="checkAdminMnemonic"
                    :disabled="adminMnemonicChecking"
                    class="w-full px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {{ adminMnemonicChecking ? '검사 중...' : '유효성 검사' }}
                  </button>
                  <div
                    v-if="adminMnemonicValidity !== null"
                    :class="adminMnemonicValidity ? 'text-green-700' : 'text-red-600'"
                    class="text-sm"
                  >
                    {{ adminMnemonicValidity ? '유효한 BIP39 니모닉' : '유효하지 않은 니모닉' }}
                    <span v-if="adminMnemonicWordCount"> ({{ adminMnemonicWordCount }}단어)</span>
                    <span
                      v-if="!adminMnemonicValidity && adminMnemonicUnknown && adminMnemonicUnknown.length"
                      class="ml-2 text-xs text-red-600"
                    >
                      [{{ adminMnemonicUnknown.join(', ') }}]
                    </span>
                    <span
                      v-if="
                        !adminMnemonicValidity &&
                        (!adminMnemonicUnknown || adminMnemonicUnknown.length === 0) &&
                        adminMnemonicErrorCode === 'checksum_failed'
                      "
                      class="ml-2 text-xs text-red-600"
                    >
                      (체크섬 불일치)
                    </span>
                  </div>
                </div>
              </div>

              <div v-if="manualPoolError" class="text-red-600 text-sm">
                {{ manualPoolError }}
              </div>

              <button
                @click="addManualMnemonicToPool"
                :disabled="loading || !isValidAdminMnemonicInput"
                class="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {{ loading ? '추가 중...' : '니모닉 풀 추가' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="space-y-6">
        <div class="bg-white rounded-lg shadow-md p-4 md:p-6 h-[700px] flex flex-col">
          <div class="flex items-center justify-between mb-1">
            <h3 class="text-base md:text-lg font-semibold text-gray-900">풀 상태</h3>
            <div class="flex items-center gap-2">
              <button
                @click="loadAllMnemonicBalances"
                :disabled="balancesLoading || adminMnemonics.length === 0"
                class="p-2 rounded text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                title="잔액 업데이트"
              >
                <template v-if="balancesLoading">
                  <div class="w-4 h-4 md:w-5 md:h-5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
                </template>
                <template v-else>
                  <svg class="w-4 h-4 md:w-5 md:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
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
              <div
                v-for="mnemonic in adminMnemonics"
                :key="mnemonic.id"
                class="flex flex-col sm:flex-row sm:items-start sm:justify-between p-2 md:p-3 bg-white rounded border gap-2 sm:gap-3"
              >
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 flex-wrap mb-1">
                    <span class="text-xs text-gray-500">ID {{ mnemonic.id }}</span>
                    <span
                      v-if="mnemonic.is_assigned"
                      class="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded"
                    >
                      {{ mnemonic.assigned_to || '미상' }}
                    </span>
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
                      <span class="text-xs text-red-500" :title="mnemonic._balance_error_detail"
                        >({{ mnemonic._balance_error }})</span
                      >
                    </span>
                    <span v-else class="flex flex-wrap items-center gap-1">
                      <span class="font-medium">{{ Number(mnemonic.balance_sats || 0).toLocaleString() }} sats</span>
                      <span class="text-gray-500 text-xs">({{ formatBtc(mnemonic.balance_sats) }})</span>
                    </span>
                  </div>
                </div>
                <div class="shrink-0 flex sm:flex-col items-center sm:items-end gap-1">
                  <div class="flex items-center gap-1">
                    <button
                      @click="fetchOnchain(mnemonic)"
                      :disabled="mnemonic._loading_balance"
                      class="p-1.5 md:p-2 rounded text-blue-600 hover:text-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      title="잔액 새로고침"
                    >
                      <svg v-if="mnemonic._loading_balance" class="w-4 h-4 md:w-5 md:h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                        />
                      </svg>
                      <svg v-else class="w-4 h-4 md:w-5 md:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                        />
                      </svg>
                    </button>
                    <button
                      v-if="mnemonic.is_assigned"
                      @click="unassignMnemonic(mnemonic)"
                      class="p-1.5 md:p-2 rounded text-amber-700 hover:text-amber-800"
                      title="할당 해제"
                    >
                      <svg class="w-4 h-4 md:w-5 md:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12h6m0 0l-3 3m3-3l-3-3M9 7a4 4 0 110 8 4 4 0 010-8z" />
                      </svg>
                    </button>
                    <button
                      @click="showMnemonicInAdmin(mnemonic)"
                      class="p-1.5 md:p-2 rounded text-gray-700 hover:text-gray-900"
                      title="보기"
                    >
                      <svg class="w-4 h-4 md:w-5 md:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M2.458 12C3.732 7.943 7.523 5 12 5c4.477 0 8.268 2.943 9.542 7-1.274 4.057-5.065 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                        />
                      </svg>
                    </button>
                    <button
                      @click="deleteMnemonic(mnemonic)"
                      class="p-1.5 md:p-2 rounded text-red-600 hover:text-red-700"
                      title="삭제"
                    >
                      <svg class="w-4 h-4 md:w-5 md:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m-3 0h14"
                        />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

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
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
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
      <div
        v-else-if="kingstoneWallets.length === 0"
        class="p-6 bg-gray-50 border border-dashed border-gray-200 rounded text-center text-sm text-gray-600"
      >
        등록된 지갑이 없습니다.
      </div>
      <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200 text-sm">
          <thead class="bg-gray-50 text-xs uppercase tracking-wide text-gray-500">
            <tr>
              <th class="px-4 py-3 text-left font-semibold">지갑 이름</th>
              <th class="px-4 py-3 text-left font-semibold">생성자</th>
              <th class="px-4 py-3 text-left font-semibold">생성일</th>
              <th class="px-4 py-3 text-left font-semibold">핀번호</th>
              <th class="px-4 py-3 text-right font-semibold">작업</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="wallet in kingstoneWallets" :key="wallet.wallet_id" class="hover:bg-gray-50 transition-colors">
              <td class="px-4 py-3 font-medium text-gray-900">{{ wallet.wallet_name }}</td>
              <td class="px-4 py-3 text-gray-700">{{ wallet.username }}</td>
              <td class="px-4 py-3 text-gray-600 whitespace-nowrap">{{ formatDate(wallet.created_at) }}</td>
              <td class="px-4 py-3 text-gray-900 font-mono">{{ wallet.pin || '미저장' }}</td>
              <td class="px-4 py-3 text-right">
                <button
                  @click="deleteKingstoneWallet(wallet)"
                  :disabled="!isAdmin || isKingstoneWalletDeleting(wallet.wallet_id)"
                  class="inline-flex items-center justify-center w-9 h-9 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="지갑 삭제"
                >
                  <svg v-if="!isKingstoneWalletDeleting(wallet.wallet_id)" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V5a2 2 0 00-2-2H9a2 2 0 00-2 2v2m-3 0h14"
                    />
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

    <div
      v-if="showMnemonicModal"
      class="fixed inset-0 bg-gray-900/70 z-50 flex items-center justify-center p-4"
      @click.self="closeMnemonicModal"
    >
      <div class="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between px-6 py-4 border-b">
          <div>
            <h3 class="text-xl font-semibold text-gray-900">니모닉 상세 보기</h3>
            <p class="text-sm text-gray-500 mt-1">ID {{ currentDisplayId }}</p>
          </div>
          <button class="p-2 rounded-full hover:bg-gray-100" @click="closeMnemonicModal">
            <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
          <div class="space-y-4">
            <div>
              <h4 class="text-lg font-semibold mb-2">니모닉 단어</h4>
              <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 font-mono text-sm leading-relaxed">
                {{ currentDisplayMnemonic }}
              </div>
            </div>
            <div class="flex flex-wrap gap-2">
              <button
                @click="copyMnemonicToClipboard"
                class="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 flex items-center gap-2"
              >
                복사
              </button>
              <button
                @click="toggleMnemonicQr"
                class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
              >
                QR 보기
              </button>
            </div>
            <div v-if="showMnemonicQr" ref="mnemonicQrContainer" class="w-48 h-48 bg-white rounded-lg shadow-inner"></div>
          </div>

          <div class="space-y-4">
            <div class="bg-gray-50 rounded-lg p-4 border border-gray-200 space-y-2">
              <div class="flex items-center justify-between">
                <div>
                  <h4 class="font-semibold text-gray-900">zpub</h4>
                  <p class="text-xs text-gray-500">마스터 지갑 공개키</p>
                </div>
                <div class="flex gap-2">
                  <button @click="copyZpubInModal" class="p-2 rounded text-gray-700 hover:text-gray-900" title="zpub 복사">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M8 7V5a2 2 0 012-2h6a2 2 0 012 2v6a2 2 0 01-2 2h-2m-4 4H6a2 2 0 01-2-2V9a2 2 0 012-2h2"
                      />
                    </svg>
                  </button>
                  <button @click="toggleZpubQr" class="p-2 rounded text-gray-700 hover:text-gray-900" title="QR 코드">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M3 7h4V3H3v4zm6 0h4V3H9v4zm6-4v4h4V3h-4zM3 13h4v-4H3v4zm6 0h4v-4H9v4zm6-4v4h4v-4h-4zM3 21h4v-4H3v4zm6 0h4v-4H9v4zm6-4v4h4v-4h-4z"
                      />
                    </svg>
                  </button>
                </div>
              </div>
              <div class="font-mono text-sm break-all text-gray-800">{{ modalZpub || '불러오는 중...' }}</div>
              <div v-if="showZpubQr" ref="zpubQrContainer" class="w-48 h-48 bg-white rounded-lg shadow-inner"></div>
              <div class="text-xs text-gray-500">Master Fingerprint: {{ modalMasterFingerprint || '-' }}</div>
            </div>

            <div class="bg-gray-50 rounded-lg p-4 border border-gray-200 space-y-3">
              <div class="flex items-center justify-between">
                <h4 class="font-semibold text-gray-900">주소 목록</h4>
                <button
                  @click="refreshAddressesInModal"
                  class="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100"
                >
                  다음 10개
                </button>
              </div>
              <div class="space-y-2 max-h-48 overflow-auto">
                <div v-for="(addr, idx) in modalAddresses" :key="idx" class="flex items-center justify-between gap-2">
                  <span class="font-mono text-xs text-gray-800 break-all">{{ addr }}</span>
                  <button
                    @click="copyAddressString(addr)"
                    class="p-2 text-gray-600 hover:text-gray-900 rounded"
                    title="복사"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M8 7V5a2 2 0 012-2h6a2 2 0 012 2v6a2 2 0 01-2 2h-2m-4 4H6a2 2 0 01-2-2V9a2 2 0 012-2h2"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="flex justify-end gap-2 px-6 pb-6 border-t">
          <button
            @click="copyAddressInModal"
            class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 text-sm"
          >
            첫 번째 주소 복사
          </button>
          <button @click="closeMnemonicModal" class="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 text-sm">
            닫기
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import * as bip39 from 'bip39'
import {
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
  apiGetKingstoneAdminWallets,
  apiAdminDeleteKingstoneWallet
} from '../../api'
import { copyToClipboard } from '../../composables/useClipboard'
import { generateQRCode } from '../../composables/useQRCode'
import { formatBtc, formatDate } from '../../utils/formatters'
import { validateMnemonic } from '../../utils/validation'
import { getAdminUsername, getCurrentUsername } from '../../utils/adminAuth'

const props = defineProps({
  isAdmin: { type: Boolean, default: false },
  showSuccess: { type: Function, required: true },
  showError: { type: Function, required: true }
})

const loading = ref(false)
const manualPoolMnemonicText = ref('')
const adminMnemonicWords = ref(Array(12).fill(''))
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
const kingstoneWallets = ref([])
const kingstoneWalletsLoading = ref(false)
const kingstoneWalletsError = ref('')
const kingstoneWalletDeleting = ref({})

const availableMnemonicsCount = computed(() => adminMnemonics.value.filter((m) => !m.is_assigned).length)

const isValidAdminMnemonicInput = computed(() => {
  const words = adminMnemonicWords.value.filter((w) => w.trim().length > 0)
  return words.length === 12 || manualPoolMnemonicText.value.trim().split(/\s+/).length === 12
})

const notifySuccess = (message) => props.showSuccess(message)
const notifyError = (message) => props.showError(message)

const loadAdminMnemonics = async () => {
  if (!props.isAdmin) return
  try {
    const username = getCurrentUsername()
    const res = await apiGetAdminMnemonics(username)
    if (res.success) {
      adminMnemonics.value = res.mnemonics || []
    }
  } catch (error) {
    console.error('Failed to load admin mnemonics:', error)
  }
}

const fetchOnchain = async (mnemonic) => {
  const index = adminMnemonics.value.findIndex((m) => m.id === mnemonic.id)
  if (index === -1) return

  try {
    adminMnemonics.value[index]._loading_balance = true
    adminMnemonics.value[index]._balance_error = null
    adminMnemonics.value[index]._balance_error_detail = null

    const res = await apiGetOnchainBalanceById(mnemonic.id, { count: 20, bothChains: true })
    if (res.success) {
      const total = res.total_sats || 0
      adminMnemonics.value[index].balance_sats = total
      adminMnemonics.value[index]._onchain_total = total

      const adminUser = getAdminUsername()
      if (adminUser) {
        try {
          await apiSetMnemonicBalance(adminUser, mnemonic.id, total)
        } catch (err) {
          console.error('Failed to save balance to server:', err)
        }
      }
    } else {
      const errorMsg = res.error || '온체인 조회 실패'
      let errorType = 'API 오류'

      if (res.error_type === 'rate_limit') errorType = 'API 제한'
      else if (res.error_type === 'timeout') errorType = '시간 초과'
      else if (res.error_type === 'service_unavailable') errorType = '서비스 불가'
      else if (res.error_type === 'network') errorType = '네트워크 오류'

      adminMnemonics.value[index]._balance_error = errorType
      adminMnemonics.value[index]._balance_error_detail = errorMsg
      notifyError(errorMsg)
    }
  } catch (err) {
    console.error('Unexpected error fetching onchain balance:', err)

    adminMnemonics.value[index]._balance_error = '예기치 않은 오류'
    adminMnemonics.value[index]._balance_error_detail =
      err.message || '잔액 조회 중 예기치 않은 오류가 발생했습니다'
    notifyError('잔액 조회 중 예기치 않은 오류가 발생했습니다')
  } finally {
    adminMnemonics.value[index]._loading_balance = false
  }
}

const unassignMnemonic = async (mnemonic) => {
  try {
    const res = await apiUnassignMnemonic(getAdminUsername(), mnemonic.id)
    if (res.success) {
      mnemonic.is_assigned = false
      mnemonic.assigned_to = ''
      notifySuccess('할당이 해제되었습니다')
    } else {
      notifyError(res.error || '할당 해제 실패')
    }
  } catch (_) {
    notifyError('네트워크 오류')
  }
}

const deleteMnemonic = async (mnemonic) => {
  if (!confirm('이 니모닉을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) return
  try {
    const res = await apiDeleteMnemonic(getAdminUsername(), mnemonic.id)
    if (res.success) {
      adminMnemonics.value = adminMnemonics.value.filter((m) => m.id !== mnemonic.id)
      notifySuccess('니모닉이 삭제되었습니다')
    } else {
      notifyError(res.error || '삭제 실패')
    }
  } catch (_) {
    notifyError('요청 실패')
  }
}

const addManualMnemonicToPool = async () => {
  manualPoolError.value = ''

  const finalMnemonic =
    manualPoolMnemonicText.value.trim() || adminMnemonicWords.value.join(' ').trim()
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
      notifySuccess('니모닉이 풀에 추가되었습니다')
      clearAdminManualMnemonic()
      await loadAdminMnemonics()
      const newMnemonic = adminMnemonics.value.find((m) => m.id === response.id)
      if (newMnemonic) {
        try {
          newMnemonic._loading_balance = true
          await fetchOnchain(newMnemonic)
          notifySuccess('잔액 조회 완료')
        } catch (err) {
          console.error(
            `Failed to load balance for new manual mnemonic ${newMnemonic.id}:`,
            err
          )
          notifyError('잔액 조회 실패')
        }
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

const generateAndFillAdminMnemonic = async () => {
  try {
    const response = await apiGenerateMnemonic()
    if (response.success && response.mnemonic) {
      const words = (response.mnemonic || '').trim().split(/\s+/)
      for (let i = 0; i < 12; i++) {
        adminMnemonicWords.value[i] = words[i] || ''
      }
      manualPoolMnemonicText.value = words.slice(0, 12).join(' ')
      adminMnemonicValidity.value = null
      adminMnemonicWordCount.value = 0
      adminMnemonicUnknown.value = []
      adminMnemonicErrorCode.value = ''
      manualPoolError.value = ''
    } else {
      notifyError(response.error || '니모닉 생성에 실패했습니다')
    }
  } catch (e) {
    notifyError('네트워크 오류가 발생했습니다')
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
  if (!text) {
    adminMnemonicValidity.value = null
    adminMnemonicWordCount.value = 0
    notifyError('니모닉을 입력하세요')
    return
  }
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
        const unknown = res.unknown_words || []
        if (unknown.length) {
          msg += `: [${unknown.join(', ')}]`
        }
        adminMnemonicUnknown.value = unknown
        manualPoolError.value = msg
        notifyError(msg)
      } else {
        adminMnemonicUnknown.value = []
        adminMnemonicErrorCode.value = ''
        manualPoolError.value = ''
        notifySuccess('유효성 검사에 문제가 없습니다')
      }
    } else {
      adminMnemonicUnknown.value = res.unknown_words || []
      const msg = adminMnemonicUnknown.value.length
        ? `유효하지 않은 단어: [${adminMnemonicUnknown.value.join(', ')}]`
        : res.error || '검증 실패'
      manualPoolError.value = msg
      notifyError(msg)
    }
  } finally {
    adminMnemonicChecking.value = false
  }
}

const handleWordInput = (index, event) => {
  const input = event.target.value.toLowerCase().trim()

  if (input.length === 0) {
    autocompleteIndex.value = -1
    autocompleteSuggestions.value = []
    return
  }

  const suggestions = bip39Wordlist.filter((word) => word.startsWith(input))

  if (suggestions.length > 0) {
    autocompleteIndex.value = index
    autocompleteSuggestions.value = suggestions.slice(0, 8)
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
  manualPoolMnemonicText.value = adminMnemonicWords.value.join(' ').trim()
}

const updateAdminFromTextarea = () => {
  const words = manualPoolMnemonicText.value.trim().split(/\s+/).filter((w) => w.length > 0)
  for (let i = 0; i < 12; i++) {
    adminMnemonicWords.value[i] = words[i] || ''
  }
}

const handleAdminPaste = (event, startIndex) => {
  event.preventDefault()
  const pastedText = (event.clipboardData || window.clipboardData).getData('text')
  const words = pastedText.trim().split(/\s+/).filter((w) => w.length > 0)

  if (words.length > 1) {
    for (let i = 0; i < 12; i++) {
      adminMnemonicWords.value[i] = words[i] || ''
    }
  } else if (words.length === 1) {
    adminMnemonicWords.value[startIndex] = words[0]
  }

  updateAdminManualMnemonic()
}

const showMnemonicInAdmin = async (mnemonic) => {
  currentDisplayMnemonic.value = mnemonic.mnemonic
  currentDisplayId.value = mnemonic.id
  modalZpub.value = ''
  modalMasterFingerprint.value = ''
  modalAddress.value = ''
  modalAddressStartIndex.value = 0
  modalAddresses.value = []
  showMnemonicQr.value = false
  showZpubQr.value = false
  showMnemonicModal.value = true
  try {
    const res = await apiGetMnemonicZpub(getAdminUsername(), currentDisplayId.value, 0)
    if (res.success && res.zpub) {
      modalZpub.value = res.zpub
      modalMasterFingerprint.value = res.master_fingerprint || ''
    }
  } catch (_) {}
  try {
    await loadAddressesInModal()
  } catch (_) {}
}

const closeMnemonicModal = () => {
  showMnemonicModal.value = false
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
    () => notifySuccess('니모닉이 클립보드에 복사되었습니다'),
    notifyError
  )
}

const copyZpubInModal = async () => {
  if (modalZpub.value) {
    await copyToClipboard(modalZpub.value, () => notifySuccess('zpub이 복사되었습니다'), notifyError)
    return
  }

  if (!currentDisplayId.value) {
    notifyError('잘못된 상태')
    return
  }

  try {
    const res = await apiGetMnemonicZpub(getAdminUsername(), currentDisplayId.value, 0)
    if (res.success && res.zpub) {
      modalZpub.value = res.zpub
      modalMasterFingerprint.value = res.master_fingerprint || ''
      await copyToClipboard(res.zpub, () => notifySuccess('zpub이 복사되었습니다'), notifyError)
    } else {
      notifyError(res.error || 'zpub 조회 실패')
    }
  } catch {
    notifyError('요청 실패')
  }
}

const copyMfpToClipboard = async () => {
  await copyToClipboard(
    modalMasterFingerprint.value,
    () => notifySuccess('MFP가 클립보드에 복사되었습니다'),
    notifyError
  )
}

const loadAddressesInModal = async () => {
  const id = currentDisplayId.value
  if (!id) return
  try {
    const username = getAdminUsername()
    const start = Number(modalAddressStartIndex.value || 0)
    const reqs = Array.from({ length: 10 }, (_, i) =>
      apiGetMnemonicAddress(username, id, { index: start + i, account: 0, change: 0 })
    )
    const results = await Promise.allSettled(reqs)
    const addrs = []
    for (const r of results) {
      if (r.status === 'fulfilled' && r.value?.success && r.value.address) addrs.push(r.value.address)
    }
    modalAddresses.value = addrs
  } catch (_) {}
}

const refreshAddressesInModal = async () => {
  modalAddressStartIndex.value = Number(modalAddressStartIndex.value || 0) + 10
  await loadAddressesInModal()
}

const copyAddressString = async (addr) => {
  try {
    await navigator.clipboard.writeText(addr)
    notifySuccess('주소가 복사되었습니다')
  } catch (_) {
    notifyError('클립보드 복사 실패')
  }
}

const copyAddressInModal = async () => {
  try {
    if (!currentDisplayId.value) {
      notifyError('잘못된 상태')
      return
    }
    const res = await apiGetMnemonicAddress(getAdminUsername(), currentDisplayId.value, {
      index: 0,
      account: 0,
      change: 0
    })
    if (res.success && res.address) {
      modalAddress.value = res.address
      try {
        await navigator.clipboard.writeText(res.address)
        notifySuccess('주소가 복사되었습니다')
      } catch (_) {
        notifySuccess('주소 생성 완료 (클립보드 권한 없음)')
      }
    } else {
      notifyError(res.error || '주소 생성 실패')
    }
  } catch (_) {
    notifyError('요청 실패')
  }
}

const loadAllMnemonicBalances = async () => {
  if (!adminMnemonics.value || adminMnemonics.value.length === 0) return

  balancesLoading.value = true
  try {
    adminMnemonics.value.forEach((m) => (m._loading_balance = true))
    const batchSize = 5
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

const loadKingstoneWallets = async () => {
  if (!props.isAdmin) {
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
        pin: wallet.pin || ''
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

const isKingstoneWalletDeleting = (walletId) => Boolean(kingstoneWalletDeleting.value[walletId])

const setKingstoneWalletDeleting = (walletId, flag) => {
  kingstoneWalletDeleting.value = {
    ...kingstoneWalletDeleting.value,
    [walletId]: flag
  }
}

const deleteKingstoneWallet = async (wallet) => {
  if (!props.isAdmin || !wallet?.wallet_id) return
  if (!confirm('이 지갑을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) return

  const walletId = wallet.wallet_id
  setKingstoneWalletDeleting(walletId, true)
  try {
    const res = await apiAdminDeleteKingstoneWallet('admin', walletId)
    if (res.success) {
      kingstoneWallets.value = kingstoneWallets.value.filter((w) => w.wallet_id !== walletId)
      notifySuccess('지갑이 삭제되었습니다')
    } else {
      notifyError(res.error || '지갑 삭제에 실패했습니다')
    }
  } catch (error) {
    console.error('Failed to delete Kingstone wallet:', error)
    notifyError('지갑 삭제 요청 중 오류가 발생했습니다')
  } finally {
    setKingstoneWalletDeleting(walletId, false)
  }
}

onMounted(async () => {
  if (props.isAdmin) {
    await loadAdminMnemonics()
    await loadKingstoneWallets()
  }
})

watch(
  () => props.isAdmin,
  async (value) => {
    if (value) {
      await loadAdminMnemonics()
      await loadKingstoneWallets()
    } else {
      adminMnemonics.value = []
      kingstoneWallets.value = []
    }
  }
)
</script>
