<template>
  <div class="min-h-screen bg-gray-50 px-3 py-4 sm:px-6 lg:px-12 xl:px-16">
    <div class="mx-auto w-full">
      <!-- Header -->
      <div class="mb-6 md:mb-8">
        <h1 class="text-2xl md:text-3xl font-bold text-gray-900 mb-2">관리자 페이지</h1>
        <p class="text-sm md:text-base text-gray-600">시스템 설정을 관리하고 데이터를 모니터링하세요.</p>
      </div>

      <!-- Access notice (no longer blocks content) -->
      <div v-if="!isAdmin" class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center mb-4">
        <p class="text-yellow-800">관리자 모드가 아닙니다. 일부 변경 기능은 비활성화됩니다.</p>
      </div>

      <!-- Admin Content (always visible; write actions gated below) -->
      <div>
        <!-- Admin Tabs -->
        <div class="mb-6">
          <div class="border-b border-gray-200">
            <nav class="-mb-px flex space-x-4 md:space-x-8 overflow-x-auto" aria-label="Tabs">
              <button
                @click="activeTab = 'mining'"
                :class="[
                  activeTab === 'mining'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-xs md:text-sm'
                ]"
              >
                비트코인 채굴
              </button>
              <button
                @click="activeTab = 'mnemonics'"
                :class="[
                  activeTab === 'mnemonics'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-xs md:text-sm'
                ]"
              >
                지갑
              </button>
              <button
                @click="activeTab = 'routing'"
                :class="[
                  activeTab === 'routing'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-xs md:text-sm'
                ]"
              >
                수수료 계산
              </button>
              <button
                @click="activeTab = 'finance'"
                :class="[
                  activeTab === 'finance'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-xs md:text-sm'
                ]"
              >
                재무 관리
              </button>
              <button
                @click="activeTab = 'compatibility'"
                :class="[
                  activeTab === 'compatibility'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-xs md:text-sm'
                ]"
              >
                궁합
              </button>
              <button
                @click="activeTab = 'time-capsule'"
                :class="[
                  activeTab === 'time-capsule'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-xs md:text-sm'
                ]"
              >
                타임캡슐
              </button>
              <button
                @click="activeTab = 'sidebar'"
                :class="[
                  activeTab === 'sidebar'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-xs md:text-sm'
                ]"
              >
                설정
              </button>
            </nav>
          </div>
        </div>

        <AdminMnemonicsTab
          v-if="activeTab === 'mnemonics'"
          :is-admin="isAdmin"
          :show-success="showSuccess"
          :show-error="showError"
        />
        <AdminRoutingTab
          v-else-if="activeTab === 'routing'"
          :is-admin="isAdmin"
          :show-success="showSuccess"
          :show-error="showError"
        />

        <AdminMiningTab
          v-else-if="activeTab === 'mining'"
          :is-admin="isAdmin"
          :show-success="showSuccess"
          :show-error="showError"
        />

        <AdminSettingsTab
          v-else-if="activeTab === 'sidebar'"
          :is-admin="isAdmin"
          :show-success="showSuccess"
          :show-error="showError"
        />

        <AdminFinanceTab
          v-else-if="activeTab === 'finance'"
          :is-admin="isAdmin"
          :show-success="showSuccess"
          :show-error="showError"
        />
        <AdminCompatibilityTab
          v-else-if="activeTab === 'compatibility'"
          :is-admin="isAdmin"
          :show-success="showSuccess"
          :show-error="showError"
        />
        <AdminTimeCapsuleTab
          v-else-if="activeTab === 'time-capsule'"
          :is-admin="isAdmin"
          :show-success="showSuccess"
          :show-error="showError"
        />

      </div>

      <!-- Notifications -->
      <div
        v-if="successMessage || errorMessage"
        class="fixed top-4 left-1/2 -translate-x-1/2 transform z-50 flex flex-col items-center space-y-2 w-full max-w-md px-4"
      >
        <div v-if="successMessage" class="bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg text-center w-full">
          {{ successMessage }}
        </div>
        <div v-if="errorMessage" class="bg-red-600 text-white px-4 py-2 rounded-lg shadow-lg text-center w-full">
          {{ errorMessage }}
        </div>
      </div>


    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import AdminMnemonicsTab from '../components/admin/AdminMnemonicsTab.vue'
import AdminRoutingTab from '../components/admin/AdminRoutingTab.vue'
import AdminFinanceTab from '../components/admin/AdminFinanceTab.vue'
import AdminSettingsTab from '../components/admin/AdminSettingsTab.vue'
import AdminMiningTab from '../components/admin/AdminMiningTab.vue'
import AdminCompatibilityTab from '../components/admin/AdminCompatibilityTab.vue'
import AdminTimeCapsuleTab from '../components/admin/AdminTimeCapsuleTab.vue'
import { useNotification } from '../composables/useNotification'

const activeTab = ref('mining')
const { successMessage, errorMessage, showSuccess, showError } = useNotification()

const isAdmin = computed(() => {
  const nickname = localStorage.getItem('nickname')
  const adminStatus = localStorage.getItem('isAdmin')
  return nickname === 'admin' && adminStatus === 'true'
})
</script>
