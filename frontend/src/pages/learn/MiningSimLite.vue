<template>
  <div class="p-4 sm:p-6">
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
      <div class="bg-white border rounded-lg p-3">
        <div class="text-xs text-slate-500 mb-1">블록 높이</div>
        <div class="font-bold text-slate-800">{{ height }}</div>
      </div>
      <div class="bg-white border rounded-lg p-3">
        <div class="text-xs text-slate-500 mb-1">난이도 (≤)</div>
        <div class="font-bold text-slate-800">{{ difficulty }}</div>
      </div>
      <div class="bg-white border rounded-lg p-3">
        <div class="text-xs text-slate-500 mb-1">블록 보상</div>
        <div class="font-bold text-slate-800">{{ reward }}</div>
      </div>
      <div class="bg-white border rounded-lg p-3">
        <div class="text-xs text-slate-500 mb-1">마지막 시도값</div>
        <div class="font-mono font-bold text-slate-800">{{ lastNonce ?? '-' }}</div>
      </div>
    </div>

    <div class="bg-orange-50 border border-orange-200 rounded-lg p-3 text-sm text-orange-800 mb-4">
      1~100,000 중 임의의 값이 현재 난이도 이하일 때 채굴 성공! 10블록마다 난이도가 절반으로 낮아지고, 보상은 20블록마다 절반으로 줄어듭니다.
    </div>

    <div class="flex gap-2 mb-4">
      <button @click="tryMine" :disabled="mining" class="px-4 py-2 bg-slate-800 text-white rounded-lg disabled:bg-slate-400">채굴 시도하기</button>
      <button @click="reset" class="px-4 py-2 bg-white border rounded-lg">초기화</button>
    </div>

    <div v-if="message" class="p-3 rounded-lg" :class="ok ? 'bg-green-50 border border-green-200 text-green-700' : 'bg-slate-50 border border-slate-200 text-slate-700'">
      {{ message }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const DIFFICULTY_BASE = 10000
const MAX_NONCE = 100000

const height = ref(0)
const lastNonce = ref(null)
const mining = ref(false)
const message = ref('')
const ok = ref(false)

function calcDifficulty(h) {
  const step = Math.floor(h / 10)
  return Math.max(1, Math.floor(DIFFICULTY_BASE / (2 ** step)))
}

function calcReward(nextHeight) {
  const step = Math.floor((nextHeight - 1) / 20)
  return Math.max(1, Math.floor(100 / (2 ** step)))
}

const difficulty = computed(() => calcDifficulty(height.value))
const reward = computed(() => calcReward(height.value + 1))

function emitMined(nonce) {
  try {
    window.dispatchEvent(new CustomEvent('lesson:mined', { detail: { nonce, difficulty: difficulty.value, height: height.value, reward: reward.value } }))
  } catch (_) {}
}

async function tryMine() {
  mining.value = true
  message.value = ''
  ok.value = false
  const nonce = Math.floor(Math.random() * MAX_NONCE) + 1
  lastNonce.value = nonce
  await new Promise(r => setTimeout(r, 200))
  if (nonce <= difficulty.value) {
    // success
    height.value += 1
    ok.value = true
    message.value = `성공! 블록 #${height.value} 채굴됨 (nonce=${nonce} ≤ ${difficulty.value})`
    emitMined(nonce)
  } else {
    ok.value = false
    message.value = `실패 (nonce=${nonce} > ${difficulty.value}). 다시 시도!`
  }
  mining.value = false
}

function reset() {
  height.value = 0
  lastNonce.value = null
  message.value = ''
  ok.value = false
}
</script>

<style scoped>
</style>

