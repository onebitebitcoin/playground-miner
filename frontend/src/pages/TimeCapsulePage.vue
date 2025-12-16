<template>
  <section class="space-y-6">
    <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6">
      <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 class="text-xl font-semibold text-slate-900">타임캡슐</h2>
          <p class="text-sm text-slate-600 mt-1">
            나만의 비밀키로 개인키와 공개키를 생성하고, 소망 메시지를 암호화하여 안전하게 봉인합니다.
            모든 암호화는 브라우저 안에서만 진행되며 서버로 전송되지 않습니다.
          </p>
        </div>
        <div class="flex flex-col items-start md:items-end gap-1">
          <span
            class="text-xs font-semibold tracking-wide px-3 py-1 rounded-full"
            :class="statusBadgeClass"
          >
            {{ statusLabel }}
          </span>
          <span class="text-xs text-slate-500">
            {{ lastUpdatedText ? `마지막 갱신: ${lastUpdatedText}` : '아직 봉인되지 않았어요' }}
          </span>
        </div>
      </div>
      <p class="text-xs text-emerald-600 bg-emerald-50 border border-emerald-100 rounded-lg px-3 py-2 mt-4 flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
        입력한 값은 전송되지 않고 이 기기 안에서만 계산됩니다.
      </p>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
      <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 flex flex-col gap-5">
        <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h3 class="text-lg font-semibold text-slate-900">
              {{ mode === 'seal' ? '1. 나만의 키와 소망 입력' : '1. 타임캡슐 열기' }}
            </h3>
            <p class="text-sm text-slate-500 mt-1">
              {{ mode === 'seal' ? '타임캡슐을 여는 열쇠와 그 안에 담을 메시지를 적어주세요.' : '봉인된 타임캡슐을 나만의 키로 열어보세요.' }}
            </p>
          </div>

          <!-- Mode Toggle -->
          <div class="flex items-center gap-2 bg-slate-100 rounded-xl p-1">
            <button
              type="button"
              class="px-4 py-2 rounded-lg text-sm font-medium transition-all"
              :class="mode === 'seal' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'"
              @click="switchMode('seal')"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              봉인
            </button>
            <button
              type="button"
              class="px-4 py-2 rounded-lg text-sm font-medium transition-all"
              :class="mode === 'unseal' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'"
              @click="switchMode('unseal')"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z" />
              </svg>
              해제
            </button>
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
            <p class="text-xs text-slate-500 mt-1">나만의 키는 개인키의 씨앗이 됩니다. 길고 예측하기 어려울수록 좋아요.</p>
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
            <p class="text-xs text-slate-500 mt-1">메시지는 비밀키에서 파생된 암호화 키로 AES-GCM 암호화되어 안전하게 봉인됩니다.</p>
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
              <div v-if="opening" class="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div class="bg-indigo-900/80 text-white px-4 py-2 rounded-lg flex items-center gap-2">
                  <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span class="text-sm font-medium">타임캡슐 복호화 중...</span>
                </div>
              </div>
            </div>
            <p class="text-xs text-slate-500 mt-1">봉인할 때 받은 암호화된 데이터를 입력하고 같은 비밀키로 열어보세요.</p>
          </div>
        </div>

        <div class="flex flex-col gap-3 sm:flex-row sm:justify-end">
          

          <!-- Seal Mode Button -->
          <button
            v-if="mode === 'seal'"
            type="button"
            class="px-5 py-2 rounded-xl text-sm font-semibold text-white shadow-sm transition relative overflow-hidden"
            :class="[
              computing || sealing ? 'bg-slate-400 cursor-progress' : 'bg-slate-900 hover:bg-slate-800',
              sealing ? 'lock-closing' : ''
            ]"
            :disabled="!hasSecret || !hasMessage || computing || sealing"
            @click="triggerImmediateComputation"
          >
            <span v-if="sealing" class="flex items-center gap-2">
              <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              봉인 중...
            </span>
            <span v-else-if="computing">계산 중...</span>
            <span v-else class="flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              바로 봉인하기
            </span>
          </button>

          <!-- Save Button (Seal Mode) -->
          <button
            v-if="mode === 'seal'"
            type="button"
            class="px-5 py-2 rounded-xl text-sm font-semibold text-white bg-emerald-500 hover:bg-emerald-600 shadow-sm transition relative overflow-hidden"
            :disabled="!encryptedHash"
            @click="copyEncryptedData"
          >
            <span class="flex items-center gap-2">
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
            class="px-5 py-2 rounded-xl text-sm font-semibold text-white shadow-sm transition relative overflow-hidden"
            :class="[
              opening ? 'bg-indigo-400 cursor-progress' : 'bg-indigo-600 hover:bg-indigo-700',
              opening ? 'unlock-opening' : ''
            ]"
            :disabled="!secretKey.trim() || !encryptedDataInput.trim() || opening"
            @click="handleUnseal"
          >
            <span v-if="opening" class="flex items-center gap-2">
              <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              복호화 중...
            </span>
            <span v-else class="flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z" />
              </svg>
              타임캡슐 열기
            </span>
          </button>
        </div>

        <div v-if="errorMessage" class="text-sm text-rose-600 bg-rose-50 border border-rose-100 rounded-xl px-4 py-2">
          {{ errorMessage }}
        </div>

        <div v-if="sealed" class="text-sm text-emerald-600 bg-emerald-50 border border-emerald-100 rounded-xl px-4 py-2 flex items-center gap-2 fade-in-up">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span class="font-medium">타임캡슐이 성공적으로 봉인되었습니다!</span>
        </div>
      </div>

      <div class="bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 flex flex-col gap-5">
        <div>
          <h3 class="text-lg font-semibold text-slate-900">2. 타임캡슐</h3>
          <p class="text-sm text-slate-500 mt-1">타임캡슐에 소망을 담아보세요.</p>
        </div>

        <div class="space-y-4">
          <!-- Time Capsule Visualization -->
          <div class="flex justify-center items-center py-8 relative" :class="[sealing ? 'sealing' : '', opening ? 'opening' : '']">
            <!-- Background Glow -->
            <div
              class="absolute inset-0 flex items-center justify-center pointer-events-none"
              :class="capsuleReady ? 'capsule-bg-glow' : ''"
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
                  <!-- Fold mark -->
                  <line x1="100" y1="60" x2="100" y2="100" stroke="#f59e0b" stroke-width="0.5" opacity="0.3"/>
                  <!-- Sparkle on paper -->
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
                  sealing || sealed ? 'lid-closing' :
                  capsuleReady && mode === 'seal' ? 'lid-closed' :
                  'lid-open'
                ">
                  <ellipse cx="100" cy="120" rx="70" ry="20" fill="url(#lidGradient)" stroke="#334155" stroke-width="2"/>
                  <ellipse cx="100" cy="115" rx="65" ry="18" fill="#475569"/>
                  <circle cx="100" cy="115" r="8" fill="#94a3b8"/>
                </g>

                <!-- Lock Icon (appears when sealed) -->
                <g v-if="capsuleReady" class="lock-icon" :class="sealed ? 'lock-appear' : ''">
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
          <div class="text-center mt-4">
            <p class="text-xl font-bold transition-colors duration-300">
              <span v-if="opening" class="text-indigo-600 flex items-center justify-center gap-2 animate-pulse">
                <svg class="w-6 h-6 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                타임캡슐 여는 중...
              </span>
              <span v-else-if="opened" class="text-emerald-600 flex items-center justify-center gap-2">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z" />
                </svg>
                열림 (OPEN)
              </span>
              <span v-else-if="sealing" class="text-amber-600 flex items-center justify-center gap-2 animate-pulse">
                <svg class="w-6 h-6 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                봉인 중...
              </span>
              <span v-else-if="sealed" class="text-rose-600 flex items-center justify-center gap-2">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                닫힘 (LOCKED)
              </span>
              <span v-else class="text-emerald-600 flex items-center justify-center gap-2">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z" />
                </svg>
                열림 (OPEN)
              </span>
            </p>
          </div>

          <div v-if="mode === 'unseal' && decryptedMessage" class="text-sm text-indigo-600 bg-indigo-50 border border-indigo-100 rounded-xl px-4 py-2 fade-in-up">
              <p class="text-xs uppercase tracking-wide text-indigo-600 mb-2 flex items-center gap-1">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
                소망 메시지
              </p>
              <p class="text-sm text-slate-900 whitespace-pre-wrap">{{ decryptedMessage }}</p>
            </div>

          <div
            v-if="sealed"
            class="bg-slate-900 rounded-2xl p-4 text-white shadow-inner relative"
            :class="[
              sealing ? 'sealing-animation' : '',
              sealed ? 'sealed-animation' : ''
            ]"
          >
            <!-- Particle effects during sealing -->
            <div v-if="sealing" class="absolute inset-0 pointer-events-none">
              <div
                v-for="i in 8"
                :key="i"
                class="particle"
                :style="{
                  left: `${Math.random() * 100}%`,
                  bottom: '20%',
                  animationDelay: `${i * 0.1}s`
                }"
              ></div>
            </div>

            <div class="flex items-center justify-between mb-3 relative z-10">
              <div>
                <p class="text-xs uppercase tracking-wide text-slate-300">타임캡슐 메시지</p>
              </div>
              <div class="flex items-center gap-2">
                <button
                  v-if="encryptedHash"
                  type="button"
                  class="text-xs font-semibold px-3 py-1 rounded-full bg-white/10 hover:bg-white/20 text-white transition"
                  @click="copyEncryptedData"
                >
                  {{ copiedEncrypted ? '복사됨!' : '복사' }}
                </button>
              </div>
            </div>
            <p
              class="font-mono text-xs sm:text-sm break-all text-emerald-100 relative z-10"
              :class="sealing ? 'scrambling' : ''"
            >
              <span v-if="encryptedHash">{{ encryptedHash }}</span>
              <span v-else>소망 메시지를 입력하면 암호화된 데이터가 나타납니다.</span>
            </p>
          </div>
        </div>
      </div>
    </div>

  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const secretKey = ref('')
const wishMessage = ref('')
const privateKey = ref('')
const publicKey = ref('')
const encryptedHash = ref('')
const lastUpdated = ref(null)
const computing = ref(false)
const errorMessage = ref('')
const showSecret = ref(true)

// Decryption states
const decryptKey = ref('')
const encryptedDataInput = ref('')
const decryptedMessage = ref('')
const decrypting = ref(false)
const decryptError = ref('')
const showDecryptSecret = ref(false)

// UI states
const copiedEncrypted = ref(false)
const sealing = ref(false)
const sealed = ref(false)
const opening = ref(false)
const opened = ref(false)
const mode = ref('seal') // 'seal' or 'unseal'

const messageLimit = 280

const hasSecret = computed(() => secretKey.value.trim().length > 0)
const hasMessage = computed(() => wishMessage.value.trim().length > 0)
const capsuleReady = computed(() => hasSecret.value && hasMessage.value && !!encryptedHash.value && sealed.value)

const statusLabel = computed(() => {
  if (!hasSecret.value) return '대기 중'
  if (computing.value) return '암호화 중'
  if (capsuleReady.value) return '봉인 완료'
  return '입력 대기'
})

const statusDescription = computed(() => {
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
  if (!hasSecret.value) return 'bg-slate-100 text-slate-700'
  if (computing.value) return 'bg-amber-100 text-amber-700 border border-amber-200'
  if (capsuleReady.value) return 'bg-emerald-100 text-emerald-700 border border-emerald-200'
  return 'bg-indigo-100 text-indigo-700 border border-indigo-200'
})

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
})

onBeforeUnmount(() => {
  if (recomputeTimer) clearTimeout(recomputeTimer)
})

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

function switchMode(newMode) {
  mode.value = newMode
  // Reset states when switching modes
  sealing.value = false
  sealed.value = false
  opening.value = false
  opened.value = false
  errorMessage.value = ''
  decryptError.value = ''
  decryptedMessage.value = ''
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
    errorMessage.value = '복호화에 실패했습니다. 비밀키가 올바른지 확인해주세요.'
    opening.value = false
  }
}

async function copyEncryptedData() {
  if (!encryptedHash.value) return

  try {
    await navigator.clipboard.writeText(encryptedHash.value)
    copiedEncrypted.value = true
    setTimeout(() => {
      copiedEncrypted.value = false
    }, 2000)
  } catch (error) {
    console.error('Failed to copy:', error)
  }
}

async function triggerImmediateComputation() {
  if (recomputeTimer) clearTimeout(recomputeTimer)

  // Trigger sealing animation
  sealing.value = true
  sealed.value = false

  await runComputation()

  // Complete sealing animation after a delay
  setTimeout(() => {
    sealing.value = false
    sealed.value = true
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
    decryptError.value = '복호화에 실패했습니다. 비밀키가 올바른지 확인해주세요.'
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

// Derive AES key from secret passphrase (deterministic)
async function deriveEncryptionKey(secret) {
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
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt']
  )
}

// Encryption using AES-GCM (with key derived from secret)
async function encryptMessage(message, secret) {
  if (!globalThis.crypto || !globalThis.crypto.subtle) {
    throw new Error('Web Crypto API not supported')
  }

  // Derive encryption key from secret
  const key = await deriveEncryptionKey(secret)

  // Generate random IV
  const iv = globalThis.crypto.getRandomValues(new Uint8Array(12))

  // Encrypt message
  const encoded = textEncoder.encode(message)
  const encrypted = await globalThis.crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    encoded
  )

  // Combine IV + encrypted data
  const result = {
    iv: arrayBufferToBase64(iv),
    ciphertext: arrayBufferToBase64(new Uint8Array(encrypted))
  }

  return btoa(JSON.stringify(result))
}

// Decryption using AES-GCM
async function decryptMessage(encryptedData, secret) {
  if (!globalThis.crypto || !globalThis.crypto.subtle) {
    throw new Error('Web Crypto API not supported')
  }

  // Parse encrypted data
  const data = JSON.parse(atob(encryptedData))

  // Derive decryption key from secret
  const key = await deriveEncryptionKey(secret)

  // Decrypt message
  const iv = base64ToArrayBuffer(data.iv)
  const ciphertext = base64ToArrayBuffer(data.ciphertext)

  const decrypted = await globalThis.crypto.subtle.decrypt(
    { name: 'AES-GCM', iv },
    key,
    ciphertext
  )

  return new TextDecoder().decode(decrypted)
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
