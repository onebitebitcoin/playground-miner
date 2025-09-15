<template>
  <div class="space-y-4">
    <!-- Header / Progress -->
    <div class="flex items-center justify-between">
      <div>
        <div class="text-xs text-slate-500">{{ courseTitle }}</div>
        <div class="text-lg font-semibold text-slate-800">Step {{ stepIndex + 1 }} / {{ steps.length }} · {{ currentStep.title }}</div>
      </div>
      <button @click="$emit('exit')" class="px-3 py-1.5 text-sm rounded-lg border bg-white hover:bg-slate-50">코스 목록</button>
    </div>

    <!-- Body: Instructions + Simulator -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div class="bg-white border border-slate-200 rounded-lg p-4">
        <div class="text-sm text-slate-700 whitespace-pre-line">{{ currentStep.text }}</div>
        <div v-if="error" class="mt-3 text-sm text-red-600">{{ error }}</div>
        <div v-if="hint && !doneSet.has(currentStep.id)" class="mt-1 text-xs text-slate-500">힌트: {{ hint }}</div>
      </div>
      <div class="bg-white border border-slate-200 rounded-lg overflow-hidden">
        <component :is="simComponent" />
      </div>
    </div>

    <!-- Actions -->
    <div class="flex items-center justify-between">
      <div class="text-xs text-slate-500">진행 상황은 브라우저에 저장됩니다</div>
      <div class="flex gap-2">
        <button @click="prev" :disabled="stepIndex===0" class="px-3 py-2 rounded-lg border bg-white disabled:opacity-50">이전</button>
        <button @click="check" :disabled="checking" class="px-3 py-2 rounded-lg border bg-white disabled:opacity-50">
          <span v-if="checking">확인중…</span><span v-else>확인</span>
        </button>
        <button @click="next" :disabled="!doneSet.has(currentStep.id) || stepIndex===steps.length-1" class="px-4 py-2 rounded-lg bg-slate-800 text-white disabled:bg-slate-400">다음</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import MiningSimLite from './MiningSimLite.vue'
import UTXOSimLite from './UTXOSimLite.vue'

const props = defineProps({ courseId: { type: String, required: true } })
const emit = defineEmits(['exit'])

// Listen for events from simulators
const lastMined = ref(null)
const lastUtxoReset = ref(null)
const lastUtxoTx = ref(null)

onMounted(() => {
  window.addEventListener('lesson:mined', (e) => { lastMined.value = e?.detail || null })
  window.addEventListener('lesson:utxo_reset', (e) => { lastUtxoReset.value = e?.detail || null })
  window.addEventListener('lesson:utxo_tx', (e) => { lastUtxoTx.value = e?.detail || null })
})

// Course definitions
const courses = {
  'mining-101': {
    title: 'Mining 101',
    sim: 'mining',
    steps: [
      { id: 'mine-first', title: '첫 블록 채굴', text: '채굴 시도하기 버튼을 눌러 난수 ≤ 난이도가 나올 때까지 시도해 보세요.', validate: async () => lastMined.value ? { ok: true } : { ok: false, error: '아직 성공 이벤트가 없어요.', hint: '버튼을 눌러 채굴을 시도하세요.' } },
      { id: 'pow-check', title: 'PoW 조건 확인', text: '방금 채굴한 데이터에서 nonce ≤ difficulty 조건을 눈으로 확인해 보세요.', validate: async () => {
        const m = lastMined.value
        if (!m) return { ok: false, error: '채굴 데이터가 없어요.', hint: '먼저 한 번 성공해야 합니다.' }
        return m.nonce <= m.difficulty ? { ok: true } : { ok: false, error: 'nonce가 난이도보다 큼.', hint: '다시 성공할 때까지 시도해 보세요.' }
      } },
      { id: 'reward-read', title: '보상 감소 개념', text: '보상 수치는 시뮬레이터에 표시됩니다. 블록 수가 늘어날수록(20개 단위) 보상이 절반이 됩니다.', validate: async () => {
        const m = lastMined.value
        return (m && typeof m.reward === 'number') ? { ok: true } : { ok: false, error: '보상을 아직 확인하지 못했어요.', hint: '한 번 채굴 성공 후 상단 보상을 확인하세요.' }
      } },
    ]
  },
  'utxo-101': {
    title: 'UTXO 101',
    sim: 'utxo',
    steps: [
      { id: 'reset-utxo', title: '초기 UTXO 만들기', text: "'새로 시작'을 눌러 3개 이상의 UTXO를 가진 상태를 만드세요.", validate: async () => {
        const r = lastUtxoReset.value
        return (r && r.utxoCount >= 3) ? { ok: true } : { ok: false, error: 'UTXO 개수가 부족합니다.', hint: '랜덤 생성이므로 한 번 더 시도해 보세요.' }
      } },
      { id: 'send-one', title: '한 명에게 보내기', text: '받는 사람 수를 1명으로 하여 임의의 금액을 전송해 보세요.', validate: async () => {
        const t = lastUtxoTx.value
        const rcpt = (t?.outputs || []).filter(o => !o.isChange).length
        return rcpt === 1 ? { ok: true } : { ok: false, error: '받는 사람이 1명이 아니에요.', hint: '받는 사람 수를 1로 맞춰보세요.' }
      } },
      { id: 'change', title: '잔돈 생성', text: '입력 합계가 전송금액보다 크면 잔돈(Change) UTXO가 생성됩니다. 잔돈이 생기는 거래를 만들어 보세요.', validate: async () => {
        const t = lastUtxoTx.value
        const hasChange = (t?.outputs || []).some(o => o.isChange && o.amount > 0)
        return hasChange ? { ok: true } : { ok: false, error: '잔돈이 생성되지 않았어요.', hint: '보낼 금액을 더 작게 해서 잔액이 남도록 해보세요.' }
      } },
    ]
  }
}

const course = computed(() => courses[props.courseId] || courses['mining-101'])
const courseTitle = computed(() => course.value.title)
const steps = computed(() => course.value.steps)
const simComponent = computed(() => course.value.sim === 'mining' ? MiningSimLite : UTXOSimLite)

// Progress persistence
const stepIndex = ref(parseInt(localStorage.getItem(lsKey('current')) || '0', 10) || 0)
const doneSet = ref(new Set(JSON.parse(localStorage.getItem(lsKey('done')) || '[]')))

function lsKey(suf) { return `course:${props.courseId}:${suf}` }
function save() {
  localStorage.setItem(lsKey('current'), String(stepIndex.value))
  localStorage.setItem(lsKey('done'), JSON.stringify(Array.from(doneSet.value)))
}

watch(() => props.courseId, () => {
  stepIndex.value = parseInt(localStorage.getItem(lsKey('current')) || '0', 10) || 0
  doneSet.value = new Set(JSON.parse(localStorage.getItem(lsKey('done')) || '[]'))
})

const currentStep = computed(() => steps.value[stepIndex.value])

const checking = ref(false)
const error = ref('')
const hint = ref('')

async function check() {
  error.value = ''
  hint.value = ''
  checking.value = true
  try {
    const res = await currentStep.value.validate()
    if (res?.ok) {
      doneSet.value.add(currentStep.value.id)
      save()
    } else {
      error.value = res?.error || '조건이 충족되지 않았습니다.'
      if (res?.hint) hint.value = res.hint
    }
  } finally {
    checking.value = false
  }
}

function next() {
  if (stepIndex.value < steps.value.length - 1 && doneSet.value.has(currentStep.value.id)) {
    stepIndex.value += 1
    save()
    error.value = ''
    hint.value = ''
  }
}

function prev() {
  if (stepIndex.value > 0) {
    stepIndex.value -= 1
    save()
    error.value = ''
    hint.value = ''
  }
}
</script>

<style scoped>
</style>

