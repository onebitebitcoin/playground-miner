<template>
  <div class="preset-card yugioh-card" :class="{ 'preset-card-selected': selected, 'card-selected': active }">
    <div class="card-inner">
      <div class="card-border"></div>
      <div class="card-content">
        <div class="card-header">
          <div class="card-name">{{ label }}</div>
        </div>
        <div class="card-image">
          <img
            v-if="imageUrl"
            :src="imageUrl"
            :alt="label"
            class="card-image-actual"
          />
          <div v-else class="card-image-placeholder">{{ placeholderIcon }}</div>
        </div>
        <div class="card-info">
          <div v-if="birthdate" class="card-birthdate">{{ formatDate(birthdate) }}</div>
          <div v-if="showTime && birthtime" class="card-time">{{ birthtime }}</div>
          <div v-if="genderLabel" class="card-gender">{{ genderLabel }}</div>
          <div v-if="selected" class="card-selected-badge">
            <svg class="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
              <path
                fill-rule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-7.01 7.01a1 1 0 01-1.414 0l-3.01-3.01A1 1 0 116.293 9.293L8.99 11.99l6.303-6.303a1 1 0 011.414 0z"
                clip-rule="evenodd"
              />
            </svg>
            <span>선택됨</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  label: String,
  imageUrl: String,
  birthdate: String,
  birthtime: String,
  gender: String,
  placeholderIcon: { type: String, default: '👤' },
  selected: Boolean,
  active: Boolean,
  showTime: { type: Boolean, default: false }
})

const genderLabel = props.gender === 'male' ? '남성' : props.gender === 'female' ? '여성' : ''

function formatDate(dateStr) {
  if (!dateDateStr) return ''
  try {
    const d = new Date(dateStr)
    return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`
  } catch (e) {
    return dateStr
  }
}
</script>

<style scoped>
/* Copied from CompatibilityPage.vue styles */
.yugioh-card {
  width: 140px;
  height: 200px;
  perspective: 1000px;
  cursor: pointer;
  position: relative;
  transition: transform 0.3s ease;
}

.yugioh-card:hover {
  transform: translateY(-5px) rotateY(5deg);
  z-index: 20;
}

.card-inner {
  width: 100%;
  height: 100%;
  background: #1e293b;
  border-radius: 8px;
  padding: 6px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.3), inset 0 0 10px rgba(255,215,0,0.2);
  display: flex;
  flex-direction: column;
  position: relative;
  border: 1px solid #475569;
}

.card-border {
  position: absolute;
  inset: 3px;
  border: 2px solid #94a3b8;
  border-radius: 6px;
  pointer-events: none;
  opacity: 0.5;
}

.card-content {
  background: #f8fafc;
  flex: 1;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  padding: 4px;
  overflow: hidden;
  border: 1px solid #0f172a;
}

.card-header {
  height: 24px;
  background: #e2e8f0;
  border: 1px solid #94a3b8;
  border-radius: 3px;
  display: flex;
  align-items: center;
  padding: 0 6px;
  margin-bottom: 4px;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.1);
}

.card-name {
  font-size: 11px;
  font-weight: 900;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-image {
  height: 90px;
  background: #0f172a;
  border: 2px solid #94a3b8;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.card-image-actual {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-image-placeholder {
  font-size: 40px;
}

.card-info {
  flex: 1;
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  border-radius: 3px;
  padding: 4px;
  font-size: 9px;
  color: #334155;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.card-birthdate, .card-time, .card-gender {
  font-weight: 700;
}

.card-selected-badge {
  margin-top: auto;
  background: #0f172a;
  color: #fbbf24;
  border-radius: 2px;
  padding: 1px 4px;
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 8px;
  font-weight: 900;
  animation: pulse 2s infinite;
}

.preset-card-selected .card-inner {
  background: #0f172a;
  border-color: #fbbf24;
  box-shadow: 0 0 15px rgba(251, 191, 36, 0.4);
}

.preset-card-selected .card-content {
  border-color: #fbbf24;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
</style>
