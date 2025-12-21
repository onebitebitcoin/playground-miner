<template>
<section class="space-y-6">
  <div
    v-if="toastSuccess || toastError"
    class="fixed top-4 left-1/2 -translate-x-1/2 transform z-[10000] flex flex-col items-center space-y-2 w-full max-w-md px-4"
  >
    <div v-if="toastSuccess" class="bg-emerald-600 text-white px-4 py-2 rounded-lg shadow-lg text-center w-full">
      {{ toastSuccess }}
    </div>
    <div v-if="toastError" class="bg-rose-600 text-white px-4 py-2 rounded-lg shadow-lg text-center w-full">
      {{ toastError }}
    </div>
  </div>
    <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
      <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 flex flex-col gap-5">
        <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h3 class="text-lg font-semibold text-slate-900">
              {{ mode === 'seal' ? '1. 나만의 키와 소망 입력' : '1. 봉인 해제하기' }}
            </h3>
            <p class="text-sm text-slate-500 mt-1">
              {{ mode === 'seal' ? '타임캡슐을 여는 열쇠와 그 안에 담을 메시지를 적어주세요.' : '봉인된 타임캡슐을 나만의 키로 열어보세요.' }}
            </p>
          </div>
        </div>

        <div class="space-y-4">
          <div>
            <label for="secret-key" class="text-sm font-medium text-slate-700 flex items-center gap-1.5">
              <svg class="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
              </svg>
              나만의 키
            </label>
            <div class="relative mt-1">
              <input
                id="secret-key"
                :type="showSecret ? 'text' : 'password'"
                v-model="secretKey"
                autocomplete="off"
                class="w-full rounded-xl border border-slate-300 px-4 py-3 pr-12 text-sm focus:border-slate-900 focus:ring-2 focus:ring-slate-200"
                placeholder="나만 알고 있는 암호키"
              />
              <button
                type="button"
                class="absolute inset-y-0 right-0 px-3 text-slate-500 hover:text-slate-800"
                @click="toggleSecretVisibility"
                aria-label="나만의 키 표시 전환"
              >
                <svg v-if="showSecret" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.976 9.976 0 011.563-3.029M6.22 6.22A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a9.966 9.966 0 01-2.164 3.368M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3l18 18" />
                </svg>
                <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M2.458 12C3.732 7.943 7.522 5 12 5c4.478 0 8.268 2.943 9.543 7-1.275 4.057-5.065 7-9.543 7-4.478 0-8.268-2.943-9.542-7z"
                  />
                </svg>
              </button>
            </div>
          </div>

          <!-- Seal Mode: Message Input -->
          <div v-if="mode === 'seal'">
            <div class="flex items-center justify-between">
              <label for="wish-message" class="text-sm font-medium text-slate-700 flex items-center gap-1.5">
                <svg class="w-4 h-4 text-rose-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
                소망 메시지
              </label>
              <span
                class="text-xs"
                :class="wishMessage.length >= messageLimit ? 'text-rose-500' : 'text-slate-500'"
              >
                {{ wishMessage.length }} / {{ messageLimit }}자
              </span>
            </div>
            <div class="relative">
              <textarea
                id="wish-message"
                v-model="wishMessage"
                :maxlength="messageLimit"
                rows="5"
                class="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm focus:border-slate-900 focus:ring-2 focus:ring-slate-200 transition-all"
                :class="sealing ? 'opacity-60 pointer-events-none' : ''"
                placeholder="타임캡슐에 담고 싶은 소망을 적어보세요"
              ></textarea>
              <div v-if="sealing" class="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div class="bg-slate-900/80 text-white px-4 py-2 rounded-lg flex items-center gap-2">
                  <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span class="text-sm font-medium">메시지 암호화 중...</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Unseal Mode: Encrypted Data Input -->
          <div v-if="mode === 'unseal'">
            <label for="encrypted-input" class="text-sm font-medium text-slate-700">암호화된 데이터</label>
            <div class="relative mt-1">
              <textarea
                id="encrypted-input"
                v-model="encryptedDataInput"
                rows="5"
                class="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm font-mono focus:border-slate-900 focus:ring-2 focus:ring-slate-200 transition-all"
                :class="opening ? 'opacity-60 pointer-events-none' : ''"
                placeholder="봉인된 타임캡슐 데이터를 붙여넣으세요"
              ></textarea>
            </div>
          </div>
        </div>

        <div class="flex flex-col gap-3">
          

          <!-- Seal Mode Button -->
          <button
            v-if="mode === 'seal' && !sealed"
            type="button"
            class="w-full sm:w-auto px-5 py-2 rounded-xl text-sm font-semibold text-white shadow-sm transition relative overflow-hidden text-center"
            :class="[
              computing
                ? 'bg-emerald-300 cursor-progress'
                : hasExistingCapsule
                  ? 'bg-slate-300 cursor-not-allowed text-slate-600'
                  : primarySealDisabled
                    ? 'bg-slate-200 text-slate-500 cursor-not-allowed'
                    : 'bg-emerald-600 hover:bg-emerald-500',
              hasExistingCapsule ? 'opacity-70' : ''
            ]"
            :disabled="primarySealDisabled"
            :title="hasExistingCapsule ? existingCapsuleWarning : ''"
            @click="triggerImmediateComputation"
          >
            <span v-if="sealing" class="flex items-center justify-center gap-2">
              <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              봉인 중...
            </span>
            <span v-else-if="computing">계산 중...</span>
            <span v-else class="flex items-center justify-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              {{ hasExistingCapsule ? '이미 봉인됨' : '바로 봉인하기' }}
            </span>
          </button>

          <!-- Save Button (Seal Mode) -->
          <button
            v-if="mode === 'seal' && sealed"
            type="button"
            class="w-full sm:w-auto px-5 py-2 rounded-xl text-sm font-semibold text-white bg-emerald-500 hover:bg-emerald-600 shadow-sm transition relative overflow-hidden text-center"
            :disabled="saving || saved || hasExistingCapsule"
            :title="hasExistingCapsule ? existingCapsuleWarning : ''"
            @click="handleSave"
          >
            <span v-if="saving" class="flex items-center justify-center gap-2">
              <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              저장 중...
            </span>
            <span v-else-if="saved" class="flex items-center justify-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              저장 완료!
            </span>
            <span v-else class="flex items-center justify-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3-3m0 0l-3 3m3-3v8m0-12H9.5a1.5 1.5 0 000 3H12" />
              </svg>
              저장하기
            </span>
          </button>

          <!-- Unseal Mode Button -->
          <button
            v-if="mode === 'unseal'"
            type="button"
            class="w-full sm:w-auto px-5 py-2 rounded-xl text-sm font-semibold text-white shadow-sm transition relative overflow-hidden text-center"
            :class="[
              opening ? 'bg-rose-300 cursor-progress' : 'bg-rose-500 hover:bg-rose-600'
            ]"
            :disabled="!secretKey.trim() || !encryptedDataInput.trim() || opening"
            @click="handleUnseal"
          >
            <span v-if="opening" class="flex items-center justify-center gap-2">
              <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              봉인 해제 중...
            </span>
            <span v-else class="flex items-center justify-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z" />
              </svg>
              봉인 해제하기
            </span>
          </button>
        </div>
        <div
          v-if="mode === 'unseal' && decryptedMessage"
          class="bg-emerald-50 border border-emerald-100 rounded-xl px-4 py-3 text-sm text-emerald-800 fade-in-up"
        >
          <p class="text-xs font-semibold uppercase tracking-wide text-emerald-700 mb-2">봉인 해제된 소망 메시지</p>
          <p class="whitespace-pre-wrap">{{ decryptedMessage }}</p>
        </div>
        <div
          v-if="mode === 'seal' && existingCapsuleWarning"
          class="mt-1 text-xs text-rose-600 bg-rose-50 border border-rose-100 rounded-xl px-3 py-2"
        >
          {{ existingCapsuleWarning }}
        </div>

        <div v-if="errorMessage" class="text-sm text-rose-600 bg-rose-50 border border-rose-100 rounded-xl px-4 py-2">
          {{ errorMessage }}
        </div>

        <div v-if="sealed" class="text-sm text-emerald-700 bg-emerald-50 border border-emerald-100 rounded-xl px-4 py-3 space-y-2 fade-in-up">
          <div class="flex items-center justify-between gap-3 flex-wrap">
            <p class="text-xs font-semibold text-emerald-700 flex items-center gap-2">
              <span class="uppercase tracking-wide">암호화된 데이터</span>
              <span v-if="encryptedHashSizeLabel" class="text-[10px] font-medium text-emerald-500 normal-case tracking-normal">
                ({{ encryptedHashSizeLabel }})
              </span>
            </p>
            <button
              type="button"
              class="text-slate-700 hover:text-slate-900"
              :aria-label="copiedEncryptedStatus ? '암호화된 메시지 복사됨' : '암호화된 메시지 복사'"
              @click="copyEncryptedHash"
            >
              <svg v-if="!copiedEncryptedStatus" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <svg v-else class="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </button>
          </div>
          <p class="font-mono text-slate-900 break-all">{{ encryptedHash }}</p>
        </div>
      </div>

      <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 flex flex-col gap-5">
        <h3 class="text-lg font-semibold text-slate-900">2. 타임캡슐</h3>

        <div class="space-y-4">
          <!-- Time Capsule Visualization -->
          <div class="flex justify-center items-center py-8 relative" :class="[sealing ? 'sealing' : '', opening ? 'opening' : '']">
            <!-- Background Glow -->
            <div
              class="absolute inset-0 flex items-center justify-center pointer-events-none"
              :class="capsuleVisualLocked ? 'capsule-bg-glow' : ''"
            >
              <div class="w-48 h-48 rounded-full bg-gradient-to-br from-emerald-100/30 to-indigo-100/30 blur-3xl"></div>
            </div>

            <div class="relative w-64 h-80 z-10">
              <!-- SVG Time Capsule -->
              <svg viewBox="0 0 200 300" class="w-full h-full">
                <!-- Capsule Shadow -->
                <ellipse cx="100" cy="250" rx="70" ry="15" fill="#1e293b" opacity="0.2"/>
                
                <!-- Capsule Interior (Hole) -->
                <ellipse cx="100" cy="120" rx="70" ry="20" fill="#0f172a"/>

                <!-- Message Paper (floating into capsule when sealing) -->
                <g v-if="sealing" class="message-paper-sealing">
                  <rect x="60" y="60" width="80" height="40" rx="4" fill="#fff" stroke="#f59e0b" stroke-width="2"/>
                  <line x1="68" y1="70" x2="132" y2="70" stroke="#f59e0b" stroke-width="1.5"/>
                  <line x1="68" y1="78" x2="132" y2="78" stroke="#fbbf24" stroke-width="1"/>
                  <line x1="68" y1="86" x2="120" y2="86" stroke="#fbbf24" stroke-width="1"/>
                  <line x1="100" y1="60" x2="100" y2="100" stroke="#f59e0b" stroke-width="0.5" opacity="0.3"/>
                  <circle cx="125" cy="68" r="2" fill="#fbbf24" opacity="0.8">
                    <animate attributeName="opacity" values="0.3;1;0.3" dur="1s" repeatCount="indefinite"/>
                  </circle>
                </g>

                <!-- Message Paper (floating out of capsule when opening) -->
                <g v-if="opening" class="message-paper-opening">
                  <rect x="60" y="160" width="80" height="40" rx="4" fill="#fff" stroke="#10b981" stroke-width="2"/>
                  <line x1="68" y1="170" x2="132" y2="170" stroke="#10b981" stroke-width="1.5"/>
                  <line x1="68" y1="178" x2="132" y2="178" stroke="#10b981" stroke-width="1"/>
                  <line x1="68" y1="186" x2="120" y2="186" stroke="#10b981" stroke-width="1"/>
                  <!-- Fold mark -->
                  <line x1="100" y1="160" x2="100" y2="200" stroke="#10b981" stroke-width="0.5" opacity="0.3"/>
                  <!-- Shine effect -->
                  <circle cx="135" cy="165" r="3" fill="#10b981" opacity="0.6">
                    <animate attributeName="opacity" values="0.3;0.9;0.3" dur="0.8s" repeatCount="indefinite"/>
                  </circle>
                  <circle cx="140" cy="172" r="2" fill="#10b981" opacity="0.4">
                    <animate attributeName="opacity" values="0.2;0.7;0.2" dur="1s" repeatCount="indefinite"/>
                  </circle>
                  <circle cx="132" cy="195" r="2.5" fill="#10b981" opacity="0.5">
                    <animate attributeName="opacity" values="0.2;0.8;0.2" dur="0.9s" repeatCount="indefinite"/>
                  </circle>
                </g>

                <!-- Capsule Body -->
                <path d="M 30 120 L 170 120 L 170 180 A 70 70 0 0 1 30 180 Z" fill="url(#capsuleGradient)" stroke="#334155" stroke-width="2"/>

                <!-- Capsule Lid -->
                <g :class="
                  opening || opened ? 'lid-opening' :
                  sealed ? 'lid-closing' :
                  shouldShowClosedLid ? 'lid-closed' :
                  'lid-open'
                ">
                  <ellipse cx="100" cy="120" rx="70" ry="20" fill="url(#lidGradient)" stroke="#334155" stroke-width="2"/>
                  <ellipse cx="100" cy="115" rx="65" ry="18" fill="#475569"/>
                  <circle cx="100" cy="115" r="8" fill="#94a3b8"/>
                </g>

                <!-- Lock Icon (appears when sealed) -->
                <g v-if="capsuleVisualLocked" class="lock-icon" :class="sealed ? 'lock-appear' : ''">
                  <circle cx="100" cy="180" r="20" fill="#10b981" opacity="0.2"/>
                  <path d="M 95 175 L 95 170 Q 95 162 100 162 Q 105 162 105 170 L 105 175 M 92 175 L 108 175 Q 110 175 110 177 L 110 188 Q 110 190 108 190 L 92 190 Q 90 190 90 188 L 90 177 Q 90 175 92 175 Z"
                        fill="#10b981" stroke="#059669" stroke-width="1"/>
                  <circle cx="100" cy="183" r="2" fill="#fff"/>
                </g>

                <!-- Gradients -->
                <defs>
                  <linearGradient id="capsuleGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#64748b;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#334155;stop-opacity:1" />
                  </linearGradient>
                  <linearGradient id="lidGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#94a3b8;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#64748b;stop-opacity:1" />
                  </linearGradient>
                </defs>
              </svg>

              <!-- Sparkles effect when sealed -->
              <div v-if="sealed" class="absolute inset-0 pointer-events-none">
                <div
                  v-for="i in 12"
                  :key="`seal-${i}`"
                  class="sparkle"
                  :style="{
                    left: `${15 + Math.random() * 70}%`,
                    top: `${20 + Math.random() * 60}%`,
                    animationDelay: `${i * 0.08}s`,
                    fontSize: `${16 + Math.random() * 10}px`
                  }"
                >{{ ['✨', '💫', '⭐', '🌟'][Math.floor(Math.random() * 4)] }}</div>
              </div>

              <!-- Star burst effect when opened -->
              <div v-if="opened" class="absolute inset-0 pointer-events-none">
                <div
                  v-for="i in 15"
                  :key="`open-${i}`"
                  class="sparkle-burst"
                  :style="{
                    left: '50%',
                    top: '50%',
                    '--angle': `${i * (360 / 15)}deg`,
                    animationDelay: `${i * 0.05}s`,
                    fontSize: `${18 + Math.random() * 12}px`
                  }"
                >{{ ['✨', '💫', '⭐', '🌟', '💎', '🎊'][Math.floor(Math.random() * 6)] }}</div>
            </div>
          </div>
        </div>

          <!-- Capsule Status Text -->
        <div class="text-center mt-6">
          <p class="text-2xl font-extrabold transition-colors duration-300 tracking-tight">
            <span v-if="opening" class="text-indigo-600 flex items-center justify-center gap-3 animate-pulse">
              <svg class="w-7 h-7 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              타임캡슐 여는 중...
            </span>
            <span v-else-if="opened" class="text-emerald-600 flex items-center justify-center gap-3">
              <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z" />
              </svg>
              열림 (OPEN)
            </span>
            <span v-else-if="sealing" class="text-amber-600 flex items-center justify-center gap-3 animate-pulse">
              <svg class="w-7 h-7 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              봉인 중...
            </span>
            <span v-else-if="capsuleVisualLocked" class="text-rose-600 flex items-center justify-center gap-3 bg-rose-50 px-4 py-2 rounded-full border border-rose-200">
              <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              봉인됨 (LOCKED)
            </span>
            <span v-else class="text-emerald-600 flex items-center justify-center gap-3 bg-emerald-50 px-4 py-2 rounded-full border border-emerald-200">
              <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z" />
              </svg>
              열림 (OPEN)
            </span>
            </p>
          </div>

        </div>
      </div>
    </div>

    <!-- All Time Capsules List -->
    <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-slate-900">전체 타임캡슐 목록</h3>
        <button
          @click="fetchCapsules(1)"
          class="inline-flex items-center justify-center w-10 h-10 rounded-full text-slate-600 hover:text-slate-900 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-400"
          aria-label="타임캡슐 목록 새로고침"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>

      <div class="hidden sm:block">
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-slate-300">
            <thead class="bg-slate-50">
              <tr>
                <th scope="col" class="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-slate-900 sm:pl-6">사용자</th>
                <th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">암호화된 메시지</th>
                <th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">
                  타임캡슐 주소
                  <span class="block text-xs font-normal text-slate-500">(From/To)</span>
                </th>
              <th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">생성일</th>
              <th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">트랜잭션</th>
              <th scope="col" class="px-3 py-3.5 text-center text-sm font-semibold text-slate-900">쿠폰 사용</th>
              <th scope="col" class="px-3 py-3.5 text-center text-sm font-semibold text-slate-900">작업</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-200 bg-white">
              <tr
                v-for="capsule in capsules"
                :key="capsule.id"
                :class="[
                  'transition-colors',
                  isMyCapsule(capsule) ? 'bg-emerald-50/80 text-slate-900 ring-1 ring-emerald-100' : 'opacity-60 hover:opacity-80'
                ]"
              >
                <td class="whitespace-nowrap py-4 pl-4 pr-3 text-sm text-slate-600 sm:pl-6">
                  {{ capsule.user_info || '-' }}
                </td>
                <td class="px-3 py-4 text-sm text-slate-500 max-w-xs">
                  <div class="flex items-center gap-2">
                    <div class="flex items-center gap-2 flex-1 min-w-0 flex-wrap">
                      <span class="truncate flex-1 min-w-0" :title="capsule.encrypted_message">
                        {{ capsule.encrypted_message }}
                      </span>
                      <span
                        v-if="capsule.encrypted_message"
                        class="text-xs text-slate-400 whitespace-nowrap"
                      >
                        {{ formatByteLength(capsule.encrypted_message) }}
                      </span>
                    </div>
                    <button
                      v-if="capsule.encrypted_message"
                      type="button"
                      class="flex-shrink-0 inline-flex items-center justify-center w-6 h-6 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-slate-400 transition"
                      :aria-label="copiedCapsuleId === capsule.id ? '복사됨' : '암호화된 메시지 복사'"
                      :title="copiedCapsuleId === capsule.id ? '복사 완료' : '암호화된 메시지 복사'"
                      @click="copyCapsuleEncryptedMessage(capsule)"
                    >
                      <svg
                        v-if="copiedCapsuleId !== capsule.id"
                        class="w-3.5 h-3.5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                        />
                      </svg>
                      <svg
                        v-else
                        class="w-3.5 h-3.5 text-emerald-500"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                    </button>
                  </div>
                </td>
                <td class="px-3 py-4 text-sm text-slate-500">
                  <span v-if="capsule.bitcoin_address" class="break-all select-text">
                    {{ capsule.bitcoin_address }}
                  </span>
                  <span v-else class="text-xs text-slate-400">주소 할당 대기중</span>
                </td>
                <td class="whitespace-nowrap px-3 py-4 text-sm text-slate-500">
                  {{ formatDate(capsule.created_at) }}
                </td>
                <td class="px-3 py-4 text-sm text-slate-500">
                  <div v-if="capsule.broadcast_txid" class="flex flex-col">
                    <a
                      :href="explorerUrlForTx(capsule.broadcast_txid)"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="text-indigo-600 hover:text-indigo-800 font-semibold w-fit"
                    >
                      {{ shortTxid(capsule.broadcast_txid) }}
                    </a>
                    <span class="text-xs text-slate-400 mt-0.5">{{ formatDate(capsule.broadcasted_at) }}</span>
                  </div>
                  <span v-else class="text-xs text-slate-400">전파 내역 없음</span>
                </td>
                <td class="whitespace-nowrap px-3 py-4 text-sm text-center">
                  <button
                    disabled
                    class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-not-allowed rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out opacity-60"
                    :class="[capsule.is_coupon_used ? 'bg-emerald-600' : 'bg-slate-200']"
                  >
                    <span class="sr-only">쿠폰 사용 여부 (읽기 전용)</span>
                    <span
                      aria-hidden="true"
                      class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                      :class="[capsule.is_coupon_used ? 'translate-x-5' : 'translate-x-0']"
                    />
                  </button>
                </td>
                <td class="whitespace-nowrap px-3 py-4 text-sm">
                  <div class="flex flex-wrap items-center justify-center gap-2">
                    <button
                      v-if="canDeleteCapsule(capsule)"
                      @click="confirmDeleteCapsule(capsule)"
                      class="inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-semibold text-white bg-rose-500 hover:bg-rose-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-rose-500 transition"
                      aria-label="타임캡슐 삭제"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7H5m3 0V5a2 2 0 012-2h4a2 2 0 012 2v2m2 0v12a2 2 0 01-2 2H8a2 2 0 01-2-2V7m3 4v6m4-6v6" />
                      </svg>
                      삭제
                    </button>
                    <button
                      type="button"
                      @click="openSealModal(capsule)"
                      class="inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition disabled:opacity-40 disabled:cursor-not-allowed"
                      :disabled="!canSealCapsule(capsule)"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L7.5 20.5H4v-3.5l12.732-12.732z" />
                      </svg>
                      봉인
                    </button>
                  </div>
                  <p v-if="!canDeleteCapsule(capsule)" class="text-xs text-slate-400 mt-1 text-center">삭제 권한 없음</p>
                  <p v-if="!canSealCapsule(capsule)" class="text-xs text-amber-500 mt-1 text-center">주소·메시지가 필요합니다.</p>
                </td>
              </tr>
              <tr v-if="capsules.length === 0">
                <td colspan="7" class="px-3 py-8 text-center text-sm text-slate-500">
                  저장된 타임캡슐이 없습니다.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="sm:hidden">
        <div v-if="capsules.length === 0" class="px-3 py-6 text-center text-sm text-slate-500 border border-dashed border-slate-200 rounded-xl">
          저장된 타임캡슐이 없습니다.
        </div>
        <div v-else class="space-y-4">
          <article
            v-for="capsule in capsules"
            :key="`mobile-${capsule.id}`"
            :class="[
              'rounded-2xl border p-4 shadow-sm space-y-4 transition-colors',
              isMyCapsule(capsule) ? 'bg-emerald-50/80 ring-1 ring-emerald-100 text-slate-900 border-emerald-200' : 'bg-white border-slate-200 text-slate-600'
            ]"
          >
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="text-sm font-semibold text-slate-900">{{ capsule.user_info || '-' }}</p>
                <p class="text-xs text-slate-500 mt-0.5">{{ formatDate(capsule.created_at) }}</p>
              </div>
              <span
                class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
                :class="capsule.is_coupon_used ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'"
              >
                {{ capsule.is_coupon_used ? '쿠폰 사용' : '쿠폰 미사용' }}
              </span>
            </div>

            <div class="space-y-1">
              <p class="text-xs font-semibold text-slate-500">암호화된 메시지</p>
              <div class="flex items-start gap-2">
                <div class="flex-1 min-w-0">
                  <p class="text-sm text-slate-600 break-words" :title="capsule.encrypted_message">
                    {{ capsule.encrypted_message || '메시지 없음' }}
                  </p>
                  <p v-if="capsule.encrypted_message" class="text-xs text-slate-400 mt-1">
                    {{ formatByteLength(capsule.encrypted_message) }}
                  </p>
                </div>
                <button
                  v-if="capsule.encrypted_message"
                  type="button"
                  class="flex-shrink-0 inline-flex items-center justify-center w-8 h-8 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-slate-400 transition"
                  :aria-label="copiedCapsuleId === capsule.id ? '복사됨' : '암호화된 메시지 복사'"
                  :title="copiedCapsuleId === capsule.id ? '복사 완료' : '암호화된 메시지 복사'"
                  @click="copyCapsuleEncryptedMessage(capsule)"
                >
                  <svg
                    v-if="copiedCapsuleId !== capsule.id"
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                    />
                  </svg>
                  <svg
                    v-else
                    class="w-4 h-4 text-emerald-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </button>
              </div>
            </div>

            <div class="space-y-1">
              <p class="text-xs font-semibold text-slate-500">
                타임캡슐 주소 <span class="text-slate-400">(From/To)</span>
              </p>
              <p v-if="capsule.bitcoin_address" class="text-sm text-slate-600 break-all select-text">
                {{ capsule.bitcoin_address }}
              </p>
              <p v-else class="text-xs text-slate-400">주소 할당 대기중</p>
            </div>

            <div class="space-y-1">
              <p class="text-xs font-semibold text-slate-500">트랜잭션</p>
              <div v-if="capsule.broadcast_txid" class="flex items-center justify-between gap-3">
                <div>
                  <a
                    :href="explorerUrlForTx(capsule.broadcast_txid)"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="text-indigo-600 hover:text-indigo-800 text-sm font-semibold"
                  >
                    {{ shortTxid(capsule.broadcast_txid) }}
                  </a>
                  <p class="text-[11px] text-slate-400 mt-0.5">{{ formatDate(capsule.broadcasted_at) }}</p>
                </div>
                <svg class="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </div>
              <p v-else class="text-xs text-slate-400">전파 내역 없음</p>
            </div>

            <div class="flex items-center justify-between pt-2">
              <div class="text-xs text-slate-500">
                ID: <span class="font-semibold text-slate-700">{{ capsule.id }}</span>
              </div>
              <div class="flex items-center gap-2">
                <button
                  type="button"
                  class="inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition disabled:opacity-40 disabled:cursor-not-allowed"
                  @click="openSealModal(capsule)"
                  :disabled="!canSealCapsule(capsule)"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L7.5 20.5H4v-3.5l12.732-12.732z" />
                  </svg>
                  봉인
                </button>
                <button
                  v-if="canDeleteCapsule(capsule)"
                  @click="confirmDeleteCapsule(capsule)"
                  class="inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-xs font-semibold text-white bg-rose-500 hover:bg-rose-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-rose-500 transition"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7H5m3 0V5a2 2 0 012-2h4a2 2 0 012 2v2m2 0v12a2 2 0 01-2 2H8a2 2 0 01-2-2V7m3 4v6m4-6v6" />
                  </svg>
                  삭제
                </button>
                <span v-else class="text-xs text-slate-400">삭제 권한 없음</span>
              </div>
            </div>
            <p v-if="!canSealCapsule(capsule)" class="text-[11px] text-amber-500">주소와 메시지가 준비된 캡슐만 봉인할 수 있습니다.</p>
          </article>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex items-center justify-between border-t border-slate-200 px-4 py-3 sm:px-6 mt-4">
        <div class="flex flex-1 justify-between sm:hidden">
          <button
            @click="changePage(currentPage - 1)"
            :disabled="!hasPrevious"
            class="relative inline-flex items-center rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            이전
          </button>
          <button
            @click="changePage(currentPage + 1)"
            :disabled="!hasNext"
            class="relative ml-3 inline-flex items-center rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            다음
          </button>
        </div>
        <div class="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
          <div>
            <p class="text-sm text-slate-700">
              총 <span class="font-medium">{{ totalCount }}</span>개 중 <span class="font-medium">{{ (currentPage - 1) * 20 + 1 }}</span> - <span class="font-medium">{{ Math.min(currentPage * 20, totalCount) }}</span>
            </p>
          </div>
          <div>
            <nav class="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
              <button
                @click="changePage(currentPage - 1)"
                :disabled="!hasPrevious"
                class="relative inline-flex items-center rounded-l-md px-2 py-2 text-slate-400 ring-1 ring-inset ring-slate-300 hover:bg-slate-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span class="sr-only">이전</span>
                <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fill-rule="evenodd" d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z" clip-rule="evenodd" />
                </svg>
              </button>
              <button
                 v-for="page in displayedPages"
                 :key="page"
                 @click="changePage(page)"
                 :class="[
                   page === currentPage ? 'z-10 bg-indigo-600 text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600' : 'text-slate-900 ring-1 ring-inset ring-slate-300 hover:bg-slate-50 focus:outline-offset-0',
                   'relative inline-flex items-center px-4 py-2 text-sm font-semibold focus:z-20'
                 ]"
              >
                {{ page }}
              </button>
              <button
                @click="changePage(currentPage + 1)"
                :disabled="!hasNext"
                class="relative inline-flex items-center rounded-r-md px-2 py-2 text-slate-400 ring-1 ring-inset ring-slate-300 hover:bg-slate-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span class="sr-only">다음</span>
                <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fill-rule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clip-rule="evenodd" />
                </svg>
              </button>
            </nav>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="deleteModal.show" class="fixed inset-0 bg-slate-900/40 z-[9999] flex items-center justify-center px-4">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6 space-y-6 text-center">
        <div class="space-y-2">
          <h3 class="text-lg font-semibold text-slate-900">타임캡슐을 삭제할까요?</h3>
          <p class="text-sm text-slate-500">
            이 작업은 되돌릴 수 없습니다.
          </p>
        </div>
        <div class="flex flex-col gap-3">
          <button
            type="button"
            @click="deleteMyCapsule"
            :disabled="deleteModal.deleting"
            class="w-full inline-flex justify-center rounded-xl px-4 py-2.5 text-sm font-semibold text-white bg-rose-600 hover:bg-rose-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ deleteModal.deleting ? '삭제 중...' : '삭제하기' }}
          </button>
          <button
            type="button"
            @click="cancelDeleteMyCapsule"
            :disabled="deleteModal.deleting"
            class="w-full inline-flex justify-center rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            취소
          </button>
        </div>
      </div>
    </div>

    <!-- Seal & Broadcast Modal -->
    <div v-if="sealModal.show" class="fixed inset-0 z-[9999] flex items-center justify-center bg-slate-900/60 p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <!-- 헤더 -->
        <div class="flex items-start justify-between border-b border-slate-200 p-4 sm:px-6 sm:py-4">
          <div class="flex-1 pr-4">
            <h3 class="text-lg sm:text-xl font-semibold text-slate-900">타임캡슐 봉인 · 전파</h3>
            <p class="text-xs sm:text-sm text-slate-500 mt-1">선택된 타임캡슐을 블록체인에 기록합니다.</p>
          </div>
          <button
            type="button"
            @click="closeSealModal"
            class="flex-shrink-0 inline-flex items-center justify-center rounded-full w-8 h-8 sm:w-10 sm:h-10 text-slate-500 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-300 disabled:opacity-40"
            :disabled="sealModal.building || sealModal.sending"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- 입력 필드 영역 -->
        <div class="p-4 sm:p-6 space-y-4">
          <div class="space-y-4">
            <div>
              <label class="text-xs font-semibold text-slate-500">
                타임캡슐 주소
                <span class="text-slate-400 font-normal">(From/To)</span>
              </label>
              <input
                v-model="sealForm.toAddress"
                readonly
                class="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs sm:text-sm font-mono text-slate-700"
              />
            </div>
            <div class="grid grid-cols-2 gap-3 sm:gap-4">
              <div>
                <label class="text-xs font-semibold text-slate-500">보낼 금액 (sats)</label>
                <input
                  v-model.number="sealForm.amountSats"
                  readonly
                  class="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs sm:text-sm text-slate-700"
                />
              </div>
              <div>
                <label class="text-xs font-semibold text-slate-500">수수료율 (sats/vB)</label>
                <input
                  v-model.number="sealForm.feeRate"
                  readonly
                  class="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs sm:text-sm text-slate-700"
                />
              </div>
            </div>
            <div>
              <label class="text-xs font-semibold text-slate-500">메모</label>
              <textarea
                v-model="sealForm.memo"
                readonly
                class="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs sm:text-sm text-slate-700 min-h-[80px] sm:min-h-[90px]"
              />
            </div>
          </div>

          <p v-if="sealBuildError" class="rounded-xl border border-rose-100 bg-rose-50 px-3 py-2 text-xs sm:text-sm text-rose-600">
            {{ sealBuildError }}
          </p>
        </div>

        <!-- 버튼 영역 -->
        <div class="px-4 pb-4 sm:px-6 sm:pb-6">
          <div class="flex flex-col sm:flex-row gap-3 sm:gap-4">
            <button
              type="button"
              class="w-full sm:flex-1 inline-flex items-center justify-center gap-2 rounded-xl px-6 py-3 sm:py-3.5 text-sm sm:text-base font-semibold text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-400 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
              @click="buildSealTransaction"
              :disabled="sealModal.building || sealModal.sending"
            >
              <svg v-if="sealModal.building" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ sealModal.building ? '생성 중...' : '봉인하기' }}
            </button>
            <button
              type="button"
              class="w-full sm:flex-1 inline-flex items-center justify-center gap-2 rounded-xl px-6 py-3 sm:py-3.5 text-sm sm:text-base font-semibold text-white bg-emerald-600 hover:bg-emerald-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
              @click="broadcastSealTransaction"
              :disabled="sealModal.sending || !sealTxPreview"
            >
              <svg v-if="sealModal.sending" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ sealModal.sending ? '전파 중...' : '타임캡슐 묻기' }}
            </button>
          </div>
        </div>

        <!-- 결과 영역 -->
        <div class="px-4 pb-4 sm:px-6 sm:pb-6 space-y-4 sm:space-y-5">

          <div
            v-if="sealTxPreview"
            class="rounded-2xl border border-slate-100 bg-slate-50 p-3 sm:p-4 space-y-3 text-xs sm:text-sm text-slate-700"
          >
            <div class="space-y-3">
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <p class="text-xs text-slate-500">보낼 금액</p>
                  <p class="font-semibold text-slate-900 text-sm sm:text-base">{{ formatSats(sealTxPreview.amount_sats) }}</p>
                </div>
                <div>
                  <p class="text-xs text-slate-500">총 수수료</p>
                  <p class="font-semibold text-slate-900 text-sm sm:text-base">
                    {{ formatSats(sealTxPreview.fee_sats) }}
                    <span class="text-xs text-slate-500 block sm:inline">
                      ({{ formatFeeRate(sealTxPreview.fee_rate_sats_vb) }} sats/vB · {{ formatVsize(sealTxPreview.vsize) }})
                    </span>
                  </p>
                </div>
                <div>
                  <p class="text-xs text-slate-500">거스름돈</p>
                  <p class="font-semibold text-slate-900 text-sm sm:text-base">{{ formatSats(sealTxPreview.change_sats) }}</p>
                </div>
              </div>

              <div v-if="sealTxPreview.from_address" class="border-t border-slate-200 pt-3">
                <p class="text-xs text-slate-500 mb-1">출금 주소 (From)</p>
                <p class="font-mono text-xs text-slate-700 break-all">{{ sealTxPreview.from_address }}</p>
              </div>
            </div>
          </div>

          <div
            v-if="sealBroadcastResult.txid"
            class="rounded-2xl border border-emerald-100 bg-emerald-50 px-3 py-3 text-xs sm:text-sm text-emerald-700 space-y-1"
          >
            <p class="font-semibold">전파 완료</p>
            <a
              :href="sealBroadcastResult.broadcastUrl || explorerUrlForTx(sealBroadcastResult.txid)"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center gap-1 text-emerald-800 font-semibold underline break-all"
            >
              <span class="break-all">{{ sealBroadcastResult.txid }}</span>
              <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 3h7m0 0v7m0-7L10 14" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10v11h11" />
              </svg>
            </a>
          </div>
          <div
            v-if="sealBroadcastResult.error"
            class="rounded-2xl border border-rose-100 bg-rose-50 px-3 py-3 text-xs sm:text-sm text-rose-700"
          >
            {{ sealBroadcastResult.error }}
          </div>
        </div>
      </div>
    </div>

  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { API_BASE_URL } from '../api'
import { useNotification } from '../composables/useNotification'

const DEFAULT_NICKNAME = 'Anonymous'
const EXISTING_CAPSULE_WARNING = '이미 저장된 타임캡슐이 있습니다. 목록에서 기존 캡슐을 삭제한 후 다시 시도해주세요.'

const { successMessage: toastSuccess, errorMessage: toastError, showSuccess, showError } = useNotification()

const secretKey = ref('')
const wishMessage = ref('')
const privateKey = ref('')
const publicKey = ref('')
const encryptedHash = ref('')
const lastUpdated = ref(null)
const computing = ref(false)
const errorMessage = ref('')
const saving = ref(false)
const saved = ref(false)
const showSecret = ref(true)

// Decryption states
const decryptKey = ref('')
const encryptedDataInput = ref('')
const decryptedMessage = ref('')
const decrypting = ref(false)
const decryptError = ref('')
const showDecryptSecret = ref(false)

// UI states
const copiedCapsuleId = ref(null)
const copiedEncryptedStatus = ref(false)
const sealing = ref(false)
const sealed = ref(false)
const opening = ref(false)
const opened = ref(false)
const mode = ref('seal') // 'seal' or 'unseal'

// My Capsules List
const capsules = ref([])
const myNickname = ref(getStoredNickname())
const hasExistingCapsule = computed(() => {
  const nickname = myNickname.value
  if (!nickname) return false
  return capsules.value.some((capsule) => normalizeUserInfo(capsule.user_info) === nickname)
})
const myCapsuleEntry = computed(() => {
  if (!hasExistingCapsule.value) return null
  const nickname = normalizeUserInfo(myNickname.value)
  return capsules.value.find((capsule) => normalizeUserInfo(capsule.user_info) === nickname) || null
})
const existingCapsuleWarning = computed(() =>
  hasExistingCapsule.value ? EXISTING_CAPSULE_WARNING : ''
)
const currentPage = ref(1)
const totalPages = ref(1)
const totalCount = ref(0)
const hasNext = ref(false)
const hasPrevious = ref(false)

const deleteModal = ref({
  show: false,
  capsule: null,
  deleting: false
})
const AUTO_SEAL_AMOUNT_SATS = 500
const MIN_SEAL_FEE_RATE = 0.5
const sealModal = ref({
  show: false,
  capsule: null,
  building: false,
  sending: false
})
const sealForm = ref({
  toAddress: '',
  memo: '',
  amountSats: AUTO_SEAL_AMOUNT_SATS,
  feeRate: MIN_SEAL_FEE_RATE
})
const sealTxPreview = ref(null)
const sealBuildError = ref('')
const sealBroadcastResult = ref({
  txid: '',
  feeSats: null,
  vsize: null,
  broadcastUrl: '',
  error: ''
})

const displayedPages = computed(() => {
  const pages = []
  const range = 2 // Current page +/- range
  for (let i = 1; i <= totalPages.value; i++) {
    if (i === 1 || i === totalPages.value || (i >= currentPage.value - range && i <= currentPage.value + range)) {
      pages.push(i)
    }
  }
  return pages.sort((a, b) => a - b).filter((page, index, self) => self.indexOf(page) === index) // Unique just in case
})

const messageLimit = 65

const hasSecret = computed(() => secretKey.value.trim().length > 0)
const hasMessage = computed(() => wishMessage.value.trim().length > 0)
const capsuleReady = computed(() => hasSecret.value && hasMessage.value && !!encryptedHash.value && sealed.value)
const primarySealDisabled = computed(() => hasExistingCapsule.value || !hasSecret.value || !hasMessage.value || computing.value || sealing.value)
const lockedByStoredCapsule = computed(() => hasExistingCapsule.value && !opening.value && !opened.value)
const capsuleVisualLocked = computed(() => lockedByStoredCapsule.value || capsuleReady.value)
const shouldShowClosedLid = computed(() => lockedByStoredCapsule.value || (capsuleReady.value && mode.value === 'seal'))
const statusLabel = computed(() => {
  if (hasExistingCapsule.value) return '봉인됨'
  if (!hasSecret.value) return '대기 중'
  if (computing.value) return '암호화 중'
  if (capsuleReady.value) return '봉인 완료'
  return '입력 대기'
})

const statusDescription = computed(() => {
  if (hasExistingCapsule.value && !opening.value && !opened.value) {
    return '이미 봉인된 타임캡슐입니다. 나만의 키로 해제해주세요.'
  }
  if (opening.value) {
    return '타임캡슐이 열리고 있습니다... 메시지가 나타나고 있어요!'
  }
  if (opened.value) {
    return '타임캡슐이 성공적으로 열렸습니다! 봉인된 소망을 확인하세요.'
  }
  if (!hasSecret.value) {
    return mode.value === 'seal'
      ? '비밀키를 입력하고 소망 메시지를 작성해주세요. 타임캡슐이 열려있습니다.'
      : '비밀키와 암호화된 데이터를 입력하여 타임캡슐을 열어보세요.'
  }
      if (sealing.value) {
      return '메시지가 타임캡슐 안으로 들어가고 있습니다...'
    }
  
  if (computing.value) {
    return '타임캡슐을 봉인하는 중입니다...'
  }
  if (capsuleReady.value && mode.value === 'seal') {
    return '타임캡슐이 안전하게 봉인되었습니다. 같은 비밀키로 언제든 열 수 있습니다.'
  }
  if (hasSecret.value && mode.value === 'seal' && !hasMessage.value) {
    return '비밀키가 준비되었습니다. 소망 메시지를 입력하고 봉인해주세요.'
  }
  if (mode.value === 'unseal') {
    return '암호화된 데이터를 붙여넣고 타임캡슐을 열어보세요.'
  }
  return '타임캡슐에 소망을 담아보세요.'
})

const statusBadgeClass = computed(() => {
  if (hasExistingCapsule.value) return 'bg-emerald-100 text-emerald-700 border border-emerald-200'
  if (!hasSecret.value) return 'bg-slate-100 text-slate-700'
  if (computing.value) return 'bg-amber-100 text-amber-700 border border-amber-200'
  if (capsuleReady.value) return 'bg-emerald-100 text-emerald-700 border border-emerald-200'
  return 'bg-indigo-100 text-indigo-700 border border-indigo-200'
})

const encryptedHashSizeLabel = computed(() => formatByteLength(encryptedHash.value))

const lastUpdatedText = computed(() => {
  if (!lastUpdated.value) return ''
  return new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).format(lastUpdated.value)
})

let recomputeTimer
let computeRunId = 0
const textEncoder = new TextEncoder()
let capsuleCopyTimer

// watch([secretKey, wishMessage], () => {
//   // Reset states when input changes
//   sealed.value = false
//   opened.value = false
  
//   if (recomputeTimer) clearTimeout(recomputeTimer)
//   recomputeTimer = setTimeout(() => {
//     runComputation()
//   }, 200)
// }, { immediate: true })

watch([secretKey, wishMessage], () => {
  encryptedHash.value = ''
  errorMessage.value = ''
  sealed.value = false
  opened.value = false
  saved.value = false
})

watch(hasExistingCapsule, (value) => {
  mode.value = value ? 'unseal' : 'seal'
}, { immediate: true })

watch(mode, () => {
  sealing.value = false
  sealed.value = false
  opening.value = false
  opened.value = false
  errorMessage.value = ''
  decryptError.value = ''
  decryptedMessage.value = ''
})

watch(myCapsuleEntry, (entry) => {
  if (entry?.encrypted_message) {
    encryptedDataInput.value = entry.encrypted_message
  } else if (!hasExistingCapsule.value) {
    encryptedDataInput.value = ''
  }
}, { immediate: true })

onBeforeUnmount(() => {
  if (recomputeTimer) clearTimeout(recomputeTimer)
  if (capsuleCopyTimer) clearTimeout(capsuleCopyTimer)
  if (typeof window !== 'undefined') {
    window.removeEventListener('storage', syncNicknameFromStorage)
  }
})

onMounted(() => {
  syncNicknameFromStorage()
  if (typeof window !== 'undefined') {
    window.addEventListener('storage', syncNicknameFromStorage)
  }
  fetchCapsules()
})

async function fetchCapsules(page = 1) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/time-capsule/admin/list?page=${page}`)
    if (response.ok) {
      const data = await response.json()
      if (data.results) {
          capsules.value = data.results
          currentPage.value = data.current_page
          totalPages.value = data.num_pages
          totalCount.value = data.count
          hasNext.value = data.has_next
          hasPrevious.value = data.has_previous
      } else {
          // Fallback if API returns array
          capsules.value = data
      }
    } else {
      console.error('Failed to fetch time capsules')
    }
  } catch (error) {
    console.error('Error fetching time capsules:', error)
  }
}

function changePage(page) {
    if (page >= 1 && page <= totalPages.value) {
        fetchCapsules(page)
    }
}

function normalizeUserInfo(value) {
  const normalized = (value ?? DEFAULT_NICKNAME).toString().trim()
  return normalized || DEFAULT_NICKNAME
}

function getStoredNickname() {
  if (typeof window === 'undefined' || !window.localStorage) {
    return DEFAULT_NICKNAME
  }
  try {
    const stored = (window.localStorage.getItem('nickname') || '').trim()
    return stored || DEFAULT_NICKNAME
  } catch (error) {
    return DEFAULT_NICKNAME
  }
}

function syncNicknameFromStorage() {
  myNickname.value = getStoredNickname()
}

function getByteLength(value) {
  if (!value) return 0
  return textEncoder.encode(typeof value === 'string' ? value : String(value)).length
}

function formatByteLength(value) {
  const bytes = getByteLength(value)
  if (!bytes) return ''
  return `${bytes.toLocaleString()} bytes`
}

function isMyCapsule(capsule) {
  return normalizeUserInfo(capsule.user_info) === myNickname.value
}

function canDeleteCapsule(capsule) {
  return isMyCapsule(capsule)
}

function canSealCapsule(capsule) {
  if (!capsule) return false
  return Boolean(capsule.bitcoin_address && capsule.encrypted_message)
}

function confirmDeleteCapsule(capsule) {
  deleteModal.value = {
    show: true,
    capsule: capsule,
    deleting: false
  }
}

function cancelDeleteMyCapsule() {
  if (deleteModal.value.deleting) return
  deleteModal.value = {
    show: false,
    capsule: null,
    deleting: false
  }
}

function resetSealModalState() {
  sealModal.value = {
    show: false,
    capsule: null,
    building: false,
    sending: false
  }
  sealForm.value = {
    toAddress: '',
    memo: '',
    amountSats: AUTO_SEAL_AMOUNT_SATS,
    feeRate: MIN_SEAL_FEE_RATE
  }
  sealTxPreview.value = null
  sealBuildError.value = ''
  sealBroadcastResult.value = {
    txid: '',
    feeSats: null,
    vsize: null,
    broadcastUrl: '',
    error: ''
  }
}

function openSealModal(capsule) {
  if (!canSealCapsule(capsule)) {
    showError('비트코인 주소와 암호화된 메시지가 있어야 봉인할 수 있습니다.')
    return
  }
  sealModal.value = {
    show: true,
    capsule,
    building: false,
    sending: false
  }
  sealForm.value = {
    toAddress: capsule.bitcoin_address || '',
    memo: capsule.encrypted_message || '',
    amountSats: AUTO_SEAL_AMOUNT_SATS,
    feeRate: MIN_SEAL_FEE_RATE
  }
  sealTxPreview.value = null
  sealBuildError.value = ''
  sealBroadcastResult.value = {
    txid: '',
    feeSats: null,
    vsize: null,
    broadcastUrl: '',
    error: ''
  }
}

function closeSealModal() {
  if (sealModal.value.building || sealModal.value.sending) return
  resetSealModalState()
}

async function deleteMyCapsule() {
  if (!deleteModal.value.capsule) return

  deleteModal.value.deleting = true

  try {
    const response = await fetch(`${API_BASE_URL}/api/time-capsule/admin/delete/${deleteModal.value.capsule.id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (response.ok) {
      // Remove from local list
      capsules.value = capsules.value.filter(c => c.id !== deleteModal.value.capsule.id)
      
      // If page became empty and we are not on first page, go back
      if (capsules.value.length === 0 && currentPage.value > 1) {
          fetchCapsules(currentPage.value - 1)
      } else {
          // Refetch to get item from next page if available
          fetchCapsules(currentPage.value)
      }

      // Reset deleting state before calling cancel
      deleteModal.value.deleting = false
      cancelDeleteMyCapsule()
    } else {
      const errorData = await response.json().catch(() => ({}))
      alert(errorData.error || '삭제에 실패했습니다.')
      deleteModal.value.deleting = false
    }
  } catch (error) {
    console.error('Error deleting time capsule:', error)
    alert('삭제 중 오류가 발생했습니다.')
    deleteModal.value.deleting = false
  }
}

async function buildSealTransaction() {
  if (!sealModal.value.show || sealModal.value.building || sealModal.value.sending) return
  const toAddress = (sealForm.value.toAddress || '').trim()
  const amount = Number(sealForm.value.amountSats)
  const feeRate = Number(sealForm.value.feeRate)
  if (!toAddress) {
    showError('받는 주소가 필요합니다.')
    return
  }
  if (!Number.isFinite(amount) || amount <= 0) {
    showError('유효한 금액이 설정되지 않았습니다.')
    return
  }
  if (!Number.isFinite(feeRate) || feeRate < MIN_SEAL_FEE_RATE) {
    showError(`수수료율은 최소 ${MIN_SEAL_FEE_RATE} sats/vB 이상이어야 합니다.`)
    return
  }
  sealModal.value.building = true
  sealTxPreview.value = null
  sealBuildError.value = ''
  try {
    const response = await fetch(appendAdminUsername(`${API_BASE_URL}/api/time-capsule/admin/build-tx`), {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        to_address: toAddress,
        from_address: toAddress,  // 🔒 전용 주소 사용으로 UTXO 충돌 방지
        amount_sats: amount,
        fee_rate_sats_vb: feeRate,
        memo_text: sealForm.value.memo || '',
      }),
    })
    const data = await response.json()
    if (response.ok && data.ok !== false) {
      sealTxPreview.value = data
      sealBuildError.value = ''
      showSuccess('트랜잭션을 생성했습니다.')
    } else {
      const message = data.error || '트랜잭션 생성에 실패했습니다.'
      sealBuildError.value = message
      showError(message)
    }
  } catch (error) {
    console.error('Failed to build seal transaction', error)
    sealBuildError.value = '트랜잭션 생성에 실패했습니다.'
    showError('트랜잭션 생성에 실패했습니다.')
  } finally {
    sealModal.value.building = false
  }
}

async function broadcastSealTransaction() {
  if (!sealTxPreview.value?.raw_tx) {
    showError('먼저 트랜잭션을 생성하세요.')
    return
  }
  if (sealModal.value.sending) return
  const feeRate = Number(sealForm.value.feeRate)
  if (!Number.isFinite(feeRate) || feeRate < MIN_SEAL_FEE_RATE) {
    showError(`수수료율은 최소 ${MIN_SEAL_FEE_RATE} sats/vB 이상이어야 합니다.`)
    return
  }
  sealModal.value.sending = true
  sealBroadcastResult.value = {
    txid: '',
    feeSats: null,
    vsize: null,
    broadcastUrl: '',
    error: ''
  }
  try {
    const response = await fetch(appendAdminUsername(`${API_BASE_URL}/api/time-capsule/admin/broadcast-tx`), {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        raw_tx: sealTxPreview.value.raw_tx,
        fee_sats: sealTxPreview.value.fee_sats,
        fee_rate_sats_vb: feeRate,
      }),
    })
    const data = await response.json()
    if (response.ok && data.ok) {
      sealBroadcastResult.value = {
        txid: data.txid,
        feeSats: data.fee_sats,
        vsize: data.vsize,
        broadcastUrl: data.broadcast_url,
        error: ''
      }
      showSuccess('트랜잭션을 전파했습니다.')
      sealTxPreview.value = null
      if (sealModal.value.capsule?.id && data.txid) {
        await recordCapsuleBroadcast(sealModal.value.capsule.id, data.txid)
      }
    } else {
      sealBroadcastResult.value.error = data.error || '트랜잭션 전파에 실패했습니다.'
      showError(sealBroadcastResult.value.error)
    }
  } catch (error) {
    console.error('Failed to broadcast seal transaction', error)
    sealBroadcastResult.value.error = '트랜잭션 전파 중 오류가 발생했습니다.'
    showError('트랜잭션 전파 중 오류가 발생했습니다.')
  } finally {
    sealModal.value.sending = false
  }
}

async function recordCapsuleBroadcast(capsuleId, txid) {
  try {
    const response = await fetch(appendAdminUsername(`${API_BASE_URL}/api/time-capsule/admin/broadcast-record/${capsuleId}`), {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ txid }),
    })
    const data = await response.json()
    if (response.ok && data.ok) {
      updateCapsuleInList(data.capsule)
      showSuccess('전파 내역을 저장했습니다.')
      return data.capsule
    }
    showError(data.error || '전파 내역을 저장하지 못했습니다.')
    return null
  } catch (error) {
    console.error('Failed to record capsule broadcast', error)
    showError('전파 내역을 저장하지 못했습니다.')
    return null
  }
}

function updateCapsuleInList(updatedCapsule) {
  if (!updatedCapsule) return
  const next = capsules.value.slice()
  const index = next.findIndex(c => c.id === updatedCapsule.id)
  if (index !== -1) {
    next[index] = { ...next[index], ...updatedCapsule }
    capsules.value = next
  }
  if (sealModal.value.capsule?.id === updatedCapsule.id) {
    sealModal.value.capsule = { ...sealModal.value.capsule, ...updatedCapsule }
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

function explorerUrlForTx(txid) {
  if (!txid) return 'https://mempool.space/tx/'
  return `https://mempool.space/tx/${txid}`
}

function shortTxid(txid) {
  if (!txid) return ''
  if (txid.length <= 12) return txid
  return `${txid.slice(0, 6)}...${txid.slice(-4)}`
}

function formatSats(value) {
  if (!Number.isFinite(Number(value))) return '-'
  return `${Number(value).toLocaleString()} sats`
}

function formatFeeRate(value) {
  if (!Number.isFinite(Number(value))) return '-'
  return `${Number(value).toFixed(2)}`
}

function formatVsize(value) {
  if (!Number.isFinite(Number(value))) return '-'
  return `${Number(value).toLocaleString()} vB`
}

function getAdminUsername() {
  if (typeof window === 'undefined' || !window.localStorage) return ''
  const nickname = window.localStorage.getItem('nickname')
  if (!nickname) return ''
  const isAdmin = window.localStorage.getItem('isAdmin')
  if (isAdmin !== 'true') return ''
  return nickname
}

function appendAdminUsername(url) {
  const username = getAdminUsername()
  if (!username) return url
  const separator = url.includes('?') ? '&' : '?'
  return `${url}${separator}username=${encodeURIComponent(username)}`
}

function toggleSecretVisibility() {
  showSecret.value = !showSecret.value
}

function toggleDecryptSecretVisibility() {
  showDecryptSecret.value = !showDecryptSecret.value
}

function handleReset() {
  secretKey.value = ''
  wishMessage.value = ''
  privateKey.value = ''
  publicKey.value = ''
  encryptedHash.value = ''
  lastUpdated.value = null
  errorMessage.value = ''
  sealed.value = false
  opened.value = false
}

function handleDecryptReset() {
  decryptKey.value = ''
  encryptedDataInput.value = ''
  decryptedMessage.value = ''
  decryptError.value = ''
}

async function handleUnseal() {
  const secret = secretKey.value.trim()
  const encrypted = encryptedDataInput.value.trim()

  if (!secret || !encrypted) {
    errorMessage.value = '비밀키와 암호화된 데이터를 모두 입력해주세요.'
    return
  }

  // Trigger opening animation
  opening.value = true
  errorMessage.value = ''
  decryptedMessage.value = ''

  try {
    // Decrypt the message
    const message = await decryptMessage(encrypted, secret)

    // Wait for animation
    await new Promise(resolve => setTimeout(resolve, 1500))

    if (opening.value) {
      decryptedMessage.value = message
      wishMessage.value = message

      // Complete opening animation
      setTimeout(() => {
        opening.value = false
        opened.value = true
      }, 500)
    }
  } catch (error) {
    console.error('Decryption error:', error)
    errorMessage.value = '봉인 해제에 실패했습니다. 비밀키가 올바른지 확인해주세요.'
    opening.value = false
  }
}

async function copyCapsuleEncryptedMessage(capsule) {
  if (!capsule?.encrypted_message) return
  try {
    await navigator.clipboard.writeText(capsule.encrypted_message)
    copiedCapsuleId.value = capsule.id
    if (capsuleCopyTimer) clearTimeout(capsuleCopyTimer)
    capsuleCopyTimer = setTimeout(() => {
      copiedCapsuleId.value = null
    }, 2000)
  } catch (error) {
    console.error('Failed to copy encrypted message:', error)
  }
}

async function copyEncryptedHash() {
  if (!encryptedHash.value) return
  try {
    await navigator.clipboard.writeText(encryptedHash.value)
    copiedEncryptedStatus.value = true
    setTimeout(() => {
      copiedEncryptedStatus.value = false
    }, 2000)
  } catch (error) {
    console.error('Failed to copy encrypted hash:', error)
  }
}

async function saveTimeCapsule(encryptedMessage) {
  try {
    const nickname = myNickname.value || DEFAULT_NICKNAME
    const response = await fetch(`${API_BASE_URL}/api/time-capsule/save`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        encrypted_message: encryptedMessage,
        user_info: nickname
      }),
    })

    if (response.ok) {
      const data = await response.json()
      return { success: true, data }
    } else {
      const errorData = await response.json().catch(() => ({}))
      return { success: false, error: errorData.error || '저장에 실패했습니다' }
    }
  } catch (error) {
    console.error('Error saving time capsule:', error)
    return { success: false, error: '네트워크 오류가 발생했습니다' }
  }
}

async function handleSave() {
  if (hasExistingCapsule.value) {
    errorMessage.value = EXISTING_CAPSULE_WARNING
    return
  }
  if (!encryptedHash.value) return
  saving.value = true
  errorMessage.value = ''

  const result = await saveTimeCapsule(encryptedHash.value)
  saving.value = false

  if (result.success) {
    saved.value = true
    showSuccess('데이터가 저장되었습니다.')
    // Refresh the list after saving
    fetchCapsules()
  } else {
    errorMessage.value = result.error
    showError(result.error || '타임캡슐 저장에 실패했습니다.')
  }
}

async function triggerImmediateComputation() {
  if (hasExistingCapsule.value) {
    errorMessage.value = EXISTING_CAPSULE_WARNING
    return
  }

  if (recomputeTimer) clearTimeout(recomputeTimer)

  sealing.value = true
  sealed.value = false

  await runComputation()

  setTimeout(() => {
    sealing.value = false
    sealed.value = true
    if (encryptedHash.value) {
      showSuccess('타임캡슐이 성공적으로 봉인되었습니다.')
    }
  }, 2000)
}

async function runComputation() {
  const localRunId = ++computeRunId
  const secret = secretKey.value.trim()
  const message = wishMessage.value.trim()

  if (!secret) {
    privateKey.value = ''
    publicKey.value = ''
    encryptedHash.value = ''
    lastUpdated.value = null
    computing.value = false
    errorMessage.value = ''
    return
  }

  computing.value = true
  errorMessage.value = ''
  try {
    // Generate key displays from seed
    const keyDisplays = await generateKeyPairFromSeed(secret)
    if (localRunId !== computeRunId) return

    // Display private key
    privateKey.value = keyDisplays.privateKeyDisplay
    if (localRunId !== computeRunId) return

    // Display public key
    publicKey.value = keyDisplays.publicKeyDisplay
    if (localRunId !== computeRunId) return

    // Encrypt message if present
    if (message) {
      const encrypted = await encryptMessage(message, secret)
      encryptedHash.value = encrypted
    } else {
      encryptedHash.value = ''
    }

    if (localRunId === computeRunId) {
      lastUpdated.value = new Date()
    }
  } catch (error) {
    if (localRunId === computeRunId) {
      errorMessage.value = '암호화 과정 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.'
    }
    console.error('Time capsule compute error:', error)
  } finally {
    if (localRunId === computeRunId) {
      computing.value = false
    }
  }
}

async function handleDecrypt() {
  const secret = decryptKey.value.trim()
  const encrypted = encryptedDataInput.value.trim()

  if (!secret || !encrypted) {
    decryptError.value = '비밀키와 암호화된 데이터를 모두 입력해주세요.'
    return
  }

  decrypting.value = true
  decryptError.value = ''
  decryptedMessage.value = ''

  try {
    const message = await decryptMessage(encrypted, secret)
    decryptedMessage.value = message
  } catch (error) {
    console.error('Decryption error:', error)
    decryptError.value = '봉인 해제에 실패했습니다. 비밀키가 올바른지 확인해주세요.'
  } finally {
    decrypting.value = false
  }
}

// Generate key displays from seed (deterministic)
async function generateKeyPairFromSeed(seed) {
  if (!globalThis.crypto || !globalThis.crypto.subtle) {
    throw new Error('Web Crypto API not supported')
  }

  // Derive deterministic private key display from seed
  const privateKeyHash = await globalThis.crypto.subtle.digest(
    'SHA-256',
    textEncoder.encode(`timecapsule-private|${seed}`)
  )

  // Derive deterministic public key display from private key
  const publicKeyHash = await globalThis.crypto.subtle.digest(
    'SHA-256',
    new Uint8Array(privateKeyHash)
  )

  return {
    privateKeyDisplay: bufferToHex(new Uint8Array(privateKeyHash)),
    publicKeyDisplay: bufferToHex(new Uint8Array(publicKeyHash))
  }
}

// Compression utilities using browser's native CompressionStream API
// Returns { data: Uint8Array, compressed: boolean }
async function compressData(data) {
  const original = textEncoder.encode(data)

  // For very short messages, compression overhead is not worth it
  if (original.byteLength < 50 || typeof CompressionStream === 'undefined') {
    return { data: original, compressed: false }
  }

  try {
    const stream = new Blob([data]).stream()
    const compressedStream = stream.pipeThrough(new CompressionStream('gzip'))
    const blob = await new Response(compressedStream).blob()
    const compressed = new Uint8Array(await blob.arrayBuffer())

    // Only use compression if it actually reduces size
    if (compressed.byteLength < original.byteLength) {
      return { data: compressed, compressed: true }
    } else {
      return { data: original, compressed: false }
    }
  } catch (error) {
    console.warn('Compression failed, using uncompressed data:', error)
    return { data: original, compressed: false }
  }
}

async function decompressData(compressedData) {
  if (typeof DecompressionStream === 'undefined') {
    // Fallback: assume it's uncompressed text
    return new TextDecoder().decode(compressedData)
  }

  try {
    const stream = new Blob([compressedData]).stream()
    const decompressedStream = stream.pipeThrough(new DecompressionStream('gzip'))
    const blob = await new Response(decompressedStream).blob()
    const decompressed = new Uint8Array(await blob.arrayBuffer())
    return new TextDecoder().decode(decompressed)
  } catch (error) {
    // If decompression fails, try to decode as plain text
    try {
      return new TextDecoder().decode(compressedData)
    } catch (decodeError) {
      throw new Error('Failed to decompress data')
    }
  }
}

// Derive AES key from secret passphrase (deterministic)
async function deriveEncryptionKey(secret, algorithm = 'AES-CTR') {
  // Import the secret as key material
  const keyMaterial = await globalThis.crypto.subtle.importKey(
    'raw',
    textEncoder.encode(secret),
    { name: 'PBKDF2' },
    false,
    ['deriveBits', 'deriveKey']
  )

  // Derive AES key using PBKDF2 with fixed salt for deterministic results
  const salt = textEncoder.encode('timecapsule-salt-2024')
  return await globalThis.crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt,
      iterations: 100000,
      hash: 'SHA-256'
    },
    keyMaterial,
    { name: algorithm, length: 256 },
    false,
    ['encrypt', 'decrypt']
  )
}

// Encryption using smart compression + AES-CTR
// Format: FLAG(1 byte) + IV(12 bytes) + encrypted data → base64
// FLAG: 0x01 = compressed, 0x00 = uncompressed
// This keeps most messages under 80 bytes for OP_RETURN
async function encryptMessage(message, secret) {
  if (!globalThis.crypto || !globalThis.crypto.subtle) {
    throw new Error('Web Crypto API not supported')
  }

  // Step 1: Smart compression (only compress if beneficial)
  const { data, compressed } = await compressData(message)

  // Step 2: Derive encryption key from secret (AES-CTR)
  const key = await deriveEncryptionKey(secret, 'AES-CTR')

  // Step 3: Generate random IV (12 bytes - optimized for size)
  const iv = globalThis.crypto.getRandomValues(new Uint8Array(12))

  // Step 4: Create counter from IV (pad to 16 bytes for AES-CTR)
  const counter = new Uint8Array(16)
  counter.set(iv)

  // Step 5: Encrypt data
  const encrypted = await globalThis.crypto.subtle.encrypt(
    { name: 'AES-CTR', counter, length: 128 },
    key,
    data
  )

  // Step 6: Combine FLAG + IV + encrypted data
  // FLAG byte: 0x01 if compressed, 0x00 if not
  const combined = new Uint8Array(1 + 12 + encrypted.byteLength)
  combined[0] = compressed ? 0x01 : 0x00
  combined.set(iv, 1)
  combined.set(new Uint8Array(encrypted), 13)

  return arrayBufferToBase64(combined)
}

// Decryption - supports multiple formats for backward compatibility
// 1. Latest format: FLAG(1) + IV(12) + encrypted data with smart compression
// 2. Previous format: IV(16) + encrypted compressed data (AES-CTR)
// 3. Older format: IV(12) + encrypted data (AES-GCM optimized)
// 4. Old format: JSON format with AES-GCM
async function decryptMessage(encryptedData, secret) {
  if (!globalThis.crypto || !globalThis.crypto.subtle) {
    throw new Error('Web Crypto API not supported')
  }

  let decrypted

  // Try to detect format and decrypt
  try {
    const combined = base64ToArrayBuffer(encryptedData)

    // Check if it's JSON format (old format #4)
    const possibleJson = new TextDecoder().decode(combined)
    if (possibleJson.startsWith('{') && possibleJson.includes('"iv"')) {
      const data = JSON.parse(possibleJson)
      const key = await deriveEncryptionKey(secret, 'AES-GCM')
      const iv = base64ToArrayBuffer(data.iv)
      const ciphertext = base64ToArrayBuffer(data.ciphertext)

      decrypted = await globalThis.crypto.subtle.decrypt(
        { name: 'AES-GCM', iv },
        key,
        ciphertext
      )

      return new TextDecoder().decode(decrypted)
    }

    // Try latest format: FLAG + IV(12) + encrypted data (#1)
    if (combined.byteLength >= 13) {
      const flag = combined[0]

      // Check if flag looks valid (0x00 or 0x01)
      if (flag === 0x00 || flag === 0x01) {
        try {
          const key = await deriveEncryptionKey(secret, 'AES-CTR')
          const iv = combined.slice(1, 13)
          const ciphertext = combined.slice(13)

          const counter = new Uint8Array(16)
          counter.set(iv)

          decrypted = await globalThis.crypto.subtle.decrypt(
            { name: 'AES-CTR', counter, length: 128 },
            key,
            ciphertext
          )

          const decryptedData = new Uint8Array(decrypted)

          // If compressed, decompress
          if (flag === 0x01) {
            return await decompressData(decryptedData)
          } else {
            return new TextDecoder().decode(decryptedData)
          }
        } catch (err) {
          // Fall through to try other formats
        }
      }
    }

    // Try format #2: IV(16) + compressed data (previous AES-CTR format)
    if (combined.byteLength >= 16) {
      try {
        const key = await deriveEncryptionKey(secret, 'AES-CTR')
        const iv = combined.slice(0, 16)
        const ciphertext = combined.slice(16)

        const counter = new Uint8Array(16)
        counter.set(iv)

        decrypted = await globalThis.crypto.subtle.decrypt(
          { name: 'AES-CTR', counter, length: 128 },
          key,
          ciphertext
        )

        // Try to decompress (format #2)
        return await decompressData(new Uint8Array(decrypted))
      } catch (ctrError) {
        // Fall through to try GCM format
      }
    }

    // Try format #3: IV(12) + encrypted data (AES-GCM)
    if (combined.byteLength >= 12) {
      const key = await deriveEncryptionKey(secret, 'AES-GCM')
      const iv = combined.slice(0, 12)
      const ciphertext = combined.slice(12)

      decrypted = await globalThis.crypto.subtle.decrypt(
        { name: 'AES-GCM', iv },
        key,
        ciphertext
      )

      return new TextDecoder().decode(decrypted)
    }

    throw new Error('Invalid encrypted data format')
  } catch (error) {
    console.error('Decryption error:', error)
    throw new Error('복호화에 실패했습니다. 비밀키를 확인해주세요.')
  }
}

async function sha256Hex(input) {
  if (globalThis.crypto && globalThis.crypto.subtle) {
    const encoded = textEncoder.encode(input)
    const hashBuffer = await globalThis.crypto.subtle.digest('SHA-256', encoded)
    return bufferToHex(new Uint8Array(hashBuffer))
  }
  return fallbackHash(input)
}

function bufferToHex(bytes) {
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('')
}

function arrayBufferToBase64(buffer) {
  let binary = ''
  const bytes = new Uint8Array(buffer)
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return globalThis.btoa(binary)
}

function arrayBufferToBase64Url(buffer) {
  const base64 = arrayBufferToBase64(buffer)
  return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '')
}

function base64ToArrayBuffer(base64) {
  const binary = globalThis.atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i)
  }
  return bytes
}

function fallbackHash(value) {
  let h1 = 0x811c9dc5
  let h2 = 0x01000193
  for (let i = 0; i < value.length; i += 1) {
    const code = value.charCodeAt(i)
    h1 ^= code
    h1 = Math.imul(h1, 0x01000193) >>> 0
    h2 ^= code + 0x9e3779b9 + ((h2 << 6) >>> 0) + (h2 >>> 2)
    h2 >>>= 0
  }
  const part = h1.toString(16).padStart(8, '0') + h2.toString(16).padStart(8, '0')
  return (part.repeat(4)).slice(0, 64)
}
</script>

<style scoped>
/* Sealing animation */
@keyframes sealingPulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4);
  }
  50% {
    transform: scale(1.02);
    box-shadow: 0 0 20px 10px rgba(16, 185, 129, 0);
  }
}

@keyframes particleRise {
  0% {
    transform: translateY(0) scale(1);
    opacity: 0;
  }
  50% {
    opacity: 1;
  }
  100% {
    transform: translateY(-100px) scale(0);
    opacity: 0;
  }
}

@keyframes shimmer {
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
  }
}

@keyframes successGlow {
  0% {
    box-shadow: 0 0 5px rgba(16, 185, 129, 0.3);
    opacity: 0;
  }
  20% {
    opacity: 1;
  }
  50% {
    box-shadow: 0 0 20px rgba(16, 185, 129, 0.6);
  }
  100% {
    box-shadow: 0 0 5px rgba(16, 185, 129, 0.3);
    opacity: 1;
  }
}

.sealing-animation {
  animation: sealingPulse 1.5s ease-in-out;
  position: relative;
  overflow: hidden;
}

.sealing-animation::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(16, 185, 129, 0.1),
    transparent
  );
  animation: shimmer 2s infinite;
}

.sealed-animation {
  animation: successGlow 1s ease-in-out;
}

.particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: #10b981;
  border-radius: 50%;
  pointer-events: none;
  animation: particleRise 2s ease-out forwards;
}

/* Text scramble effect */
@keyframes scramble {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.scrambling {
  animation: scramble 0.5s ease-in-out 3;
}

/* Lock closing animation */
@keyframes lockClose {
  0% {
    transform: rotate(0deg);
  }
  50% {
    transform: rotate(-10deg);
  }
  100% {
    transform: rotate(0deg);
  }
}

.lock-closing {
  animation: lockClose 0.6s ease-in-out;
}

/* Unlock Opening Animation */
.unlock-opening {
  animation: unlockShake 0.8s ease-in-out;
}

@keyframes unlockShake {
  0%, 100% {
    transform: rotate(0deg);
  }
  25% {
    transform: rotate(5deg);
  }
  75% {
    transform: rotate(-5deg);
  }
}

/* Fade in animation */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-in-up {
  animation: fadeInUp 0.5s ease-out;
}

/* Time Capsule Animations */
/* Lid States */
.lid-open {
  transform: translateY(-30px);
  opacity: 0.8;
  transition: all 0.8s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.lid-closing {
  animation: lidClose 1.5s ease-in-out forwards;
}

.lid-closed {
  transform: translateY(0);
  opacity: 1;
  transition: all 0.5s ease-out;
}

@keyframes lidClose {
  0% {
    transform: translateY(-30px);
    opacity: 0.8;
  }
  50% {
    transform: translateY(-15px) rotate(-2deg);
  }
  100% {
    transform: translateY(0) rotate(0deg);
    opacity: 1;
  }
}

/* Lid Opening Animation */
.lid-opening {
  animation: lidOpen 1.5s ease-out forwards;
}

@keyframes lidOpen {
  0% {
    transform: translateY(0) rotate(0deg);
    opacity: 1;
  }
  30% {
    transform: translateY(-10px) rotate(3deg);
  }
  100% {
    transform: translateY(-40px) rotate(-5deg);
    opacity: 0.7;
  }
}

/* Message Paper Animation - Sealing */
.message-paper-sealing {
  animation: paperFloatIn 2s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  transform-origin: center;
  filter: drop-shadow(0 4px 8px rgba(245, 158, 11, 0.4));
}

@keyframes paperFloatIn {
  0% {
    transform: translateY(-80px) scale(1.2) rotate(-10deg);
    opacity: 0;
  }
  15% {
    opacity: 1;
  }
  25% {
    transform: translateY(-40px) scale(1.1) rotate(8deg);
    opacity: 1;
  }
  50% {
    transform: translateY(10px) scale(0.95) rotate(-5deg);
    opacity: 1;
  }
  70% {
    transform: translateY(60px) scale(0.7) rotate(3deg);
    opacity: 0.8;
  }
  85% {
    transform: translateY(95px) scale(0.4) rotate(-2deg);
    opacity: 0.4;
  }
  100% {
    transform: translateY(120px) scale(0.1) rotate(0deg);
    opacity: 0;
  }
}

/* Message Paper Animation - Opening */
.message-paper-opening {
  animation: paperFloatOut 2s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  transform-origin: center;
  filter: drop-shadow(0 0 15px rgba(16, 185, 129, 0.7));
}

@keyframes paperFloatOut {
  0% {
    transform: translateY(30px) scale(0.1) rotate(0deg);
    opacity: 0;
  }
  15% {
    transform: translateY(0px) scale(0.4) rotate(-3deg);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-25px) scale(0.6) rotate(5deg);
    opacity: 0.7;
  }
  50% {
    transform: translateY(-50px) scale(0.8) rotate(-8deg);
    opacity: 0.9;
  }
  70% {
    transform: translateY(-75px) scale(0.95) rotate(4deg);
    opacity: 1;
  }
  85% {
    transform: translateY(-95px) scale(1.05) rotate(-2deg);
    opacity: 1;
  }
  100% {
    transform: translateY(-110px) scale(1) rotate(0deg);
    opacity: 1;
  }
}

/* Lock Icon Animation */
.lock-icon {
  opacity: 0;
  transform: scale(0);
}

.lock-appear {
  animation: lockAppear 0.6s ease-out forwards;
}

@keyframes lockAppear {
  0% {
    opacity: 0;
    transform: scale(0) rotate(-180deg);
  }
  60% {
    transform: scale(1.2) rotate(10deg);
  }
  100% {
    opacity: 1;
    transform: scale(1) rotate(0deg);
  }
}

/* Sparkle Animation */
.sparkle {
  position: absolute;
  font-size: 20px;
  animation: sparkleFloat 2s ease-out forwards;
  pointer-events: none;
}

@keyframes sparkleFloat {
  0% {
    transform: translateY(0) scale(0) rotate(0deg);
    opacity: 0;
  }
  20% {
    opacity: 1;
    transform: translateY(-10px) scale(1) rotate(90deg);
  }
  100% {
    transform: translateY(-60px) scale(0) rotate(180deg);
    opacity: 0;
  }
}

/* Sparkle Burst Animation (radial explosion) */
.sparkle-burst {
  position: absolute;
  animation: sparkleBurst 1.5s ease-out forwards;
  pointer-events: none;
}

@keyframes sparkleBurst {
  0% {
    transform: translate(-50%, -50%) rotate(var(--angle)) translateY(0) scale(0) rotate(0deg);
    opacity: 0;
  }
  20% {
    opacity: 1;
  }
  100% {
    transform: translate(-50%, -50%) rotate(var(--angle)) translateY(-100px) scale(1) rotate(360deg);
    opacity: 0;
  }
}

/* Capsule Body Glow when sealing */
.sealing svg rect {
  filter: drop-shadow(0 0 10px rgba(16, 185, 129, 0.5));
  animation: capsuleGlowSeal 1.5s ease-in-out;
}

@keyframes capsuleGlowSeal {
  0%, 100% {
    filter: drop-shadow(0 0 5px rgba(16, 185, 129, 0.3));
  }
  50% {
    filter: drop-shadow(0 0 20px rgba(16, 185, 129, 0.8));
  }
}

/* Capsule Body Glow when opening */
.opening svg rect {
  filter: drop-shadow(0 0 15px rgba(99, 102, 241, 0.6));
  animation: capsuleGlowOpen 1.5s ease-in-out;
}

@keyframes capsuleGlowOpen {
  0%, 100% {
    filter: drop-shadow(0 0 10px rgba(99, 102, 241, 0.4));
  }
  50% {
    filter: drop-shadow(0 0 25px rgba(99, 102, 241, 0.9));
  }
}

/* Background Glow Animation */
.capsule-bg-glow {
  animation: bgGlowPulse 3s ease-in-out infinite;
}

@keyframes bgGlowPulse {
  0%, 100% {
    opacity: 0.5;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.1);
  }
}
</style>
