<template>
  <div class="bg-slate-900 rounded-2xl p-5 sm:p-6 shadow-inner flex flex-col gap-4">
    <div class="flex items-center justify-between gap-4">
      <div class="relative flex-1 min-h-[3.5rem] sm:min-h-[3.8rem] flex items-center">
        <p
          class="typewriter-text text-2xl sm:text-3xl font-black leading-tight tracking-tight text-[#ffd400] flex flex-wrap items-center gap-2"
          :class="heroAnimationActive ? 'opacity-0' : 'opacity-100 transition-opacity duration-300'"
          :key="heroAnimationKey"
        >
          <span
            class="editable-chunk"
            contenteditable="true"
            spellcheck="false"
            role="textbox"
            aria-label="투자 시점(년 전)"
            @focus="handleEditableFocus"
            @keydown="handleEditableKeydown"
            @paste="handleEditablePaste"
            @blur="handleBlur('year', $event)"
          >{{ investmentYearsAgo }}</span>
          <span>&nbsp;년 전에&nbsp;</span>
          <span class="font-black">비트코인&nbsp;</span>
          <span
            class="editable-chunk"
            contenteditable="true"
            spellcheck="false"
            role="textbox"
            aria-label="투자 금액"
            @focus="handleEditableFocus"
            @keydown="handleEditableKeydown"
            @paste="handleEditablePaste"
            @blur="handleBlur('amount', $event)"
          >{{ formattedInvestmentAmountNumber }}</span>
          <span>&nbsp;만원을 샀다면 지금 얼마일까?</span>
        </p>

        <p
          v-if="heroAnimationActive"
          class="hero-typewriter-overlay text-2xl sm:text-3xl font-black leading-tight tracking-tight text-[#ffd400] flex items-center"
          aria-hidden="true"
        >
          {{ displayedHeroText }}<span class="hero-typewriter-cursor"></span>
        </p>
      </div>
      
      <button
        @click="$emit('search')"
        :disabled="loading || customAssetResolving"
        class="p-3 rounded-xl text-[#ffd400] hover:text-[#ffc400] active:scale-95 transition-all flex-shrink-0 group disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 search-button-glow"
        :class="{'animate-attention': searchButtonAttention}"
        aria-label="분석 시작"
      >
        <svg class="w-6 h-6 group-hover:rotate-12 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
        </svg>
      </button>
    </div>
    
    <slot name="extra"></slot>
  </div>
</template>

<script setup>
const props = defineProps({
  investmentYearsAgo: [Number, String],
  investmentAmount: [Number, String],
  formattedInvestmentAmountNumber: String,
  heroAnimationActive: Boolean,
  displayedHeroText: String,
  heroAnimationKey: Number,
  loading: Boolean,
  customAssetResolving: Boolean,
  searchButtonAttention: Boolean
})

const emit = defineEmits(['update:years', 'update:amount', 'search'])

function handleEditableFocus(event) {
  selectEditableContents(event.target)
}

function handleEditableKeydown(event) {
  if (event.key === 'Enter') {
    event.preventDefault()
    event.currentTarget?.blur()
    emit('search')
    return
  }

  const allowedKeys = [
    'Backspace', 'Delete', 'Tab', 'Escape',
    'ArrowLeft', 'ArrowRight', 'Home', 'End'
  ]
  if (allowedKeys.includes(event.key)) return
  if (event.ctrlKey || event.metaKey) return

  if (!/^\d$/.test(event.key)) {
    event.preventDefault()
  }
}

function handleEditablePaste(event) {
  event.preventDefault()
  const clipboard = (event.clipboardData || window.clipboardData)
  if (!clipboard) return
  const text = clipboard.getData('text')
  document.execCommand('insertText', false, text.replace(/[^\d]/g, ''))
}

function handleBlur(field, event) {
  const rawText = event.target.innerText.replace(/[^\d]/g, '')
  const parsed = rawText ? parseInt(rawText, 10) : 0
  
  if (field === 'year') {
    emit('update:years', parsed || 1)
  } else if (field === 'amount') {
    emit('update:amount', parsed || 1)
  }
}

function selectEditableContents(el) {
  if (!el || !window.getSelection) return
  const selection = window.getSelection()
  if (!selection) return
  const range = document.createRange()
  range.selectNodeContents(el)
  selection.removeAllRanges()
  selection.addRange(range)
}
</script>

<style scoped>
.editable-chunk {
  display: inline-block;
  min-width: 1ch;
  border-bottom: 2px dashed rgba(255, 212, 0, 0.4);
  cursor: text;
  transition: all 0.2s ease;
  outline: none;
  padding: 0 4px;
  border-radius: 4px;
}

.editable-chunk:hover {
  background: rgba(255, 212, 0, 0.1);
  border-bottom-color: rgba(255, 212, 0, 0.8);
}

.editable-chunk:focus {
  background: rgba(255, 212, 0, 0.2);
  border-bottom-style: solid;
  border-bottom-color: #ffd400;
  box-shadow: 0 0 0 4px rgba(255, 212, 0, 0.1);
}

@keyframes attention {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); filter: brightness(1.2); }
}

.animate-attention {
  animation: attention 2s infinite ease-in-out;
}

.search-button-glow {
  box-shadow: 0 0 20px rgba(255, 212, 0, 0.4);
}

.search-button-glow:hover:not(:disabled) {
  box-shadow: 0 0 30px rgba(255, 212, 0, 0.6), 0 0 60px rgba(255, 212, 0, 0.3);
}

.search-button-glow:disabled {
  box-shadow: none;
}

.hero-typewriter-cursor {
  display: inline-block;
  width: 3px;
  height: 1.2em;
  background-color: #ffd400;
  margin-left: 4px;
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  from, to { opacity: 1; }
  50% { opacity: 0; }
}
</style>
