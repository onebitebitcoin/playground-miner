<template>
  <div class="flex flex-col items-center justify-center select-none">
    <div class="relative w-48 h-48">
      <!-- 땅/바닥 -->
      <div class="absolute bottom-6 left-0 right-0 h-4 bg-amber-800/40 rounded"></div>

      <!-- 바위 -->
      <div class="absolute bottom-10 left-10 w-16 h-12 bg-slate-500 rounded-lg shadow-inner"></div>
      <div class="absolute bottom-11 left-24 w-14 h-10 bg-slate-400 rounded-lg shadow-inner"></div>

      <!-- 곡괭이 -->
      <div :class="['absolute -top-2 left-20 origin-bottom-left', state === 'mining' ? 'animate-swing' : '']">
        <svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="37" y="8" width="6" height="56" rx="3" fill="#F59E0B" />
          <path d="M20 26 C40 8, 60 8, 74 30" stroke="#374151" stroke-width="10" stroke-linecap="round" />
        </svg>
      </div>

      <!-- 코인 -->
      <div class="absolute bottom-16 right-6">
        <div :class="['w-10 h-10 rounded-full grid place-items-center font-bold',
                       state === 'success' ? 'animate-pop bg-amber-300 text-amber-900 shadow-lg' : 'bg-amber-200 text-amber-800']">
          ₿
        </div>
      </div>

      <!-- 먼지 효과 -->
      <div v-if="state === 'mining'" class="absolute bottom-10 left-8 w-3 h-3 bg-slate-300 rounded-full animate-dust"></div>
      <div v-if="state === 'mining'" class="absolute bottom-12 left-14 w-2 h-2 bg-slate-300 rounded-full animate-dust delay-150"></div>
      <div v-if="state === 'mining'" class="absolute bottom-9 left-16 w-2 h-2 bg-slate-300 rounded-full animate-dust delay-300"></div>
    </div>
    <div class="mt-2 text-sm text-slate-600">
      <span v-if="state === 'idle'">대기 중…</span>
      <span v-else-if="state === 'mining'">채굴 중… 곡괭이를 휘두르는 중!</span>
      <span v-else-if="state === 'success'" class="text-emerald-700 font-medium">성공! 블록이 생성되었습니다.</span>
      <span v-else-if="state === 'fail'" class="text-amber-700">실패! 다음에 다시 시도해요.</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  state: { type: String, default: 'idle' } // 'idle' | 'mining' | 'success' | 'fail'
})
</script>

<style scoped>
@keyframes swing {
  0% { transform: rotate(-20deg); }
  50% { transform: rotate(20deg); }
  100% { transform: rotate(-20deg); }
}
.animate-swing { animation: swing 0.6s ease-in-out infinite; }

@keyframes pop {
  0% { transform: scale(0.6); opacity: 0.2; }
  60% { transform: scale(1.15); opacity: 1; }
  100% { transform: scale(1); }
}
.animate-pop { animation: pop 450ms ease-out; }

@keyframes dust {
  0% { transform: translateY(0) translateX(0); opacity: 0.9; }
  100% { transform: translateY(-16px) translateX(8px); opacity: 0; }
}
.animate-dust { animation: dust 700ms ease-out infinite; }
.delay-150 { animation-delay: 150ms; }
.delay-300 { animation-delay: 300ms; }
</style>
