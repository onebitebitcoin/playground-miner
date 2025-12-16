<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-medium leading-6 text-slate-900">타임캡슐 관리</h3>
      <button
        @click="fetchTimeCapsules"
        class="inline-flex items-center px-3 py-2 border border-slate-300 shadow-sm text-sm leading-4 font-medium rounded-md text-slate-700 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
      >
        <svg class="-ml-0.5 mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        새로고침
      </button>
    </div>

    <!-- Stats or Summary -->
    <div class="grid grid-cols-1 gap-5 sm:grid-cols-3">
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="px-4 py-5 sm:p-6">
          <dt class="text-sm font-medium text-slate-500 truncate">총 타임캡슐</dt>
          <dd class="mt-1 text-3xl font-semibold text-slate-900">{{ capsules.length }}</dd>
        </div>
      </div>
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="px-4 py-5 sm:p-6">
          <dt class="text-sm font-medium text-slate-500 truncate">쿠폰 사용됨</dt>
          <dd class="mt-1 text-3xl font-semibold text-emerald-600">{{ usedCouponsCount }}</dd>
        </div>
      </div>
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="px-4 py-5 sm:p-6">
          <dt class="text-sm font-medium text-slate-500 truncate">쿠폰 미사용</dt>
          <dd class="mt-1 text-3xl font-semibold text-slate-600">{{ capsules.length - usedCouponsCount }}</dd>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="flex flex-col">
      <div class="-my-2 -mx-4 overflow-x-auto sm:-mx-6 lg:-mx-8">
        <div class="inline-block min-w-full py-2 align-middle md:px-6 lg:px-8">
          <div class="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
            <table class="min-w-full divide-y divide-slate-300">
              <thead class="bg-slate-50">
                <tr>
                  <th scope="col" class="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-slate-900 sm:pl-6">생성일</th>
                  <th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">사용자 정보</th>
                  <th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">비트코인 주소</th>
                  <th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">암호화된 메시지</th>
                  <th scope="col" class="px-3 py-3.5 text-center text-sm font-semibold text-slate-900">쿠폰 사용</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-200 bg-white">
                <tr v-for="capsule in capsules" :key="capsule.id">
                  <td class="whitespace-nowrap py-4 pl-4 pr-3 text-sm text-slate-500 sm:pl-6">
                    {{ formatDate(capsule.created_at) }}
                  </td>
                  <td class="whitespace-nowrap px-3 py-4 text-sm text-slate-900">
                    {{ capsule.user_info || '-' }}
                  </td>
                  <td class="whitespace-nowrap px-3 py-4 text-sm font-mono text-slate-600">
                    {{ shortAddress(capsule.bitcoin_address) }}
                    <button @click="copyText(capsule.bitcoin_address)" class="ml-1 text-slate-400 hover:text-slate-600">
                      <svg class="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3-3m0 0l-3 3m3-3v8m0-12H9.5a1.5 1.5 0 000 3H12" />
                      </svg>
                    </button>
                  </td>
                  <td class="px-3 py-4 text-sm text-slate-500 max-w-xs truncate" :title="capsule.encrypted_message">
                    {{ capsule.encrypted_message }}
                  </td>
                  <td class="whitespace-nowrap px-3 py-4 text-sm text-center">
                    <button
                      @click="toggleCoupon(capsule)"
                      class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                      :class="[capsule.is_coupon_used ? 'bg-emerald-600' : 'bg-slate-200']"
                    >
                      <span class="sr-only">쿠폰 사용 여부</span>
                      <span
                        aria-hidden="true"
                        class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                        :class="[capsule.is_coupon_used ? 'translate-x-5' : 'translate-x-0']"
                      />
                    </button>
                  </td>
                </tr>
                <tr v-if="capsules.length === 0">
                  <td colspan="5" class="px-3 py-8 text-center text-sm text-slate-500">
                    저장된 타임캡슐이 없습니다.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { API_BASE_URL } from '../../api'

const capsules = ref([])

const usedCouponsCount = computed(() => {
  return capsules.value.filter(c => c.is_coupon_used).length
})

async function fetchTimeCapsules() {
  try {
    const response = await fetch(`${API_BASE_URL}/time-capsule/admin/list`)
    if (response.ok) {
      capsules.value = await response.json()
    } else {
      console.error('Failed to fetch time capsules')
    }
  } catch (error) {
    console.error('Error fetching time capsules:', error)
  }
}

async function toggleCoupon(capsule) {
  const newValue = !capsule.is_coupon_used
  // Optimistic update
  capsule.is_coupon_used = newValue
  
  try {
    const response = await fetch(`${API_BASE_URL}/time-capsule/admin/update-coupon/${capsule.id}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ is_coupon_used: newValue }),
    })
    
    if (!response.ok) {
      // Revert if failed
      capsule.is_coupon_used = !newValue
      alert('상태 업데이트에 실패했습니다.')
    }
  } catch (error) {
    console.error('Error updating coupon:', error)
    capsule.is_coupon_used = !newValue
    alert('오류가 발생했습니다.')
  }
}

function formatDate(isoString) {
  if (!isoString) return '-'
  return new Date(isoString).toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function shortAddress(address) {
  if (!address) return ''
  if (address.length < 12) return address
  return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`
}

function copyText(text) {
  if (!text) return
  navigator.clipboard.writeText(text)
    .then(() => alert('복사되었습니다.'))
    .catch(err => console.error('Failed to copy:', err))
}

onMounted(() => {
  fetchTimeCapsules()
})
</script>
