<template>
  <div class="space-y-6">
    <!-- Compact Status Bar -->
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-3 sm:p-4">
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-4 text-center">
        <div class="flex items-center justify-center gap-1 sm:gap-2">
          <div class="w-6 h-6 sm:w-8 sm:h-8 rounded-lg bg-orange-100 flex items-center justify-center">
            <svg class="w-3 h-3 sm:w-4 sm:h-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <div>
            <div class="font-bold text-slate-800 text-sm sm:text-base">{{ status.height }}</div>
            <div class="text-[10px] sm:text-xs text-slate-500">블록 높이</div>
          </div>
        </div>
        <div class="flex items-center justify-center gap-1 sm:gap-2">
          <div class="w-6 h-6 sm:w-8 sm:h-8 rounded-lg bg-blue-100 flex items-center justify-center">
            <svg class="w-3 h-3 sm:w-4 sm:h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
            </svg>
          </div>
          <div>
            <div class="font-bold text-slate-800 text-sm sm:text-base">≤ {{ status.difficulty }}</div>
            <div class="text-[10px] sm:text-xs text-slate-500">난이도</div>
          </div>
        </div>
        <div class="flex items-center justify-center gap-1 sm:gap-2">
          <CoinIcon />
          <div>
            <div class="font-bold text-slate-800 tabular-nums text-sm sm:text-base">{{ currentReward }}</div>
            <div class="text-[10px] sm:text-xs text-slate-500">블록 보상</div>
          </div>
        </div>
        <div class="flex items-center justify-center gap-1 sm:gap-2">
          <div class="w-6 h-6 sm:w-8 sm:h-8 rounded-lg bg-orange-100 flex items-center justify-center">
            <svg class="w-3 h-3 sm:w-4 sm:h-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
            </svg>
          </div>
          <div>
            <div class="font-bold text-slate-800 tabular-nums text-sm sm:text-base">{{ myReward }}</div>
            <div class="text-[10px] sm:text-xs text-slate-500">내 보상</div>
          </div>
        </div>
        <button 
          @click="showPeersModal = true"
          class="flex items-center justify-center gap-1 sm:gap-2 hover:bg-slate-50 rounded-lg p-1 sm:p-2 transition-colors"
        >
          <div class="w-6 h-6 sm:w-8 sm:h-8 rounded-lg bg-blue-100 flex items-center justify-center">
            <svg class="w-3 h-3 sm:w-4 sm:h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
            </svg>
          </div>
          <div>
            <div class="font-bold text-slate-800 text-sm sm:text-base">{{ totalPeerCount }}</div>
            <div class="text-[10px] sm:text-xs text-slate-500">접속자</div>
          </div>
        </button>
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6">
      <!-- Left Column - Mining Interface -->
      <div class="order-1">
        <!-- Mining Controls -->
        <div class="bg-white rounded-2xl shadow-lg border border-slate-200 p-4 sm:p-6 mb-4 sm:mb-6">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 sm:w-12 sm:h-12 bg-slate-800 rounded-xl flex items-center justify-center">
              <svg class="w-5 h-5 sm:w-6 sm:h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h3 class="text-lg sm:text-xl font-bold text-slate-800">채굴 시작</h3>
          </div>
          
          <label class="block mb-4">
            <span class="text-sm font-medium text-slate-700 mb-2 block">채굴자 닉네임</span>
            <input 
              v-model="miner" 
              class="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition-all" 
              placeholder="예: satoshi" 
              inputmode="text" 
            />
          </label>

          <div class="bg-orange-50 rounded-xl p-3 sm:p-4 mb-4 border border-orange-100">
            <div class="text-xs sm:text-sm text-orange-800 leading-relaxed">
              1~100,000 범위의 난수 중 현재 난이도 이하가 나오면 블록을 채굴할 수 있습니다.
              10블록마다 난이도는 절반으로 낮아집니다.
            </div>
          </div>

          <!-- Mining Animation Above Button -->
          <div class="bg-slate-50 border border-slate-200 rounded-xl p-4 sm:p-6 mb-4 flex items-center justify-center">
            <MiningAnim :state="miningState" />
          </div>

          <!-- Mining Button -->
          <button
            class="w-full bg-slate-800 hover:bg-slate-700 disabled:bg-slate-400 text-white rounded-xl px-4 sm:px-6 py-3 sm:py-4 font-semibold text-base sm:text-lg transition-all duration-200 disabled:cursor-not-allowed"
            :disabled="miningState === 'mining'"
            @click="tryMine"
          >
            <span v-if="miningState === 'mining'" class="flex items-center justify-center gap-2">
              <svg class="animate-spin w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="10" stroke-width="3" stroke-dasharray="31.416" stroke-dashoffset="31.416" class="animate-spin" style="animation: spin 1s linear infinite;" />
              </svg>
              채굴 중...
            </span>
            <span v-else>채굴 시도하기</span>
          </button>

          <div v-if="lastAttempt" class="text-center mb-4">
            <span class="text-sm text-slate-600">마지막 시도값:</span>
            <span class="font-mono text-lg font-bold text-slate-800 ml-2">{{ lastAttempt }}</span>
          </div>

          <div v-if="message" class="p-4 rounded-xl" :class="messageType === 'ok' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-orange-50 text-orange-700 border border-orange-200'">
            {{ message }}
          </div>
        </div>


      </div>

      <!-- Right Column - Block Controls -->
      <div class="order-2">
        <!-- Block Grid -->
        <div class="bg-white rounded-2xl shadow-lg border border-slate-200 p-4 sm:p-6 mb-4 sm:mb-6">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 sm:w-10 sm:h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                <svg class="w-4 h-4 sm:w-5 sm:h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.783 0-2.676-2.153-1.415-3.414l5-5A2 2 0 009 9.172V5L8 4z" />
                </svg>
              </div>
              <h3 class="text-base sm:text-lg font-bold text-slate-800">블록 체인</h3>
            </div>
            <button
              @click="showBlocksModal = true"
              class="px-3 sm:px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-all duration-200 text-sm sm:text-base"
            >
              최신 블록 보기
            </button>
          </div>
          <BlockGrid :blocks="blocks" :limit="60" />
        </div>
      </div>
    </div>

    <!-- Latest Blocks Modal -->
    <div v-if="showBlocksModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-2 sm:p-4">
      <div class="bg-white rounded-xl sm:rounded-2xl shadow-2xl max-w-4xl w-full max-h-[95vh] sm:max-h-[90vh] flex flex-col">
        <!-- Modal Header -->
        <div class="flex items-center justify-between p-4 sm:p-6 border-b border-slate-200">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 sm:w-10 sm:h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 sm:w-5 sm:h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 class="text-lg sm:text-xl font-bold text-slate-800">최신 블록</h3>
          </div>
          <button
            @click="showBlocksModal = false"
            class="p-2 hover:bg-slate-100 rounded-full transition-colors"
          >
            <svg class="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <!-- Modal Content -->
        <div class="flex-1 overflow-y-auto p-3 sm:p-6">
          <div v-if="broadcastMsg" class="mb-4 p-3 sm:p-4 rounded-xl border border-orange-200 bg-orange-50 text-orange-700 text-sm">
            {{ broadcastMsg }}
          </div>

          <TransitionGroup name="list" tag="div" class="space-y-3">
            <div
              v-for="b in blocks.slice(0, 20)"
              :key="b.height"
              class="p-4 rounded-xl border border-slate-100 bg-gradient-to-r from-slate-50 to-white hover:shadow-md transition-all duration-200"
              :class="{ 'block-highlight border-green-200 bg-green-50': highlighted.has(b.height) }"
            >
              <div class="flex items-center justify-between mb-3">
                <div class="flex items-center gap-2">
                  <div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span class="text-blue-600 text-sm font-bold">#</span>
                  </div>
                  <span class="font-bold text-lg text-slate-800">{{ b.height }}</span>
                </div>
                <div class="text-xs text-slate-500">{{ new Date(b.timestamp).toLocaleString() }}</div>
              </div>
              
              <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div class="bg-white rounded-lg p-3">
                  <div class="text-slate-500 text-xs mb-1">난이도</div>
                  <div class="font-bold text-slate-800 tabular-nums">{{ b.difficulty }}</div>
                </div>
                <div class="bg-white rounded-lg p-3">
                  <div class="text-slate-500 text-xs mb-1">Nonce</div>
                  <div class="font-bold text-slate-800 tabular-nums">{{ b.nonce }}</div>
                </div>
                <div class="bg-white rounded-lg p-3">
                  <div class="text-slate-500 text-xs mb-1">보상</div>
                  <div class="flex items-center gap-1 font-bold text-slate-800">
                    <CoinIcon /> 
                    <span class="tabular-nums">{{ b.reward || 0 }}</span>
                  </div>
                </div>
                <div class="bg-white rounded-lg p-3 md:col-span-1 col-span-2">
                  <div class="text-slate-500 text-xs mb-1">채굴자</div>
                  <div class="font-medium text-slate-800 truncate">{{ b.miner }}</div>
                </div>
              </div>
            </div>
          </TransitionGroup>
        </div>
      </div>
    </div>

    <!-- Connected Users Modal -->
    <div v-if="showPeersModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full max-h-[80vh] flex flex-col">
        <!-- Modal Header -->
        <div class="flex items-center justify-between p-6 border-b border-slate-200">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
              </svg>
            </div>
            <h3 class="text-xl font-bold text-slate-800">접속 중인 사용자</h3>
          </div>
          <button
            @click="showPeersModal = false"
            class="p-2 hover:bg-slate-100 rounded-full transition-colors"
          >
            <svg class="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <!-- Modal Content -->
        <div class="flex-1 overflow-y-auto p-6">
          <div v-if="peers.length === 0" class="text-center py-8 text-slate-500">
            현재 접속자가 없습니다.
          </div>
          <div v-else class="space-y-3">
            <div 
              v-for="(peer, index) in peers" 
              :key="peer || index" 
              class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 transition-colors"
            >
              <div class="w-3 h-3 rounded-full bg-green-500 animate-pulse flex-shrink-0"></div>
              <div class="flex-1 min-w-0">
                <div class="font-medium text-slate-800 truncate">
                  {{ peer || 'Unknown User' }}
                  <span v-if="peer === miner" class="text-xs text-green-600 ml-2 font-normal">(나)</span>
                </div>
                <div class="text-xs text-slate-500">온라인</div>
              </div>
              <div v-if="peer === miner" class="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                <svg class="w-3 h-3 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- Notification Overlay -->
    <div class="fixed top-4 right-4 z-50 space-y-2">
      <TransitionGroup name="notification" tag="div">
        <div
          v-for="notification in notifications"
          :key="notification.id"
          class="bg-white border border-green-200 rounded-lg shadow-lg p-4 max-w-sm"
        >
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <svg class="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <div class="font-medium text-slate-800">새 사용자 입장</div>
              <div class="text-sm text-slate-500 truncate">{{ notification.user }}님이 입장했습니다</div>
            </div>
            <button
              @click="removeNotification(notification.id)"
              class="text-slate-400 hover:text-slate-600 p-1"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, reactive, ref, computed } from 'vue'
import { fetchStatus, fetchBlocks, postMine, connectEvents, connectBlockStream, apiInitReset } from '../../api'
import MiningAnim from '../../components/MiningAnim.vue'
import BlockGrid from '../../components/BlockGrid.vue'
import CoinIcon from '../../components/CoinIcon.vue'

const status = reactive({ height: 0, difficulty: 10000, reward: 100 })
const blocks = ref([])
const lastAttempt = ref(null)
const message = ref('')
const messageType = ref('info') // 'ok' | 'info'
const miningState = ref('idle') // 'idle' | 'mining' | 'success' | 'fail'
let stopMining = false
const miner = ref('guest')
let es = null
let wsWrapper = null
const broadcastMsg = ref('')
const peers = ref([])
let pollTimer = null
const savedNick = localStorage.getItem('nickname') || ''
const highlighted = new Set()
const showBlocksModal = ref(false)
const showPeersModal = ref(false)
const previousPeerCount = ref(0)
const notifications = ref([])
const notificationId = ref(0)

function startPolling() {
  if (pollTimer) return
  pollTimer = setInterval(async () => {
    try {
      const s = await fetchStatus()
      const prev = status.height
      applyStatus(s)
      if (status.height !== prev) {
        const b = await fetchBlocks()
        applyBlocks(b.blocks)
      }
    } catch (_) {}
  }, 2000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// 보상 집계: 각 블록의 reward 합산
const rewardByMiner = computed(() => {
  const acc = new Map()
  for (const b of blocks.value) {
    const key = b.miner || 'guest'
    acc.set(key, (acc.get(key) || 0) + (b.reward || 0))
  }
  const list = Array.from(acc.entries()).map(([miner, amount]) => ({ miner, amount }))
  list.sort((a, b) => b.amount - a.amount || a.miner.localeCompare(b.miner))
  return list
})

const myReward = computed(() => {
  const f = rewardByMiner.value.find(i => i.miner === miner.value)
  return f ? f.amount : 0
})

// 현재 블록 보상: 서버 상태 값 사용
const currentReward = computed(() => status.reward ?? 0)

// 자신을 포함한 전체 접속자 수
const totalPeerCount = computed(() => {
  const peerCount = peers.value.length
  // 자신이 peers 목록에 없다면 +1 추가
  const includesSelf = peers.value.includes(miner.value)
  return includesSelf ? peerCount : peerCount + 1
})

function difficultyOk(val) {
  return val <= status.difficulty
}

function showUserJoinNotification(username) {
  const id = ++notificationId.value
  const notification = {
    id,
    user: username || '알 수 없는 사용자',
    timestamp: Date.now()
  }
  
  notifications.value.push(notification)
  
  // 5초 후 자동 제거
  setTimeout(() => {
    removeNotification(id)
  }, 5000)
}

function removeNotification(id) {
  const index = notifications.value.findIndex(n => n.id === id)
  if (index > -1) {
    notifications.value.splice(index, 1)
  }
}

function setBlocksSortedUnique(list) {
  const map = new Map()
  for (const b of list) {
    if (!map.has(b.height)) map.set(b.height, b)
  }
  // 높이 내림차순 정렬(최신 우선)
  blocks.value = Array.from(map.values()).sort((a, b) => b.height - a.height)
}

function addOrUpdateBlock(block) {
  setBlocksSortedUnique([block, ...blocks.value])
  try {
    highlighted.add(block.height)
    setTimeout(() => highlighted.delete(block.height), 1200)
  } catch (_) {}
}

async function tryMine() {
  if (!miner.value) miner.value = 'guest'
  message.value = '성공할 때까지 자동 재시도 중입니다…'
  messageType.value = 'info'
  miningState.value = 'mining'
  stopMining = false

  const attempt = async () => {
    const nonce = Math.floor(Math.random() * 100000) + 1
    lastAttempt.value = nonce
    if (difficultyOk(nonce)) {
      const res = await postMine({ miner: miner.value, nonce })
      if (res && res.ok) {
        message.value = `축하합니다! 블록 #${res.block.height} 채굴에 성공했습니다.`
        messageType.value = 'ok'
        miningState.value = 'success'
        // 낙관적 업데이트: SSE 수신을 기다리지 않고 즉시 반영
        addOrUpdateBlock(res.block)
        applyStatus(res.status)
        // 학습 코스 진행을 위한 이벤트 브로드캐스트 (CryptoZombies/Codecademy 스타일 레슨)
        try {
          window.dispatchEvent(new CustomEvent('lesson:mined', { detail: { block: res.block, status: res.status } }))
        } catch (_) {}
        return true
      }
      // 서버가 거부하면 계속 재시도 (예: 경합 상황)
    }
    return false
  }

  try {
    let success = false
    while (!success && !stopMining) {
      success = await attempt()
      if (!success) await new Promise(r => setTimeout(r, 60))
    }
  } catch (e) {
    message.value = '네트워크 오류 또는 서버 오류가 발생했습니다.'
    messageType.value = 'info'
    miningState.value = 'fail'
  } finally {
    setTimeout(() => {
      if (miningState.value !== 'mining') miningState.value = 'idle'
    }, 1200)
  }
}

function applyStatus(s) {
  // 보장: 블록 높이는 단조 증가(이전 값보다 낮아지지 않음)
  status.height = Math.max(status.height, s.height)
  status.difficulty = s.difficulty
  if ('reward' in s) status.reward = s.reward
}

function applyBlocks(list) {
  // 최신 높이 기준 내림차순 + 중복 제거
  setBlocksSortedUnique(list)
}

onMounted(async () => {
  if (savedNick) miner.value = savedNick
  const s = await fetchStatus()
  applyStatus(s)
  const b = await fetchBlocks()
  applyBlocks(b.blocks)

  // Always connect without nickname to ensure guest connection
  console.log('Connecting to SSE stream...') // Debug log
  
  // Prefer WebSocket if available, else SSE
  try {
    wsWrapper = connectEvents((payload) => handleMessage(payload), null) // Don't pass nickname
    if (wsWrapper.kind === 'ws') {
      // Stop polling when WS is open (handled in onopen)
      try { wsWrapper.socket.onopen = () => stopPolling() } catch (_) {}
    } else if (wsWrapper.kind === 'sse') {
      es = wsWrapper.socket
    }
  } catch (_) {
    // Fallback to SSE if WS creation failed synchronously
    es = connectBlockStream((payload) => handleMessage(payload), null) // Don't pass nickname
  }

  function handleMessage(payload) {
    console.log('SSE Message received:', payload) // Debug log
    if (payload.type === 'snapshot') {
      applyBlocks(payload.blocks)
      applyStatus(payload.status)
      // 서버가 부여한 자동 게스트명 반영
      if (payload.me && payload.me.nickname) {
        miner.value = payload.me.nickname
      }
      if (Array.isArray(payload.peers)) {
        console.log('Setting peers from snapshot:', payload.peers) // Debug log
        peers.value = payload.peers
      }
      // 실시간 연결 정상화 시 폴링 중지
      stopPolling()
    } else if (payload.type === 'block') {
      // 새 블록 추가
      addOrUpdateBlock(payload.block)
      applyStatus(payload.status)
      // 추가 안전장치: 이벤트의 블록 높이로 현재 높이 상향
      if (payload.block && typeof payload.block.height === 'number') {
        status.height = Math.max(status.height, payload.block.height)
      }
      // 브로드캐스트 공지 표시
      const who = payload.block?.miner || '알 수 없음'
      const h = payload.block?.height
      broadcastMsg.value = payload.notice || `${who} 님이 블록 #${h}를 채굴했습니다.`
      // 몇 초 뒤 자동 숨김
      setTimeout(() => { if (broadcastMsg.value) broadcastMsg.value = '' }, 3500)
    } else if (payload.type === 'status') {
      applyStatus(payload.status)
    } else if (payload.type === 'peers') {
      console.log('Updating peers:', payload.peers) // Debug log
      if (Array.isArray(payload.peers)) {
        const newPeerCount = payload.peers.length
        const oldPeerCount = previousPeerCount.value
        
        // 새 사용자 연결 알림
        if (newPeerCount > oldPeerCount && oldPeerCount > 0) {
          const newUsers = payload.peers.filter(p => !peers.value.includes(p))
          if (newUsers.length > 0) {
            showUserJoinNotification(newUsers[0]) // 첫 번째 새 사용자만 알림
          }
        }
        
        peers.value = payload.peers
        previousPeerCount.value = newPeerCount
      }
    }
  }

  // SSE 오류 시 폴링으로 폴백, 연결되면 중지
  if (es) {
    try {
      es.onerror = () => startPolling()
      es.onopen = () => stopPolling()
    } catch (_) {}
  } else if (wsWrapper && wsWrapper.kind === 'ws') {
    try {
      wsWrapper.socket.onerror = () => startPolling()
      wsWrapper.socket.onclose = () => startPolling()
    } catch (_) {}
  }
})

onBeforeUnmount(() => {
  stopMining = true
  if (es) es.close()
  if (wsWrapper && wsWrapper.kind === 'ws') {
    try { wsWrapper.socket.close() } catch (_) {}
  }
  stopPolling()
})
</script>

<style scoped>
</style>

<!-- -->
