<template>
  <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
    <div class="flex gap-5 sm:gap-8 items-start flex-wrap md:flex-nowrap">
      <div class="flex-shrink-0">
        <div class="w-24 h-24 sm:w-32 sm:h-32 rounded-2xl overflow-hidden border-2 border-slate-200 bg-slate-100 flex items-center justify-center shadow-sm">
          <img
            v-if="imageUrl"
            :src="imageUrl"
            :alt="title"
            class="w-full h-full object-cover"
          />
          <div v-else class="text-4xl">{{ icon }}</div>
        </div>
      </div>
      <div class="flex-1 space-y-2 min-w-0">
        <h4 class="text-lg font-bold text-slate-900 truncate">{{ title }}</h4>
        <div class="text-base text-slate-700 space-y-1.5 leading-relaxed select-text">
          <div v-for="(fact, idx) in facts" :key="idx" class="flex items-center gap-2">
            <span class="w-1 h-1 rounded-full bg-slate-300"></span>
            {{ fact }}
          </div>
        </div>
        <p v-if="story" class="text-base text-slate-700 leading-relaxed mt-3 select-text italic opacity-80">
          "{{ story }}"
        </p>
      </div>

      <!-- Small Radar Chart -->
      <div v-if="radarChart" class="profile-radar hidden md:flex items-center justify-center flex-shrink-0">
        <svg
          :viewBox="`0 0 ${radarChart.size} ${radarChart.size}`"
          :width="radarChart.size"
          :height="radarChart.size"
        >
          <circle
            :cx="radarChart.center"
            :cy="radarChart.center"
            :r="radarChart.maxRadius"
            class="fill-slate-50 stroke-slate-100"
          ></circle>
          <line
            v-for="(axis, index) in radarChart.axes"
            :key="`ax-${index}`"
            :x1="radarChart.center"
            :y1="radarChart.center"
            :x2="axis.x2"
            :y2="axis.y2"
            class="stroke-slate-100"
            stroke-width="1"
          ></line>
          <polygon
            :points="radarChart.polygonPoints"
            class="fill-indigo-400/20 stroke-indigo-400"
            stroke-width="1.5"
          ></polygon>
          <circle
            v-for="marker in radarChart.markers"
            :key="marker.key"
            :cx="marker.x"
            :cy="marker.y"
            r="3"
            class="fill-indigo-400"
          ></circle>
          <text
            v-for="axis in radarChart.axes"
            :key="`lbl-${axis.key}`"
            :x="axis.labelX"
            :y="axis.labelY"
            class="text-[10px] fill-slate-400 font-bold"
            text-anchor="middle"
            dominant-baseline="middle"
          >
            {{ axis.label }}
          </text>
        </svg>
      </div>
    </div>

    <!-- Highlight Panel -->
    <div v-if="highlightedNarrative || highlightLoading" class="rounded-2xl border border-amber-200 bg-amber-50/70 p-4 space-y-3 highlight-panel">
      <div v-if="highlightLoading" class="flex items-center gap-2 text-xs text-amber-700">
        <svg class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        핵심 요약 추출 중...
      </div>
      <div v-else-if="highlightedNarrative" class="prose prose-slate prose-sm max-w-none markdown-highlight select-text">
        <div v-html="renderMarkdown(highlightedNarrative)"></div>
      </div>
      <div v-if="agentProvider" class="text-[10px] text-amber-800 bg-white/70 rounded-lg px-2 py-1 w-fit ml-auto">
        Powered by {{ agentProvider }}
      </div>
    </div>

    <!-- Full Narrative -->
    <div v-if="narrative" class="prose prose-slate max-w-none narrative-content select-text">
      <div v-html="renderMarkdown(narrative)"></div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  title: String,
  icon: { type: String, default: '👤' },
  imageUrl: String,
  facts: Array,
  story: String,
  narrative: String,
  highlightedNarrative: String,
  highlightLoading: Boolean,
  agentProvider: String,
  radarChart: Object
})

function renderMarkdown(text) {
  if (!text) return ''
  let html = text
    .replace(/## (.*)/g, '<h2>$1</h2>')
    .replace(/\n- (.*)/g, '<li>$1</li>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/==(.*?)/g, '<mark>$1</mark>')
    .replace(/\n/g, '<br>')
  
  if (html.includes('<li>')) {
    html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
  }
  return html
}
</script>

<style scoped>
.narrative-content :deep(h2) {
  font-size: 1.125rem;
  font-weight: 800;
  color: #0f172a;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 0.25rem;
}

.narrative-content :deep(p) {
  line-height: 1.7;
  margin-bottom: 1rem;
}

.narrative-content :deep(ul) {
  list-style-type: none;
  padding-left: 0;
}

.narrative-content :deep(li) {
  position: relative;
  padding-left: 1.25rem;
  margin-bottom: 0.5rem;
}

.narrative-content :deep(li::before) {
  content: "•";
  position: absolute;
  left: 0;
  color: #6366f1;
  font-weight: bold;
}

.markdown-highlight :deep(mark) {
  background-color: #fef08a;
  color: #854d0e;
  padding: 0 2px;
  border-radius: 2px;
  font-weight: 600;
}

.markdown-highlight :deep(h2) {
  font-size: 0.875rem;
  font-weight: 800;
  color: #92400e;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}
</style>