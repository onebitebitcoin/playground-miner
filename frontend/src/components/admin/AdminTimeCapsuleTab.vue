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
                  <th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">암호화된 메시지</th>
                  <th scope="col" class="px-3 py-3.5 text-center text-sm font-semibold text-slate-900">쿠폰 사용</th>
                  <th scope="col" class="px-3 py-3.5 text-center text-sm font-semibold text-slate-900">작업</th>
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
                  <td class="whitespace-nowrap px-3 py-4 text-sm text-center">
                    <button
                      @click="confirmDelete(capsule)"
                      class="inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs font-medium rounded text-rose-700 bg-rose-100 hover:bg-rose-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-rose-500 transition-colors"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      <span class="ml-1">삭제</span>
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

    <!-- Delete Confirmation Modal -->
    <div v-if="deleteConfirmModal.show" class="fixed z-10 inset-0 overflow-y-auto">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 bg-slate-500 bg-opacity-75 transition-opacity" @click="cancelDelete"></div>
        <span class="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>
        <div class="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
          <div class="sm:flex sm:items-start">
            <div class="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-rose-100 sm:mx-0 sm:h-10 sm:w-10">
              <svg class="h-6 w-6 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
              <h3 class="text-lg leading-6 font-medium text-slate-900">타임캡슐 삭제</h3>
              <div class="mt-2">
                <p class="text-sm text-slate-500">
                  이 타임캡슐을 정말 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
                </p>
                <div class="mt-2 text-xs text-slate-400 bg-slate-50 p-2 rounded">
                  <div><strong>생성일:</strong> {{ formatDate(deleteConfirmModal.capsule?.created_at) }}</div>
                  <div><strong>사용자:</strong> {{ deleteConfirmModal.capsule?.user_info || '-' }}</div>
                </div>
              </div>
            </div>
          </div>
          <div class="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
            <button
              type="button"
              @click="deleteCapsule"
              :disabled="deleteConfirmModal.deleting"
              class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-rose-600 text-base font-medium text-white hover:bg-rose-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-rose-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg v-if="deleteConfirmModal.deleting" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ deleteConfirmModal.deleting ? '삭제 중...' : '삭제' }}
            </button>
            <button
              type="button"
              @click="cancelDelete"
              :disabled="deleteConfirmModal.deleting"
              class="mt-3 w-full inline-flex justify-center rounded-md border border-slate-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              취소
            </button>
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
const deleteConfirmModal = ref({
  show: false,
  capsule: null,
  deleting: false
})

const usedCouponsCount = computed(() => {
  return capsules.value.filter(c => c.is_coupon_used).length
})

async function fetchTimeCapsules() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/time-capsule/admin/list`)
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
    const response = await fetch(`${API_BASE_URL}/api/time-capsule/admin/update-coupon/${capsule.id}`, {
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


function confirmDelete(capsule) {
  deleteConfirmModal.value = {
    show: true,
    capsule: capsule,
    deleting: false
  }
}

function cancelDelete() {
  if (deleteConfirmModal.value.deleting) return
  deleteConfirmModal.value = {
    show: false,
    capsule: null,
    deleting: false
  }
}

async function deleteCapsule() {
  if (!deleteConfirmModal.value.capsule) return

  deleteConfirmModal.value.deleting = true

  try {
    const response = await fetch(`${API_BASE_URL}/api/time-capsule/admin/delete/${deleteConfirmModal.value.capsule.id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (response.ok) {
      // Remove from local list
      capsules.value = capsules.value.filter(c => c.id !== deleteConfirmModal.value.capsule.id)
      // Reset deleting state before calling cancelDelete
      deleteConfirmModal.value.deleting = false
      cancelDelete()
    } else {
      const errorData = await response.json().catch(() => ({}))
      alert(errorData.error || '삭제에 실패했습니다.')
      deleteConfirmModal.value.deleting = false
    }
  } catch (error) {
    console.error('Error deleting time capsule:', error)
    alert('삭제 중 오류가 발생했습니다.')
    deleteConfirmModal.value.deleting = false
  }
}

onMounted(() => {
  fetchTimeCapsules()
})
</script>
