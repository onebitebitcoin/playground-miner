<template>
  <div class="space-y-6">
    <section class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
      <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between mb-6">
        <div>
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wide">궁합 분석 내역</p>
          <h3 class="text-xl font-semibold text-slate-900 mt-1">사용자 분석 기록</h3>
          <p class="text-sm text-slate-500 mt-1">
            저장된 비트코인 궁합 분석 결과를 확인할 수 있습니다.
          </p>
        </div>
        <div class="text-sm text-slate-600">
          총 {{ pagination.total_count }}건
        </div>
      </div>

      <div v-if="loading" class="text-center py-12 text-slate-500">
        분석 내역을 불러오는 중...
      </div>

      <div v-else-if="analyses.length === 0" class="text-center py-12 text-slate-500">
        저장된 분석 내역이 없습니다.
      </div>

      <div v-else class="space-y-4">
        <div
          v-for="analysis in analyses"
          :key="analysis.id"
          class="border border-slate-200 rounded-2xl p-4 hover:border-slate-300 transition-colors"
        >
          <div class="flex flex-col gap-3">
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <div class="flex items-center gap-3 mb-2">
                  <span class="text-lg font-bold text-slate-900">{{ analysis.element }}</span>
                  <span class="text-sm text-slate-600">{{ analysis.zodiac }}</span>
                  <span class="text-xs px-2 py-1 rounded-full bg-slate-100 text-slate-700">{{ analysis.yin_yang }}</span>
                  <span v-if="analysis.gender" class="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-700">
                    {{ analysis.gender === 'male' ? '남성' : '여성' }}
                  </span>
                </div>
                <div class="flex items-center gap-4 text-sm text-slate-600">
                  <span>생년월일: {{ formatDate(analysis.birthdate) }}</span>
                  <span v-if="analysis.birth_time">시간: {{ analysis.birth_time }}</span>
                  <span class="text-xs text-slate-400">IP: {{ analysis.user_ip || 'N/A' }}</span>
                </div>
              </div>
              <div class="text-right">
                <div class="text-xs text-slate-500 mb-1">궁합 점수</div>
                <div class="text-3xl font-black text-slate-900">{{ analysis.score }}</div>
                <div class="text-xs text-slate-600 mt-1">{{ analysis.rating }}</div>
              </div>
            </div>

            <div class="border-t border-slate-100 pt-3">
              <button
                @click="toggleNarrative(analysis.id)"
                class="text-sm text-slate-700 hover:text-slate-900 font-medium flex items-center gap-2"
              >
                <svg class="w-4 h-4 transition-transform" :class="{ 'rotate-90': expandedId === analysis.id }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
                {{ expandedId === analysis.id ? '분석 내용 접기' : '분석 내용 보기' }}
              </button>

              <div v-if="expandedId === analysis.id" class="mt-3 p-4 bg-slate-50 rounded-xl">
                <div class="prose prose-slate prose-sm max-w-none">
                  <pre class="whitespace-pre-wrap text-xs leading-relaxed text-slate-700 font-sans">{{ analysis.narrative }}</pre>
                </div>
              </div>
            </div>

            <div class="text-xs text-slate-400 text-right">
              {{ formatDateTime(analysis.created_at) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="pagination.total_pages > 1" class="mt-6 flex items-center justify-center gap-2">
        <button
          @click="goToPage(pagination.page - 1)"
          :disabled="!pagination.has_previous"
          class="px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          이전
        </button>

        <div class="flex items-center gap-1">
          <button
            v-for="page in visiblePages"
            :key="page"
            @click="goToPage(page)"
            class="px-3 py-2 rounded-lg text-sm"
            :class="page === pagination.page
              ? 'bg-slate-900 text-white font-semibold'
              : 'border border-slate-200 text-slate-700 hover:bg-slate-50'"
          >
            {{ page }}
          </button>
        </div>

        <button
          @click="goToPage(pagination.page + 1)"
          :disabled="!pagination.has_next"
          class="px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          다음
        </button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchCompatibilityAnalysisList } from '../../services/compatibilityService'

const props = defineProps({
  showSuccess: { type: Function, required: true },
  showError: { type: Function, required: true }
})

const loading = ref(true)
const analyses = ref([])
const expandedId = ref(null)
const pagination = ref({
  page: 1,
  per_page: 10,
  total_pages: 0,
  total_count: 0,
  has_next: false,
  has_previous: false
})

const visiblePages = computed(() => {
  const current = pagination.value.page
  const total = pagination.value.total_pages
  const pages = []

  // Show max 7 pages
  let start = Math.max(1, current - 3)
  let end = Math.min(total, current + 3)

  // Adjust if near boundaries
  if (end - start < 6) {
    if (start === 1) {
      end = Math.min(total, start + 6)
    } else if (end === total) {
      start = Math.max(1, end - 6)
    }
  }

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }

  return pages
})

const loadAnalyses = async (page = 1) => {
  loading.value = true
  try {
    const data = await fetchCompatibilityAnalysisList({ page, perPage: 10 })
    analyses.value = data.analyses
    pagination.value = data.pagination
  } catch (error) {
    props.showError(error.message || '분석 내역을 불러올 수 없습니다.')
  } finally {
    loading.value = false
  }
}

const goToPage = (page) => {
  if (page < 1 || page > pagination.value.total_pages) return
  loadAnalyses(page)
}

const toggleNarrative = (id) => {
  expandedId.value = expandedId.value === id ? null : id
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

const formatDateTime = (dateTimeString) => {
  if (!dateTimeString) return 'N/A'
  const date = new Date(dateTimeString)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

onMounted(() => {
  loadAnalyses()
})
</script>
