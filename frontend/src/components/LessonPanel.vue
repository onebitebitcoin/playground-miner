<template>
  <div class="bg-white border border-slate-200 rounded-xl p-4 md:p-6">
    <div class="flex items-center justify-between mb-3">
      <h2 class="text-lg font-semibold text-slate-800">{{ title }}</h2>
      <span class="text-xs text-slate-500">{{ completedCount }}/{{ steps.length }}</span>
    </div>
    <p v-if="description" class="text-slate-600 text-sm mb-4">{{ description }}</p>

    <div class="space-y-3">
      <div v-for="(step, i) in steps" :key="step.id" class="border rounded-lg p-3" :class="isDone(step.id) ? 'border-green-200 bg-green-50' : 'border-slate-200'">
        <div class="flex items-center justify-between">
          <div>
            <div class="font-medium text-slate-800">{{ i + 1 }}. {{ step.title }}</div>
            <div class="text-sm text-slate-600 whitespace-pre-line mt-1">{{ step.text }}</div>
          </div>
          <div class="flex items-center gap-2">
            <button
              class="px-3 py-1.5 text-sm rounded-lg border"
              :class="isChecking === step.id ? 'bg-slate-100 text-slate-600' : 'bg-white hover:bg-slate-50 text-slate-700'"
              :disabled="isChecking === step.id"
              @click="check(step)"
            >
              <span v-if="isChecking === step.id">확인중…</span>
              <span v-else>확인</span>
            </button>
            <span v-if="isDone(step.id)" class="inline-flex items-center gap-1 text-green-700 text-sm">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              완료
            </span>
          </div>
        </div>
        <div v-if="errors[step.id]" class="mt-2 text-sm text-red-600">{{ errors[step.id] }}</div>
        <div v-if="hints[step.id] && !isDone(step.id)" class="mt-2 text-xs text-slate-500">힌트: {{ hints[step.id] }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  courseId: { type: String, required: true },
  title: { type: String, required: true },
  description: { type: String, default: '' },
  steps: { type: Array, required: true }, // [{ id, title, text, validate: async () => ({ ok, error, hint }) }]
})

const isChecking = ref('')
const errors = ref({})
const hints = ref({})

const storageKey = computed(() => `lesson-progress:${props.courseId}`)
const doneSet = ref(new Set(JSON.parse(localStorage.getItem(storageKey.value) || '[]')))

function isDone(id) {
  return doneSet.value.has(id)
}

function save() {
  localStorage.setItem(storageKey.value, JSON.stringify(Array.from(doneSet.value)))
}

async function check(step) {
  isChecking.value = step.id
  errors.value = { ...errors.value, [step.id]: '' }
  hints.value = { ...hints.value, [step.id]: '' }
  try {
    const res = await step.validate()
    if (res && res.ok) {
      doneSet.value.add(step.id)
      save()
    } else {
      errors.value = { ...errors.value, [step.id]: res?.error || '조건이 충족되지 않았습니다.' }
      if (res?.hint) hints.value = { ...hints.value, [step.id]: res.hint }
    }
  } catch (e) {
    errors.value = { ...errors.value, [step.id]: '검증 중 오류가 발생했습니다.' }
  } finally {
    isChecking.value = ''
  }
}

watch(() => props.courseId, () => {
  doneSet.value = new Set(JSON.parse(localStorage.getItem(storageKey.value) || '[]'))
  errors.value = {}
  hints.value = {}
})

const completedCount = computed(() => doneSet.value.size)
</script>

<style scoped>
</style>

