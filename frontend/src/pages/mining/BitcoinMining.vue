<template>
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <div class="lg:col-span-2 space-y-4">
      <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
        <h3 class="font-semibold mb-2">네트워크 상태</h3>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <div class="p-3 bg-slate-50 rounded">
            <div class="text-slate-500">현재 블록 높이</div>
            <div class="text-xl font-bold">{{ status.height }}</div>
          </div>
          <div class="p-3 bg-slate-50 rounded">
            <div class="text-slate-500">현재 난이도(허용 최대값)</div>
            <div class="text-xl font-bold">≤ {{ status.difficulty }}</div>
          </div>
          <div class="p-3 bg-slate-50 rounded">
            <div class="text-slate-500">현재 블록 보상</div>
            <div class="text-xl font-bold flex items-center gap-2">
              <CoinIcon />
              <span class="tabular-nums">{{ currentReward }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 블록 스택(최신이 왼쪽) -->
      <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
        <BlockGrid :blocks="blocks" :limit="60" />
      </div>

      <!-- 최신 블록: 데스크톱에서만 이 위치에 표시 -->
      <div class="hidden md:block bg-white rounded-lg shadow-sm border border-slate-200 p-4">
        <h3 class="font-semibold mb-3">최신 블록</h3>
        <div v-if="broadcastMsg" class="mb-2 text-sm p-2 rounded border border-indigo-200 bg-indigo-50 text-indigo-700">
          {{ broadcastMsg }}
        </div>

        <!-- Mobile: card list (숨김) -->
        <div class="space-y-2 md:hidden">
          <div
            v-for="b in blocks"
            :key="b.height"
            class="p-3 rounded border border-slate-200 bg-slate-50"
          >
            <div class="flex items-center justify-between text-sm">
              <div class="font-semibold">#{{ b.height }}</div>
              <div class="text-slate-500">{{ new Date(b.timestamp).toLocaleString() }}</div>
            </div>
            <div class="mt-2 grid grid-cols-2 gap-2 text-sm">
              <div>
                <div class="text-slate-500">난이도</div>
                <div class="tabular-nums">{{ b.difficulty }}</div>
              </div>
              <div>
                <div class="text-slate-500">Nonce</div>
                <div class="tabular-nums">{{ b.nonce }}</div>
              </div>
              <div class="col-span-2 flex items-center gap-2">
                <div class="text-slate-500">보상</div>
                <span class="inline-flex items-center gap-1 font-medium"><CoinIcon /> <span class="tabular-nums">{{ b.reward || 0 }}</span></span>
              </div>
              <div class="col-span-2">
                <div class="text-slate-500">채굴자</div>
                <div class="truncate">{{ b.miner }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Desktop: table -->
        <div class="hidden md:block overflow-auto max-h-96">
          <table class="min-w-full text-sm">
            <thead class="text-left text-slate-500">
              <tr>
                <th class="py-2 pr-4">높이</th>
                <th class="py-2 pr-4">난이도</th>
                <th class="py-2 pr-4">보상</th>
                <th class="py-2 pr-4">Nonce</th>
                <th class="py-2 pr-4">채굴자</th>
                <th class="py-2 pr-4">시간</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="b in blocks" :key="b.height" class="border-t">
                <td class="py-2 pr-4">{{ b.height }}</td>
                <td class="py-2 pr-4">{{ b.difficulty }}</td>
                <td class="py-2 pr-4">
                  <span class="inline-flex items-center gap-1"><CoinIcon /> <span class="tabular-nums">{{ b.reward || 0 }}</span></span>
                </td>
                <td class="py-2 pr-4">{{ b.nonce }}</td>
                <td class="py-2 pr-4">{{ b.miner }}</td>
                <td class="py-2 pr-4">{{ new Date(b.timestamp).toLocaleString() }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="space-y-4">
      <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-4 space-y-3">
        <h3 class="font-semibold">채굴 시도</h3>
        <label class="block text-sm">
          닉네임
          <input v-model="miner" class="mt-1 w-full border rounded px-3 py-2" placeholder="예: satoshi" inputmode="text" />
        </label>

        <div class="text-sm text-slate-600">
          1~100000 범위의 난수 중 현재 난이도(최대 허용값) 이하가 나오면 블록을 채굴할 수 있습니다.
          10블록마다 난이도는 절반으로 낮아집니다(최대 허용값 감소). 초기 난이도는 10000입니다.
        </div>

        <button
          class="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white rounded px-4 py-2 font-medium"
          :disabled="miningState === 'mining'"
          @click="tryMine"
        >
          채굴 시도하기
        </button>

        <div class="text-sm" v-if="lastAttempt">
          마지막 시도값: <span class="font-mono">{{ lastAttempt }}</span>
        </div>

        <div v-if="message" class="p-3 rounded" :class="messageType === 'ok' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-yellow-50 text-yellow-700 border border-yellow-200'">
          {{ message }}
        </div>
      </div>

      <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
        <MiningAnim :state="miningState" />
      </div>

      <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
        <h3 class="font-semibold mb-2">보상 현황</h3>
        <div class="mb-2 text-sm text-slate-700">
          내 보상:
          <span class="inline-flex items-center gap-1 font-semibold">
            <CoinIcon /> × <span class="tabular-nums">{{ myReward }}</span>
          </span>
        </div>
        <ul class="text-sm divide-y max-h-64 overflow-auto">
          <li v-for="item in rewardByMiner" :key="item.miner" class="py-1 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span :class="{'font-semibold text-slate-900': item.miner === miner}">{{ item.miner }}</span>
            </div>
            <div class="flex items-center gap-1">
              <CoinIcon />
              <span class="tabular-nums">{{ item.amount }}</span>
            </div>
          </li>
        </ul>
      </div>

      <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
        <h3 class="font-semibold mb-2">접속 중인 게스트</h3>
        <div v-if="peers.length === 0" class="text-sm text-slate-500">현재 접속자가 없습니다.</div>
        <ul v-else class="text-sm space-y-1 max-h-64 overflow-auto">
          <li v-for="p in peers" :key="p" class="flex items-center gap-2">
            <span class="inline-block w-2 h-2 rounded-full bg-green-500"></span>
            <span :class="{'font-semibold text-slate-900': p === miner}">{{ p }}<span v-if="p === miner" class="text-xs text-slate-500"> (나)</span></span>
          </li>
        </ul>
      </div>
    </div>

    <!-- 모바일 전용: 페이지 맨 아래에 최신 블록 배치 -->
    <div class="md:hidden bg-white rounded-lg shadow-sm border border-slate-200 p-4">
      <h3 class="font-semibold mb-3">최신 블록</h3>
      <div v-if="broadcastMsg" class="mb-2 text-sm p-2 rounded border border-indigo-200 bg-indigo-50 text-indigo-700">
        {{ broadcastMsg }}
      </div>
      <div class="space-y-2">
        <div
          v-for="b in blocks"
          :key="b.height"
          class="p-3 rounded border border-slate-200 bg-slate-50"
        >
          <div class="flex items-center justify-between text-sm">
            <div class="font-semibold">#{{ b.height }}</div>
            <div class="text-slate-500">{{ new Date(b.timestamp).toLocaleString() }}</div>
          </div>
          <div class="mt-2 grid grid-cols-2 gap-2 text-sm">
            <div>
              <div class="text-slate-500">난이도</div>
              <div class="tabular-nums">{{ b.difficulty }}</div>
            </div>
            <div>
              <div class="text-slate-500">Nonce</div>
              <div class="tabular-nums">{{ b.nonce }}</div>
            </div>
            <div class="col-span-2 flex items-center gap-2">
              <div class="text-slate-500">보상</div>
              <span class="inline-flex items-center gap-1 font-medium"><CoinIcon /> <span class="tabular-nums">{{ b.reward || 0 }}</span></span>
            </div>
            <div class="col-span-2">
              <div class="text-slate-500">채굴자</div>
              <div class="truncate">{{ b.miner }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, reactive, ref, computed } from 'vue'
import { fetchStatus, fetchBlocks, postMine, connectBlockStream } from '../../api'
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
const broadcastMsg = ref('')
const peers = ref([])
let pollTimer = null

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

function difficultyOk(val) {
  return val <= status.difficulty
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
  const s = await fetchStatus()
  applyStatus(s)
  const b = await fetchBlocks()
  applyBlocks(b.blocks)

  es = connectBlockStream((payload) => {
    if (payload.type === 'snapshot') {
      applyBlocks(payload.blocks)
      applyStatus(payload.status)
      // 서버가 부여한 자동 게스트명 반영
      if (payload.me && payload.me.nickname) {
        miner.value = payload.me.nickname
      }
      if (Array.isArray(payload.peers)) {
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
      if (Array.isArray(payload.peers)) peers.value = payload.peers
    }
  })

  // SSE 오류 시 폴링으로 폴백, 연결되면 중지
  try {
    es.onerror = () => startPolling()
    es.onopen = () => stopPolling()
  } catch (_) {}
})

onBeforeUnmount(() => {
  stopMining = true
  if (es) es.close()
  stopPolling()
})
</script>

<style scoped>
</style>

<!-- -->
