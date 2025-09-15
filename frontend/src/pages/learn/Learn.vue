<template>
  <div>
    <!-- Landing -->
    <div v-if="mode==='home'" class="grid sm:grid-cols-2 gap-4">
      <div class="border rounded-xl p-4 bg-white">
        <div class="text-xs text-slate-500 mb-1">코스</div>
        <div class="text-lg font-semibold text-slate-800 mb-1">Mining 101</div>
        <div class="text-sm text-slate-600 mb-3">난이도·논스·보상 감소 개념을 실습으로 익힙니다.</div>
        <div class="flex items-center justify-between">
          <div class="text-xs text-slate-500">완료 {{ progress('mining-101') }}/3</div>
          <button class="px-3 py-2 rounded-lg bg-slate-800 text-white" @click="start('mining-101')">시작/계속</button>
        </div>
      </div>
      <div class="border rounded-xl p-4 bg-white">
        <div class="text-xs text-slate-500 mb-1">코스</div>
        <div class="text-lg font-semibold text-slate-800 mb-1">UTXO 101</div>
        <div class="text-sm text-slate-600 mb-3">입력/출력과 잔돈(Change) 생성 원리를 익힙니다.</div>
        <div class="flex items-center justify-between">
          <div class="text-xs text-slate-500">완료 {{ progress('utxo-101') }}/3</div>
          <button class="px-3 py-2 rounded-lg bg-slate-800 text-white" @click="start('utxo-101')">시작/계속</button>
        </div>
      </div>
    </div>

    <!-- Runner -->
    <div v-else>
      <CourseRunner :course-id="currentId" @exit="exitCourse" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import CourseRunner from './CourseRunner.vue'

const mode = ref('home')
const currentId = ref('')

function key(id, suf) { return `course:${id}:${suf}` }
function progress(id) { return (JSON.parse(localStorage.getItem(key(id,'done')) || '[]') || []).length }

function start(id) {
  currentId.value = id
  mode.value = 'course'
}

function exitCourse() {
  mode.value = 'home'
  currentId.value = ''
}
</script>

<style scoped>
</style>
