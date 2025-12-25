<template>
  <div class="space-y-10 sm:space-y-14">
    <section class="pastel-home-hero p-6 sm:p-10 relative">
      <div class="grid gap-8 lg:grid-cols-2 items-center relative z-10">
        <div class="space-y-6 text-gray-900">
          <span class="inline-flex items-center gap-2 text-sm font-semibold text-indigo-700">
            <span class="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse"></span>
            한입 놀이터
          </span>
          <div class="space-y-5">
            <template v-if="hasSession">
              <div>
                <h1 class="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight leading-tight space-y-3">
                  <span class="block">{{ currentNickname }}님,</span>
                  <span class="block">한입 놀이터에 오신 것을 환영합니다</span>
                </h1>
                <p class="mt-4 text-base sm:text-lg text-slate-700">
                  비트코인을 눈으로 보고 즐기세요. 채굴, UTXO, 지갑, 궁합까지 한 자리에서 경험하세요.
                </p>
              </div>
            </template>
            <template v-else>
              <div class="space-y-4">
                <h1 class="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight leading-tight space-y-3">
                  <span class="flex flex-wrap items-baseline gap-3">
                    <label class="relative">
                      <span class="sr-only">닉네임 입력</span>
                      <input
                        v-model="nicknameInput"
                        @keyup.enter="handleNicknameSave"
                        type="text"
                        class="min-w-[160px] rounded-2xl border border-slate-200 bg-white/70 px-4 py-2 text-2xl sm:text-3xl font-semibold text-gray-900 shadow-inner focus:border-gray-900 focus:ring-2 focus:ring-gray-900/30 outline-none transition"
                        placeholder="사용자"
                        maxlength="20"
                      />
                    </label>
                    <span class="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-gray-900">
                      님,
                    </span>
                  </span>
                  <span class="block text-2xl sm:text-3xl lg:text-4xl font-extrabold text-gray-900">
                    한입 놀이터에 오신 것을 환영합니다
                  </span>
                </h1>
                <p class="text-base sm:text-lg text-slate-700">
                  비트코인을 눈으로 보고 즐기세요. 채굴, UTXO, 지갑, 궁합까지 한 자리에서 경험하세요.
                </p>
                <div class="space-y-2">
                  <div class="flex flex-wrap gap-3">
                    <button
                      class="px-6 py-3 rounded-2xl text-base font-semibold text-gray-900 bg-gradient-to-r from-pink-200 via-indigo-200 to-sky-200 hover:from-pink-300 hover:via-indigo-300 hover:to-sky-300 disabled:opacity-60 transition flex items-center justify-center gap-2 shadow-sm"
                      :class="{ 'flex-1 sm:flex-none': !existingNickname }"
                      :disabled="isSavingNickname || !nicknameInput.trim()"
                      @click="handleNicknameSave"
                    >
                      <svg
                        v-if="isSavingNickname"
                        class="h-5 w-5 animate-spin"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                      >
                        <path
                          d="M12 3v3m6.364.636l-2.121 2.121M21 12h-3m-.636 6.364l-2.121-2.121M12 21v-3m-6.364-.636l2.121-2.121M3 12h3m.636-6.364l2.121 2.121"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                        />
                      </svg>
                      <span>{{ isSavingNickname ? '등록 중...' : '등록하기' }}</span>
                    </button>
                    <button
                      v-if="existingNickname"
                      class="px-6 py-3 rounded-2xl text-base font-semibold text-gray-900 bg-gradient-to-r from-indigo-200 via-blue-200 to-teal-200 hover:from-indigo-300 hover:via-blue-300 hover:to-teal-300 transition shadow-sm"
                      @click="useExistingNickname"
                    >
                      사용하기
                    </button>
                  </div>
                  <p v-if="nickError" class="text-sm text-red-600">{{ nickError }}</p>
                </div>
              </div>
            </template>
          </div>
        </div>

        <div class="relative h-72 sm:h-80 lg:h-96">
          <div class="floating-bitcoin">
            <div class="coin-glow"></div>
            <div class="coin-core">₿</div>
          </div>

          <div class="character character-a">
            <div class="character-face">🤖</div>
            <div class="character-coin">₿</div>
          </div>

          <div class="character character-b">
            <div class="character-face">🧑‍🚀</div>
            <div class="character-coin">₿</div>
          </div>

          <div class="character character-c">
            <div class="character-face">🧙‍♂️</div>
            <div class="character-coin">₿</div>
          </div>
        </div>
      </div>
    </section>

    <section class="space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-bold text-slate-900">놀이터 살펴보기</h2>
          <p class="text-slate-500 text-sm sm:text-base">각 공간을 둘러보고 마음에 드는 플레이를 바로 시작하세요.</p>
        </div>
      </div>

      <div class="grid gap-4 sm:gap-6 md:grid-cols-2 xl:grid-cols-3">
        <article
          v-for="card in featureCards"
          :key="card.key"
          class="rounded-3xl border border-white/40 bg-white/70 backdrop-blur-lg shadow-[0_15px_50px_rgba(83,44,255,0.08)] p-5 flex flex-col gap-4 transition hover:-translate-y-1 hover:shadow-[0_18px_60px_rgba(83,44,255,0.16)]"
        >
          <div class="flex items-center gap-3">
            <div :class="['w-12 h-12 rounded-2xl flex items-center justify-center text-2xl text-slate-800', card.iconBg]">
              <component :is="card.icon" class="w-6 h-6" />
            </div>
            <div>
              <h3 class="text-lg font-semibold text-slate-900">{{ card.title }}</h3>
              <p class="text-xs uppercase tracking-wide text-slate-400">{{ card.subtitle }}</p>
            </div>
          </div>

          <p class="text-slate-600 flex-1 text-sm sm:text-base leading-relaxed">
            {{ card.description }}
          </p>

          <div class="flex justify-end pt-2">
            <button
              class="px-4 py-2 rounded-full text-sm font-semibold text-white transition"
              :class="hasSession ? 'bg-slate-900 hover:bg-slate-800' : 'bg-gray-300 cursor-not-allowed'"
              :disabled="!hasSession"
              @click="hasSession ? goTo(card.route) : null"
            >
              바로가기
            </button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, h } from 'vue'
import { useRouter } from 'vue-router'
import { apiCheckNickname, apiRegisterNickname } from '../api'

const router = useRouter()

const currentNickname = ref(localStorage.getItem('nickname') || '')
const nicknameInput = ref(currentNickname.value || '')
const isSavingNickname = ref(false)
const nickError = ref('')
const existingNickname = ref('')

const hasSession = computed(() => !!currentNickname.value)

watch(nicknameInput, () => {
  nickError.value = ''
  existingNickname.value = ''
})

const persistNickname = (name) => {
  localStorage.setItem('nickname', name)
  localStorage.removeItem('isAdmin')
  window.dispatchEvent(new CustomEvent('nicknameChanged', { detail: name }))
  currentNickname.value = name
  existingNickname.value = ''
}

const handleNicknameSave = async () => {
  const trimmed = (nicknameInput.value || '').trim()
  if (!trimmed) {
    nickError.value = '닉네임을 입력하세요'
    return
  }
  if (trimmed.length < 2) {
    nickError.value = '닉네임은 2자 이상이어야 합니다'
    return
  }
  if (trimmed.length > 20) {
    nickError.value = '닉네임은 20자 이하여야 합니다'
    return
  }
  if (trimmed.toLowerCase() === 'admin') {
    nickError.value = '관리자 계정은 일반 사용자 등록으로 사용할 수 없습니다'
    return
  }

  isSavingNickname.value = true
  nickError.value = ''

  try {
    const checkRes = await apiCheckNickname(trimmed)
    if (!checkRes?.ok) {
      nickError.value = checkRes?.error || '중복 체크에 실패했습니다'
      return
    }

    if (checkRes.exists) {
      nickError.value = '이미 등록된 사용자입니다. 그대로 사용하시려면 사용하기 버튼을 누르시고 다시 등록하시려면 새로운 사용자명을 입력하고 등록하기를 눌러주세요'
      existingNickname.value = trimmed
      return
    }

    const registerRes = await apiRegisterNickname(trimmed)
    if (registerRes?.ok && registerRes.nickname) {
      persistNickname(registerRes.nickname)
    } else {
      nickError.value = registerRes?.error || '닉네임 등록에 실패했습니다'
    }
  } catch (error) {
    nickError.value = '네트워크 오류가 발생했습니다'
  } finally {
    isSavingNickname.value = false
  }
}

const handleNicknameChanged = (value) => {
  currentNickname.value = value
  nicknameInput.value = value
  existingNickname.value = ''
  nickError.value = ''
}

const useExistingNickname = () => {
  if (!existingNickname.value) return
  persistNickname(existingNickname.value)
  nickError.value = ''
}

const nicknameChangedListener = (event) => {
  handleNicknameChanged(event.detail || localStorage.getItem('nickname') || '')
}

const storageListener = (event) => {
  if (event.key === 'nickname') {
    handleNicknameChanged(event.newValue || '')
  }
}

onMounted(() => {
  window.addEventListener('nicknameChanged', nicknameChangedListener)
  window.addEventListener('storage', storageListener)
})

onBeforeUnmount(() => {
  window.removeEventListener('nicknameChanged', nicknameChangedListener)
  window.removeEventListener('storage', storageListener)
})

const goTo = (routeName) => {
  router.push({ name: routeName })
}

const iconFactory = (path) => ({
  render() {
    return h('svg', {
      fill: 'none',
      stroke: 'currentColor',
      'stroke-width': '2',
      viewBox: '0 0 24 24'
    }, [
      h('path', {
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        d: path
      })
    ])
  }
})

const featureCards = [
  {
    key: 'mining',
    title: '비트코인 채굴',
    subtitle: 'MINING',
    description: '난이도와 보상을 확인하며 버튼 한 번으로 채굴 체험을 즐겨보세요. 실시간 블록 체인 스택을 확인할 수 있어요.',
    route: 'mining',
    icon: iconFactory('M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10'),
    iconBg: 'bg-gradient-to-br from-amber-200 to-orange-200'
  },
  {
    key: 'utxo',
    title: 'UTXO 탐험',
    subtitle: 'UTXO',
    description: 'UTXO 구조를 시각적으로 이해할 수 있도록 트랜잭션 흐름을 단계별로 풀어 설명합니다.',
    route: 'utxo',
    icon: iconFactory('M13 7h8m0 0v8m0-8l-8 8-4-4-6 6'),
    iconBg: 'bg-gradient-to-br from-violet-200 to-pink-200'
  },
  {
    key: 'wallet',
    title: '지갑 체험',
    subtitle: 'WALLET',
    description: '킹스톤 지갑을 통해 지갑 생성부터 트랜잭션 확인까지 따라 할 수 있는 인터랙션을 제공합니다.',
    route: 'wallet',
    icon: iconFactory('M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z'),
    iconBg: 'bg-gradient-to-br from-sky-200 to-indigo-200'
  },
  {
    key: 'fee',
    title: '수수료 계산',
    subtitle: 'FEE',
    description: '네트워크 상태에 따라 추천 수수료를 계산하고 지갑 송금 시 필요한 정보를 빠르게 파악하세요.',
    route: 'fee',
    icon: iconFactory('M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z'),
    iconBg: 'bg-gradient-to-br from-green-200 to-emerald-200'
  },
  {
    key: 'finance',
    title: '재무 관리',
    subtitle: 'FINANCE',
    description: '비트코인 자산과 투자 계획을 한눈에 정리할 수 있는 재무 보드에서 목표를 관리하세요.',
    route: 'finance',
    icon: iconFactory('M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z'),
    iconBg: 'bg-gradient-to-br from-yellow-200 to-lime-200'
  },
  {
    key: 'compatibility',
    title: '궁합 보기',
    subtitle: 'COMPATIBILITY',
    description: '비트코인을 매개로 다양한 궁합 시나리오를 즐겨보세요. 재미있는 결과가 기다리고 있습니다.',
    route: 'compatibility',
    icon: iconFactory('M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z'),
    iconBg: 'bg-gradient-to-br from-rose-200 to-orange-200'
  },
  {
    key: 'timecapsule',
    title: '타임캡슐',
    subtitle: 'TIMECAPSULE',
    description: '미래의 나에게 메시지를 저장하고, 시간이 지난 후 꺼내볼 수 있는 디지털 타임캡슐입니다.',
    route: 'timecapsule',
    icon: iconFactory('M6 3h12M6 3v4l6 6-6 6v4M18 3v4l-6 6 6 6v4M6 21h12'),
    iconBg: 'bg-gradient-to-br from-cyan-200 to-lime-200'
  }
]
</script>

<style scoped>
.pastel-home-hero {
  background: inherit;
  isolation: isolate;
}

.floating-bitcoin {
  position: absolute;
  top: 15%;
  left: 50%;
  transform: translateX(-50%);
  width: 180px;
  height: 180px;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, #ffd54f, #f39c12);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 20px 40px rgba(243, 156, 18, 0.4);
  animation: float 6s ease-in-out infinite;
}

.coin-glow {
  position: absolute;
  inset: -15px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 212, 79, 0.35), transparent 70%);
  filter: blur(6px);
}

.coin-core {
  font-size: 4rem;
  color: rgba(0, 0, 0, 0.65);
  font-weight: 600;
  text-shadow: 0 10px 20px rgba(0, 0, 0, 0.15);
}

.character {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  animation: float 5s ease-in-out infinite;
}

.character-face {
  font-size: 2.8rem;
  filter: drop-shadow(0 10px 15px rgba(0, 0, 0, 0.2));
}

.character-coin {
  background: white;
  border-radius: 9999px;
  padding: 0.4rem 1rem;
  font-size: 1.1rem;
  font-weight: 600;
  color: #f39c12;
  box-shadow: 0 5px 15px rgba(243, 156, 18, 0.25);
}

.character-a {
  top: 10%;
  left: 10%;
  animation-delay: 0.3s;
}

.character-b {
  bottom: 5%;
  right: 15%;
  animation-delay: 0.8s;
}

.character-c {
  top: 55%;
  left: 25%;
  animation-delay: 1.2s;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-15px);
  }
}
</style>
