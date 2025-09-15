<template>
  <div class="p-4 sm:p-6 space-y-4">
    <div class="flex items-center justify-between">
      <div class="font-semibold text-slate-800">내 UTXO</div>
      <div class="flex items-center gap-2">
        <div class="text-sm text-slate-500">개수: <span class="font-medium text-slate-800">{{ myUTXOs.length }}</span></div>
        <div class="text-sm text-slate-500">잔액: <span class="font-medium text-slate-800">{{ totalBalance }} BTC</span></div>
        <button @click="reset" class="px-3 py-2 bg-orange-500 text-white rounded-lg">새로 시작</button>
      </div>
    </div>

    <div class="grid md:grid-cols-2 gap-4">
      <div class="space-y-3">
        <div>
          <label class="block text-sm text-slate-700 mb-1">받는 사람 수</label>
          <select v-model.number="recipientCount" class="border rounded-lg px-2 py-1">
            <option :value="1">1명</option>
            <option :value="2">2명</option>
            <option :value="3">3명</option>
          </select>
        </div>
        <div v-for="(r, i) in recipients" :key="i" class="border rounded-lg p-3">
          <div class="text-xs text-slate-500 mb-1">받는 사람 {{ i+1 }}</div>
          <input type="number" min="1" step="1" v-model.number="r.amount" class="w-full border rounded px-2 py-1" placeholder="보낼 금액 (BTC)" />
        </div>
        <button @click="simulate" class="w-full px-4 py-2 bg-slate-800 text-white rounded-lg">거래 시뮬레이션</button>
        <div v-if="error" class="text-sm text-red-600">{{ error }}</div>
      </div>
      <div class="space-y-3">
        <div class="text-sm text-slate-700">보유 UTXO</div>
        <div class="grid sm:grid-cols-2 gap-2">
          <div v-for="u in myUTXOs" :key="u.id" class="border rounded-lg p-2">
            <div class="text-sm font-medium text-slate-800">{{ u.amount }} BTC</div>
          </div>
        </div>
        <div v-if="lastTx" class="mt-2 border rounded-lg p-3">
          <div class="text-sm font-semibold text-slate-800 mb-2">최근 거래</div>
          <div class="text-xs text-slate-500 mb-1">입력</div>
          <div class="flex flex-wrap gap-1 mb-2">
            <span v-for="inp in lastTx.inputs" :key="inp.id" class="px-2 py-1 bg-slate-100 rounded text-xs">{{ inp.amount }} BTC</span>
          </div>
          <div class="text-xs text-slate-500 mb-1">출력</div>
          <div class="flex flex-wrap gap-1">
            <span v-for="(out,i) in lastTx.outputs" :key="i" class="px-2 py-1 rounded text-xs" :class="out.isChange ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'">
              {{ out.amount }} BTC {{ out.isChange ? '(잔돈)' : '' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const myUTXOs = ref([])
const recipients = ref([{ amount: 1 }])
const recipientCount = ref(1)
const lastTx = ref(null)
const error = ref('')

const totalBalance = computed(() => myUTXOs.value.reduce((s, u) => s + u.amount, 0))

watch(recipientCount, (n) => {
  const cur = recipients.value.length
  if (n > cur) {
    for (let i = cur; i < n; i++) recipients.value.push({ amount: 1 })
  } else if (n < cur) {
    recipients.value = recipients.value.slice(0, n)
  }
})

function genId() { return Math.random().toString(36).slice(2) }

function emitReset() {
  try { window.dispatchEvent(new CustomEvent('lesson:utxo_reset', { detail: { utxoCount: myUTXOs.value.length } })) } catch (_) {}
}

function emitTx(tx) {
  try {
    const outSummary = tx.outputs.map(o => ({ amount: o.amount, isChange: !!o.isChange }))
    const inSummary = tx.inputs.map(i => i.amount)
    window.dispatchEvent(new CustomEvent('lesson:utxo_tx', { detail: { id: tx.id, outputs: outSummary, inputs: inSummary } }))
  } catch (_) {}
}

function reset() {
  myUTXOs.value = []
  for (let i = 0; i < Math.floor(Math.random()*5)+3; i++) {
    myUTXOs.value.push({ id: genId(), amount: Math.floor(Math.random()*10)+1 })
  }
  recipients.value = [{ amount: 1 }]
  recipientCount.value = 1
  lastTx.value = null
  error.value = ''
  emitReset()
}

function selectUTXOs(target) {
  const sorted = [...myUTXOs.value].sort((a,b)=>b.amount - a.amount)
  let sum = 0
  const sel = []
  for (const u of sorted) { sel.push(u); sum += u.amount; if (sum >= target) break }
  return { selected: sel, total: sum }
}

function simulate() {
  error.value = ''
  const totalNeed = recipients.value.reduce((s,r)=> s + (r.amount||0), 0)
  if (totalNeed <= 0) { error.value = '올바른 금액을 입력하세요.'; return }
  if (totalNeed > totalBalance.value) { error.value = '잔액이 부족합니다.'; return }
  const { selected, total } = selectUTXOs(totalNeed)
  if (total < totalNeed) { error.value = '충분한 UTXO를 찾지 못했습니다.'; return }

  // build tx
  const tx = { id: genId(), inputs: selected.map(s=>({ ...s })), outputs: [] }
  recipients.value.forEach(r => { tx.outputs.push({ amount: r.amount, isChange: false }) })
  const change = total - totalNeed
  if (change > 0) tx.outputs.push({ amount: change, isChange: true })

  // apply
  const ids = new Set(selected.map(s=>s.id))
  myUTXOs.value = myUTXOs.value.filter(u => !ids.has(u.id))
  if (change > 0) myUTXOs.value.push({ id: genId(), amount: change })
  lastTx.value = tx
  emitTx(tx)
}

// init
reset()
</script>

<style scoped>
</style>

