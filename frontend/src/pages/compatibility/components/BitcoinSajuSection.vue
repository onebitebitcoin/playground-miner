<template>
  <section class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 space-y-6">
    <div class="flex flex-col gap-3">
      <div class="flex items-start justify-between gap-4">
        <div class="flex-1">
          <p class="text-sm font-semibold text-slate-500 uppercase tracking-wider">비트코인의 사주는?</p>
          <h2 class="text-xl font-bold text-slate-900 mt-1">금(金)이 주력인 디지털 금, 수·화가 극단을 이루는 에너지</h2>
        </div>
      </div>
    </div>
    <div class="grid gap-6 lg:grid-cols-2 items-center">
      <div class="space-y-4">
        <div class="rounded-2xl bg-slate-50 p-5 space-y-3 min-h-[220px]">
          <div v-if="selectedHighlight" class="space-y-3">
            <div class="flex items-center gap-3">
              <span class="text-3xl">{{ selectedHighlight.icon }}</span>
              <div>
                <p class="text-lg font-bold text-slate-900">{{ selectedHighlight.label }}</p>
                <p class="text-sm text-slate-500">{{ selectedHighlight.value }}</p>
              </div>
              <span class="ml-auto text-lg font-black text-slate-900">{{ selectedHighlight.ratio }}%</span>
            </div>
            <div class="w-full bg-slate-200 rounded-full h-2">
              <div
                class="h-2 rounded-full transition-all duration-300"
                :class="selectedHighlight.colorClass"
                :style="{ width: `${selectedHighlight.ratio}%` }"
              ></div>
            </div>
            <p class="text-sm text-slate-600 leading-relaxed">
              {{ selectedHighlight.description }}
            </p>
          </div>
          <div v-else class="text-sm text-slate-500">표시할 핵심 기운이 없습니다.</div>
        </div>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="trait in highlights"
            :key="trait.elementKey"
            type="button"
            class="px-3 py-1.5 rounded-full border text-xs font-semibold transition-all"
            :class="{
              'bg-slate-900 text-white border-slate-900 shadow-sm': trait.elementKey === selectedKey,
              'bg-white text-slate-600 border-slate-200 hover:border-slate-400': trait.elementKey !== selectedKey
            }"
            @click="$emit('selectHighlight', trait.elementKey)"
          >
            {{ trait.label }}
          </button>
        </div>
      </div>
      <div class="rounded-2xl bg-white p-4 flex items-center justify-center">
        <svg
          v-if="radarChart.markers.length"
          :viewBox="`0 0 ${radarChart.size} ${radarChart.size}`"
          :width="radarChart.size"
          :height="radarChart.size"
          class="max-w-full"
        >
          <circle
            :cx="radarChart.center"
            :cy="radarChart.center"
            :r="radarChart.maxRadius"
            class="fill-slate-50 stroke-slate-200"
          ></circle>
          <line
            v-for="(axis, index) in radarChart.axes"
            :key="`axis-${index}`"
            :x1="radarChart.center"
            :y1="radarChart.center"
            :x2="axis.x2"
            :y2="axis.y2"
            class="stroke-slate-200"
            stroke-width="1"
          ></line>
          <polygon
            :points="radarChart.polygonPoints"
            class="fill-indigo-400/20 stroke-indigo-500 radar-polygon"
            stroke-width="2"
          ></polygon>
          <circle
            v-for="marker in radarChart.markers"
            :key="marker.key"
            :cx="marker.x"
            :cy="marker.y"
            :r="marker.active ? 8 : 6"
            :class="marker.active ? 'fill-indigo-500' : 'fill-white stroke-indigo-400'"
            :stroke-width="marker.active ? 3 : 2"
            @click="$emit('selectHighlight', marker.key)"
            class="cursor-pointer transition-all duration-200 radar-point"
          ></circle>
          <text
            v-for="marker in radarChart.markers"
            :key="`percent-${marker.key}`"
            :x="marker.x"
            :y="marker.y - 14"
            class="text-[11px] fill-indigo-500 font-bold pointer-events-none"
            text-anchor="middle"
          >
            {{ marker.ratio }}%
          </text>
          <text
            v-for="marker in radarChart.markers"
            :key="`label-${marker.key}`"
            :x="marker.x"
            :y="marker.y + 20"
            class="text-[10px] fill-slate-400 font-medium pointer-events-none"
            text-anchor="middle"
          >
            {{ marker.label }}
          </text>
        </svg>
      </div>
    </div>
  </section>
</template>

<script setup>
const props = defineProps({
  selectedHighlight: Object,
  selectedKey: String,
  highlights: Array,
  radarChart: Object
})

defineEmits(['selectHighlight'])
</script>

<style scoped>
.radar-polygon {
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}
.radar-point {
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
}
.radar-point:hover {
  filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));
}
</style>
